import streamlit as st
import sqlite3

# Function to save patient form data


def save_patient_form(data):
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO patient_info (
            patient_id, name, age, sex, height, weight, bmi, bmi_category,
            hypertension, hypertension_duration, diabetes, diabetes_duration,
            dyslipidemia, alcohol, alcohol_frequency, smoking,
            smoking_packs, smoking_duration, family_history, family_details,
            obesity, hf_types, symptoms, symptom_severities, symptom_onset,
            symptom_triggers, other_trigger, impact, pulse, bp,
            medications, other_meds, physical_activity
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()

# Function to save doctor form data


def save_doctor_form(data):
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO doctor_form (
            patient_id, heart_rate, systolic_bp, diastolic_bp, respiratory_rate, oxygen_saturation, temperature,
            hf_type, lvef, nyha, bnp,
            cardiopulmonary_symptoms, systemic_symptoms, gi_symptoms, symptom_severity,
            symptom_triggers, symptom_duration, daily_impact,
            comorbidities, medications, other_meds, cv_events,
            creatinine, potassium, sodium, anemia_status, anemia_present,
            iron_supplement, ferritin_issue,
            walk_test, vo2_max,
            devices, ecg, echo, echo_other, follow_plan
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()


st.title("Heart Failure Patient Information Form")

# Mode selection: Patient or Doctor
mode = st.radio("Choose form mode:", ("Patient", "Doctor"))

# --- Patient Form ---
if mode == "Patient":
    st.subheader("Patient Demographics")
    name = st.text_input("Name")
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

    st.subheader("Risk Factors")

    hypertension = st.checkbox("Hypertension")
    if hypertension:
        hypertension_duration = st.number_input(
            "Duration:", min_value=0, key="hypertension")

    diabetes = st.checkbox("Diabetes")
    if diabetes:
        diabetes_duration = st.number_input(
            "Duration:", min_value=0, key="diabetes")

    dyslipidemia = st.checkbox("Dyslipidemia")

    alcohol = st.checkbox("Alcohol Consumption")
    if alcohol:
        alcohol_frequency = st.selectbox("How often do you drink alcohol?", [
            "Rarely (a few times a year)",
            "Occasionally (1–3 times/month)",
            "Regularly (1–3 times/week)",
            "Frequently (daily or almost daily)"
        ])

    smoking = st.checkbox("Smoking")
    if smoking:
        smoking_packs = st.number_input(
            "Packs per day:", min_value=0.0, step=0.1, key="smoking_packs")
        smoking_duration = st.number_input(
            "Smoking duration (years):", min_value=0, key="smoking_duration")
    family_history = st.checkbox("Family History of Heart Disease")
    if family_history:
        family_details = st.text_input("Relationship(s)")

    Obesity = st.checkbox("Obesity")

    st.subheader("Type of Heart Failure (If known)")
    hf_types = st.multiselect("Select type(s) of heart failure", [
        "Ischemic Heart Failure",
        "Dilated Cardiomyopathy (DCM)",
        "Hypertrophic Cardiomyopathy (HCM)",
        "Valvular Heart Disease",
        "Peripartum Cardiomyopathy",
        "Genetic Cardiomyopathy"
    ])

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
        "Depression or mood issues"
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
    onset_description = f"{onset_value} {onset_unit}"

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
    if "Other" in triggers:
        other_trigger = st.text_input(
            "Please describe other triggers (optional)")

    st.subheader("Impact on Daily Life")
    impact = st.selectbox("How much do your symptoms affect your daily life?", [
        "Not at all",
        "Mildly – I can still do most activities",
        "Moderately – I need to rest or avoid certain things",
        "Severely – I struggle with daily activities"
    ])

    st.subheader("Signs")
    pulse = st.text_input("Pulse")
    bp = st.text_input("Blood Pressure")

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
    other_meds = st.text_input("Other medications taken:")

    st.subheader("Physical Activity")
    activity = st.selectbox("Level of physical activity", [
        "None - Sedentary lifestyle, minimal movement",
        "Light activity - Occasional walking or household chores",
        "Moderate activity - Regular walking, light exercise 3-4 days/week",
        "High - Frequent workouts or physically demanding job"
    ])

    if st.button("Submit"):
        patient_data = (name, age, sex, height, weight, bmi, bmi_category,
                        hypertension, hypertension_duration if hypertension else None,
                        diabetes, diabetes_duration if diabetes else None,
                        dyslipidemia, alcohol, alcohol_frequency if alcohol else None,
                        smoking, smoking_packs if smoking else None, smoking_duration if smoking else None,
                        family_history, family_details if family_history else None,
                        Obesity, ",".join(hf_types), ",".join(symptoms),
                        str(symptom_severities), onset_description,
                        ",".join(
                            triggers), other_trigger if "Other" in triggers else None,
                        impact, pulse, bp, ",".join(meds), other_meds, activity)

        save_patient_form(patient_data)

        st.success("✅ Patient form submitted and saved.")

# --- Doctor Form Modes ---
elif mode == "Doctor":
    st.subheader("Doctor Options")
    doctor_action = st.radio("Choose action:", [
                             "Create New Patient", "Choose Existing Patient", "General Questioning"])

    if doctor_action == "Create New Patient":
        st.subheader("Patient Overview")
        patient_name = st.text_input("Patient Name")
        age = st.number_input("Age", min_value=0, key="age")
        sex = st.selectbox("Sex", ["Male", "Female", "Other"])
        height = st.number_input("Height (cm)", min_value=0.0, key="height")
        weight = st.number_input("Weight (kg)", min_value=0.0, key="weight")
        bmi = round(weight / ((height / 100) ** 2), 2) if height > 0 else 0
        st.text(f"BMI: {bmi}")

        st.subheader("Vital Signs (Recent)")
        heart_rate = st.number_input(
            "Heart Rate (bpm)", min_value=0, key="heart_rate")
        systolic_bp = st.number_input(
            "Systolic BP (mmHg)", min_value=0, key="systolic_bp")
        diastolic_bp = st.number_input(
            "Diastolic BP (mmHg)", min_value=0, key="diastolic_bp")
        respiratory_rate = st.number_input(
            "Respiratory Rate (breaths/min)", min_value=0, key="respiratory_rate")
        oxygen_saturation = st.number_input(
            "Oxygen Saturation (%)", min_value=0.0, max_value=100.0, key="oxygen_saturation")
        temperature = st.number_input(
            "Temperature (°C)", min_value=30.0, max_value=45.0, key="temperature")

        st.subheader("Clinical Status")
        hf_type = st.selectbox("Heart Failure Type", [
                               "HFrEF", "HFpEF", "HFmrEF", "Unclear"])
        lvef = st.number_input("LVEF (%)", min_value=0.0,
                               max_value=100.0, key="lvef")
        nyha = st.selectbox("NYHA Class", ["I", "II", "III", "IV"])
        bnp = st.number_input("BNP / NT-proBNP", key="bnp")

        st.subheader("Symptoms")
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

        st.subheader("Symptom Severity (Clinical Assessment)")
        symptom_severity_doctor = {}
        for section, symptoms in {
            "Cardiopulmonary": cardiopulmonary_symptoms,
            "Systemic & Functional": systemic_symptoms,
            "Gastrointestinal / Renal": gastrointestinal_symptoms
        }.items():
            for symptom in symptoms:
                severity = st.slider(f"{symptom} severity", 1, 5, 3)
                symptom_severity_doctor[symptom] = severity

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
        if "Other" in symptom_triggers:
            st.text_input("Describe other trigger (optional)")

        symptom_duration = st.selectbox("When did symptoms begin?", [
            "Acute (within days)",
            "Subacute (1–4 weeks)",
            "Chronic (>1 month)",
            "Unclear"
        ])

        daily_impact = st.selectbox("How are daily activities affected?", [
            "No impact",
            "Mild – Can perform daily tasks with some fatigue",
            "Moderate – Avoids physical activities",
            "Severe – Needs assistance for most tasks"
        ])

        st.subheader("Comorbidities")
        comorbidities = st.multiselect("Check all that apply", [
            "Hypertension",
            "Diabetes",
            "Dyslipidemia",
            "Kidney Disease",
            "Obesity",
            "Sleep Apnea"
        ])

        if "Hypertension" in comorbidities:
            st.selectbox("Blood pressure control", [
                         "Controlled (<140/90)", "Uncontrolled"])
            st.multiselect("Signs of end-organ damage",
                           ["LVH", "Proteinuria", "Retinopathy"])

        if "Diabetes" in comorbidities:
            st.selectbox("Type of Diabetes", ["Type 1", "Type 2"])
            st.selectbox("HbA1c range", ["<6.5%", "6.5–7.5%", ">7.5%"])
            st.multiselect("Diabetic complications", [
                           "Neuropathy", "Nephropathy", "Retinopathy"])

        if "Dyslipidemia" in comorbidities:
            st.selectbox("Lipid control", ["Controlled", "Uncontrolled"])
            st.multiselect(
                "Treatment", ["Statins", "PCSK9 inhibitors", "Lifestyle only"])

        if "Kidney Disease" in comorbidities:
            st.selectbox("eGFR Range", [
                         ">90 (Normal)", "60–89 (Mild)", "30–59 (Moderate)", "<30 (Severe)"])
            st.selectbox("On Dialysis", ["No", "Yes"])

        if "Obesity" in comorbidities:
            st.selectbox("BMI Classification", [
                "Overweight (25–29.9)",
                "Obesity Class I (30–34.9)",
                "Obesity Class II (35–39.9)",
                "Obesity Class III (≥40)"
            ])
            st.checkbox("Weight loss plan advised")

        if "Sleep Apnea" in comorbidities:
            st.checkbox("Diagnosed via sleep study")
            st.selectbox("Type of Sleep Apnea", ["Obstructive", "Central"])
            st.selectbox("Treatment", ["On CPAP", "Not treated"])

        st.subheader("Current Medications")
        medications = st.multiselect("Medications", [
            "ACEi/ARB/ARNI", "Beta Blocker", "Diuretic", "MRA",
            "SGLT2i", "Ivabradine", "Anticoagulant", "Antiplatelet",
            "Statins", "Antiarrhythmics", "Other"
        ])
        if "Other" in medications:
            other_meds = st.text_input("Please specify other medication(s):")

        st.subheader("History of Cardiovascular Events")
        st.checkbox("History of MI")
        st.checkbox("PCI / CABG")
        st.checkbox("Stroke")
        st.checkbox("Hospitalization for HF (in past year)")
        st.checkbox("Repeated ED visits")
        st.checkbox("Cardiogenic shock")

        st.subheader("Recent Lab Results")
        st.number_input("Creatinine (mg/dL)", min_value=0.0, key="Creatinine")
        st.number_input("Potassium (mmol/L)", min_value=0.0, key="Potassium")
        st.number_input("Sodium (mmol/L)", min_value=0.0, key="Sodium")
        anemia_status = st.selectbox(
            "Anemia Status", ["No Anemia", "Mild", "Moderate", "Severe"])
        if anemia_status in ["Mild", "Moderate", "Severe"]:
            st.checkbox("Iron supplementation ongoing")
            st.checkbox("Ferritin <100 or TSAT <20%")
        st.checkbox("Anemia present")
        st.checkbox("Iron supplementation ongoing")
        st.checkbox("Ferritin <100 or TSAT <20%")

        st.subheader("Functional Assessment (Optional)")
        st.number_input("6-Minute Walk Test distance (meters)",
                        min_value=0, key="6-Minute Walk Test distance (meters)")
        st.number_input("VO2 max (ml/kg/min)", min_value=0.0, key="VO2 max")

        st.subheader("Device Therapy")
        devices = st.multiselect("Devices in use", [
            "ICD", "CRT", "Pacemaker", "None"
        ])

        st.subheader("Diagnostics")
        ecg = st.text_area("ECG Findings (optional)")
        echo = st.multiselect("Echo Findings", [
            "Reduced LVEF", "Dilated LV", "Valve disease",
            "LVH", "Pericardial effusion"
        ])
        echo_other = st.text_input("Other echo findings (optional)")

        st.subheader("Plan / Follow-up")
        follow_plan = st.text_area("Treatment plan and follow-up notes")

        if st.button("Submit Patient Form"):
            doctor_data = (
                heart_rate, systolic_bp, diastolic_bp, respiratory_rate, oxygen_saturation, temperature,
                hf_type, lvef, nyha, bnp,
                ",".join(cardiopulmonary_symptoms),
                ",".join(systemic_symptoms),
                ",".join(gastrointestinal_symptoms),
                str(symptom_severity_doctor),
                ",".join(symptom_triggers),
                symptom_duration,
                daily_impact,
                ",".join(comorbidities),
                ",".join(medications),
                other_meds,
                # Placeholder for CV events (you can add checkboxes like "if st.checkbox('History of MI')")
                "",
                # creatinine, potassium, sodium (can be filled in as needed)
                None, None, None,
                anemia_status,
                None,  # anemia_present
                None,  # iron_supplement
                None,  # ferritin_issue
                None,  # walk_test
                None,  # vo2_max
                ",".join(devices),
                ecg,
                ",".join(echo),
                echo_other,
                follow_plan
            )
            save_doctor_form(doctor_data)
            st.success("✅ Doctor form submitted and saved.")

    elif doctor_action == "Choose Existing Patient":
        st.info(
            "[Placeholder] Here you can load an existing patient profile from your system")

    elif doctor_action == "General Questioning":
        st.info(
            "[Placeholder] Use this area to ask general medical questions not tied to a patient.")
