import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import streamlit as st
import pandas as pd
from agent.graph import ask
from agent.schema import TABLE_REASONS
from agent.patient_timeline import get_patient_list, get_patient_summary, generate_narrative
from dotenv import load_dotenv
load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="ClinIQ", page_icon="🏥", layout="centered")
st.title("🏥 ClinIQ")
st.caption("EHR SQL Agent — Built by Scott Xin Shi")

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
    <style>
    .sidebar-card {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 1.2rem;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        margin-bottom: 1rem;
    }
    .secondary-text {
        color: #86868b;
        font-size: 0.85rem;
        line-height: 1.4;
    }
    .card-header {
        font-weight: 600;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .patient-card {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 1rem 1.2rem;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        margin-bottom: 0.8rem;
    }
    .narrative-box {
        background-color: rgba(0, 122, 255, 0.08);
        border-left: 3px solid #0A84FF;
        padding: 1rem 1.2rem;
        border-radius: 0 10px 10px 0;
        margin-bottom: 1rem;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    hr {
        margin: 1em 0px !important;
        opacity: 0.2 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 👋 About")

    st.markdown("""
    <div class="sidebar-card">
        <div style="font-size: 0.9rem;">
            <b>ClinIQ</b> is a natural language interface to synthetic patient records,
            built on the OMOP Common Data Model — the real clinical standard used by Epic
            and major health systems.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding-left: 5px; margin-bottom: 20px;">
        <p class="secondary-text" style="font-weight: 600; font-size: 0.7rem; letter-spacing: 0.05em;">BUILT BY SCOTT XIN SHI</p>
        <div style="display: flex; gap: 10px; margin-top: 8px;">
            <a href="https://www.linkedin.com/in/scott-xin-shi" target="_blank"><img src="https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin"></a>
            <a href="https://github.com/scottxinshi/cliniq" target="_blank"><img src="https://img.shields.io/badge/GitHub-Project-717171?style=flat&logo=github"></a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("### Benchmark")

    st.markdown("""
    <div class="sidebar-card">
        <div class="card-header">Evaluation Harness</div>
        <div class="secondary-text">
            25 curated clinical questions scored against ground truth SQL.<br><br>
            <b style="font-size: 1.1rem;">10 / 10</b> &nbsp; 100% accuracy<br>
            <span style="font-size: 0.75rem;">Easy: 6/6 &nbsp;·&nbsp; Medium: 3/3 &nbsp;·&nbsp; Hard: 1/1</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("### 💡 Try asking")

    sample_questions = [
        "How many patients have diabetes?",
        "What are the most common conditions?",
        "Which medications are most prescribed?",
        "How many patients had an ER visit?",
        "What is the average glucose level?",
    ]

    for q in sample_questions:
        st.markdown(f"<div class='secondary-text'>• {q}</div>", unsafe_allow_html=True)

    st.divider()

    st.markdown("""
    <div class="secondary-text">
        Data: 5,000 synthetic patients<br>
        Schema: OMOP CDM<br>
        LLM: Groq · Llama 3.3 70B<br>
        DB: DuckDB
    </div>
    """, unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2 = st.tabs(["💬 Population Query", "🏥 Patient Timeline"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Population Query (existing chat)
# ════════════════════════════════════════════════════════════════════════════

with tab1:

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "previous_sql" not in st.session_state:
        st.session_state.previous_sql = ""

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sql"):
                with st.expander("View SQL"):
                    st.code(message["sql"], language="sql")
            if message.get("table") is not None:
                st.dataframe(message["table"])
            if message.get("tables_used"):
                with st.expander("🗂️ OMOP tables used by the schema router"):
                    for table in message["tables_used"]:
                        reason = TABLE_REASONS.get(table, "")
                        st.markdown(f"**`{table}`** — {reason}")

    if prompt := st.chat_input("Ask a question about your patients..."):

        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            try:
                with st.status("Working...", expanded=True) as status:
                    st.write("🗂️ Selecting relevant OMOP tables...")
                    time.sleep(0.3)
                    st.write("🧠 Generating SQL from your question...")
                    history = st.session_state.messages[-6:]
                    result = ask(prompt, history=history, previous_sql=st.session_state.previous_sql)
                    st.write("⚙️ Executing query against patient records...")
                    time.sleep(0.2)
                    st.write("💬 Narrating the answer...")
                    status.update(label="Done", state="complete", expanded=False)
            except Exception as e:
                if "rate_limit" in str(e).lower() or "429" in str(e):
                    st.warning("⏳ Groq rate limit reached — please wait a minute and try again.")
                else:
                    st.error(f"Something went wrong: {str(e)}")
                st.stop()

            sql     = result.get("sql", "")
            answer  = result.get("answer", "")
            df      = result.get("result_df")
            retries = result.get("retries", 0)

            st.markdown(answer)

            if sql:
                with st.expander("View SQL"):
                    st.code(sql, language="sql")

            if df is not None and not df.empty:
                st.dataframe(df)

            tables_used = result.get("tables_used", [])
            if tables_used:
                with st.expander("🗂️ OMOP tables used by the schema router"):
                    for table in tables_used:
                        reason = TABLE_REASONS.get(table, "")
                        st.markdown(f"**`{table}`** — {reason}")

            if retries > 0:
                st.caption(f"Self-corrected: {retries} retry attempt(s)")

        if sql and not result.get("error"):
            st.session_state.previous_sql = sql

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sql": sql,
            "table": df if df is not None and not df.empty else None,
            "tables_used": result.get("tables_used", []),
        })

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Patient Timeline
# ════════════════════════════════════════════════════════════════════════════

with tab2:

    st.markdown("#### Select a Patient")

    try:
        patient_list = get_patient_list()

        # Build display labels: "Patient 42 · Age 10 · MALE"
        patient_list["label"] = patient_list.apply(
            lambda r: f"Patient {r.person_id} · Age {r.age} · {r.gender}", axis=1
        )

        selected_label = st.selectbox(
            "Search by patient",
            options=patient_list["label"].tolist(),
            index=0,
            label_visibility="collapsed",
        )

        selected_id = int(selected_label.split("·")[0].replace("Patient", "").strip())
        summary = get_patient_summary(selected_id)
        demo    = summary["demographics"].iloc[0]
        conds   = summary["conditions"]
        meds    = summary["medications"]
        visits  = summary["visits"]
        measurs = summary["measurements"]

        # ── Demographics card ────────────────────────────────────────────
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Age", demo["age"])
        col2.metric("Gender", demo["gender"])
        col3.metric("Race", demo["race"])
        col4.metric("Visits", len(visits))

        # ── AI Narrative ─────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 🩺 Clinical Summary")

        if "narrative_id" not in st.session_state or st.session_state.narrative_id != selected_id:
            with st.spinner("Generating clinical summary..."):
                try:
                    narrative = generate_narrative(summary)
                    st.session_state.narrative_id = selected_id
                    st.session_state.narrative_text = narrative
                except Exception as e:
                    if "rate_limit" in str(e).lower() or "429" in str(e):
                        st.session_state.narrative_text = "⏳ Rate limit reached — narrative unavailable. Patient data shown below."
                    else:
                        st.session_state.narrative_text = f"Could not generate narrative: {str(e)}"

        st.markdown(
            f"<div class='narrative-box'>{st.session_state.get('narrative_text', '')}</div>",
            unsafe_allow_html=True,
        )

        # ── Conditions & Medications side by side ────────────────────────
        st.markdown("---")
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("#### 🦠 Conditions")
            if conds.empty:
                st.markdown("<div class='secondary-text'>No conditions on record.</div>", unsafe_allow_html=True)
            else:
                for _, row in conds.iterrows():
                    st.markdown(f"""
                    <div class='patient-card'>
                        <div style='font-size: 0.9rem; font-weight: 500;'>{row.condition}</div>
                        <div class='secondary-text'>Diagnosed: {row.diagnosed}</div>
                    </div>
                    """, unsafe_allow_html=True)

        with col_b:
            st.markdown("#### 💊 Medications")
            if meds.empty:
                st.markdown("<div class='secondary-text'>No medications on record.</div>", unsafe_allow_html=True)
            else:
                for _, row in meds.iterrows():
                    st.markdown(f"""
                    <div class='patient-card'>
                        <div style='font-size: 0.9rem; font-weight: 500;'>{row.medication}</div>
                        <div class='secondary-text'>Started: {row.started}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # ── Visit History ────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 🗓️ Visit History")
        if visits.empty:
            st.markdown("<div class='secondary-text'>No visits on record.</div>", unsafe_allow_html=True)
        else:
            st.dataframe(visits, use_container_width=True, hide_index=True)

        # ── Measurements ─────────────────────────────────────────────────
        if not measurs.empty:
            st.markdown("---")
            st.markdown("#### 🔬 Recent Measurements")
            st.dataframe(measurs, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Could not load patient data: {str(e)}")
        st.info("Make sure the OMOP database has been generated. Run: python scripts/generate_omop_data.py")
