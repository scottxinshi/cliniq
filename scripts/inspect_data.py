"""
ClinIQ — Data Inspector
Run from cliniq/ folder: python scripts/inspect_data.py
"""

import duckdb

con = duckdb.connect("data/omop.duckdb")

tables = ["person", "visit_occurrence", "condition_occurrence", "drug_exposure", "measurement", "concept"]

for table in tables:
    print(f"\n{'='*60}")
    print(f"  TABLE: {table}")
    print(f"{'='*60}")
    count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  Total rows: {count:,}")
    print(f"\n  Sample (5 rows):")
    df = con.execute(f"SELECT * FROM {table} LIMIT 5").df()
    print(df.to_string(index=False))

con.close()
