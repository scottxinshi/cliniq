"""
ClinIQ — Query Executor
Runs SQL against the OMOP DuckDB database and returns results or error messages.
"""

import os
import duckdb
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/omop.duckdb")


def run_query(sql: str) -> tuple[pd.DataFrame | None, str | None]:
    """
    Execute a SQL query against the OMOP database.
    Returns (dataframe, None) on success or (None, error_message) on failure.
    """
    try:
        con = duckdb.connect(DB_PATH, read_only=True)
        df = con.execute(sql).df()
        con.close()
        return df, None
    except Exception as e:
        return None, str(e)


def format_result(df: pd.DataFrame, max_rows: int = 20) -> str:
    """Convert a dataframe result into a readable string for the narrator."""
    if df is None or df.empty:
        return "The query returned no results."
    total = len(df)
    preview = df.head(max_rows)
    result = preview.to_string(index=False)
    if total > max_rows:
        result += f"\n... ({total - max_rows} more rows not shown)"
    return result
