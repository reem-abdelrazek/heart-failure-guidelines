import sqlite3

conn = sqlite3.connect("patients.db")
cursor = conn.cursor()


def save_patient_form(data):
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_info (
            patient_id TEXT PRIMARY KEY,
            name TEXT,
            age INTEGER,
            sex TEXT,
            height REAL,
            weight REAL,
            bmi REAL,
            bmi_category TEXT,
            hypertension BOOLEAN,
            hypertension_duration INTEGER,
            diabetes BOOLEAN,
            diabetes_duration INTEGER,
            dyslipidemia BOOLEAN,
            alcohol BOOLEAN,
            alcohol_frequency TEXT,
            smoking BOOLEAN,
            smoking_packs REAL,
            smoking_duration INTEGER,
            family_history BOOLEAN,
            family_details TEXT,
            obesity BOOLEAN,
            hf_types TEXT,
            symptoms TEXT,
            symptom_severities TEXT,
            symptom_onset TEXT,
            symptom_triggers TEXT,
            other_trigger TEXT,
            impact TEXT,
            pulse TEXT,
            bp TEXT,
            medications TEXT,
            other_meds TEXT,
            physical_activity TEXT
        )
    """)

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


def save_doctor_form(data):
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctor_form (
            patient_id TEXT,
            heart_rate INTEGER,
            systolic_bp INTEGER,
            diastolic_bp INTEGER,
            respiratory_rate INTEGER,
            oxygen_saturation REAL,
            temperature REAL,
            hf_type TEXT,
            lvef REAL,
            nyha TEXT,
            bnp REAL,
            cardiopulmonary_symptoms TEXT,
            systemic_symptoms TEXT,
            gi_symptoms TEXT,
            symptom_severity TEXT,
            symptom_triggers TEXT,
            symptom_duration TEXT,
            daily_impact TEXT,
            comorbidities TEXT,
            medications TEXT,
            other_meds TEXT,
            cv_events TEXT,
            creatinine REAL,
            potassium REAL,
            sodium REAL,
            anemia_status TEXT,
            anemia_present BOOLEAN,
            iron_supplement BOOLEAN,
            ferritin_issue BOOLEAN,
            walk_test INTEGER,
            vo2_max REAL,
            devices TEXT,
            ecg TEXT,
            echo TEXT,
            echo_other TEXT,
            follow_plan TEXT
        )
    """)

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
