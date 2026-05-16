"""
ClinIQ — Synthetic OMOP Data Generator
Generates realistic synthetic patient data in OMOP CDM format and loads into DuckDB.
No real patient data. No PHI. Safe for portfolio use.
"""

import duckdb
import random
import uuid
from datetime import date, timedelta
from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)

DB_PATH = "data/omop.duckdb"
N_PATIENTS = 5000

GENDERS = {8507: "MALE", 8532: "FEMALE"}

RACES = {
    8527: "White", 8516: "Black or African American",
    8515: "Asian", 8657: "Native Hawaiian or Other Pacific Islander",
    0: "Unknown"
}

CONDITIONS = {
    201826: "Type 2 diabetes mellitus",
    4329847: "Myocardial infarction",
    316866: "Hypertensive disorder",
    255573: "Chronic obstructive lung disease",
    314659: "Coronary arteriosclerosis",
    443392: "Malignant neoplastic disease",
    192279: "Chronic renal disease",
    436670: "Atrial fibrillation",
    4185932: "Asthma",
    380378: "Heart failure",
    4313290: "Allergic rhinitis due to pollen",
    379019:  "Atopic conjunctivitis",
    375545:  "Seasonal allergic rhinitis",
    4227006: "Blurred vision",
}

PEDIATRIC_CONDITIONS = {4313290, 379019, 375545, 4185932}
ALLERGY_CONDITIONS   = {4313290, 379019, 375545}

DRUGS = {
    1503297:  "Metformin 500 MG Oral Tablet",
    1124957:  "Lisinopril 10 MG Oral Tablet",
    1307046:  "Atorvastatin 20 MG Oral Tablet",
    1118084:  "Aspirin 81 MG Oral Tablet",
    1301025:  "Amlodipine 5 MG Oral Tablet",
    1308216:  "Losartan 50 MG Oral Tablet",
    19078461: "Omeprazole 20 MG Oral Capsule",
    1154343:  "Albuterol 0.083 MG/ML Inhalant Solution",
    1326012:  "Furosemide 40 MG Oral Tablet",
    40163554: "Warfarin 5 MG Oral Tablet",
}

ALLERGY_DRUGS = {
    19011773: "Cetirizine 10 MG Oral Tablet",
    1140088:  "Loratadine 10 MG Oral Tablet",
    1154161:  "Montelukast 10 MG Oral Tablet",
    1150771:  "Fluticasone propionate 0.05 MG/ACTUAT Nasal Spray",
    19135843: "Fexofenadine 180 MG Oral Tablet",
}

ALL_DRUGS = {**DRUGS, **ALLERGY_DRUGS}

MEASUREMENTS = {
    3004249: ("Systolic blood pressure", 90, 180, "mmHg"),
    3012888: ("Diastolic blood pressure", 60, 120, "mmHg"),
    3013682: ("Body weight", 45, 150, "kg"),
    3023540: ("Body height", 150, 200, "cm"),
    3005131: ("Glucose", 70, 300, "mg/dL"),
    3007070: ("Hemoglobin A1c", 4.5, 12.0, "%"),
    3016723: ("Creatinine", 0.5, 5.0, "mg/dL"),
    3023103: ("Potassium", 3.0, 6.5, "mEq/L"),
    3019550: ("Sodium", 130, 150, "mEq/L"),
    3000963: ("Hemoglobin", 7.0, 18.0, "g/dL"),
}

VISIT_TYPES = {
    9201: "Inpatient Visit",
    9202: "Outpatient Visit",
    9203: "Emergency Room Visit",
}


