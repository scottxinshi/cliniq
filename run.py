"""
ClinIQ — Quick Test Runner
Run from the cliniq/ folder: python run.py
"""

from agent.graph import ask

TEST_QUESTIONS = [
    "How many patients are in the database?",
    "What are the most common conditions diagnosed?",
    "Which medications are most frequently prescribed?",
    "How many patients have been diagnosed with diabetes?",
    "What is the average glucose measurement across all patients?",
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
        print("="*60)
