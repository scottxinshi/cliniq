"""
ClinIQ — Patient Timeline
Queries a single patient's full OMOP record and generates an AI clinical narrative.
"""

import os
import duckdb
import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "data/omop.duckdb"


def get_patient_list() -> pd.DataFrame:
    """Return a summary list of all patients for the selector."""
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute("""
        SELECT
            p.person_id,
            p.first_name,
            p.last_name,
            (2026 - p.year_of_birth) AS age,
            gc.concept_name AS gender,
            rc.concept_name AS race,
            p.phone,
            p.email,
            p.address,
            COUNT(DISTINCT co.condition_occurrence_id) AS conditions,
            COUNT(DISTINCT de.drug_exposure_id) AS medications,
            COUNT(DISTINCT v.visit_occurrence_id) AS visits
        FROM person p
        LEFT JOIN concept gc ON p.gender_concept_id = gc.concept_id
        LEFT JOIN concept rc ON p.race_concept_id = rc.concept_id
        LEFT JOIN condition_occurrence co ON p.person_id = co.person_id
        LEFT JOIN drug_exposure de ON p.person_id = de.person_id
        LEFT JOIN visit_occurrence v ON p.person_id = v.person_id
        GROUP BY p.person_id, p.first_name, p.last_name, age,
                 gc.concept_name, rc.concept_name, p.phone, p.email, p.address
        ORDER BY p.last_name, p.first_name
    """).df()
    con.close()
    return df


def get_patient_summary(patient_id: int) -> dict:
    """Fetch all OMOP data for a single patient."""
    con = duckdb.connect(DB_PATH, read_only=True)

    # Demographics
    demo = con.execute("""
        SELECT
            p.person_id,
            p.first_name,
            p.last_name,
            (2026 - p.year_of_birth) AS age,
            p.year_of_birth,
            gc.concept_name AS gender,
            rc.concept_name AS race,
            p.phone,
            p.email,
            p.address
        FROM person p
        LEFT JOIN concept gc ON p.gender_concept_id = gc.concept_id
        LEFT JOIN concept rc ON p.race_concept_id = rc.concept_id
        WHERE p.person_id = ?
    """, [patient_id]).df()

    # Conditions
    conditions = con.execute("""
        SELECT
            c.concept_name AS condition,
            strftime(co.condition_start_date, '%b %d, %Y') AS diagnosed,
            strftime(co.condition_end_date,   '%b %d, %Y') AS resolved
        FROM condition_occurrence co
        JOIN concept c ON co.condition_concept_id = c.concept_id
        WHERE co.person_id = ?
        ORDER BY co.condition_start_date
    """, [patient_id]).df()

    # Medications
    medications = con.execute("""
        SELECT
            c.concept_name AS medication,
            strftime(de.drug_exposure_start_date, '%b %d, %Y') AS started,
            strftime(de.drug_exposure_end_date,   '%b %d, %Y') AS ended,
            de.quantity
        FROM drug_exposure de
        JOIN concept c ON de.drug_concept_id = c.concept_id
        WHERE de.person_id = ?
        ORDER BY de.drug_exposure_start_date
    """, [patient_id]).df()

    # Visits
    visits = con.execute("""
        SELECT
            vc.concept_name AS visit_type,
            strftime(v.visit_start_date, '%b %d, %Y') AS date,
            strftime(v.visit_end_date,   '%b %d, %Y') AS end_date
        FROM visit_occurrence v
        JOIN concept vc ON v.visit_concept_id = vc.concept_id
        WHERE v.person_id = ?
        ORDER BY v.visit_start_date DESC
    """, [patient_id]).df()

    # Measurements (latest per type)
    measurements = con.execute("""
        SELECT
            c.concept_name AS measurement,
            m.value_as_number AS value,
            m.unit_source_value AS unit,
            strftime(m.measurement_date, '%b %d, %Y') AS date
        FROM measurement m
        JOIN concept c ON m.measurement_concept_id = c.concept_id
        WHERE m.person_id = ?
        ORDER BY m.measurement_date DESC
        LIMIT 10
    """, [patient_id]).df()

    con.close()

    return {
        "demographics": demo,
        "conditions": conditions,
        "medications": medications,
        "visits": visits,
        "measurements": measurements,
    }


def generate_narrative(summary: dict) -> str:
    """Generate a plain-language clinical summary using the LLM."""
    demo = summary["demographics"]
    if demo.empty:
        return "Patient not found."

    row = demo.iloc[0]
    age = row["age"]
    gender = row["gender"]
    race = row["race"]

    conditions = summary["conditions"]["condition"].tolist() if not summary["conditions"].empty else []
    medications = summary["medications"]["medication"].tolist() if not summary["medications"].empty else []
    visits = len(summary["visits"])
    measurements = summary["measurements"]

    # Build context string for LLM
    context = f"""
Patient: {gender}, age {age}, {race}
Total visits: {visits}
Diagnosed conditions: {", ".join(conditions) if conditions else "None on record"}
Current medications: {", ".join(medications) if medications else "None on record"}
Recent measurements: {", ".join([f"{r.measurement} {r.value} {r.unit}" for _, r in measurements.iterrows()]) if not measurements.empty else "None on record"}
"""

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.3,
    )

    messages = [
        SystemMessage(content="""You are a clinical documentation assistant.
Given a patient's structured record, write a concise clinical summary (3-5 sentences) 
that a doctor could read at the start of a visit. 
Focus on: active conditions, current medications, any notable patterns or concerns.
Write in plain clinical language. Do not invent information not in the record.
Do not mention specific dates or numeric IDs."""),
        HumanMessage(content=f"Summarize this patient record:\n{context}"),
    ]

    response = llm.invoke(messages)
    return response.content