def create_schema(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS person (
            person_id INTEGER PRIMARY KEY,
            gender_concept_id INTEGER,
            year_of_birth INTEGER,
            month_of_birth INTEGER,
            day_of_birth INTEGER,
            race_concept_id INTEGER,
            ethnicity_concept_id INTEGER,
            person_source_value VARCHAR,
            first_name VARCHAR,
            last_name VARCHAR,
            phone VARCHAR,
            email VARCHAR,
            address VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS visit_occurrence (
            visit_occurrence_id INTEGER PRIMARY KEY,
            person_id INTEGER,
            visit_concept_id INTEGER,
            visit_start_date DATE,
            visit_end_date DATE,
            visit_type_concept_id INTEGER
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS condition_occurrence (
            condition_occurrence_id INTEGER PRIMARY KEY,
            person_id INTEGER,
            condition_concept_id INTEGER,
            condition_start_date DATE,
            condition_end_date DATE,
            visit_occurrence_id INTEGER,
            condition_source_value VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS drug_exposure (
            drug_exposure_id INTEGER PRIMARY KEY,
            person_id INTEGER,
            drug_concept_id INTEGER,
            drug_exposure_start_date DATE,
            drug_exposure_end_date DATE,
            quantity FLOAT,
            visit_occurrence_id INTEGER,
            drug_source_value VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS measurement (
            measurement_id INTEGER PRIMARY KEY,
            person_id INTEGER,
            measurement_concept_id INTEGER,
            measurement_date DATE,
            value_as_number FLOAT,
            unit_source_value VARCHAR,
            visit_occurrence_id INTEGER
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS procedure_occurrence (
            procedure_occurrence_id INTEGER PRIMARY KEY,
            person_id INTEGER,
            procedure_concept_id INTEGER,
            procedure_date DATE,
            visit_occurrence_id INTEGER,
            procedure_source_value VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS concept (
            concept_id INTEGER PRIMARY KEY,
            concept_name VARCHAR,
            domain_id VARCHAR,
            vocabulary_id VARCHAR
        )
    """)


def populate_concepts(con):
    rows = []
    for cid, name in GENDERS.items():
        rows.append((cid, name, "Gender", "Gender"))
    for cid, name in RACES.items():
        rows.append((cid, name, "Race", "Race"))
    for cid, name in CONDITIONS.items():
        rows.append((cid, name, "Condition", "SNOMED"))
    for cid, name in ALL_DRUGS.items():
        rows.append((cid, name, "Drug", "RxNorm"))
    for cid, (name, *_) in MEASUREMENTS.items():
        rows.append((cid, name, "Measurement", "LOINC"))
    for cid, name in VISIT_TYPES.items():
        rows.append((cid, name, "Visit", "Visit"))
    con.executemany("INSERT OR IGNORE INTO concept VALUES (?, ?, ?, ?)", rows)


def random_date(start_year=2015, end_year=2024):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))


def generate_patients(n):
    patients = []
    for i in range(1, n + 1):
        if random.random() < 0.15:
            dob = fake.date_of_birth(minimum_age=5, maximum_age=17)
        else:
            dob = fake.date_of_birth(minimum_age=18, maximum_age=90)
        gender_id = random.choice(list(GENDERS.keys()))
        race_id = random.choice(list(RACES.keys()))
        first_name = fake.first_name()
        last_name = fake.last_name()
        phone = fake.phone_number()
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,99)}@{fake.free_email_domain()}"
        address = fake.address().replace("\n", ", ")
        patients.append((
            i, gender_id, dob.year, dob.month, dob.day,
            race_id, 0, str(uuid.uuid4()),
            first_name, last_name, phone, email, address
        ))
    return patients


def generate_visits(patients):
    visits = []
    vid = 1
    patient_visits = {}
    for (pid, *_) in patients:
        n_visits = random.randint(1, 8)
        patient_visits[pid] = []
        for _ in range(n_visits):
            visit_type = random.choice(list(VISIT_TYPES.keys()))
            start = random_date()
            end = start + timedelta(days=random.randint(0, 5))
            visits.append((vid, pid, visit_type, start, end, 44818517))
            patient_visits[pid].append((vid, start))
            vid += 1
    return visits, patient_visits


def generate_conditions(patients, patient_visits):
    rows = []
    cid = 1
    all_conditions = list(CONDITIONS.keys())
    adult_conditions = [c for c in all_conditions if c not in PEDIATRIC_CONDITIONS]
    pediatric_conditions = list(PEDIATRIC_CONDITIONS)
    for (pid, gender_id, year_of_birth, *_) in patients:
        age = 2026 - year_of_birth
        is_child = age < 18
        if is_child:
            n_conditions = random.randint(1, 3)
            pool = pediatric_conditions + random.sample(adult_conditions, 2)
            chosen = random.sample(pool, min(n_conditions, len(pool)))
        else:
            n_conditions = random.randint(0, 4)
            pool = adult_conditions
            if random.random() < 0.2:
                pool = pool + pediatric_conditions
            chosen = random.sample(pool, min(n_conditions, len(pool)))
        for concept_id in chosen:
            start = random_date()
            vid = random.choice(patient_visits[pid])[0] if patient_visits[pid] else None
            rows.append((
                cid, pid, concept_id, start,
                start + timedelta(days=random.randint(30, 730)),
                vid, CONDITIONS[concept_id]
            ))
            cid += 1
    return rows


def generate_drugs(patients, patient_visits, condition_rows):
    allergy_patient_ids = {
        row[1] for row in condition_rows if row[2] in ALLERGY_CONDITIONS
    }
    asthma_patient_ids = {
        row[1] for row in condition_rows if row[2] == 4185932
    }
    rows = []
    did = 1
    general_drug_list = list(DRUGS.keys())
    allergy_drug_list = list(ALLERGY_DRUGS.keys())
    for (pid, *_) in patients:
        chosen = []
        if pid in allergy_patient_ids:
            n_allergy = random.randint(2, min(4, len(allergy_drug_list)))
            chosen += random.sample(allergy_drug_list, n_allergy)
            n_general = random.randint(0, 2)
            chosen += random.sample(general_drug_list, n_general)
        elif pid in asthma_patient_ids:
            chosen.append(1154343)
            n_other = random.randint(0, 3)
            chosen += random.sample(general_drug_list, n_other)
        else:
            n_drugs = random.randint(0, 5)
            chosen = random.sample(general_drug_list, min(n_drugs, len(general_drug_list)))
        for concept_id in chosen:
            start = random_date()
            vid = random.choice(patient_visits[pid])[0] if patient_visits[pid] else None
            rows.append((
                did, pid, concept_id, start,
                start + timedelta(days=random.randint(30, 365)),
                random.randint(1, 3) * 30.0,
                vid, ALL_DRUGS[concept_id]
            ))
            did += 1
    return rows


def generate_measurements(patients, patient_visits):
    rows = []
    mid = 1
    meas_list = list(MEASUREMENTS.keys())
    for (pid, *_) in patients:
        n_meas = random.randint(2, 10)
        chosen = random.choices(meas_list, k=n_meas)
        for concept_id in chosen:
            name, low, high, unit = MEASUREMENTS[concept_id]
            value = round(random.uniform(low, high), 1)
            mdate = random_date()
            vid = random.choice(patient_visits[pid])[0] if patient_visits[pid] else None
            rows.append((mid, pid, concept_id, mdate, value, unit, vid))
            mid += 1
    return rows


def main():
    import os
    os.makedirs("data", exist_ok=True)

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing database at {DB_PATH}")

    print(f"Connecting to DuckDB at {DB_PATH}...")
    con = duckdb.connect(DB_PATH)

    print("Creating OMOP schema...")
    create_schema(con)
    populate_concepts(con)

    print(f"Generating {N_PATIENTS} synthetic patients...")
    patients = generate_patients(N_PATIENTS)
    con.executemany("INSERT INTO person VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", patients)

    print("Generating visits...")
    visits, patient_visits = generate_visits(patients)
    con.executemany("INSERT INTO visit_occurrence VALUES (?,?,?,?,?,?)", visits)

    print("Generating conditions...")
    conditions = generate_conditions(patients, patient_visits)
    con.executemany("INSERT INTO condition_occurrence VALUES (?,?,?,?,?,?,?)", conditions)

    print("Generating drug exposures (allergy-aware)...")
    drugs = generate_drugs(patients, patient_visits, conditions)
    con.executemany("INSERT INTO drug_exposure VALUES (?,?,?,?,?,?,?,?)", drugs)

    print("Generating measurements...")
    measurements = generate_measurements(patients, patient_visits)
    con.executemany("INSERT INTO measurement VALUES (?,?,?,?,?,?,?)", measurements)

    print("\n Done. Row counts:")
    for table in ["person", "visit_occurrence", "condition_occurrence",
                  "drug_exposure", "measurement", "concept"]:
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count:,}")

    con.close()
    print(f"\nDatabase saved to {DB_PATH}")


if __name__ == "__main__":
    main()
