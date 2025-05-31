import streamlit as st
import sqlite3
from form import save_patient, save_patient_data, save_consent, withdraw_consent_and_delete_data, log_consent_action
from services.chatbot_service import chat_interface
from visual_summary_utilities import show_visual_summary
from datetime import datetime

st.title("Heart Failure Patient Information Form")
# Mode selection: Patient or Doctor
mode = st.radio("Choose form mode:", ("Patient", "Doctor"))

# Initialize session state variables if they don't exist
if 'patient_id' not in st.session_state:
    st.session_state['patient_id'] = None
if 'show_visual_summary' not in st.session_state:
    st.session_state['show_visual_summary'] = False

# --- Patient Form ---
if mode == "Patient":
    st.subheader("Consent")

    # Required consent for clinical care
    clinical_care_consent = st.checkbox(
        "I consent to the collection and use of my medical data for diagnosis, treatment, and ongoing care.",
        help="This consent is required to use the system."
    )

    # Optional consents
    quality_research_consent = st.checkbox(
        "I consent to the de-identified use of my health data for internal quality-improvement and medical research.",
        help="This consent is optional."
    )

    ai_training_consent = st.checkbox(
        "I consent to the de-identified use of my health data to train and improve AI models.",
        help="This consent is optional."
    )

    if not clinical_care_consent:
        st.warning(
            "Please provide consent for clinical care to proceed with the form.")
    else:
        st.subheader("Patient Demographics")
        patient_name = st.text_input("Name")
        age = st.number_input("Age", min_value=0, max_value=120, key="age")
        sex = st.selectbox("Sex", ["Male", "Female", "Other"])
        height = st.number_input("Height (cm)", min_value=0.0, key="height")
        weight = st.number_input("Weight (kg)", min_value=0.0, key="weight")
        bmi = round(weight / ((height / 100) ** 2), 2) if height > 0 else 0
        st.text(f"BMI: {bmi}")

        if bmi > 0:
            if bmi < 25:
                bmi_category = "Normal"
            elif bmi < 30:
                bmi_category = "Overweight (25–29.9)"
            elif bmi < 35:
                bmi_category = "Obesity Class I (30–34.9)"
            elif bmi < 40:
                bmi_category = "Obesity Class II (35–39.9)"
            else:
                bmi_category = "Obesity Class III (≥40)"
            st.text(f"BMI Category: {bmi_category}")
        else:
            bmi_category = None

        # -------------------- Risk Factors (Comorbidities) --------------------
        st.subheader("Risk Factors")

        hypertension = st.checkbox("Hypertension")

        diabetes = st.checkbox("Diabetes")
        diabetes_type = st.selectbox(
            "Type of Diabetes", ["Type 1", "Type 2"]) if diabetes else None

        dyslipidemia = st.checkbox("Dyslipidemia")
        obesity = st.checkbox("Obesity")

        alcohol = st.checkbox("Alcohol Consumption")
        alcohol_frequency = st.selectbox("How often do you drink alcohol?", [
            "Rarely (a few times a year)",
            "Occasionally (1–3 times/month)",
            "Regularly (1–3 times/week)",
            "Frequently (daily or almost daily)"
        ]) if alcohol else None

        smoking = st.checkbox("Smoking")
        smoking_packs = st.number_input(
            "Packs per day:", min_value=0.0, step=0.1, key="smoking_packs") if smoking else None
        smoking_duration = st.number_input(
            "Smoking duration (years):", min_value=0, key="smoking_duration") if smoking else None

        family_history = st.checkbox("Family History of Heart Disease")
        family_details = st.text_input(
            "Relationship(s)") if family_history else None

        # -------------------- Type of Heart Failure --------------------
        st.subheader("Type of Heart Failure (If known)")
        hf_types = st.multiselect("Select type(s) of heart failure", [
            "Ischemic Heart Failure",
            "Dilated Cardiomyopathy (DCM)",
            "Hypertrophic Cardiomyopathy (HCM)",
            "Valvular Heart Disease",
            "Peripartum Cardiomyopathy",
            "Genetic Cardiomyopathy"
        ])
        hf_type = ",".join(hf_types) if hf_types else None

        # -------------------- Symptoms --------------------
        st.subheader("Symptoms")
        symptoms = st.multiselect("Check all that apply", [
            "Shortness of Breath (Dyspnea)",
            "Orthopnea",
            "Waking up at night feeling short of breath",
            "Chest pain",
            "Pulmonary Edema",
            "Fatigue and Weakness",
            "Lower limb swelling",
            "Palpitations",
            "Persistent Coughing or Wheezing",
            "Increased Need to Urinate at Night",
            "Difficulty Concentrating or Decreased Alertness",
            "Lack of Appetite and Nausea",
            "Depression or mood issues",
            "Anxiety and Emotional stress"
        ])

        symptom_severities = {}
        for symptom in symptoms:
            severity = st.slider(f"Severity of '{symptom}'", 1, 5, 3)
            symptom_severities[symptom] = severity

        st.subheader("Symptom Onset")
        onset_value = st.number_input(
            "How long have you had these symptoms?", min_value=0, value=None, key="onset_value")
        onset_unit = st.selectbox(
            "Time unit", ["days", "weeks", "months", "years"])
        symptom_onset = f"{onset_value} {onset_unit}" if onset_value else None

        # Store individual symptoms
        patient_individual_symptoms = []
        for symptom in symptoms:
            patient_individual_symptoms.append({
                "symptom": symptom,
                "severity": symptom_severities.get(symptom, None),
                "duration": symptom_onset,
                "category": "Patient Reported"
            })

        # -------------------- Symptom Triggers --------------------
        st.subheader("Symptom Triggers")
        triggers = st.multiselect("What situations make your symptoms worse?", [
            "Lying down",
            "Physical activity",
            "Emotional stress",
            "Cold weather",
            "After meals",
            "None",
            "Other"
        ])
        symptom_triggers_str = ",".join(triggers) if triggers else None
        other_trigger_detail = st.text_input(
            "Please describe other triggers (optional)") if "Other" in triggers else None

        # -------------------- Impact --------------------
        st.subheader("Impact on Daily Life")
        impact = st.selectbox("How much do your symptoms affect your daily life?", [
            "Not at all",
            "Mildly – I can still do most activities",
            "Moderately – I need to rest or avoid certain things",
            "Severely – I struggle with daily activities"
        ])

        st.subheader("Signs")
        heart_rate = st.number_input(
            "Heart Rate (bpm)", min_value=0, value=None)
        rhythm = st.selectbox(
            "Rhythm",
            ["Regular", "Irregular"]
        )
        systolic_bp = st.number_input(
            "Systolic BP (mmHg)", min_value=0, value=None)
        diastolic_bp = st.number_input(
            "Diastolic BP (mmHg)", min_value=0, value=None)
        respiratory_rate = st.number_input(
            "Respiratory Rate (breaths/min)", min_value=0, value=None)
        oxygen_saturation = st.number_input(
            "Oxygen Saturation (%)", min_value=0.0, max_value=100.0, value=None)
        temperature = st.number_input(
            "Temperature (°C)", min_value=30.0, max_value=45.0, value=None)

        # -------------------- Treatment --------------------
        st.subheader("Treatment Information")
        meds = st.multiselect("Current Heart failure medications:", [
            "ACE Inhibitors / ARBs / ARNI",
            "Beta Blockers",
            "Diuretics",
            "MRAs",
            "SGLT2 Inhibitors",
            "Ivabradine",
            "Antiplatelet",
            "Anticoagulant",
            "Lipid lowering",
            "Antiarrhythmic"
        ])
        medications_str = ",".join(meds) if meds else None
        other_meds = st.text_input("Other medications taken:")

        # -------------------- Physical Activity --------------------
        st.subheader("Physical Activity")
        activity = st.selectbox("Level of physical activity", [
            "None - Sedentary lifestyle, minimal movement",
            "Light activity - Occasional walking or household chores",
            "Moderate activity - Regular walking, light exercise 3-4 days/week",
            "High - Frequent workouts or physically demanding job"
        ])

        # -------------------- Submit --------------------
        if st.button("Submit Patient Form"):
            try:
                # Step 1: Save patient core info
                patient_id = save_patient(
                    patient_name, age, sex, height, weight, bmi,
                    heart_rate, rhythm, systolic_bp, diastolic_bp, respiratory_rate,
                    oxygen_saturation, temperature, None, None, None, None, None, None, None, None, None,
                    hf_type, None, None, None, None,
                    symptom_triggers_str if symptom_triggers_str else None,
                    other_trigger_detail, impact,
                    alcohol, alcohol_frequency,
                    smoking, smoking_packs, smoking_duration, activity,
                    medications_str, other_meds,
                    None, None, None,  # Labs (creatinine, potassium, sodium)
                    # Anemia related (anemia_status, anemia_present, iron_supplement, ferritin_issue)
                    None, None, None, None,
                    # Functional assessment (walk_test, vo2_max, devices_str)
                    None, None, None,
                    # Diagnostics (ecg, echo_str, echo_other)
                    None, None, None,
                    # Additional diagnostics (ca_findings, ca_other_details, mri_findings, mri_other_details)
                    None, None, None, None,
                    # More diagnostics (holter_findings, holter_other_details)
                    None, None,
                    None  # Follow-up plan
                )

                # Step 2: Save consent data
                save_consent(patient_id, clinical_care_consent,
                             quality_research_consent, ai_training_consent)

                # Step 3: Save comorbidities (flags)
                patient_comorbidities_data = {
                    "Hypertension": hypertension,
                    "Diabetes": diabetes,
                    "Dyslipidemia": dyslipidemia,
                    "Kidney Disease": None,
                    "Obesity": obesity,
                    "Sleep Apnea": None,
                    "Family History of Heart Disease": family_history
                }

                # Step 4: Save comorbidity details
                patient_comorbidity_details = []
                if diabetes_type:
                    patient_comorbidity_details.append(
                        {"detail_key": "Diabetes Type", "detail_value": f"{diabetes_type} years"})
                if family_details:
                    patient_comorbidity_details.append(
                        {"detail_key": "Family History Details", "detail_value": family_details})
                if bmi_category:
                    patient_comorbidity_details.append(
                        {"detail_key": "BMI Classification", "detail_value": bmi_category})

                # Step 5: Insert into related tables
                save_patient_data(
                    patient_id,
                    patient_individual_symptoms,
                    patient_comorbidities_data,
                    patient_comorbidity_details,
                    {}  # No CV events for patient form
                )

                st.success(
                    f"✅ Patient form submitted. Patient ID: {patient_id}")
                st.session_state['patient_id'] = patient_id

            except Exception as e:
                st.error(f"Error submitting form: {str(e)}")

    # Add chatbot interface when patient_id is in session state
    if 'patient_id' in st.session_state:
        chat_interface(st.session_state['patient_id'], mode)

        # Consent Management Section
        if st.session_state['patient_id']:
            st.write("---")
            st.subheader("Consent Management")

            # Get current consent status
            try:
                # Initialize withdrawal state if not exists
                if 'withdrawal_started' not in st.session_state:
                    st.session_state.withdrawal_started = False

                # Clinical Care Consent (Required)
                st.write("#### Clinical Care Consent")
                if clinical_care_consent:
                    st.success("✓ Clinical care consent is active")

                    if not st.session_state.withdrawal_started:
                        if st.button("Withdraw Consent", key="withdraw_button"):
                            st.session_state.withdrawal_started = True
                            st.rerun()
                    else:
                        st.info(
                            "Note: Withdrawing clinical care consent will remove the patient's data from our system.")
                        confirm = st.checkbox(
                            "I understand that this will remove the patient's data", key="confirm_checkbox")

                        if confirm:
                            if st.button("Confirm Deletion", key="confirm_delete"):
                                try:
                                    # Delete data from local database
                                    withdraw_consent_and_delete_data(
                                        st.session_state['patient_id'])

                                    # Clear all session state
                                    for key in list(st.session_state.keys()):
                                        del st.session_state[key]
                                    st.rerun()
                                except Exception as e:
                                    st.error(
                                        f"Error withdrawing consent: {str(e)}")

                            if st.button("Cancel", key="cancel_withdrawal"):
                                st.session_state.withdrawal_started = False
                                st.rerun()
                else:
                    st.warning("Clinical care consent is not active")

                # Quality Research Consent (Optional)
                st.write("#### Quality Research Consent")
                if quality_research_consent:
                    st.success("✓ Quality research consent is active")
                    if st.button("Withdraw Quality Research Consent", key="withdraw_quality"):
                        try:
                            # Update consent status
                            log_consent_action(
                                st.session_state['patient_id'],
                                "quality_research",
                                False
                            )
                            st.success("Quality research consent withdrawn.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error withdrawing consent: {str(e)}")
                else:
                    st.info("Quality research consent is not active")

                # AI Training Consent (Optional)
                st.write("#### AI Training Consent")
                if ai_training_consent:
                    st.success("✓ AI training consent is active")
                    if st.button("Withdraw AI Training Consent", key="withdraw_ai"):
                        try:
                            # Update consent status
                            log_consent_action(
                                st.session_state['patient_id'],
                                "ai_training",
                                False
                            )
                            st.success("AI training consent withdrawn.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error withdrawing consent: {str(e)}")
                else:
                    st.info("AI training consent is not active")

            except Exception as e:
                st.error(f"Error managing consents: {str(e)}")

