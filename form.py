import streamlit as st
import sqlite3


def create_patient_table():
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT,
            age INTEGER,
            sex TEXT,
            height REAL,
            weight REAL,
            bmi REAL,
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
            symptom_triggers TEXT,
            other_trigger_detail TEXT,
            daily_impact TEXT,
            alcohol BOOLEAN,
            alcohol_frequency TEXT,
            smoking BOOLEAN,
            smoking_packs REAL,
            smoking_duration INTEGER,
            medications TEXT,
            other_meds TEXT,
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
            );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_symptoms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            symptom TEXT,
            category TEXT,
            present BOOLEAN,
            severity INTEGER,
            duration TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_comorbidities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            hypertension BOOLEAN,
            diabetes BOOLEAN,
            dyslipidemia BOOLEAN,
            kidney_disease BOOLEAN,
            obesity BOOLEAN,
            sleep_apnea BOOLEAN,
            family_history BOOLEAN,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comorbidity_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            comorbidity_record_id INTEGER,
            detail_key TEXT,
            detail_value TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY (comorbidity_record_id) REFERENCES patient_comorbidities(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cv_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            event_key TEXT,
            event_present BOOLEAN,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        );
""")
    conn.commit()
    conn.close()


def save_patient(
    patient_name, age, sex, height, weight, bmi,
    heart_rate, systolic_bp, diastolic_bp, respiratory_rate,
    oxygen_saturation, temperature, hf_type, lvef, nyha, bnp,
    symptom_triggers_str, other_trigger_detail, daily_impact,
    alcohol, alcohol_frequency, smoking, smoking_packs, smoking_duration,
    medications_str, other_meds, creatinine, potassium, sodium,
    anemia_status, anemia_present, iron_supplement, ferritin_issue,
    walk_test, vo2_max, devices_str, ecg, echo_str, echo_other,
    follow_plan
):
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO patients (
            patient_name, age, sex, height, weight, bmi,
            heart_rate, systolic_bp, diastolic_bp, respiratory_rate,
            oxygen_saturation, temperature, hf_type, lvef, nyha, bnp,
            symptom_triggers, other_trigger_detail, daily_impact,
            alcohol, alcohol_frequency, smoking, smoking_packs, smoking_duration,
            medications, other_meds, creatinine, potassium, sodium,
            anemia_status, anemia_present, iron_supplement, ferritin_issue,
            walk_test, vo2_max, devices, ecg, echo, echo_other,
            follow_plan
        ) VALUES (?, ?, ?, ?, ?,
                   ?, ?, ?, ?, ?,
                   ?, ?, ?, ?, ?,
                   ?, ?, ?, ?, ?,
                   ?, ?, ?, ?, ?,
                   ?, ?, ?, ?, ?,
                   ?, ?, ?, ?, ?,
                   ?, ?, ?, ?, ?)
    """, (
        patient_name, age, sex, height, weight, bmi,
        heart_rate, systolic_bp, diastolic_bp, respiratory_rate,
        oxygen_saturation, temperature, hf_type, lvef, nyha, bnp,
        symptom_triggers_str, other_trigger_detail, daily_impact,
        alcohol, alcohol_frequency, smoking, smoking_packs, smoking_duration,
        medications_str, other_meds, creatinine, potassium, sodium,
        anemia_status, anemia_present, iron_supplement, ferritin_issue,
        walk_test, vo2_max, devices_str, ecg, echo_str, echo_other,
        follow_plan
    ))

    patient_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return patient_id


def save_patient_data(patient_id, individual_symptoms, comorbidities_data, comorbidity_details_data, cv_events_data):
    """
    Inserts related data for a patient into:
    - patient_symptoms
    - patient_comorbidities
    - comorbidity_details
    - cv_events

    Arguments:
    - patient_id: The patient_id from the patients table.
    - individual_symptoms: List of dicts with keys: symptom, category, severity, duration.
    - comorbidities_data: Dict of boolean flags for comorbidities.
    - comorbidity_details_data: List of dicts with keys: detail_key, detail_value.
    - cv_events_data: Dict with keys (event name) and boolean values.
    """
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    # Insert symptoms
    for symptom_entry in individual_symptoms:
        cursor.execute("""
            INSERT INTO patient_symptoms (patient_id, symptom, category, present, severity, duration)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            patient_id,
            symptom_entry['symptom'],
            symptom_entry['category'],
            True,
            symptom_entry['severity'],
            symptom_entry['duration']
        ))

    # Insert comorbidities (main boolean flags)
    cursor.execute("""
        INSERT INTO patient_comorbidities (
            patient_id, hypertension, diabetes, dyslipidemia,
            kidney_disease, obesity, sleep_apnea, family_history
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        patient_id,
        comorbidities_data.get("Hypertension", False),
        comorbidities_data.get("Diabetes", False),
        comorbidities_data.get("Dyslipidemia", False),
        comorbidities_data.get("Kidney Disease", False),
        comorbidities_data.get("Obesity", False),
        comorbidities_data.get("Sleep Apnea", False),
        comorbidities_data.get("Family History of Heart Disease", False)
    ))
    comorbidity_record_id = cursor.lastrowid

    # Insert comorbidity details (e.g. BP control, eGFR range)
    for detail in comorbidity_details_data:
        cursor.execute("""
            INSERT INTO comorbidity_details (patient_id, comorbidity_record_id, detail_key, detail_value)
            VALUES (?, ?, ?, ?)
        """, (
            patient_id,
            comorbidity_record_id,
            detail['detail_key'],
            detail['detail_value']
        ))

    # Insert cardiovascular events
    for event_key, event_present in cv_events_data.items():
        cursor.execute("""
            INSERT INTO cv_events (patient_id, event_key, event_present)
            VALUES (?, ?, ?)
        """, (
            patient_id,
            event_key,
            event_present
        ))

    conn.commit()
    conn.close()


# Create the merged table when the module loads
create_patient_table()
