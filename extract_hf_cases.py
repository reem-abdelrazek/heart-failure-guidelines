import os
import glob
import random
import pandas as pd
import numpy as np


def load_csv(folder, name):
    """
    Robust loader: finds any file in `folder` whose name starts with `name`
    (case-insensitive) and ends with .csv or .csv.gz.
    """
    for fname in os.listdir(folder):
        low = fname.lower()
        if low.startswith(name.lower()) and low.endswith('.csv'):
            return pd.read_csv(os.path.join(folder, fname))
        if low.startswith(name.lower()) and low.endswith('.csv.gz'):
            return pd.read_csv(os.path.join(folder, fname), compression='gzip')
    raise FileNotFoundError(f"No {name}.csv(.gz) in {folder}")


# ----------------------------------------
# Configuration: your actual Windows paths
# ----------------------------------------
HOSP_DIR = r"C:\Users\reema\OneDrive\Desktop\thesis\heart-failure-guidelines\hosp"
ICU_DIR = r"C:\Users\reema\OneDrive\Desktop\thesis\heart-failure-guidelines\icu"
OUTPUT = "heart_failure_cases.csv"
TOTAL_CASES = 30
AGE_QUOTAS = {"<60": 10, "60-75": 10, ">75": 10}

# 1) Load & filter for HF admissions by ICD-9 "428.*" or ICD-10 "I50.*"
print("Loading diagnoses...")
diag = load_csv(HOSP_DIR, "diagnoses_icd")
hf_diag = diag[diag["icd_code"].str.startswith(("428.", "I50"))]
hf_adm = hf_diag["hadm_id"].drop_duplicates()

# 2) Pull demographics & bin ages
print("Loading demographics...")
pts = load_csv(HOSP_DIR, "patients")
adm = load_csv(HOSP_DIR, "admissions")
demo = adm[adm["hadm_id"].isin(
    hf_adm)][["hadm_id", "subject_id", "admittime", "dischtime"]]
demo = demo.merge(pts[["subject_id", "gender", "anchor_age", "anchor_year", "anchor_year_group"]],
                  on="subject_id", how="left") \
    .rename(columns={"anchor_age": "age"})
demo["age_bin"] = demo["age"].apply(
    lambda x: "<60" if x < 60 else ("60-75" if x <= 75 else ">75"))
demo["los_days"] = (pd.to_datetime(demo["dischtime"]) -
                    pd.to_datetime(demo["admittime"])).dt.days

# 3) Stratified sample by age quotas
print("Selecting diverse cases...")
samples = []
for bin_label, quota in AGE_QUOTAS.items():
    ids = demo[demo["age_bin"] == bin_label]["hadm_id"].tolist()
    if ids:
        samples += random.sample(ids, min(quota, len(ids)))
remaining = list(set(hf_adm) - set(samples))
if len(samples) < TOTAL_CASES and remaining:
    samples += random.sample(remaining, TOTAL_CASES - len(samples))
cases = pd.DataFrame({"hadm_id": samples})

# 4) Merge back demographic fields
cases = cases.merge(demo.drop_duplicates("hadm_id"), on="hadm_id", how="left")

# 5) Height & weight → BMI
print("Loading vitals and measurements...")
charte = load_csv(ICU_DIR, "chartevents")[
    ["hadm_id", "itemid", "valuenum", "charttime"]]
hw = charte[charte["itemid"].isin([226707, 226512])]  # height and weight
hw = hw.groupby(["hadm_id", "itemid"])["valuenum"].mean().unstack()
hw.columns = ["height_cm", "weight_kg"]
cases = cases.merge(hw.reset_index(), on="hadm_id", how="left")
cases["bmi"] = (cases["weight_kg"] / ((cases["height_cm"]/100)**2)).round(1)

# 6) Vitals in the first hour
vmap = {
    220045: "heart_rate", 220179: "systolic_bp", 220180: "diastolic_bp",
    220210: "respiratory_rate", 220277: "oxygen_saturation", 223761: "temperature"
}
v = charte[charte["itemid"].isin(vmap)].copy()
v["measure"] = v["itemid"].map(vmap)
v = v.groupby(["hadm_id", "measure"])["valuenum"].agg(
    ['mean', 'min', 'max']).reset_index()
v = v.pivot(index="hadm_id", columns="measure", values=["mean", "min", "max"])
v.columns = [f"{col[1]}_{col[0]}" for col in v.columns]
cases = cases.merge(v.reset_index(), on="hadm_id", how="left")

# 7) Labs
print("Loading lab results...")
labs = load_csv(HOSP_DIR, "labevents")[
    ["hadm_id", "itemid", "valuenum", "charttime"]]
