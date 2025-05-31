import streamlit as st
import sqlite3
from pymilvus import connections, Collection
from sentence_transformers import SentenceTransformer
from configuration.config import EMBEDDING_MODEL, MILVUS_HOST, MILVUS_PORT, COLLECTION_NAME, CHATBOT_MODEL_NAME
import httpx


class ChatbotService:
    def __init__(self):
        # Initialize Milvus connection
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        self.collection = Collection(COLLECTION_NAME)
        self.collection.load()

        # Initialize embedding model
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)

        # Initialize SQLite connection
        self.conn = sqlite3.connect("patients.db")
        self.cursor = self.conn.cursor()

        # Initialize Groq client with httpx client
        try:
            from groq import Groq
            self.client = Groq(
                api_key="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",
                http_client=httpx.Client(verify=False)
            )
        except Exception as e:
            st.error(f"Failed to initialize Groq client: {str(e)}")
            self.client = None

        self.system_message = """You are a medical AI assistant specialized in heart failure.
        Respond only with a clear final answer based strictly on the ESC guidelines and the patient information provided.
        Do not include any internal thoughts, reasoning steps, or explanations of your thought process.
        Cite the ESC guideline sources briefly if relevant. Do not preface or summarize your reasoning."""

    def get_patient_data(self, patient_id):
        """Retrieve all patient data from normalized tables and return as a structured dictionary."""
        patient_data = {}

        # -------------------- Patients Table --------------------
        self.cursor.execute(
            "SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
        patient_info = self.cursor.fetchone()
        if not patient_info:
            return None  # Patient not found

        patient_columns = [desc[0] for desc in self.cursor.description]
        patient_data.update(dict(zip(patient_columns, patient_info)))

        # -------------------- Symptoms --------------------
        self.cursor.execute(
            "SELECT symptom, category, severity, duration FROM patient_symptoms WHERE patient_id = ?", (patient_id,))
        symptoms = self.cursor.fetchall()
        patient_data["symptoms"] = [
            {"symptom": row[0], "category": row[1],
                "severity": row[2], "duration": row[3]}
            for row in symptoms
        ]

        # -------------------- Comorbidities --------------------
        self.cursor.execute(
            "SELECT * FROM patient_comorbidities WHERE patient_id = ?", (patient_id,))
        comorbidities_row = self.cursor.fetchone()
        if comorbidities_row:
            comorbidity_columns = [desc[0] for desc in self.cursor.description]
            comorbidities_dict = dict(
                zip(comorbidity_columns, comorbidities_row))
            # Remove internal ID
            comorbidities_dict.pop("comorbidity_record_id", None)
            comorbidities_dict.pop("patient_id")  # Already captured
            patient_data["comorbidities"] = comorbidities_dict

            # -------------------- Comorbidity Details --------------------
            # comorbidity_record_id
            comorbidity_record_id = comorbidities_row[0]
            self.cursor.execute(
                "SELECT detail_key, detail_value FROM comorbidity_details WHERE comorbidity_record_id = ?", (comorbidity_record_id,))
            comorbidity_details = self.cursor.fetchall()
            patient_data["comorbidity_details"] = [
                {"detail_key": row[0], "detail_value": row[1]} for row in comorbidity_details
            ]
        else:
            patient_data["comorbidities"] = {}
            patient_data["comorbidity_details"] = []

        # -------------------- Cardiovascular Events --------------------
        self.cursor.execute(
            "SELECT event_key, event_present FROM cv_events WHERE patient_id = ?", (patient_id,))
        cv_events = self.cursor.fetchall()
        patient_data["cv_events"] = [
            {"event_key": row[0], "event_present": bool(row[1])} for row in cv_events
        ]

        if 'activity' in patient_data:
            patient_data['physical_activity'] = patient_data['activity']

        return patient_data

    def search_guidelines(self, query, top_k=5):
        """Search Milvus database for relevant guidelines"""
        # Generate embedding for the query
        query_embedding = self.embedder.encode(query).tolist()

        # Search parameters
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }

        # Perform the search
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text"]
        )

        return results[0]

    def generate_patient_response(self, patient_id, user_query):
        """Generate a response based on patient data and guidelines"""
        if not self.client:
            return "Error: Chatbot service is not properly initialized. Please try again later."

        # Get patient data
        patient_data = self.get_patient_data(patient_id)
        if not patient_data:
            return "Patient not found. Please check the patient ID."

       # Get patient data
        patient_data = self.get_patient_data(patient_id)
        if not patient_data:
            return "Patient not found. Please check the patient ID."

        # -------------------- Symptoms --------------------
        if patient_data.get("symptoms"):
            symptoms_formatted = "\n".join([
                f"  • {symptom['symptom']} (Severity: {symptom['severity']}, Duration: {symptom['duration']})"
                for symptom in patient_data["symptoms"]
            ])
        else:
            symptoms_formatted = "None reported."

        # -------------------- Comorbidities --------------------
        comorbidities = patient_data.get("comorbidities", {})
        comorbidities_formatted = ", ".join([
            key.replace("_", " ").capitalize()
            for key, present in comorbidities.items() if present
        ]) or "None reported."

        # -------------------- Comorbidity Details --------------------
        comorbidity_details = patient_data.get("comorbidity_details", [])
        comorbidity_details_formatted = "\n".join([
            f"  • {detail['detail_key']}: {detail['detail_value']}"
            for detail in comorbidity_details
        ]) if comorbidity_details else "None provided."

        # -------------------- Cardiovascular Events --------------------
        cv_events = patient_data.get("cv_events", [])
        cv_events_formatted = "\n".join([
            f"  • {event['event_key']}"
            for event in cv_events if event['event_present']
        ]) or "None reported."

        # -------------------- Other Patient-Reported Data --------------------
        alcohol_info = "Yes" if patient_data.get("alcohol") else "No"
        if patient_data.get("alcohol_frequency"):
            alcohol_info += f" ({patient_data['alcohol_frequency']})"

        smoking_info = "Yes" if patient_data.get("smoking") else "No"
        if patient_data.get("smoking_packs"):
            smoking_info += f", {patient_data['smoking_packs']} packs/day"
        if patient_data.get("smoking_duration"):
            smoking_info += f", for {patient_data['smoking_duration']} years"

        # -------------------- Build full context --------------------
        context_query = f"""
        Patient Information:
        - Name: {patient_data.get('patient_name')}
        - Age: {patient_data.get('age')}
        - Sex: {patient_data.get('sex')}
        - Height: {patient_data.get('height')} cm
        - Weight: {patient_data.get('weight')} kg
        - BMI: {patient_data.get('bmi')}
        - BMI Category: {next((d['detail_value'] for d in comorbidity_details if d['detail_key'] == 'BMI Classification'), 'Not provided')}

        - Alcohol Consumption: {alcohol_info}
        - Smoking: {smoking_info}

        - Physical Activity: {patient_data.get('physical_activity')}
        - Heart Failure Type (if known): {patient_data.get('hf_type')}

        - Symptoms:
        {symptoms_formatted}

        - Symptom Triggers: {patient_data.get('symptom_triggers', 'Not provided')}
        - Other Trigger Details: {patient_data.get('other_trigger_detail', 'None')}
        - Daily Impact: {patient_data.get('daily_impact', 'Not provided')}

        - Current Medications: {patient_data.get('medications')}
        - Other Medications: {patient_data.get('other_meds')}

        - Comorbidities: {comorbidities_formatted}
        - Comorbidity Details:
        {comorbidity_details_formatted}

        - Cardiovascular Events:
        {cv_events_formatted}

        Question: {user_query}
        """

        # Search for relevant guidelines
        search_results = self.search_guidelines(context_query)

        # Format the guidelines for the AI model
        guidelines_text = "\n\n".join([f"Guideline {i+1}: {hit.entity.get('text')}"
                                       for i, hit in enumerate(search_results)])

        # Create the prompt for Groq
        user_message = f"""
        Patient Information:
        {context_query}a
        
        Relevant ESC Guidelines:
        {guidelines_text}
        
        You are a caring medical assistant. Using the patient's information and the ESC guidelines, write a clear, concise, and reassuring answer for someone without medical training.
          Acknowledge the patient's concern in a warm tone.  
        - Explain why they're experiencing these symptoms in plain language.  
        - If their situation sounds urgent, recommend they seek immediate medical attention.  
        - Offer 4 practical tips they can try right away, present each tip in a comprehensive detailed way, why it helps, and how to do it, when you 
        give hydration advice: if the patient shows volume overload (edema, rapid weight gain) recommend ≤1.5 L/day.
        If he has stable volume status, normal kidney function and no restriction, suggest up to 2 L/day, recommend tracking daily weight, swelling and report sudden changes.  
        - If you haven't already urged a visit, list any "red-flag" signs that mean they should see a doctor, and briefly what the doctor would do.  
        - End with a one-sentence summary of the main points.

    Do not include citations, jargon, or your internal reasoning.
 """

        try:
            # Get response from Groq
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": user_message}
            ]

            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=CHATBOT_MODEL_NAME
            )

            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def generate_doc_response(self, patient_id, user_query):
        """Generate a response based on patient data and guidelines"""
        if not self.client:
            return "Error: Chatbot service is not properly initialized. Please try again later."

        # Get patient data
        patient_data = self.get_patient_data(patient_id)
        if not patient_data:
            return "Patient not found. Please check the patient ID."

        # -------------------- Symptoms --------------------
        if patient_data.get("symptoms"):
            symptoms_formatted = "\n".join([
                f"  • {symptom['symptom']} (Severity: {symptom['severity']}, Duration: {symptom['duration']})"
                for symptom in patient_data["symptoms"]
            ])
        else:
            symptoms_formatted = "None reported."

        # -------------------- Comorbidities --------------------
        comorbidities = patient_data.get("comorbidities", {})
        comorbidities_formatted = ", ".join([
            key.replace("_", " ").capitalize()
            for key, present in comorbidities.items() if present
        ]) or "None reported."

        # -------------------- Comorbidity Details --------------------
        comorbidity_details = patient_data.get("comorbidity_details", [])
        comorbidity_details_formatted = "\n".join([
            f"  • {detail['detail_key']}: {detail['detail_value']}"
            for detail in comorbidity_details
        ]) if comorbidity_details else "None provided."

        # -------------------- Cardiovascular Events --------------------
        cv_events = patient_data.get("cv_events", [])
        cv_events_formatted = "\n".join([
            f"  • {event['event_key']}"
            for event in cv_events if event['event_present']
        ]) or "None reported."

        # -------------------- Build full context --------------------
        context_query = f"""
        Patient Information (Doctor Input):
        - Name: {patient_data.get('patient_name')}
        - Age: {patient_data.get('age')}
        - Sex: {patient_data.get('sex')}
        - Height: {patient_data.get('height')} cm
        - Weight: {patient_data.get('weight')} kg
        - BMI: {patient_data.get('bmi')}

        - Heart Rate: {patient_data.get('heart_rate')} bpm
        - Rhythm: {patient_data.get('rhythm')}
        - Blood Pressure: {patient_data.get('systolic_bp')}/{patient_data.get('diastolic_bp')} mmHg
        - Respiratory Rate: {patient_data.get('respiratory_rate')} breaths/min
        - Oxygen Saturation: {patient_data.get('oxygen_saturation')}%
        - Temperature: {patient_data.get('temperature')} °C

        - Peripheral Edema: {patient_data.get('edema_locations')} (Grade: {patient_data.get('edema_grade')})
        - JVP: {patient_data.get('jvp')}
        - Hepatomegaly: {patient_data.get('hepatomegaly')} {f"({patient_data.get('hepatomegaly_span')} cm)" if patient_data.get('hepatomegaly') == 'Yes' and patient_data.get('hepatomegaly_span') else ''}
        - Lung Auscultation: {patient_data.get('lung_findings')}
        - Heart Sounds: {patient_data.get('heart_sounds')}
        - Murmurs: {patient_data.get('murmurs')}
        - Other Murmur: {patient_data.get('murmur_other')}

        - Coronary Angiography: {patient_data.get('ca_findings')}
        - Coronary Angiography Other: {patient_data.get('ca_other_details')}
        - Cardiac MRI: {patient_data.get('mri_findings')}
        - Cardiac MRI Other: {patient_data.get('mri_other_details')}
        - Holter Monitor: {patient_data.get('holter_findings')}
        - Holter Monitor Other: {patient_data.get('holter_other_details')}

        - Heart Failure Type: {patient_data.get('hf_type')}
        - LVEF: {patient_data.get('lvef')}%
        - NYHA Class: {patient_data.get('nyha')}
        - BNP / NT-proBNP: {patient_data.get('bnp')}

        - Symptoms (Clinical Assessment):
        {symptoms_formatted}

        - Symptom Triggers: {patient_data.get('symptom_triggers', 'Not provided')}
        - Other Trigger Details: {patient_data.get('other_trigger_detail', 'None')}
        - Daily Impact: {patient_data.get('daily_impact', 'Not provided')}

        - Current Medications: {patient_data.get('medications')}
        - Other Medications: {patient_data.get('other_meds')}

        - Recent Lab Results:
        • Creatinine: {patient_data.get('creatinine')} mg/dL
        • Potassium: {patient_data.get('potassium')} mmol/L
        • Sodium: {patient_data.get('sodium')} mmol/L
        • Anemia Status: {patient_data.get('anemia_status')}
        • Iron Supplementation: {"Yes" if patient_data.get('iron_supplement') else "No"}
        • Ferritin Issue: {"Yes" if patient_data.get('ferritin_issue') else "No"}

        - Functional Assessment:
        • 6-Minute Walk Test: {patient_data.get('walk_test')} meters
        • VO2 Max: {patient_data.get('vo2_max')} ml/kg/min

        - Device Therapy: {patient_data.get('devices')}
        - ECG Findings: {patient_data.get('ecg')}
        - Echo Findings: {patient_data.get('echo')}
        - Other Echo Findings: {patient_data.get('echo_other')}

        - Comorbidities: {comorbidities_formatted}
        - Comorbidity Details:
        {comorbidity_details_formatted}

        - Cardiovascular Events:
        {cv_events_formatted}

        - Treatment Plan / Follow-up: {patient_data.get('follow_plan')}

        Question: {user_query}
        """

        # Search for relevant guidelines
        search_results = self.search_guidelines(context_query)

        # Format the guidelines for the AI model
        guidelines_text = "\n\n".join([f"Guideline {i+1}: {hit.entity.get('text')}"
                                       for i, hit in enumerate(search_results)])

        # Create the prompt for Groq
        user_message = f"""
        Patient Information:
        {context_query}
        
        Relevant ESC Guidelines:
        {guidelines_text}
        
        You are a cardiology AI assistant. Based on the patient's form data and the latest ESC heart failure guidelines, provide a concise, clinically actionable answer to the physician's question.  

        **Provide a consise summary of the patient's case**
        **Answer the Question First**  
        Begin with a direct response to the doctor's inquiry.  

        **Medication Optimization**  
        - If dose adjustment is indicated, specify "Increase [drug] by X mg every Y weeks until reaching a target dose of Z mg daily" (e.g. metoprolol uptitration; ESC §5.2.2).  
        - If switching therapies, include required wash-out periods (e.g. 36 hours between ACE-I and ARNI; ESC §5.2.2).  

        **Laboratory & Safety Monitoring**  
        - Recommend checks of renal function (creatinine/eGFR), electrolytes (potassium, sodium), and BNP/NT-proBNP.  
        - Tie frequency to medication changes (e.g. "Check creatinine and potassium at baseline, 1–2 weeks after each dose change, then every 3 months").  

        **Device Management & Referral**  
        - If ICD/CRT programming or implantation review is needed, state timing (e.g. "Refer for CRT evaluation if LVEF remains ≤ 35% after 3 months of OMT").  
        - Arrhythmia: "In AF with symptoms despite rate control, consider cardioversion or antiarrhythmic per ESC §X.X."  
        - Surgical/referral: "Refer for revascularization if multivessel CAD with LVEF < 35 %"

        **Lifestyle & Supportive Measures**  
        - Offer specific dietary guidance (e.g. "Restrict sodium to ≤ 2 g/day and fluid to X L/day based on volume status").  
        - Provide exercise prescription or referral to cardiac rehabilitation (e.g. "Begin supervised exercise 3 times/week for 12 weeks").  

        **Comorbidity & Risk-Factor Control**  
        - List only relevant targets (e.g. "Aim for BP < 130/80 mmHg with uptitration of ACE-I").  
        - Advise on diabetes, lipids, smoking, etc., if present.  

        **Advanced & Procedural Interventions**  
        - If revascularization is indicated, specify PCI vs. CABG referral criteria (e.g. "Refer for CABG in multivessel disease with LVEF < 35%").  
        - Note valve, LVAD or transplant evaluation triggers if applicable.  

        **Summary**  
        - End with a brief bulleted recap of the plan.

        **Instructions:**  
        - Only surface recommendations from sections above that apply to this patient, so choose only the relevant sections and be detailed and comprehensive in each section, and provide a medical rationale for the actions you recommend.
        - If there is more than one recommendation, Indicate which intervention to tackle first (e.g. "First address volume overload with diuretic uptitration, then consider X"). 
        - Only when relevant, warn about possible risks for you recommendation or intervention and what to do if they occur (ex. Hypotension , over-diuresis)
        - Cite specific ESC guideline section numbers after each recommendation and at the end.
        - Do **not** include your reasoning or internal thought process—deliver only the final, guideline-based plan.  
"""

        try:
            # Get response from Groq
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": user_message}
            ]

            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=CHATBOT_MODEL_NAME
            )

            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def close(self):
        """Close database connections"""
        self.conn.close()
        connections.disconnect("default")