# --- Doctor Form Modes ---
elif mode == "Doctor":
    st.subheader("Doctor Options")
    doctor_action = st.radio("Choose action:", [
        "Create New Patient", "Choose Existing Patient", "General Questioning"])

    if doctor_action == "Create New Patient":
        # -------------------- Consent Section --------------------
        st.subheader("Patient Consent")

        # Required consent for clinical care
        clinical_care_consent = st.checkbox(
            "Patient consents to collection, storage, and processing of their medical data for diagnosis, treatment, and care.",
            help="This consent is required to use the system."
        )

        # Optional consents
        quality_research_consent = st.checkbox(
            "Patient consents to de-identified use of their data for research and quality improvement.",
            help="This consent is optional."
        )

        ai_training_consent = st.checkbox(
            "Patient consents to de-identified use of their data for AI model development.",
            help="This consent is optional."
        )

        if not clinical_care_consent:
            st.warning(
                "Please obtain patient consent for clinical care to proceed with the form.")
        else:
            # -------------------- Patient Overview --------------------
            st.subheader("Patient Overview")
            patient_name = st.text_input("Patient Name")
            age = st.number_input("Age", min_value=0, key="doc_age")
            sex = st.selectbox(
                "Sex", ["Male", "Female", "Other"], key="doc_sex")
            height = st.number_input(
                "Height (cm)", min_value=0.0, key="doc_height")
            weight = st.number_input(
                "Weight (kg)", min_value=0.0, key="doc_weight")
            bmi = round(weight / ((height / 100) ** 2), 2) if height > 0 else 0
            st.text(f"BMI: {bmi}")

            # -------------------- Vital Signs --------------------
            st.subheader("Vital Signs (Recent)")
            heart_rate = st.number_input(
                "Heart Rate (bpm)", min_value=0, value=None)
            rhythm = st.selectbox(
                "Rhythm",
                ["Regular", "Irregular"]
            )
            systolic_bp = st.number_input(
                "Systolic BP (mmHg)", min_value=0, value=None)
            diastolic_bp = st.number_input(
                "Diastolic BP (mmHg)", min_value=0, value=None)
            respiratory_rate = st.number_input(
                "Respiratory Rate (breaths/min)", min_value=0, value=None)
            oxygen_saturation = st.number_input(
                "Oxygen Saturation (%)", min_value=0.0, max_value=100.0, value=None)
            temperature = st.number_input(
                "Temperature (°C)", min_value=30.0, max_value=45.0, value=None)

            # -------------------- Physical Exam --------------------
            st.subheader("Physical Exam")

            # A. Peripheral Edema
            st.markdown("#### A. Peripheral Edema")
            edema_locations = st.multiselect(
                "Location(s):",
                ["Ankle", "Below knee", "Above knee",
                    "Lower abdominal wall", "Scrotal"]
            )
            edema_grade = st.selectbox(
                "Grade (pitting scale):",
                ["0", "1+", "2+", "3+", "4+"],
                index=0,
                help="Optional: Use if you assess pitting edema."
            )
            edema_locations_str = ",".join(
                edema_locations) if edema_locations else None

            # B. Jugular Venous Pressure
            st.markdown("#### B. Jugular Venous Pressure")
            jvp = st.radio(
                "JVP:",
                ["Non-congested", "Congested"],
                help=">3 cm above sternal angle is considered congested."
            )

            # C. Hepatomegaly
            st.markdown("#### C. Hepatomegaly")
            hepatomegaly = st.radio("Hepatomegaly:", ["No", "Yes"])
            hepatomegaly_span = None
            if hepatomegaly == "Yes":
                hepatomegaly_span = st.number_input(
                    "Span (cm below costal margin):", min_value=0.0, step=0.1
                )

            # D. Lung Auscultation
            st.markdown("#### D. Lung Auscultation")
            lung_findings = st.multiselect(
                "Findings:",
                ["Basal rales", "Mid-zone rales", "Pulmonary edema crackles"]
            )
            lung_findings_str = ",".join(
                lung_findings) if lung_findings else None

            # E. Cardiac Auscultation
            st.markdown("#### E. Cardiac Auscultation")
            heart_sounds = st.multiselect(
                "Heart sounds:",
                ["S1", "S2", "S3", "S4"]
            )
            heart_sounds_str = ",".join(heart_sounds) if heart_sounds else None
            murmurs = st.multiselect(
                "Murmurs:",
                ["Mitral regurgitation", "Aortic stenosis",
                    "Tricuspid regurgitation", "Other"]
            )
            murmurs_str = ",".join(murmurs) if murmurs else None
            murmur_other = None
            if "Other" in murmurs:
                murmur_other = st.text_input("Other murmur (specify):")

            # -------------------- History --------------------
            st.subheader("History")
            st.subheader("Symptoms")
            symptom_duration = st.selectbox("When did symptoms begin?", [
                "No symptoms", "Acute (within days)", "Subacute (1–4 weeks)", "Chronic (>1 month)", "Unclear"
            ])

            individual_symptoms = []

            def collect_symptoms(symptom_list, category):
                for symptom in symptom_list:
                    severity = st.slider(f"{symptom} severity",
                                         1, 5, 3, key=f"{symptom}_severity")
                    individual_symptoms.append({
                        "symptom": symptom,
                        "severity": severity,
                        "duration": symptom_duration,
                        "category": category
                    })

            cardiopulmonary_symptoms = st.multiselect("Cardiopulmonary Symptoms", [
                "Dyspnea (shortness of breath)",
                "Orthopnea",
                "Paroxysmal Nocturnal Dyspnea (PND)",
                "Chest pain or discomfort",
                "Palpitations",
                "Persistent cough or wheezing",
                "Exercise intolerance"
            ])
            systemic_symptoms = st.multiselect("Systemic & Functional Symptoms", [
                "Fatigue or weakness",
                "Peripheral edema",
                "Sudden weight gain",
                "Decreased alertness or confusion",
                "Syncope or dizziness"
            ])
            gastrointestinal_symptoms = st.multiselect("Gastrointestinal / Renal Symptoms", [
                "Nausea or poor appetite",
                "Early satiety (feeling full quickly)",
                "Nocturia",
                "Abdominal discomfort or bloating"
            ])

            collect_symptoms(cardiopulmonary_symptoms, "Cardiopulmonary")
            collect_symptoms(systemic_symptoms, "Systemic & Functional")
            collect_symptoms(gastrointestinal_symptoms,
                             "Gastrointestinal / Renal")

            # -------------------- Symptom Triggers --------------------
            st.subheader("Additional Symptom Context")
            symptom_triggers = st.multiselect("What triggers or worsens symptoms?", [
                "Physical exertion",
                "Lying down",
                "Emotional stress",
                "Cold exposure",
                "Large meals",
                "Nighttime",
                "Unspecified",
                "Other"
            ])
            other_trigger_detail = st.text_input(
                "Describe other trigger (optional)") if "Other" in symptom_triggers else None

            daily_impact = st.selectbox("How are daily activities affected?", [
                "No impact",
                "Mild – Can perform daily tasks with some fatigue",
                "Moderate – Avoids physical activities",
                "Severe – Needs assistance for most tasks"
            ])

            # -------------------- Lifestyle --------------------
            st.subheader("Lifestyle")
            alcohol = st.checkbox("Alcohol Consumption")
            alcohol_frequency = st.selectbox("How often do you drink alcohol?", [
                "Rarely (a few times a year)",
                "Occasionally (1–3 times/month)",
                "Regularly (1–3 times/week)",
                "Frequently (daily or almost daily)"
            ]) if alcohol else None

            smoking = st.checkbox("Smoking")
            smoking_packs = st.number_input(
                "Packs per day:", min_value=0.0, step=0.1) if smoking else None
            smoking_duration = st.number_input(
                "Smoking duration (years):", min_value=0) if smoking else None

            # -------------------- Physical Activity --------------------
            st.subheader("Physical Activity")
            activity = st.selectbox("Level of physical activity", [
                "None - Sedentary lifestyle, minimal movement",
                "Light activity - Occasional walking or household chores",
                "Moderate activity - Regular walking, light exercise 3-4 days/week",
                "High - Frequent workouts or physically demanding job"
            ])

            # -------------------- Comorbidities --------------------
            st.subheader("Comorbidities")
            comorbidities = st.multiselect("Check all that apply", [
                "Hypertension",
                "Diabetes",
                "Dyslipidemia",
                "Kidney Disease",
                "Obesity",
                "Sleep Apnea",
                "Family History of Heart Disease"
            ])

            # Follow-up variables:
            bp_control = None
            end_organ_damage = None
            diabetes_type = None
            hba1c_range = None
            diabetes_complications = None
            lipid_control = None
            lipid_treatment = None
            egfr_range = None
            dialysis = None
            bmi_classification = None
            weight_loss_plan = None
            sleep_study = None
            sleep_apnea_type = None
            sleep_apnea_treatment = None
            family_details = None

            if "Hypertension" in comorbidities:
                bp_control = st.selectbox("Blood pressure control", [
                                          "Controlled (<140/90)", "Uncontrolled"])
                end_organ_damage = st.multiselect(
                    "Signs of end-organ damage", ["LVH", "Proteinuria", "Retinopathy"])
            if "Diabetes" in comorbidities:
                diabetes_type = st.selectbox(
                    "Type of Diabetes", ["Type 1", "Type 2"])
                hba1c_range = st.selectbox(
                    "HbA1c range", ["<6.5%", "6.5–7.5%", ">7.5%"])
                diabetes_complications = st.multiselect(
                    "Diabetic complications", ["Neuropathy", "Nephropathy", "Retinopathy"])
            if "Dyslipidemia" in comorbidities:
                lipid_control = st.selectbox(
                    "Lipid control", ["Controlled", "Uncontrolled"])
                lipid_treatment = st.multiselect(
                    "Treatment", ["Statins", "PCSK9 inhibitors", "Lifestyle only"])
            if "Kidney Disease" in comorbidities:
                egfr_range = st.selectbox("eGFR Range", [
                                          ">90 (Normal)", "60–89 (Mild)", "30–59 (Moderate)", "<30 (Severe)"])
                dialysis = st.selectbox("On Dialysis", ["No", "Yes"])
            if "Obesity" in comorbidities:
                bmi_classification = st.selectbox("BMI Classification", ["Overweight (25–29.9)",
                                                                         "Obesity Class I (30–34.9)",
                                                                         "Obesity Class II (35–39.9)",
                                                                         "Obesity Class III (≥40)"])
                weight_loss_plan = st.checkbox("Weight loss plan advised")
            if "Sleep Apnea" in comorbidities:
                sleep_study = st.checkbox("Diagnosed via sleep study")
                sleep_apnea_type = st.selectbox(
                    "Type of Sleep Apnea", ["Obstructive", "Central"])
                sleep_apnea_treatment = st.selectbox(
                    "Treatment", ["On CPAP", "Not treated"])
            if "Family History of Heart Disease" in comorbidities:
                family_details = st.text_input("Relationship(s)")

            # -------------------- Medications --------------------
            st.subheader("Current Medications")

            # Dictionary to store medication selections and dosages
            medications_data = {}

            # Define drug classes and their medications
            drug_classes = {
                "ACE Inhibitors": ["Lisinopril", "Ramipril", "Captopril"],
                "ARBs": ["Losartan", "Valsartan", "Candesartan"],
                "ARNI": ["Sacubitril + Valsartan"],
                "Beta-Blockers": ["Metoprolol", "Bisoprolol", "Carvedilol"],
                "Diuretics": ["Furosemide", "Hydrochlorothiazide", "Torasemide"],
                "MRAs": ["Spironolactone", "Eplerenone", "Finerenone"],
                "SGLT2 Inhibitors": ["Empagliflozin", "Dapagliflozin", "Canagliflozin"],
                "Ivabradine": ["Ivabradine"],
                "Antiplatelet Agents": ["Aspirin (acetylsalicylic acid)", "Clopidogrel", "Ticagrelor"],
                "Anticoagulants": ["Warfarin", "Rivaroxaban", "Apixaban"],
                "Lipid-Lowering Agents": ["Atorvastatin", "Simvastatin", "Rosuvastatin"],
                "Antiarrhythmics": ["Amiodarone", "Sotalol", "Flecainide"]
            }

            # Initialize session state for medications if not exists
            if 'medications' not in st.session_state:
                st.session_state.medications = {}

            # Multiselect for drug classes
            selected_classes = st.multiselect(
                "Select Drug Classes",
                list(drug_classes.keys()),
                key="drug_classes"
            )

            # Remove medications for classes that are no longer selected
            for class_name in list(st.session_state.medications.keys()):
                if class_name not in selected_classes:
                    del st.session_state.medications[class_name]

            # For each selected class, show medication selection and dosage
            for class_name in selected_classes:
                st.write(f"**{class_name}**")
                col1, col2 = st.columns([2, 1])

                with col1:
                    specific_drug = st.selectbox(
                        f"Select {class_name}",
                        drug_classes[class_name],
                        key=f"drug_{class_name}"
                    )

                with col2:
                    dose = st.number_input(
                        "Dosage (mg/day)",
                        min_value=0.0,
                        step=0.1,
                        value=None,
                        key=f"dose_{class_name}"
                    )

                # Update the medication for this class
                st.session_state.medications[class_name] = [{
                    "drug": specific_drug,
                    "dose": dose if dose is not None else ""
                }]

            # Other medications
            other_meds = st.text_input("Other medications (not listed above):")
            if other_meds:
                medications_data["Other"] = other_meds

            # Convert medications to string for database storage
            medications_list = []
            for class_name, meds in st.session_state.medications.items():
                for med in meds:
                    if med['dose']:
                        medications_list.append(
                            f"{class_name}: {med['drug']} {med['dose']} mg/day")
                    else:
                        medications_list.append(f"{class_name}: {med['drug']}")
            if other_meds:
                medications_list.append(f"Other: {other_meds}")

            medications_str = "; ".join(
                medications_list) if medications_list else None

            # -------------------- CV Events --------------------
            st.subheader("History of Cardiovascular Events")
            cv_event_mi = st.checkbox("History of MI")
            cv_event_pci = st.checkbox("PCI / CABG")
            cv_event_stroke = st.checkbox("Stroke")
            cv_event_hf_hosp = st.checkbox(
                "Hospitalization for HF (in past year)")
            cv_event_ed_visits = st.checkbox("Repeated ED visits")
            cv_event_shock = st.checkbox("Cardiogenic shock")

            # -------------------- Labs --------------------
            st.subheader("Recent Lab Results")
            creatinine = st.number_input(
                "Creatinine (mg/dL)", min_value=0.0, value=None)
            potassium = st.number_input(
                "Potassium (mmol/L)", min_value=0.0, value=None)
            sodium = st.number_input(
                "Sodium (mmol/L)", min_value=0.0, value=None)
            anemia_status = st.selectbox(
                "Anemia Status", ["No Anemia", "Mild", "Moderate", "Severe"])
            anemia_present = st.checkbox("Anemia present")
            iron_supplement = st.checkbox("Iron supplementation ongoing")
            ferritin_issue = st.checkbox("Ferritin <100 or TSAT <20%")

            # -------------------- Functional Assessment --------------------
            st.subheader("Functional Assessment (Optional)")
            walk_test = st.number_input(
                "6-Minute Walk Test distance (meters)", min_value=0, value=None)
            vo2_max = st.number_input(
                "VO2 max (ml/kg/min)", min_value=0.0, value=None)

            # -------------------- Devices --------------------
            st.subheader("Device Therapy")
            devices = st.multiselect(
                "Devices in use", ["ICD", "CRT", "Pacemaker", "None"])
            devices_str = ",".join(devices) if devices else None

            # -------------------- Diagnostics --------------------
            st.subheader("Diagnostics")
            ecg = st.text_area("ECG Findings (optional)")
            echo = st.multiselect("Echo Findings", ["Reduced LVEF", "Dilated LV", "Valve disease",
                                                    "LVH", "Pericardial effusion"])
            echo_str = ",".join(echo) if echo else None
            echo_other = st.text_input("Other echo findings (optional)")

            # --- Coronary Angiography ---
            ca_options = [
                "No significant stenosis",
                "LAD lesion",
                "LCx lesion",
                "RCA lesion",
                "Bypass graft patent",
                "Collateral vessels present",
                "Other"
            ]
            ca_findings = st.multiselect(
                "Coronary Angiography Findings:", ca_options)
            ca_other_details = None
            if "Other" in ca_findings:
                ca_other_details = st.text_input(
                    "Other details (Coronary Angiography):"
                )
            ca_findings_str = ",".join(ca_findings) if ca_findings else None

            # --- Cardiac MRI ---
            mri_options = [
                "Reduced LVEF",
                "Late gadolinium enhancement",
                "Myocardial edema",
                "Intracardiac thrombus",
                "Other"
            ]
            mri_findings = st.multiselect("Cardiac MRI Findings:", mri_options)
            mri_other_details = None
            if "Other" in mri_findings:
                mri_other_details = st.text_input(
                    "Other details (Cardiac MRI):"
                )
            mri_findings_str = ",".join(mri_findings) if mri_findings else None

            # --- Holter Monitor ---
            holter_options = [
                "PACs",
                "PVCs",
                "NSVT runs",
                "Atrial fibrillation episodes",
                "Bradycardia (< 40 bpm)",
                "Tachycardia (> 100 bpm)",
                "Other"
            ]
            holter_findings = st.multiselect(
                "Holter Monitor Arrhythmias:", holter_options)
            holter_other_details = None
            if "Other" in holter_findings:
                holter_other_details = st.text_input(
                    "Other details (Holter Monitor):"
                )
            holter_findings_str = ",".join(
                holter_findings) if holter_findings else None

            # -------------------- Diagnosis --------------------
            st.subheader("Diagnosis")
            hf_type = st.selectbox("Etiology of Heart Failure", [
                None,
                "Ischemic Heart Failure",
                "Dilated Cardiomyopathy (DCM)",
                "Hypertrophic Cardiomyopathy (HCM)",
                "Valvular Heart Disease",
                "Peripartum Cardiomyopathy",
                "Genetic Cardiomyopathy"
            ])
            EF_type = st.selectbox("Ejection Fraction", [
                None, "HFrEF", "HFpEF", "HFmrEF", "Unclear"])
            lvef = st.number_input("LVEF (%)", min_value=0.0,
                                   max_value=100.0, value=None)
            nyha = st.selectbox("NYHA Class", [None, "I", "II", "III", "IV"])
            bnp = st.number_input("BNP / NT-proBNP", value=None)

            # -------------------- Plan --------------------
            st.subheader("Plan / Follow-up")
            follow_plan = st.text_area("Treatment plan and follow-up notes")

            if st.button("Submit Patient Form"):
                try:
                    # Step 1: Save patient core info
                    patient_id = save_patient(
                        patient_name, age, sex, height, weight, bmi,
                        heart_rate, rhythm, systolic_bp, diastolic_bp, respiratory_rate,
                        oxygen_saturation, temperature, edema_locations_str, edema_grade, jvp,
                        hepatomegaly, hepatomegaly_span, lung_findings_str, heart_sounds_str,
                        murmurs_str, murmur_other,
                        hf_type, EF_type, lvef, nyha, bnp,
                        ",".join(
                            symptom_triggers) if symptom_triggers else None,
                        other_trigger_detail,
                        daily_impact,
                        alcohol, alcohol_frequency,
                        smoking, smoking_packs, smoking_duration, activity,
                        medications_str, other_meds,
                        creatinine, potassium, sodium,
                        anemia_status, anemia_present, iron_supplement, ferritin_issue,
                        walk_test, vo2_max, devices_str,
                        ecg, echo_str, echo_other,
                        ca_findings_str, ca_other_details,
                        mri_findings_str, mri_other_details,
                        holter_findings_str, holter_other_details,
                        follow_plan
                    )

                    # Step 2: Save consent data
                    save_consent(patient_id, clinical_care_consent,
                                 quality_research_consent, ai_training_consent)

                    # Step 3: Prepare data for related tables
                    # Symptoms (already structured as individual_symptoms)
                    # Example:
                    # individual_symptoms = [{"symptom": "Dyspnea", "severity": 4, "duration": "Chronic", "category": "Cardiopulmonary"}, ...]

                    # Comorbidities main flags
                    comorbidities_data = {
                        "Hypertension": "Hypertension" in comorbidities,
                        "Diabetes": "Diabetes" in comorbidities,
                        "Dyslipidemia": "Dyslipidemia" in comorbidities,
                        "Kidney Disease": "Kidney Disease" in comorbidities,
                        "Obesity": "Obesity" in comorbidities,
                        "Sleep Apnea": "Sleep Apnea" in comorbidities,
                        "Family History of Heart Disease": "Family History of Heart Disease" in comorbidities
                    }

                    # Comorbidity details
                    comorbidity_details_data = []
                    if bp_control:
                        comorbidity_details_data.append(
                            {"detail_key": "BP Control", "detail_value": bp_control})
                    if end_organ_damage:
                        comorbidity_details_data.append(
                            {"detail_key": "End-organ damage", "detail_value": ", ".join(end_organ_damage)})
                    if diabetes_type:
                        comorbidity_details_data.append(
                            {"detail_key": "Diabetes Type", "detail_value": diabetes_type})
                    if hba1c_range:
                        comorbidity_details_data.append(
                            {"detail_key": "HbA1c Range", "detail_value": hba1c_range})
                    if diabetes_complications:
                        comorbidity_details_data.append(
                            {"detail_key": "Diabetes Complications", "detail_value": ", ".join(diabetes_complications)})
                    if lipid_control:
                        comorbidity_details_data.append(
                            {"detail_key": "Lipid Control", "detail_value": lipid_control})
                    if lipid_treatment:
                        comorbidity_details_data.append(
                            {"detail_key": "Lipid Treatment", "detail_value": ", ".join(lipid_treatment)})
                    if egfr_range:
                        comorbidity_details_data.append(
                            {"detail_key": "eGFR Range", "detail_value": egfr_range})
                    if dialysis:
                        comorbidity_details_data.append(
                            {"detail_key": "On Dialysis", "detail_value": dialysis})
                    if bmi_classification:
                        comorbidity_details_data.append(
                            {"detail_key": "BMI Classification", "detail_value": bmi_classification})
                    if weight_loss_plan is not None:
                        comorbidity_details_data.append(
                            {"detail_key": "Weight Loss Plan Advised", "detail_value": str(weight_loss_plan)})
                    if sleep_study is not None:
                        comorbidity_details_data.append(
                            {"detail_key": "Diagnosed via Sleep Study", "detail_value": str(sleep_study)})
                    if sleep_apnea_type:
                        comorbidity_details_data.append(
                            {"detail_key": "Sleep Apnea Type", "detail_value": sleep_apnea_type})
                    if sleep_apnea_treatment:
                        comorbidity_details_data.append(
                            {"detail_key": "Sleep Apnea Treatment", "detail_value": sleep_apnea_treatment})
                    if family_details:
                        comorbidity_details_data.append(
                            {"detail_key": "Family History Details", "detail_value": family_details})

                    # CV events
                    cv_events_data = {
                        "History of MI": cv_event_mi,
                        "PCI / CABG": cv_event_pci,
                        "Stroke": cv_event_stroke,
                        "Hospitalization for HF": cv_event_hf_hosp,
                        "Repeated ED visits": cv_event_ed_visits,
                        "Cardiogenic shock": cv_event_shock
                    }

                    # Step 4: Insert related data
                    save_patient_data(
                        patient_id,
                        individual_symptoms,
                        comorbidities_data,
                        comorbidity_details_data,
                        cv_events_data
                    )

                    st.success(
                        f"✅ Doctor form submitted and saved. Patient ID: {patient_id}")

                    # After successful submission, update session state
                    st.session_state['patient_id'] = patient_id
                    st.session_state['hf_type_structural'] = hf_type
                    st.session_state['show_visual_summary'] = False
                    st.rerun()

                except Exception as e:
                    st.error(f"Error submitting form: {str(e)}")

            # Show chat interface and visual summary if patient_id exists
            if st.session_state.get('patient_id'):
                chat_interface(st.session_state['patient_id'], mode)

                # Consent Management Section
                if st.session_state['patient_id']:
                    st.write("---")
                    st.subheader("Consent Management")

                    # Get current consent status
                    try:
                        # Initialize withdrawal state if not exists
                        if 'withdrawal_started' not in st.session_state:
                            st.session_state.withdrawal_started = False

                        # Clinical Care Consent (Required)
                        st.write("#### Clinical Care Consent")
                        if clinical_care_consent:
                            st.success("✓ Clinical care consent is active")

                            if not st.session_state.withdrawal_started:
                                if st.button("Withdraw Consent", key="withdraw_button"):
                                    st.session_state.withdrawal_started = True
                                    st.rerun()
                            else:
                                st.info(
                                    "Note: Withdrawing clinical care consent will remove the patient's data from our system.")
                                confirm = st.checkbox(
                                    "I understand that this will remove the patient's data", key="confirm_checkbox")

                                if confirm:
                                    if st.button("Confirm Deletion", key="confirm_delete"):
                                        try:
                                            # Delete data from local database
                                            withdraw_consent_and_delete_data(
                                                st.session_state['patient_id'])

                                            # Clear all session state
                                            for key in list(st.session_state.keys()):
                                                del st.session_state[key]
                                            st.rerun()
                                        except Exception as e:
                                            st.error(
                                                f"Error withdrawing consent: {str(e)}")

                            if st.button("Cancel", key="cancel_withdrawal"):
                                st.session_state.withdrawal_started = False
                                st.rerun()
                        else:
                            st.warning("Clinical care consent is not active")

                        # Quality Research Consent (Optional)
                        st.write("#### Quality Research Consent")
                        if quality_research_consent:
                            st.success("✓ Quality research consent is active")
                            if st.button("Withdraw Quality Research Consent", key="withdraw_quality"):
                                try:
                                    # Update consent status
                                    log_consent_action(
                                        st.session_state['patient_id'],
                                        "quality_research",
                                        False
                                    )
                                    st.success(
                                        "Quality research consent withdrawn.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(
                                        f"Error withdrawing consent: {str(e)}")
                        else:
                            st.info("Quality research consent is not active")

                        # AI Training Consent (Optional)
                        st.write("#### AI Training Consent")
                        if ai_training_consent:
                            st.success("✓ AI training consent is active")
                            if st.button("Withdraw AI Training Consent", key="withdraw_ai"):
                                try:
                                    # Update consent status
                                    log_consent_action(
                                        st.session_state['patient_id'],
                                        "ai_training",
                                        False
                                    )
                                    st.success(
                                        "AI training consent withdrawn.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(
                                        f"Error withdrawing consent: {str(e)}")
                        else:
                            st.info("AI training consent is not active")

                    except Exception as e:
                        st.error(f"Error managing consents: {str(e)}")

                # Show visual summary button only for doctors
                if mode == "Doctor":
                    if st.button("🖼️ Visual Summary"):
                        st.session_state['show_visual_summary'] = not st.session_state.get(
                            'show_visual_summary', False)
                        st.rerun()

                # Show visual summary if toggled and hf_type exists
                if st.session_state.get('show_visual_summary') and st.session_state.get('hf_type_structural'):
                    try:
                        # Get patient's symptoms and comorbidities
                        conn = sqlite3.connect("patients.db")
                        cursor = conn.cursor()

                        # Get symptoms
                        cursor.execute("""
                            SELECT DISTINCT symptom FROM patient_symptoms 
                            WHERE patient_id = ?
                        """, (st.session_state['patient_id'],))
                        symptoms = [row[0] for row in cursor.fetchall()]

                        # Get comorbidities
                        cursor.execute("""
                            SELECT hypertension,
                                   diabetes,
                                   dyslipidemia,
                                   kidney_disease,
                                   obesity,
                                   sleep_apnea,
                                   family_history
                              FROM patient_comorbidities
                             WHERE patient_id = ?
                        """, (st.session_state['patient_id'],))
                        row = cursor.fetchone()

                        # column-names mapped to human-readable labels
                        label_map = [
                            ("Hypertension",
                             row[0] if row else False),
                            ("Diabetes",
                             row[1] if row else False),
                            ("Dyslipidemia",
                             row[2] if row else False),
                            ("Kidney Disease",
                             row[3] if row else False),
                            ("Obesity",
                             row[4] if row else False),
                            ("Sleep Apnea",
                             row[5] if row else False),
                            ("Family History of Heart Disease",
                             row[6] if row else False),
                        ]

                        # build a simple list of only the True ones
                        comorbidities = [label for label,
                                         present in label_map if present]

                        conn.close()

                        show_visual_summary(
                            hf_types=[st.session_state['hf_type_structural']
                                      ] if st.session_state['hf_type_structural'] else None,
                            symptoms=symptoms,
                            comorbidities=comorbidities
                        )
                    except Exception as e:
                        st.error(f"Error loading patient data: {str(e)}")
                        conn.close()
                elif st.session_state.get('show_visual_summary'):
                    st.info(
                        "No heart failure type information available for this patient.")

    elif doctor_action == "Choose Existing Patient":
        # Connect to database
        conn = sqlite3.connect("patients.db")
        cursor = conn.cursor()

        # Get all patients
        cursor.execute(
            "SELECT patient_id, patient_name, age, sex FROM patients ORDER BY patient_id DESC")
        patients = cursor.fetchall()
        conn.close()

        if not patients:
            st.warning("No existing patients found in the database.")
        else:
            # Create a list of patient options with formatted display
            patient_options = [
                f"ID: {p[0]} - {p[1]} (Age: {p[2]}, Sex: {p[3]})" for p in patients]

            # Show patient selection dropdown
            selected_patient = st.selectbox(
                "Select a patient:", patient_options)

            if selected_patient:
                # Extract patient ID from selection
                patient_id = int(selected_patient.split(" - ")
                                 [0].split(": ")[1])

                # Store patient ID in session state
                st.session_state['patient_id'] = patient_id

                # Get patient's heart failure type for visual summary
                conn = sqlite3.connect("patients.db")
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT hf_type FROM patients WHERE patient_id = ?", (patient_id,))
                hf_type_result = cursor.fetchone()
                conn.close()

                # Store hf_type in session state, default to None if not found
                hf_type = hf_type_result[0] if hf_type_result and hf_type_result[0] else None
                st.session_state['hf_type_structural'] = hf_type

                # Initialize show_visual_summary if not already set
                if 'show_visual_summary' not in st.session_state:
                    st.session_state['show_visual_summary'] = False

                # Show chat interface
                chat_interface(patient_id, mode)

                # Show visual summary button only for doctors
                if mode == "Doctor":
                    st.write("---")  # Add a separator

                    # Create a unique key for this button
                    button_key = f"visual_summary_{patient_id}"

                    if st.button("🖼️ Visual Summary", key=button_key):
                        st.session_state['show_visual_summary'] = not st.session_state.get(
                            'show_visual_summary', False)
                        st.rerun()

                    # Show visual summary if toggled and hf_type exists
                    if st.session_state.get('show_visual_summary', False):
                        if st.session_state.get('hf_type_structural'):
                            try:
                                # Get patient's symptoms and comorbidities
                                conn = sqlite3.connect("patients.db")
                                cursor = conn.cursor()

                                # Get symptoms
                                cursor.execute("""
                                    SELECT DISTINCT symptom FROM patient_symptoms 
                                    WHERE patient_id = ?
                                """, (patient_id,))
                                symptoms = [row[0]
                                            for row in cursor.fetchall()]

                                # Get comorbidities
                                cursor.execute("""
                                    SELECT hypertension,
                                           diabetes,
                                           dyslipidemia,
                                           kidney_disease,
                                           obesity,
                                           sleep_apnea,
                                           family_history
                                      FROM patient_comorbidities
                                     WHERE patient_id = ?
                                """, (patient_id,))
                                row = cursor.fetchone()

                                # column-names mapped to human-readable labels
                                label_map = [
                                    ("Hypertension", row[0] if row else False),
                                    ("Diabetes", row[1] if row else False),
                                    ("Dyslipidemia", row[2] if row else False),
                                    ("Kidney Disease",
                                     row[3] if row else False),
                                    ("Obesity", row[4] if row else False),
                                    ("Sleep Apnea", row[5] if row else False),
                                    ("Family History of Heart Disease",
                                     row[6] if row else False),
                                ]

                                # build a simple list of only the True ones
                                comorbidities = [label for label,
                                                 present in label_map if present]

                                conn.close()

                                # Convert hf_type to list format
                                hf_type = st.session_state['hf_type_structural']
                                if hf_type:
                                    show_visual_summary(
                                        hf_types=[hf_type],
                                        symptoms=symptoms,
                                        comorbidities=comorbidities
                                    )
                            except Exception as e:
                                st.error(
                                    f"Error loading patient data: {str(e)}")
                                conn.close()
                        else:
                            st.info(
                                "No heart failure type information available for this patient.")

    elif doctor_action == "General Questioning":
        # Set a special patient ID for general questions
        st.session_state['patient_id'] = "general"
        st.session_state['show_visual_summary'] = False

        # Show chat interface directly
        chat_interface("general", mode)
