"""
ClinIQ — Schema Router
Knows the OMOP CDM table definitions and selects only the relevant ones
for a given question. This is the "schema-aware prompting" feature —
instead of dumping all 30+ tables into every prompt, we inject only what's needed.
"""

# Full OMOP table definitions available to the router
OMOP_SCHEMA = {
    "person": """
        person (
            person_id INTEGER,           -- unique patient ID
            gender_concept_id INTEGER,   -- join concept for gender label
            year_of_birth INTEGER,
            month_of_birth INTEGER,
            day_of_birth INTEGER,
            race_concept_id INTEGER,     -- join concept for race label
            ethnicity_concept_id INTEGER
        )
    """,

    "visit_occurrence": """
        visit_occurrence (
            visit_occurrence_id INTEGER,
            person_id INTEGER,
            visit_concept_id INTEGER,    -- type: inpatient, outpatient, ER
            visit_start_date DATE,
            visit_end_date DATE,
            visit_type_concept_id INTEGER
        )
    """,

    "condition_occurrence": """
        condition_occurrence (
            condition_occurrence_id INTEGER,
            person_id INTEGER,
            condition_concept_id INTEGER,   -- join concept for diagnosis name
            condition_start_date DATE,
            condition_end_date DATE,
            visit_occurrence_id INTEGER,
            condition_source_value VARCHAR  -- human-readable diagnosis name
        )
    """,

    "drug_exposure": """
        drug_exposure (
            drug_exposure_id INTEGER,
            person_id INTEGER,
            drug_concept_id INTEGER,        -- join concept for drug name
            drug_exposure_start_date DATE,
            drug_exposure_end_date DATE,
            quantity FLOAT,
            visit_occurrence_id INTEGER,
            drug_source_value VARCHAR        -- human-readable drug name
        )
    """,

    "measurement": """
        measurement (
            measurement_id INTEGER,
            person_id INTEGER,
            measurement_concept_id INTEGER,  -- join concept for measurement name
            measurement_date DATE,
            value_as_number FLOAT,
            unit_source_value VARCHAR,
            visit_occurrence_id INTEGER
        )
    """,

    "procedure_occurrence": """
        procedure_occurrence (
            procedure_occurrence_id INTEGER,
            person_id INTEGER,
            procedure_concept_id INTEGER,
            procedure_date DATE,
            visit_occurrence_id INTEGER,
            procedure_source_value VARCHAR
        )
    """,

    "concept": """
        concept (
            concept_id INTEGER,     -- the ID used in all other tables
            concept_name VARCHAR,   -- the human-readable label
            domain_id VARCHAR,      -- e.g. 'Condition', 'Drug', 'Measurement'
            vocabulary_id VARCHAR   -- e.g. 'SNOMED', 'RxNorm', 'LOINC'
        )
    """,
}

# Keyword → table mapping for routing
ROUTING_RULES = {
    "person":           ["patient", "person", "age", "gender", "male", "female",
                         "race", "born", "year of birth", "demographic"],
    "visit_occurrence": ["visit", "admission", "inpatient", "outpatient",
                         "emergency", "hospital", "clinic", "appointment"],
    "condition_occurrence": ["condition", "diagnosis", "diagnosed", "disease",
                              "disorder", "diabetes", "hypertension", "cancer",
                              "asthma", "heart failure", "kidney"],
    "drug_exposure":    ["drug", "medication", "prescription", "prescribed",
                         "metformin", "lisinopril", "atorvastatin", "aspirin",
                         "dose", "quantity"],
    "measurement":      ["measurement", "lab", "result", "blood pressure",
                         "glucose", "a1c", "hemoglobin", "creatinine",
                         "sodium", "potassium", "weight", "height", "bmi"],
    "procedure_occurrence": ["procedure", "surgery", "operation", "performed"],
    "concept":          ["name", "label", "called", "what is", "meaning"],
}

# Always include concept — it's the lookup table for human-readable names
ALWAYS_INCLUDE = {"concept"}

# Human-readable reason for each table selection — shown in the UI
TABLE_REASONS = {
    "person":               "Contains patient demographics (age, gender, race)",
    "visit_occurrence":     "Contains hospital and clinic visit records",
    "condition_occurrence": "Contains diagnoses and medical conditions",
    "drug_exposure":        "Contains medication and prescription records",
    "measurement":          "Contains lab results and vital signs",
    "procedure_occurrence": "Contains medical procedures performed",
    "concept":              "Lookup table — maps IDs to human-readable names (SNOMED, RxNorm, LOINC)",
}


def get_relevant_tables(question: str) -> dict[str, str]:
    """
    Given a natural language question, return only the OMOP table definitions
    that are likely relevant. Always includes concept for name lookups.
    """
    question_lower = question.lower()
    selected = set(ALWAYS_INCLUDE)

    for table, keywords in ROUTING_RULES.items():
        if any(kw in question_lower for kw in keywords):
            selected.add(table)

    # Fallback: if nothing matched beyond concept, include the core tables
    if len(selected) <= 1:
        selected.update({"person", "condition_occurrence", "visit_occurrence"})

    return {table: OMOP_SCHEMA[table] for table in selected if table in OMOP_SCHEMA}


def format_schema_context(tables: dict[str, str]) -> str:
    """Format selected table definitions into a prompt-ready string."""
    lines = ["Relevant OMOP CDM tables:\n"]
    for name, definition in tables.items():
        lines.append(f"TABLE: {definition.strip()}\n")
    return "\n".join(lines)