# Streamlit UI for the chatbot


def chat_interface(patient_id, mode):
    st.title("Heart Failure Guidelines Chatbot")

    # Initialize chatbot service
    chatbot = ChatbotService()

    # Display patient info
    patient_data = chatbot.get_patient_data(patient_id)
    if patient_data:
        st.subheader(f"Patient: {patient_data.get('patient_name')}")
        st.write(f"Age: {patient_data.get('age')}")
        st.write(f"HF Type: {patient_data.get('hf_type')}")
        st.write(f"Current Medications: {patient_data.get('medications')}")

    # Initialize chat history in session state if it doesn't exist
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Chat interface
    user_query = st.text_input(
        "Ask a question about heart failure guidelines:",
        key=f"chat_input_{patient_id}_{mode}"
    )

    # Process the query when Enter is pressed
    if user_query:
        if mode == "Doctor":
            response = chatbot.generate_doc_response(patient_id, user_query)
        else:
            response = chatbot.generate_patient_response(
                patient_id, user_query)

        # Add the exchange to chat history
        st.session_state.chat_history.append(
            {"user": user_query, "assistant": response})

        # Display chat history
        for exchange in st.session_state.chat_history:
            st.write("You:", exchange["user"])
            st.write("Assistant:", exchange["assistant"])
            st.write("---")

    # Close connections when done
    chatbot.close()
