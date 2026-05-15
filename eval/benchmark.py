"""
ClinIQ — Evaluation Benchmark
10 curated question/expected-SQL pairs covering a range of OMOP query complexity.
Run from cliniq/ folder: python eval/benchmark.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb
import pandas as pd
from agent.graph import ask

DB_PATH = "data/omop.duckdb"

# ── Benchmark questions with expected SQL ────────────────────────────────────

BENCHMARK = [
    {
        "id": 1,
        "question": "How many patients are in the database?",
        "expected_sql": """
            SELECT COUNT(*) AS total_patients FROM person
        """,
        "difficulty": "easy",
    },
    {
        "id": 2,
        "question": "How many male and female patients are there?",
        "expected_sql": """
            SELECT c.concept_name AS gender, COUNT(*) AS count
            FROM person p
            JOIN concept c ON p.gender_concept_id = c.concept_id
            GROUP BY c.concept_name
            ORDER BY c.concept_name
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
            GROUP BY c.concept_name
            ORDER BY count DESC
            LIMIT 5
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
            GROUP BY c.concept_name
            ORDER BY prescriptions DESC
            LIMIT 1
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
            WHERE c.concept_name ILIKE '%hypertension%'
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
                SELECT co.person_id
                FROM condition_occurrence co
                JOIN concept c ON co.condition_concept_id = c.concept_id
                WHERE c.concept_name ILIKE '%diabetes%'
            ) diabetic
            INNER JOIN (
                SELECT co.person_id
                FROM condition_occurrence co
                JOIN concept c ON co.condition_concept_id = c.concept_id
                WHERE c.concept_name ILIKE '%hypertensive%'
            ) hypertensive
            ON diabetic.person_id = hypertensive.person_id
        """,
        "difficulty": "hard",
    },
]


# ── Scoring ──────────────────────────────────────────────────────────────────

def run_expected_sql(sql: str) -> pd.DataFrame | None:
    """Run the expected SQL to get the ground truth result."""
    try:
        con = duckdb.connect(DB_PATH, read_only=True)
        df = con.execute(sql).df()
        con.close()
        return df
    except Exception as e:
        print(f"  [ERROR] Expected SQL failed: {e}")
        return None


def results_match(expected_df: pd.DataFrame, agent_sql: str) -> bool:
    """
    Compare agent SQL output to expected output.
    - Single row: compare first value (numeric with tolerance, or string)
    - Multi row: compare sorted first-column values as sets
    """
    try:
        con = duckdb.connect(DB_PATH, read_only=True)
        agent_df = con.execute(agent_sql).df()
        con.close()

        # Multi-row: compare first column values as sorted sets
        if len(expected_df) > 1:
            expected_vals = sorted([str(v).strip().lower() for v in expected_df.iloc[:, 0]])
            agent_vals = sorted([str(v).strip().lower() for v in agent_df.iloc[:, 0]])
            return expected_vals == agent_vals

        # Single row: compare first value
        expected_val = expected_df.iloc[0, 0]
        agent_val = agent_df.iloc[0, 0]

        try:
            return abs(float(expected_val) - float(agent_val)) < 0.01
        except (TypeError, ValueError):
            return str(expected_val).strip().lower() == str(agent_val).strip().lower()

    except Exception:
        return False


# ── Main runner ───────────────────────────────────────────────────────────────

def run_benchmark():
    print("\n" + "=" * 65)
    print("  ClinIQ — Evaluation Benchmark")
    print("=" * 65)

    results = []

    for item in BENCHMARK:
        print(f"\n[Q{item['id']}] ({item['difficulty'].upper()}) {item['question']}")
        print("-" * 65)

        # Get ground truth
        expected_df = run_expected_sql(item["expected_sql"])
        if expected_df is None:
            print("  [SKIP] Expected SQL failed — check benchmark definition")
            continue
        expected_val = expected_df.iloc[0, 0]
        print(f"  Expected result: {expected_val}")

        # Run agent
        agent_result = ask(item["question"])
        agent_sql = agent_result.get("sql", "")
        retries = agent_result.get("retries", 0)

        print(f"  Agent SQL: {agent_sql.strip()}")
        print(f"  Retries: {retries}")

        # Score
        passed = results_match(expected_df, agent_sql)
        status = "PASS ✓" if passed else "FAIL ✗"
        print(f"  Status: {status}")
        print(f"  Agent answer: {agent_result.get('answer', '')[:120]}")

        results.append({
            "id": item["id"],
            "difficulty": item["difficulty"],
            "passed": passed,
            "retries": retries,
        })

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print("\n" + "=" * 65)
    print(f"  RESULTS: {passed}/{total} passed ({round(100*passed/total)}% accuracy)")
    print("=" * 65)

    by_difficulty = {}
    for r in results:
        d = r["difficulty"]
        by_difficulty.setdefault(d, {"passed": 0, "total": 0})
        by_difficulty[d]["total"] += 1
        if r["passed"]:
            by_difficulty[d]["passed"] += 1

    for diff, counts in by_difficulty.items():
        print(f"  {diff.capitalize()}: {counts['passed']}/{counts['total']}")

    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_benchmark()
