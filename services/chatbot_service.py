#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Filename:    chatbot_service.py
# @Author:      Kuro
# @Time:        3/22/2025 7:27 PM

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
        {context_query}
        
        Relevant ESC Guidelines:
        {guidelines_text}
        
        Using the patient’s information and the ESC guidelines, write an answer in simple, clear, and reassuring language that is easy to understand for someone without medical training.

        Do not include citations, medical jargon, or any explanations of how you arrived at the answer.

        Just give the final answer in a way that helps the patient feel informed and supported. The response should be brief but not overly short—enough to feel complete and helpful.
        Do not show your reasoning or thinking process."""

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
        - Blood Pressure: {patient_data.get('systolic_bp')}/{patient_data.get('diastolic_bp')} mmHg
        - Respiratory Rate: {patient_data.get('respiratory_rate')} breaths/min
        - Oxygen Saturation: {patient_data.get('oxygen_saturation')}%
        - Temperature: {patient_data.get('temperature')} °C

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
        
        Based on the patient's clinical profile and the ESC guidelines, provide a medically accurate answer. Please structure your answer with headings and include a summary of the main points at the end.

        You may use appropriate medical terminology, include relevant citations from the ESC guidelines, and explain the clinical rationale where necessary.

        However, avoid including any meta-level reasoning or commentary about your thinking process—just provide the medically grounded recommendation or explanation supported by guideline references.
        Do not show your reasoning or thinking process."""

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
        st.subheader(f"Patient: {patient_data.get('name')}")
        st.write(f"Age: {patient_data.get('age')}")
        st.write(f"HF Type: {patient_data.get('hf_type')}")
        st.write(f"Current Medications: {patient_data.get('medications')}")

    # Chat interface
    user_query = st.text_input(
        "Ask a question about heart failure guidelines:")

    if user_query and mode == "Doctor":
        response = chatbot.generate_doc_response(patient_id, user_query)
        st.write(response)

    if user_query and mode == "Patient":
        response = chatbot.generate_patient_response(patient_id, user_query)
        st.write(response)

    # Close connections when done
    chatbot.close()
