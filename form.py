import streamlit as st
import sqlite3


def create_patient_table():
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_info (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            sex TEXT NOT NULL,
            height REAL NOT NULL,
            weight REAL NOT NULL,
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
            hf_type TEXT,  -- merged column from hf_types/hf_type
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
            physical_activity TEXT,
            heart_rate INTEGER,
            systolic_bp INTEGER,
            diastolic_bp INTEGER,
            respiratory_rate INTEGER,
            oxygen_saturation REAL,
            temperature REAL,
            lvef REAL,
            nyha TEXT,
            bnp REAL,
            cardiopulmonary_symptoms TEXT,
            systemic_symptoms TEXT,
            gi_symptoms TEXT,
            symptom_severity TEXT,
            symptom_duration TEXT,
            daily_impact TEXT,
            comorbidities TEXT,
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
    conn.commit()
    conn.close()


def save_patient(data):
    """
    Inserts a new record into the merged patient_info table and returns the new patient_id.
    'data' should be a tuple with 63 values corresponding to all columns except patient_id.
    """
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO patient_info (
            name, age, sex, height, weight, bmi, bmi_category,
            hypertension, hypertension_duration, diabetes, diabetes_duration,
            dyslipidemia, alcohol, alcohol_frequency, smoking,
            smoking_packs, smoking_duration, family_history, family_details,
            obesity, hf_type, symptoms, symptom_severities, symptom_onset,
            symptom_triggers, other_trigger, impact, pulse, bp,
            medications, other_meds, physical_activity,
            heart_rate, systolic_bp, diastolic_bp, respiratory_rate, oxygen_saturation,
            temperature, lvef, nyha, bnp, cardiopulmonary_symptoms,
            systemic_symptoms, gi_symptoms, symptom_severity, symptom_duration, daily_impact,
            comorbidities, cv_events, creatinine, potassium, sodium,
            anemia_status, anemia_present, iron_supplement, ferritin_issue, walk_test,
            vo2_max, devices, ecg, echo, echo_other, follow_plan
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?
        )
    """, data)
    conn.commit()
    patient_id = cursor.lastrowid  # Capture the new patient ID
    conn.close()
    return patient_id  # Return the captured patient_id


# Create the merged table when the module loads
create_patient_table()
