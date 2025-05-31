import streamlit as st
import sqlite3


def create_patient_table():
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    # Drop existing patient_consents table if it exists
    cursor.execute("DROP TABLE IF EXISTS patient_consents;")

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
            rhythm TEXT,
            systolic_bp INTEGER,
            diastolic_bp INTEGER,
            respiratory_rate INTEGER,
            oxygen_saturation REAL,
            temperature REAL,
            edema_locations TEXT,
            edema_grade TEXT,
            jvp TEXT,
            hepatomegaly TEXT,
            hepatomegaly_span REAL,
            lung_findings TEXT,
            heart_sounds TEXT,
            murmurs TEXT,
            murmur_other TEXT,
            hf_type TEXT,
            EF_type TEXT,
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
            activity TEXT,
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
            ca_findings TEXT,
            ca_other_details TEXT,
            mri_findings TEXT,
            mri_other_details TEXT,
            holter_findings TEXT,
            holter_other_details TEXT,
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_consents (
            consent_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            clinical_care_consent BOOLEAN,
            quality_research_consent BOOLEAN,
            ai_training_consent BOOLEAN,
            consent_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consent_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            action TEXT NOT NULL,
            purpose TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        );
    """)
    conn.commit()
    conn.close()


def save_consent(patient_id, clinical_care_consent, quality_research_consent, ai_training_consent):
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    # First, log the consent action
    log_consent_action(patient_id, "CONSENT_GIVEN",
                       "CLINICAL_CARE" if clinical_care_consent else "CONSENT_DENIED")
    if quality_research_consent:
        log_consent_action(patient_id, "CONSENT_GIVEN", "QUALITY_RESEARCH")
    if ai_training_consent:
        log_consent_action(patient_id, "CONSENT_GIVEN", "AI_TRAINING")

    # Then save the consent data
    cursor.execute("""
        INSERT INTO patient_consents 
        (patient_id, clinical_care_consent, quality_research_consent, ai_training_consent)
        VALUES (?, ?, ?, ?)
    """, (patient_id, clinical_care_consent, quality_research_consent, ai_training_consent))
    conn.commit()
    conn.close()


def save_patient(
    patient_name, age, sex, height, weight, bmi,
    heart_rate, rhythm, systolic_bp, diastolic_bp, respiratory_rate,
    oxygen_saturation, temperature, edema_locations, edema_grade, jvp, hepatomegaly, hepatomegaly_span, lung_findings, heart_sounds, murmurs, murmur_other,
    hf_type, EF_type, lvef, nyha, bnp,
    symptom_triggers_str, other_trigger_detail, daily_impact,
    alcohol, alcohol_frequency, smoking, smoking_packs, smoking_duration, activity,
    medications_str, other_meds, creatinine, potassium, sodium,
    anemia_status, anemia_present, iron_supplement, ferritin_issue,
    walk_test, vo2_max, devices_str, ecg, echo_str, echo_other,
    ca_findings, ca_other_details, mri_findings, mri_other_details, holter_findings, holter_other_details,
    follow_plan
):
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO patients (
            patient_name, age, sex, height, weight, bmi,
            heart_rate, rhythm, systolic_bp, diastolic_bp, respiratory_rate,
            oxygen_saturation, temperature, edema_locations, edema_grade, jvp, hepatomegaly, hepatomegaly_span, lung_findings, heart_sounds, murmurs, murmur_other,
            hf_type, EF_type, lvef, nyha, bnp,
            symptom_triggers, other_trigger_detail, daily_impact,
            alcohol, alcohol_frequency, smoking, smoking_packs, smoking_duration, activity,
            medications, other_meds, creatinine, potassium, sodium,
            anemia_status, anemia_present, iron_supplement, ferritin_issue,
            walk_test, vo2_max, devices, ecg, echo, echo_other,
            ca_findings, ca_other_details, mri_findings, mri_other_details, holter_findings, holter_other_details,
            follow_plan
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        patient_name, age, sex, height, weight, bmi,
        heart_rate, rhythm, systolic_bp, diastolic_bp, respiratory_rate,
        oxygen_saturation, temperature, edema_locations, edema_grade, jvp, hepatomegaly, hepatomegaly_span, lung_findings, heart_sounds, murmurs, murmur_other,
        hf_type, EF_type, lvef, nyha, bnp,
        symptom_triggers_str, other_trigger_detail, daily_impact,
        alcohol, alcohol_frequency, smoking, smoking_packs, smoking_duration, activity,
        medications_str, other_meds, creatinine, potassium, sodium,
        anemia_status, anemia_present, iron_supplement, ferritin_issue,
        walk_test, vo2_max, devices_str, ecg, echo_str, echo_other,
        ca_findings, ca_other_details, mri_findings, mri_other_details, holter_findings, holter_other_details,
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


def check_consent(patient_id, purpose):
    """Check if a patient has given consent for a specific purpose"""
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT consent_given, withdrawal_date 
        FROM patient_consents 
        WHERE patient_id = ? AND purpose = ?
        ORDER BY consent_date DESC LIMIT 1
    """, (patient_id, purpose))

    result = cursor.fetchone()
    conn.close()

    if not result:
        return False

    consent_given, withdrawal_date = result
    return consent_given and withdrawal_date is None


