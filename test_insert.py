import sqlite3

conn = sqlite3.connect("patients.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS patient_info (
        patient_id TEXT PRIMARY KEY,
        name TEXT
    )
""")

cursor.execute(
    "INSERT OR REPLACE INTO patient_info (patient_id, name) VALUES (?, ?)", ("123", "Test Patient"))

conn.commit()
conn.close()
print("✅ Inserted!")
