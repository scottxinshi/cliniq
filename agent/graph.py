"""
ClinIQ — LangGraph Agent
Pipeline: Question → Schema Router → SQL Generator → Executor → Self-Corrector → Narrator

Each node does one job. The self-correction loop retries up to MAX_RETRIES
times if the SQL fails or returns empty results.
"""

import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from agent.schema import get_relevant_tables, format_schema_context
from agent.executor import run_query, format_result

load_dotenv()

MAX_RETRIES = 3
MODEL = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
llm = ChatGroq(model=MODEL, temperature=0)


# ── Agent state ─────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    question: str           # original user question
    schema_context: str     # relevant table definitions
    sql: str                # generated SQL
    result_df: object       # query result dataframe
    result_str: str         # formatted result string
    error: str              # last error message (if any)
    answer: str             # final narrated answer
    retries: int            # number of self-correction attempts


# ── Node 1: Schema Router ────────────────────────────────────────────────────

def schema_router(state: AgentState) -> AgentState:
    """Select only the relevant OMOP tables for this question."""
    tables = get_relevant_tables(state["question"])
    state["schema_context"] = format_schema_context(tables)
    return state


# ── Node 2: SQL Generator ────────────────────────────────────────────────────

def sql_generator(state: AgentState) -> AgentState:
    """Generate a DuckDB-compatible SQL query from the question and schema."""
    error_context = ""
    if state.get("error"):
        error_context = f"""
The previous SQL attempt failed with this error:
{state['error']}

Previous SQL:
{state.get('sql', 'N/A')}

Please fix the issue and generate corrected SQL.
"""

    system_prompt = f"""You are a clinical data analyst expert in OMOP CDM and DuckDB SQL.
Generate a single, valid DuckDB SQL query to answer the user's question.

Rules:
- Use only the tables provided in the schema
- Always use concept table joins to get human-readable names where helpful
- Return only the SQL query, no explanation, no markdown, no backticks
- Use DuckDB syntax (e.g. DATE_DIFF for date math)
- Limit results to 100 rows unless counting or aggregating

{state['schema_context']}
{error_context}"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["question"])
    ])

    state["sql"] = response.content.strip()
    state["error"] = ""
    return state


# ── Node 3: Executor ─────────────────────────────────────────────────────────

def executor(state: AgentState) -> AgentState:
    """Run the SQL and capture results or errors."""
    df, error = run_query(state["sql"])
    if error:
        state["error"] = error
        state["result_df"] = None
        state["result_str"] = ""
    else:
        state["result_df"] = df
        state["result_str"] = format_result(df)
        state["error"] = ""
    return state


# ── Node 4: Narrator ─────────────────────────────────────────────────────────

def narrator(state: AgentState) -> AgentState:
    """Convert raw query results into a plain-language clinical answer."""
    system_prompt = """You are a clinical data assistant explaining query results to a healthcare professional.
Convert the data into a clear, concise plain-language answer.
Include specific numbers. Be direct. No filler phrases."""

    prompt = f"""Question: {state['question']}

Query results:
{state['result_str']}

Provide a clear, professional answer in 2-3 sentences."""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ])

    state["answer"] = response.content.strip()
    return state


# ── Node 5: Error Handler ─────────────────────────────────────────────────────

def error_handler(state: AgentState) -> AgentState:
    """Called when retries are exhausted."""
    state["answer"] = (
        f"I was unable to answer this question after {MAX_RETRIES} attempts. "
        f"Last error: {state.get('error', 'unknown error')}\n\n"
        f"Last SQL attempted:\n{state.get('sql', 'N/A')}"
    )
    return state


# ── Routing logic ─────────────────────────────────────────────────────────────

def should_retry(state: AgentState) -> str:
    """After execution, decide: narrate, retry, or give up."""
    if not state.get("error"):
        return "narrator"
    retries = state.get("retries", 0) + 1
    state["retries"] = retries
    if retries < MAX_RETRIES:
        return "sql_generator"
    return "error_handler"


# ── Build the graph ───────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("schema_router", schema_router)
    graph.add_node("sql_generator", sql_generator)
    graph.add_node("executor", executor)
    graph.add_node("narrator", narrator)
    graph.add_node("error_handler", error_handler)

    graph.set_entry_point("schema_router")
    graph.add_edge("schema_router", "sql_generator")
    graph.add_edge("sql_generator", "executor")
    graph.add_conditional_edges("executor", should_retry, {
        "narrator": "narrator",
        "sql_generator": "sql_generator",
        "error_handler": "error_handler",
    })
    graph.add_edge("narrator", END)
    graph.add_edge("error_handler", END)

    return graph.compile()


# ── Public interface ──────────────────────────────────────────────────────────

agent = build_graph()


def ask(question: str) -> dict:
    """Run the ClinIQ agent on a plain-language question."""
    result = agent.invoke({
        "question": question,
        "schema_context": "",
        "sql": "",
        "result_df": None,
        "result_str": "",
        "error": "",
        "answer": "",
        "retries": 0,
    })
    return result