lmap = {
    50384: "bnp", 50912: "creatinine", 50983: "potassium",
    50902: "sodium", 51221: "hemoglobin", 51222: "hematocrit",
    51248: "wbc", 51249: "platelet", 51250: "rdw", 51251: "mcv",
    51252: "mch", 51253: "mchc", 51254: "rbc", 51255: "hct"
}
lab = labs[labs["itemid"].isin(lmap)].copy()
lab["lab"] = lab["itemid"].map(lmap)
lab = lab.groupby(["hadm_id", "lab"])["valuenum"].agg(
    ['mean', 'min', 'max']).reset_index()
lab = lab.pivot(index="hadm_id", columns="lab", values=["mean", "min", "max"])
lab.columns = [f"{col[1]}_{col[0]}" for col in lab.columns]
cases = cases.merge(lab.reset_index(), on="hadm_id", how="left")

# 8) Comorbidity flags and details
print("Processing comorbidities...")
flags = {
    # Expanded hypertension codes
    "hypertension": ["401.", "402.", "403.", "404.", "405."],
    "diabetes": ["250.", "E11.", "E10.", "E13."],  # Added ICD-10 codes
    "dyslipidemia": ["272.", "E78."],  # Added ICD-10 codes
    "kidney_disease": ["585.", "N18.", "N19."],  # Added ICD-10 codes
    "obesity": ["278.", "E66."],  # Added ICD-10 codes
    "sleep_apnea": ["327.23", "G47.3"],  # Added ICD-10 codes
    "anemia": ["280.", "281.", "282.", "283.", "284.", "285.", "D50.", "D51.", "D52.", "D53.", "D55.", "D56.", "D57.", "D58.", "D59."],
    "atrial_fibrillation": ["427.3", "I48."],  # Added ICD-10 codes
    "coronary_artery_disease": ["414.", "I25."],  # Added ICD-10 codes
    "peripheral_vascular": ["443.", "I73."],  # Added ICD-10 codes
    "stroke": ["434.", "I63.", "I64."],  # Added ICD-10 codes
    "copd": ["496.", "J44."]  # Added ICD-10 codes
}

# Print total number of diagnoses for debugging
print(f"\nTotal number of diagnoses: {len(diag)}")
print(f"Number of unique hadm_ids: {diag['hadm_id'].nunique()}")

for col, codes in flags.items():
    # Check for any matching codes
    has = set(diag[diag["icd_code"].str.startswith(tuple(codes))]["hadm_id"])
    cases[col] = cases["hadm_id"].isin(has)
    # Print debugging information
    print(f"\n{col}:")
    print(f"Number of patients with {col}: {cases[col].sum()}")
    print(f"ICD codes used: {codes}")

# 9) Heart Failure Type Classification
print("Classifying heart failure types...")
hf_types = {
    # Ischemic heart disease
    "Ischemic": ["410.", "411.", "412.", "413.", "414."],
    "Dilated": ["425.4"],  # Dilated cardiomyopathy
    "Hypertrophic": ["425.1"],  # Hypertrophic cardiomyopathy
    # Valvular heart disease
    "Valvular": ["394.", "395.", "396.", "397.", "424."],
    "Peripartum": ["674.5"],  # Peripartum cardiomyopathy
    "Restrictive": ["425.5"],  # Restrictive cardiomyopathy
    "Right Ventricular": ["425.2"]  # Right ventricular cardiomyopathy
}

cases["hf_type"] = "Other"
for hf_type, codes in hf_types.items():
    mask = diag[diag["hadm_id"].isin(cases["hadm_id"]) &
                diag["icd_code"].str.startswith(tuple(codes))]["hadm_id"]
    cases.loc[cases["hadm_id"].isin(mask), "hf_type"] = hf_type

# 10) Medications
print("Processing medications...")
pres = load_csv(HOSP_DIR, "prescriptions")
pres["drug"] = pres["drug"].str.lower()
hfmed = pres[pres["drug"].str.contains(
    "lisinopril|furosemide|metoprolol|spironolactone|carvedilol|bisoprolol|"
    "sacubitril|valsartan|digoxin|hydralazine|nitrate|diltiazem|verapamil|"
    "amiodarone|dofetilide|sotalol|warfarin|apixaban|rivaroxaban|dabigatran|"
    "aspirin|clopidogrel|ticagrelor|prasugrel|atorvastatin|rosuvastatin|"
    "simvastatin|pravastatin|insulin|metformin|glipizide|glimepiride")]
