import duckdb

con = duckdb.connect("data/omop.duckdb")

result = con.execute("""
    SELECT COUNT(DISTINCT co.person_id)
    FROM condition_occurrence co
    JOIN concept c ON co.condition_concept_id = c.concept_id
    WHERE c.concept_name ILIKE '%diabetes%'
""").fetchone()

print(f"Patients with diabetes: {result[0]}")
con.close()
