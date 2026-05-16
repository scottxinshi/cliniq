"""
ClinIQ — Quick Test Runner
Run from the cliniq/ folder: python run.py
"""

from agent.graph import ask

TEST_QUESTIONS = [
    # Multi-table — clinical story (son's visit)
    "How many patients between age 8 and 12 have been diagnosed with pollen allergies or conjunctivitis?",
    "What medications are most commonly prescribed to children under 12 with pollen allergies?",
    "How many children with pollen allergies also have asthma?",

    # Multi-table — adult pivot (Scott's diagnosis)
    "How many adult patients over 30 have both allergic rhinitis and blurred vision?",
    "What medications are most commonly prescribed to those patients?",

    # Complex joins
    "What medications are most commonly prescribed to diabetic patients over 65?",
    "How many patients have been diagnosed with both diabetes and hypertensive disorder?",
    "How many patients had an emergency room visit in the last 2 years?",
]

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  ClinIQ — EHR SQL Agent")
    print("="*60)

    for question in TEST_QUESTIONS:
        print(f"\nQ: {question}")
        print("-" * 60)
        result = ask(question)
        print(f"SQL:\n{result['sql']}\n")
        print(f"Answer: {result['answer']}")
        if result.get("retries", 0) > 0:
            print(f"Retries: {result['retries']}")
        print("="*60)
