import streamlit as st
import os
import psycopg2
from form import save_patient, save_patient_data
from services.chatbot_service import chat_interface

DB_CONN = os.getenv("DB_CONN")

st.title("Heart Failure Patient Information Form")

# Mode selection: Patient or Doctor
mode = st.radio("Choose form mode:", ("Patient", "Doctor"))

# --- Patient Form ---
if mode == "Patient":
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
        "Type of Diabetes", ["Type 1", "Type 2"])

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
        "How long have you had these symptoms?", min_value=0, key="onset_value")
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
    heart_rate = st.number_input("Heart Rate (bpm)", min_value=0)
    systolic_bp = st.number_input("Systolic BP (mmHg)", min_value=0)
    diastolic_bp = st.number_input("Diastolic BP (mmHg)", min_value=0)

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
        # Step 1: Save patient core info (Vitals, labs, etc. are None for patients)
        patient_id = save_patient(
            patient_name, age, sex, height, weight, bmi,
            heart_rate, systolic_bp, diastolic_bp, None, None, None,  # Vitals
            None, None, None, None, None, None,  # HF clinical
            symptom_triggers_str, other_trigger_detail, impact,
            alcohol, alcohol_frequency, smoking, smoking_packs, smoking_duration,
            medications_str, other_meds,
            None, None, None,  # Labs
            None, None, None,  # More labs
            None, None, None,  # Diagnostics
            activity, None, None
        )

        # Step 2: Save comorbidities (flags)
        patient_comorbidities_data = {
            "Hypertension": hypertension,
            "Diabetes": diabetes,
            "Dyslipidemia": dyslipidemia,
            "Kidney Disease": None,
            "Obesity": obesity,
            "Sleep Apnea": None,
            "Family History of Heart Disease": family_history
        }

        # Step 3: Save comorbidity details
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

        # Step 4: Insert into related tables
        save_patient_data(
            patient_id,
            patient_individual_symptoms,
            patient_comorbidities_data,
            patient_comorbidity_details,
            {}  # No CV events for patient form
        )

        st.success(f"✅ Patient form submitted. Patient ID: {patient_id}")

        # After successful submission, show the chatbot interface
        st.session_state['patient_id'] = patient_id
        st.rerun()

    # Add chatbot interface when patient_id is in session state
    if 'patient_id' in st.session_state:
        chat_interface(st.session_state['patient_id'], mode)

