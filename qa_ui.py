import streamlit as st
import sqlite3
from form import save_patient  # using the unified save_patient function from form.py
from services.chatbot_service import chat_interface

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
    else:
        bmi_category = None

    st.subheader("Risk Factors")

    hypertension = st.checkbox("Hypertension")
    hypertension_duration = st.number_input(
        "Duration:", min_value=0, key="hypertension") if hypertension else None

    diabetes = st.checkbox("Diabetes")
    diabetes_duration = st.number_input(
        "Duration:", min_value=0, key="diabetes") if diabetes else None

    dyslipidemia = st.checkbox("Dyslipidemia")

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

    obesity = st.checkbox("Obesity")

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
    symptoms_str = ",".join(symptoms) if symptoms else None

    symptom_severities = {}
    for symptom in symptoms:
        severity = st.slider(f"Severity of '{symptom}'", 1, 5, 3)
        symptom_severities[symptom] = severity
    symptom_severities_str = str(
        symptom_severities) if symptom_severities else None

    st.subheader("Symptom Onset")
    onset_value = st.number_input(
        "How long have you had these symptoms?", min_value=0, key="onset_value")
    onset_unit = st.selectbox(
        "Time unit", ["days", "weeks", "months", "years"])
    symptom_onset = f"{onset_value} {onset_unit}" if onset_value else None

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
    symptom_triggers = ",".join(triggers) if triggers else None
    other_trigger = st.text_input(
        "Please describe other triggers (optional)") if "Other" in triggers else None

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
    medications = ",".join(meds) if meds else None
    other_meds = st.text_input("Other medications taken:")

    st.subheader("Physical Activity")
    activity = st.selectbox("Level of physical activity", [
        "None - Sedentary lifestyle, minimal movement",
        "Light activity - Occasional walking or household chores",
        "Moderate activity - Regular walking, light exercise 3-4 days/week",
        "High - Frequent workouts or physically demanding job"
    ])

    if st.button("Submit"):
        # Build the 32 patient-specific values:
        patient_values = [
            name,                                   # 1. name
            age,                                    # 2. age
            sex,                                    # 3. sex
            height,                                 # 4. height
            weight,                                 # 5. weight
            bmi,                                    # 6. bmi
            bmi_category,                           # 7. bmi_category
            hypertension,                           # 8. hypertension
            hypertension_duration if hypertension else None,  # 9. hypertension_duration
            diabetes,                               # 10. diabetes
            diabetes_duration if diabetes else None,         # 11. diabetes_duration
            dyslipidemia,                           # 12. dyslipidemia
            alcohol,                                # 13. alcohol
            alcohol_frequency if alcohol else None,          # 14. alcohol_frequency
            smoking,                                # 15. smoking
            smoking_packs if smoking else None,              # 16. smoking_packs
            smoking_duration if smoking else None,           # 17. smoking_duration
            family_history,                         # 18. family_history
            family_details if family_history else None,      # 19. family_details
            obesity,                                # 20. obesity
            hf_type,                                # 21. hf_type (merged)
            symptoms_str,                           # 22. symptoms
            symptom_severities_str if symptoms else None,    # 23. symptom_severities
            symptom_onset,                          # 24. symptom_onset
            symptom_triggers if triggers else None,         # 25. symptom_triggers
            other_trigger if "Other" in triggers else None,   # 26. other_trigger
            impact,                                 # 27. impact
            pulse,                                  # 28. pulse
            bp,                                     # 29. bp
            medications,                            # 30. medications
            other_meds,                             # 31. other_meds
            activity                                # 32. physical_activity
        ]
        # Append 31 None values for the doctor-specific fields:
        doctor_defaults = [None] * (63 - len(patient_values))
        patient_data = tuple(patient_values + doctor_defaults)
        st.write("Patient data:", patient_data)
        st.write("Number of values submitted:", len(patient_data))

        # Call save_patient only once and capture the returned patient_id
        patient_id = save_patient(patient_data)
        st.success(
            f"✅ Patient form submitted and saved. Patient ID: {patient_id}")
        
        # After successful submission, show the chatbot interface
        st.session_state['patient_id'] = patient_id
        st.rerun()

    # Add chatbot interface when patient_id is in session state
    if 'patient_id' in st.session_state:
        chat_interface(st.session_state['patient_id'])

