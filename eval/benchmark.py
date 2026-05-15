"""
ClinIQ — Evaluation Benchmark
25 curated question/expected-SQL pairs covering a range of OMOP query complexity.
Run from cliniq/ folder: python eval/benchmark.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb
import pandas as pd
from agent.graph import ask

DB_PATH = "data/omop.duckdb"

BENCHMARK = [
    {
        "id": 1,
        "question": "How many patients are in the database?",
        "expected_sql": "SELECT COUNT(*) AS total_patients FROM person",
        "difficulty": "easy",
    },
    {
        "id": 2,
        "question": "How many male and female patients are there?",
        "expected_sql": """
            SELECT c.concept_name AS gender, COUNT(*) AS count
            FROM person p
            JOIN concept c ON p.gender_concept_id = c.concept_id
            GROUP BY c.concept_name ORDER BY c.concept_name
        """,
        "difficulty": "easy",
    },
    {
        "id": 3,
        "question": "What are the top 5 most common conditions diagnosed?",
        "expected_sql": """
            SELECT c.concept_name AS condition, COUNT(*) AS count
            FROM condition_occurrence co
            JOIN concept c ON co.condition_concept_id = c.concept_id
            GROUP BY c.concept_name ORDER BY count DESC LIMIT 5
        """,
        "difficulty": "easy",
    },
    {
        "id": 4,
        "question": "How many patients have been diagnosed with diabetes?",
        "expected_sql": """
            SELECT COUNT(DISTINCT co.person_id) AS diabetic_patients
            FROM condition_occurrence co
            JOIN concept c ON co.condition_concept_id = c.concept_id
            WHERE c.concept_name ILIKE '%diabetes%'
        """,
        "difficulty": "easy",
    },
    {
        "id": 5,
        "question": "What is the most frequently prescribed medication?",
        "expected_sql": """
            SELECT c.concept_name AS medication, COUNT(*) AS prescriptions
            FROM drug_exposure de
            JOIN concept c ON de.drug_concept_id = c.concept_id
            GROUP BY c.concept_name ORDER BY prescriptions DESC LIMIT 1
        """,
        "difficulty": "easy",
    },
    {
        "id": 6,
        "question": "How many patients have hypertension?",
        "expected_sql": """
            SELECT COUNT(DISTINCT co.person_id) AS hypertension_patients
            FROM condition_occurrence co
            JOIN concept c ON co.condition_concept_id = c.concept_id
            WHERE c.concept_name ILIKE '%hypertens%'
        """,
        "difficulty": "easy",
    },
    {
        "id": 7,
        "question": "What is the average glucose measurement across all patients?",
        "expected_sql": """
            SELECT ROUND(AVG(m.value_as_number), 2) AS avg_glucose
            FROM measurement m
            JOIN concept c ON m.measurement_concept_id = c.concept_id
            WHERE c.concept_name ILIKE '%glucose%'
        """,
        "difficulty": "medium",
    },
    {
        "id": 8,
        "question": "How many patients had an emergency room visit?",
        "expected_sql": """
            SELECT COUNT(DISTINCT v.person_id) AS er_patients
            FROM visit_occurrence v
            JOIN concept c ON v.visit_concept_id = c.concept_id
            WHERE c.concept_name ILIKE '%emergency%'
        """,
        "difficulty": "medium",
    },
    {
        "id": 9,
        "question": "What percentage of patients are female?",
        "expected_sql": """
            SELECT ROUND(
                100.0 * COUNT(CASE WHEN c.concept_name = 'FEMALE' THEN 1 END) / COUNT(*), 2
            ) AS female_percentage
            FROM person p
            JOIN concept c ON p.gender_concept_id = c.concept_id
        """,
        "difficulty": "medium",
    },
    {
        "id": 10,
        "question": "How many patients have ever been diagnosed with both diabetes and hypertensive disorder?",
        "expected_sql": """
            SELECT COUNT(*) AS patients_with_both
            FROM (
                SELECT co.person_id FROM condition_occurrence co
                JOIN concept c ON co.condition_concept_id = c.concept_id
                WHERE c.concept_name ILIKE '%diabetes%'
            ) diabetic
            INNER JOIN (
                SELECT co.person_id FROM condition_occurrence co
                JOIN concept c ON co.condition_concept_id = c.concept_id
                WHERE c.concept_name ILIKE '%hypertensive%'
            ) hypertensive ON diabetic.person_id = hypertensive.person_id
        """,
        "difficulty": "hard",
    },
    {
        "id": 11,
        "question": "How many patients have been diagnosed with asthma?",
        "expected_sql": """
            SELECT COUNT(DISTINCT co.person_id) AS asthma_patients
            FROM condition_occurrence co
            JOIN concept c ON co.condition_concept_id = c.concept_id
            WHERE c.concept_name ILIKE '%asthma%'
        """,
        "difficulty": "easy",
    },
    {
        "id": 12,
        "question": "How many patients had an inpatient visit?",
        "expected_sql": """
            SELECT COUNT(DISTINCT v.person_id) AS inpatient_patients
            FROM visit_occurrence v
            JOIN concept c ON v.visit_concept_id = c.concept_id
            WHERE c.concept_name ILIKE '%inpatient%'
        """,
        "difficulty": "easy",
    },
    {
        "id": 13,
        "question": "What are the top 5 most prescribed medications?",
        "expected_sql": """
            SELECT c.concept_name AS medication, COUNT(*) AS prescriptions
            FROM drug_exposure de
            JOIN concept c ON de.drug_concept_id = c.concept_id
            GROUP BY c.concept_name ORDER BY prescriptions DESC LIMIT 5
        """,
        "difficulty": "easy",
    },
    {
        "id": 14,
        "question": "How many patients have been diagnosed with heart failure?",
        "expected_sql": """
            SELECT COUNT(DISTINCT co.person_id) AS heart_failure_patients
            FROM condition_occurrence co
            JOIN concept c ON co.condition_concept_id = c.concept_id
            WHERE c.concept_name ILIKE '%heart failure%'
        """,
        "difficulty": "easy",
    },
    {
        "id": 15,
        "question": "What is the average age of patients in the database?",
        "expected_sql": """
            SELECT ROUND(AVG(2026 - year_of_birth), 1) AS avg_age FROM person
        """,
        "difficulty": "medium",
    },
    {
        "id": 16,
        "question": "What is the most common race among patients?",
        "expected_sql": """
            SELECT c.concept_name AS race, COUNT(*) AS count
            FROM person p
            JOIN concept c ON p.race_concept_id = c.concept_id
            GROUP BY c.concept_name ORDER BY count DESC LIMIT 1
        """,
        "difficulty": "medium",
    },
    {
        "id": 17,
        "question": "What is the average systolic blood pressure across all patients?",
        "expected_sql": """
            SELECT ROUND(AVG(m.value_as_number), 2) AS avg_systolic_bp
            FROM measurement m
            JOIN concept c ON m.measurement_concept_id = c.concept_id
            WHERE c.concept_name ILIKE '%systolic%'
        """,
        "difficulty": "medium",
    },
    {
        "id": 18,
        "question": "How many patients have been prescribed Metformin?",
        "expected_sql": """
            SELECT COUNT(DISTINCT de.person_id) AS metformin_patients
            FROM drug_exposure de
            JOIN concept c ON de.drug_concept_id = c.concept_id
            WHERE c.concept_name ILIKE '%metformin%'
        """,
        "difficulty": "medium",
    },
    {
        "id": 19,
        "question": "What is the most common visit type?",
        "expected_sql": """
            SELECT c.concept_name AS visit_type, COUNT(*) AS count
            FROM visit_occurrence v
            JOIN concept c ON v.visit_concept_id = c.concept_id
            GROUP BY c.concept_name ORDER BY count DESC LIMIT 1
        """,
        "difficulty": "medium",
    },
    {
        "id": 20,
        "question": "How many patients under 18 have been diagnosed with asthma?",
        "expected_sql": """
            SELECT COUNT(DISTINCT co.person_id) AS pediatric_asthma_patients
            FROM condition_occurrence co
            JOIN concept c ON co.condition_concept_id = c.concept_id
            JOIN person p ON co.person_id = p.person_id
            WHERE c.concept_name ILIKE '%asthma%'
              AND (2026 - p.year_of_birth) < 18
        """,
        "difficulty": "medium",
    },
    {
        "id": 21,
        "question": "What is the average number of visits per patient?",
        "expected_sql": """
            SELECT ROUND(AVG(visit_count), 2) AS avg_visits_per_patient
            FROM (
                SELECT person_id, COUNT(*) AS visit_count
                FROM visit_occurrence GROUP BY person_id
            ) sub
        """,
        "difficulty": "medium",
    },
    {
        "id": 22,
        "question": "What medications are most commonly prescribed to patients with diabetes?",
        "expected_sql": """
            SELECT c2.concept_name AS medication, COUNT(*) AS n
            FROM condition_occurrence co
            JOIN concept c1 ON co.condition_concept_id = c1.concept_id
            JOIN drug_exposure de ON co.person_id = de.person_id
            JOIN concept c2 ON de.drug_concept_id = c2.concept_id
            WHERE c1.concept_name ILIKE '%diabetes%'
            GROUP BY c2.concept_name ORDER BY n DESC LIMIT 5
        """,
        "difficulty": "hard",
    },
    {
        "id": 23,
        "question": "How many patients have both heart failure and atrial fibrillation?",
        "expected_sql": """
            SELECT COUNT(*) AS patients_with_both
            FROM (
                SELECT co.person_id FROM condition_occurrence co
                JOIN concept c ON co.condition_concept_id = c.concept_id
                WHERE c.concept_name ILIKE '%heart failure%'
            ) hf
            INNER JOIN (
                SELECT co.person_id FROM condition_occurrence co
                JOIN concept c ON co.condition_concept_id = c.concept_id
                WHERE c.concept_name ILIKE '%atrial fibrillation%'
            ) af ON hf.person_id = af.person_id
        """,
        "difficulty": "hard",
    },
    {
        "id": 24,
        "question": "What is the average number of conditions per patient?",
        "expected_sql": """
            SELECT ROUND(AVG(condition_count), 2) AS avg_conditions_per_patient
            FROM (
                SELECT person_id, COUNT(*) AS condition_count
                FROM condition_occurrence GROUP BY person_id
            ) sub
        """,
        "difficulty": "hard",
    },
    {
        "id": 25,
        "question": "Which race group has the highest average number of conditions per patient?",
        "expected_sql": """
            SELECT c.concept_name AS race, ROUND(AVG(cond_count), 2) AS avg_conditions
            FROM person p
            JOIN concept c ON p.race_concept_id = c.concept_id
            JOIN (
                SELECT person_id, COUNT(*) AS cond_count
                FROM condition_occurrence GROUP BY person_id
            ) sub ON p.person_id = sub.person_id
            GROUP BY c.concept_name ORDER BY avg_conditions DESC LIMIT 1
        """,
        "difficulty": "hard",
    },
]


def run_expected_sql(sql: str) -> pd.DataFrame | None:
    try:
        con = duckdb.connect(DB_PATH, read_only=True)
        df = con.execute(sql).df()
        con.close()
        return df
    except Exception as e:
        print(f"  [ERROR] Expected SQL failed: {e}")
        return None


def results_match(expected_df: pd.DataFrame, agent_sql: str) -> bool:
    try:
        con = duckdb.connect(DB_PATH, read_only=True)
        agent_df = con.execute(agent_sql).df()
        con.close()

        if len(expected_df) > 1:
            expected_vals = sorted([str(v).strip().lower() for v in expected_df.iloc[:, 0]])
            agent_vals = sorted([str(v).strip().lower() for v in agent_df.iloc[:, 0]])
            return expected_vals == agent_vals

        expected_val = expected_df.iloc[0, 0]
        agent_val = agent_df.iloc[0, 0]

        try:
            return abs(float(expected_val) - float(agent_val)) < 0.01
        except (TypeError, ValueError):
            return str(expected_val).strip().lower() == str(agent_val).strip().lower()

    except Exception:
        return False


def run_benchmark():
    print("\n" + "=" * 65)
    print("  ClinIQ — Evaluation Benchmark (25 questions)")
    print("=" * 65)

    results = []

    for item in BENCHMARK:
        qid = item["id"]
        diff = item["difficulty"]
        print(f"\n[Q{qid}] ({diff.upper()}) {item['question']}")
        print("-" * 65)

        expected_df = run_expected_sql(item["expected_sql"])
        if expected_df is None:
            print("  [SKIP] Expected SQL failed")
            continue
        print(f"  Expected result: {expected_df.iloc[0, 0]}")

        agent_result = ask(item["question"])
        agent_sql = agent_result.get("sql", "")
        retries = agent_result.get("retries", 0)

        print(f"  Agent SQL: {agent_sql.strip()}")
        print(f"  Retries: {retries}")

        passed = results_match(expected_df, agent_sql)
        print(f"  Status: {'PASS' if passed else 'FAIL'}")
        print(f"  Agent answer: {agent_result.get('answer', '')[:120]}")

        results.append({"id": qid, "difficulty": diff, "passed": passed, "retries": retries})

    total = len(results)
    n_passed = sum(1 for r in results if r["passed"])
    print("\n" + "=" * 65)
    print(f"  RESULTS: {n_passed}/{total} passed ({round(100*n_passed/total)}% accuracy)")
    print("=" * 65)

    by_difficulty = {}
    for r in results:
        d = r["difficulty"]
        by_difficulty.setdefault(d, {"passed": 0, "total": 0})
        by_difficulty[d]["total"] += 1
        if r["passed"]:
            by_difficulty[d]["passed"] += 1

    for diff, counts in sorted(by_difficulty.items()):
        print(f"  {diff.capitalize()}: {counts['passed']}/{counts['total']}")

    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_benchmark()