# --- Doctor Form Modes ---
elif mode == "Doctor":
    st.subheader("Doctor Options")
    doctor_action = st.radio("Choose action:", [
        "Create New Patient", "Choose Existing Patient", "General Questioning"])

    if doctor_action == "Create New Patient":
        # -------------------- Patient Overview --------------------
        st.subheader("Patient Overview")
        patient_name = st.text_input("Patient Name")
        age = st.number_input("Age", min_value=0, key="doc_age")
        sex = st.selectbox("Sex", ["Male", "Female", "Other"], key="doc_sex")
        height = st.number_input(
            "Height (cm)", min_value=0.0, key="doc_height")
        weight = st.number_input(
            "Weight (kg)", min_value=0.0, key="doc_weight")
        bmi = round(weight / ((height / 100) ** 2), 2) if height > 0 else 0
        st.text(f"BMI: {bmi}")

        # -------------------- Vital Signs --------------------
        st.subheader("Vital Signs (Recent)")
        heart_rate = st.number_input("Heart Rate (bpm)", min_value=0)
        systolic_bp = st.number_input("Systolic BP (mmHg)", min_value=0)
        diastolic_bp = st.number_input("Diastolic BP (mmHg)", min_value=0)
        respiratory_rate = st.number_input(
            "Respiratory Rate (breaths/min)", min_value=0)
        oxygen_saturation = st.number_input(
            "Oxygen Saturation (%)", min_value=0.0, max_value=100.0)
        temperature = st.number_input(
            "Temperature (°C)", min_value=30.0, max_value=45.0)

        # -------------------- Clinical Status --------------------
        st.subheader("Clinical Status")
        hf_type = st.selectbox("Heart Failure Type", [
            "HFrEF", "HFpEF", "HFmrEF", "Unclear"])
        lvef = st.number_input("LVEF (%)", min_value=0.0, max_value=100.0)
        nyha = st.selectbox("NYHA Class", ["I", "II", "III", "IV"])
        bnp = st.number_input("BNP / NT-proBNP")

        # -------------------- Symptoms --------------------
        st.subheader("Symptoms")
        symptom_duration = st.selectbox("When did symptoms begin?", [
            "Acute (within days)", "Subacute (1–4 weeks)", "Chronic (>1 month)", "Unclear"
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
        collect_symptoms(gastrointestinal_symptoms, "Gastrointestinal / Renal")

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
        meds = st.multiselect("Medications", ["ACEi/ARB/ARNI", "Beta Blocker", "Diuretic", "MRA",
                                              "SGLT2i", "Ivabradine", "Anticoagulant", "Antiplatelet",
                                              "Statins", "Antiarrhythmics", "Other"])
        medications_str = ",".join(meds) if meds else None
        other_meds = st.text_input("Please specify other medication(s):")

        # -------------------- CV Events --------------------
        st.subheader("History of Cardiovascular Events")
        cv_event_mi = st.checkbox("History of MI")
        cv_event_pci = st.checkbox("PCI / CABG")
        cv_event_stroke = st.checkbox("Stroke")
        cv_event_hf_hosp = st.checkbox("Hospitalization for HF (in past year)")
        cv_event_ed_visits = st.checkbox("Repeated ED visits")
        cv_event_shock = st.checkbox("Cardiogenic shock")

        # -------------------- Labs --------------------
        st.subheader("Recent Lab Results")
        creatinine = st.number_input("Creatinine (mg/dL)", min_value=0.0)
        potassium = st.number_input("Potassium (mmol/L)", min_value=0.0)
        sodium = st.number_input("Sodium (mmol/L)", min_value=0.0)
        anemia_status = st.selectbox(
            "Anemia Status", ["No Anemia", "Mild", "Moderate", "Severe"])
        anemia_present = st.checkbox("Anemia present")
        iron_supplement = st.checkbox("Iron supplementation ongoing")
        ferritin_issue = st.checkbox("Ferritin <100 or TSAT <20%")

        # -------------------- Functional Assessment --------------------
        st.subheader("Functional Assessment (Optional)")
        walk_test = st.number_input(
            "6-Minute Walk Test distance (meters)", min_value=0)
        vo2_max = st.number_input("VO2 max (ml/kg/min)", min_value=0.0)

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

        # -------------------- Plan --------------------
        st.subheader("Plan / Follow-up")
        follow_plan = st.text_area("Treatment plan and follow-up notes")

        if st.button("Submit Patient Form"):
            # Step 1: Insert into patients table
            patient_id = save_patient(
                patient_name, age, sex, height, weight, bmi,
                heart_rate, systolic_bp, diastolic_bp, respiratory_rate,
                oxygen_saturation, temperature, hf_type, lvef, nyha, bnp,
                ",".join(symptom_triggers) if symptom_triggers else None,
                other_trigger_detail,
                daily_impact,
                alcohol, alcohol_frequency,
                smoking, smoking_packs, smoking_duration,
                medications_str, other_meds,
                creatinine, potassium, sodium,
                anemia_status, anemia_present, iron_supplement, ferritin_issue,
                walk_test, vo2_max, devices_str,
                ecg, echo_str, echo_other, follow_plan
            )

            # Step 2: Prepare data for related tables

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

            # Step 3: Insert related data
            save_patient_data(
                patient_id,
                individual_symptoms,
                comorbidities_data,
                comorbidity_details_data,
                cv_events_data
            )

            st.success(
                f"✅ Doctor form submitted and saved. Patient ID: {patient_id}")

            # After successful submission, show the chatbot interface
            st.session_state['patient_id'] = patient_id
            st.rerun()

        # Add chatbot interface when patient_id is in session state
        if 'patient_id' in st.session_state:
            chat_interface(st.session_state['patient_id'], mode)

    elif doctor_action == "Choose Existing Patient":
        st.info(
            "[Placeholder] Here you can load an existing patient profile from your system")
    elif doctor_action == "General Questioning":
        st.info(
            "[Placeholder] Use this area to ask general medical questions not tied to a patient.")