md = hfmed.groupby("hadm_id")["drug"] \
    .unique().apply(lambda a: ", ".join(a)) \
    .reset_index().rename(columns={"drug": "medications"})
cases = cases.merge(md, on="hadm_id", how="left")

# 11) Procedures and Devices
print("Processing procedures and devices...")
proc = load_csv(HOSP_DIR, "procedures_icd")
device_codes = {
    "ICD": ["37.94", "37.95", "37.96", "37.97", "37.98"],  # ICD codes
    "Pacemaker": ["37.80", "37.81", "37.82", "37.83"],  # Pacemaker codes
    "CABG": ["36.1"],  # CABG codes
    "PCI": ["36.06", "36.07"]  # PCI codes
}

for device, codes in device_codes.items():
    has = set(proc[proc["icd_code"].str.startswith(tuple(codes))]["hadm_id"])
    cases[f"has_{device.lower()}"] = cases["hadm_id"].isin(has)

# 12) Add derived fields
print("Adding derived fields...")
# NYHA Classification based on symptoms and vitals
cases["nyha"] = pd.cut(
    cases["oxygen_saturation_mean"],
    bins=[0, 90, 95, 98, 100],
    labels=["IV", "III", "II", "I"]
)

# Anemia status
cases["anemia_status"] = pd.cut(
    cases["hemoglobin_mean"],
    bins=[0, 10, 12, 14, 100],
    labels=["Severe", "Moderate", "Mild", "Normal"]
)

# 13) Clean and format final output
print("Preparing final output...")
# Define all possible columns
all_columns = [
    # Demographics
    "hadm_id", "subject_id", "age", "gender", "height_cm", "weight_kg", "bmi",
    "los_days", "anchor_year_group",

    # Vitals (mean, min, max)
    "heart_rate_mean", "heart_rate_min", "heart_rate_max",
    "systolic_bp_mean", "systolic_bp_min", "systolic_bp_max",
    "diastolic_bp_mean", "diastolic_bp_min", "diastolic_bp_max",
    "respiratory_rate_mean", "respiratory_rate_min", "respiratory_rate_max",
    "oxygen_saturation_mean", "oxygen_saturation_min", "oxygen_saturation_max",
    "temperature_mean", "temperature_min", "temperature_max",

    # Clinical Status
    "hf_type", "nyha",

    # Labs (mean, min, max)
    "bnp_mean", "bnp_min", "bnp_max",
    "creatinine_mean", "creatinine_min", "creatinine_max",
    "potassium_mean", "potassium_min", "potassium_max",
    "sodium_mean", "sodium_min", "sodium_max",
    "hemoglobin_mean", "hemoglobin_min", "hemoglobin_max",
    "hematocrit_mean", "hematocrit_min", "hematocrit_max",
    "wbc_mean", "wbc_min", "wbc_max",
    "platelet_mean", "platelet_min", "platelet_max",

    # Comorbidities
    "hypertension", "diabetes", "dyslipidemia", "kidney_disease",
    "obesity", "sleep_apnea", "anemia", "atrial_fibrillation",
    "coronary_artery_disease", "peripheral_vascular", "stroke", "copd",

    # Procedures and Devices
    "has_icd", "has_pacemaker", "has_cabg", "has_pci",

    # Medications
    "medications"
]

# Store summary statistics before column renaming
age_distribution = cases["age_bin"].value_counts()
hf_types_distribution = cases["hf_type"].value_counts()
nyha_distribution = cases["nyha"].value_counts()
comorbidity_counts = {
    "Hypertension": cases["hypertension"].sum(),
    "Diabetes": cases["diabetes"].sum(),
    "Dyslipidemia": cases["dyslipidemia"].sum(),
    "Kidney Disease": cases["kidney_disease"].sum(),
    "Obesity": cases["obesity"].sum(),
    "Sleep Apnea": cases["sleep_apnea"].sum(),
    "Anemia": cases["anemia"].sum(),
    "Atrial Fibrillation": cases["atrial_fibrillation"].sum()
}

# Add any missing columns with NaN values
for col in all_columns:
    if col not in cases.columns:
        cases[col] = np.nan

# Select and rename columns
cases = cases[all_columns].copy()
cases.columns = [col.replace("_", " ").title() for col in cases.columns]

# 14) Export
print("Saving results...")
cases.to_csv(OUTPUT, index=False)

# Print summary statistics using stored values
print("\nAge distribution:")
print(age_distribution)
print("\nHeart failure types:")
print(hf_types_distribution)
print("\nNYHA classification:")
print(nyha_distribution)
print("\nComorbidities:")
for condition, count in comorbidity_counts.items():
    print(f"{condition}: {count} cases")