def record_consent(patient_id, purpose, consent_given, consent_text, consent_version):
    """Record a new consent decision"""
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO patient_consents 
        (patient_id, purpose, consent_given, consent_text, consent_version)
        VALUES (?, ?, ?, ?, ?)
    """, (patient_id, purpose, consent_given, consent_text, consent_version))

    conn.commit()
    conn.close()


def withdraw_consent(patient_id, purpose):
    """Withdraw consent for a specific purpose"""
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE patient_consents 
        SET withdrawal_date = CURRENT_TIMESTAMP
        WHERE patient_id = ? AND purpose = ? AND withdrawal_date IS NULL
    """, (patient_id, purpose))

    conn.commit()
    conn.close()


def log_consent_action(patient_id, action, purpose, ip_address=None, user_agent=None):
    """Log consent-related actions for audit purposes"""
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO consent_audit_log 
        (patient_id, action, purpose, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?)
    """, (patient_id, action, purpose, ip_address, user_agent))

    conn.commit()
    conn.close()


def get_patient_data(patient_id):
    """Get patient data with decryption"""
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    # Get patient data
    cursor.execute("""
        SELECT * FROM patients WHERE patient_id = ?
    """, (patient_id,))

    columns = [description[0] for description in cursor.description]
    patient_data = dict(zip(columns, cursor.fetchone()))

    conn.close()
    return patient_data


def get_patient_symptoms(patient_id):
    """Get patient symptoms with decryption"""
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM patient_symptoms WHERE patient_id = ?
    """, (patient_id,))

    columns = [description[0] for description in cursor.description]
    symptoms = []
    for row in cursor.fetchall():
        symptom_data = dict(zip(columns, row))
        symptoms.append(symptom_data)

    conn.close()
    return symptoms


def get_patient_consents(patient_id):
    """Get patient consents with decryption"""
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM patient_consents WHERE patient_id = ?
    """, (patient_id,))

    columns = [description[0] for description in cursor.description]
    consents = []
    for row in cursor.fetchall():
        consent_data = dict(zip(columns, row))
        consents.append(consent_data)

    conn.close()
    return consents


def withdraw_consent_and_delete_data(patient_id):
    """Withdraw consent and delete all patient data"""
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    try:
        # Log the withdrawal action
        log_consent_action(patient_id, "CONSENT_WITHDRAWN", "CLINICAL_CARE")

        # Delete from all related tables
        cursor.execute(
            "DELETE FROM patient_symptoms WHERE patient_id = ?", (patient_id,))
        cursor.execute(
            "DELETE FROM patient_comorbidities WHERE patient_id = ?", (patient_id,))
        cursor.execute(
            "DELETE FROM comorbidity_details WHERE patient_id = ?", (patient_id,))
        cursor.execute(
            "DELETE FROM cv_events WHERE patient_id = ?", (patient_id,))
        cursor.execute(
            "DELETE FROM patient_consents WHERE patient_id = ?", (patient_id,))
        cursor.execute(
            "DELETE FROM patients WHERE patient_id = ?", (patient_id,))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# Create the merged table when the module loads
create_patient_table()