# --- Doctor Form Modes ---
elif mode == "Doctor":
    st.subheader("Doctor Options")
    doctor_action = st.radio("Choose action:", [
                             "Create New Patient", "Choose Existing Patient", "General Questioning"])

    if doctor_action == "Create New Patient":
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
        combined_symptoms = cardiopulmonary_symptoms + \
            systemic_symptoms + gastrointestinal_symptoms
        symptoms_str = ",".join(
            combined_symptoms) if combined_symptoms else None

        st.subheader("Symptom Severity (Clinical Assessment)")
        symptom_severity_doctor = {}
        for section, symptom_list in {
            "Cardiopulmonary": cardiopulmonary_symptoms,
            "Systemic & Functional": systemic_symptoms,
            "Gastrointestinal / Renal": gastrointestinal_symptoms
        }.items():
            for symptom in symptom_list:
                severity = st.slider(f"{symptom} severity", 1, 5, 3)
                symptom_severity_doctor[symptom] = severity
        # For doctor mode, we leave patient-reported symptom severities as None.
        patient_symptom_severities = None
        doctor_symptom_severity_str = str(
            symptom_severity_doctor) if symptom_severity_doctor else None

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
        # The UI element for "Other" remains; its value is not captured.
        _ = st.text_input(
            "Describe other trigger (optional)") if "Other" in symptom_triggers else None

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
        meds = st.multiselect("Medications", [
            "ACEi/ARB/ARNI", "Beta Blocker", "Diuretic", "MRA",
            "SGLT2i", "Ivabradine", "Anticoagulant", "Antiplatelet",
            "Statins", "Antiarrhythmics", "Other"
        ])
        medications_str = ",".join(meds) if meds else None
        other_meds = st.text_input("Please specify other medication(s):")

        st.subheader("History of Cardiovascular Events")
        _ = st.checkbox("History of MI")
        _ = st.checkbox("PCI / CABG")
        _ = st.checkbox("Stroke")
        _ = st.checkbox("Hospitalization for HF (in past year)")
        _ = st.checkbox("Repeated ED visits")
        _ = st.checkbox("Cardiogenic shock")
        cv_events = ""  # Placeholder

        st.subheader("Recent Lab Results")
        creatinine = st.number_input(
            "Creatinine (mg/dL)", min_value=0.0, key="Creatinine")
        potassium = st.number_input(
            "Potassium (mmol/L)", min_value=0.0, key="Potassium")
        sodium = st.number_input(
            "Sodium (mmol/L)", min_value=0.0, key="Sodium")
        anemia_status = st.selectbox(
            "Anemia Status", ["No Anemia", "Mild", "Moderate", "Severe"])
        _ = st.checkbox("Anemia present")
        _ = st.checkbox("Iron supplementation ongoing")
        _ = st.checkbox("Ferritin <100 or TSAT <20%")

        st.subheader("Functional Assessment (Optional)")
        walk_test = st.number_input(
            "6-Minute Walk Test distance (meters)", min_value=0, key="walk_test")
        vo2_max = st.number_input(
            "VO2 max (ml/kg/min)", min_value=0.0, key="vo2_max")

        st.subheader("Device Therapy")
        devices = st.multiselect(
            "Devices in use", ["ICD", "CRT", "Pacemaker", "None"])
        devices_str = ",".join(devices) if devices else None

        st.subheader("Diagnostics")
        ecg = st.text_area("ECG Findings (optional)")
        echo = st.multiselect("Echo Findings", [
            "Reduced LVEF", "Dilated LV", "Valve disease",
            "LVH", "Pericardial effusion"
        ])
        echo_str = ",".join(echo) if echo else None
        echo_other = st.text_input("Other echo findings (optional)")

        st.subheader("Plan / Follow-up")
        follow_plan = st.text_area("Treatment plan and follow-up notes")

        if st.button("Submit Patient Form"):
            # Build tuple of 63 fields for doctor mode.
            doctor_data = (
                patient_name,                # 1. name
                age,                         # 2. age
                sex,                         # 3. sex
                height,                      # 4. height
                weight,                      # 5. weight
                bmi,                         # 6. bmi
                None,                        # 7. bmi_category (not provided)
                None,                        # 8. hypertension
                None,                        # 9. hypertension_duration
                None,                        # 10. diabetes
                None,                        # 11. diabetes_duration
                None,                        # 12. dyslipidemia
                None,                        # 13. alcohol
                None,                        # 14. alcohol_frequency
                None,                        # 15. smoking
                None,                        # 16. smoking_packs
                None,                        # 17. smoking_duration
                None,                        # 18. family_history
                None,                        # 19. family_details
                None,                        # 20. obesity
                hf_type,                     # 21. hf_type
                symptoms_str,                # 22. symptoms
                # 23. symptom_severities (patient-reported not provided)
                None,
                None,                        # 24. symptom_onset
                # 25. symptom_triggers
                ",".join(symptom_triggers) if symptom_triggers else None,
                None,                        # 26. other_trigger (not captured)
                None,                        # 27. impact
                None,                        # 28. pulse
                None,                        # 29. bp
                medications_str,             # 30. medications
                other_meds,                  # 31. other_meds
                None,                        # 32. physical_activity
                heart_rate,                  # 33. heart_rate
                systolic_bp,                 # 34. systolic_bp
                diastolic_bp,                # 35. diastolic_bp
                respiratory_rate,            # 36. respiratory_rate
                oxygen_saturation,           # 37. oxygen_saturation
                temperature,                 # 38. temperature
                lvef,                        # 39. lvef
                nyha,                        # 40. nyha
                bnp,                         # 41. bnp
                # 42. cardiopulmonary_symptoms
                ",".join(
                    cardiopulmonary_symptoms) if cardiopulmonary_symptoms else None,
                # 43. systemic_symptoms
                ",".join(systemic_symptoms) if systemic_symptoms else None,
                # 44. gi_symptoms
                ",".join(
                    gastrointestinal_symptoms) if gastrointestinal_symptoms else None,
                # 45. symptom_severity (doctor-assessed)
                doctor_symptom_severity_str,
                symptom_duration,            # 46. symptom_duration
                daily_impact,                # 47. daily_impact
                # 48. comorbidities
                ",".join(comorbidities) if comorbidities else None,
                cv_events,                   # 49. cv_events
                creatinine,                  # 50. creatinine
                potassium,                   # 51. potassium
                sodium,                      # 52. sodium
                anemia_status,               # 53. anemia_status
                # 54. anemia_present (not captured)
                None,
                # 55. iron_supplement (not captured)
                None,
                # 56. ferritin_issue (not captured)
                None,
                walk_test,                   # 57. walk_test
                vo2_max,                     # 58. vo2_max
                devices_str,                 # 59. devices
                ecg,                         # 60. ecg
                echo_str,                    # 61. echo
                echo_other,                  # 62. echo_other
                follow_plan                  # 63. follow_plan
            )
            # Call save_patient once and capture patient_id
            patient_id = save_patient(doctor_data)
            st.success(
                f"✅ Doctor form submitted and saved. Patient ID: {patient_id}")
            st.markdown(
                f"[Go to Chatbot Service](chatbot_service.py?patient_id={patient_id})")

    elif doctor_action == "Choose Existing Patient":
        st.info(
            "[Placeholder] Here you can load an existing patient profile from your system")
    elif doctor_action == "General Questioning":
        st.info(
            "[Placeholder] Use this area to ask general medical questions not tied to a patient.")
