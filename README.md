# ClinIQ — EHR SQL Agent

![CI](https://github.com/scottxinshi/cliniq/actions/workflows/ci.yml/badge.svg)

> A natural language interface to patient records, built on the OMOP Common Data Model.
> Ask plain questions. Get plain answers. No screen-navigating required.

---

## Benchmark Results

| Version | Change | Accuracy |
|---|---|---|
| Baseline | No prompt improvements | 40% (4/10) |
| v2 | Added ILIKE rule | 80% (8/10) |
| v3 | Added OR parentheses + no-date rule | **100% (10/10)** |

10 curated clinical questions scored against ground truth SQL across three difficulty levels.
Each improvement was driven by a specific failure the benchmark caught — not guesswork.

---

## What It Does

ClinIQ lets clinicians ask questions about patient records in plain English:

```
"How many patients between age 8 and 12 have been diagnosed with pollen allergies?"
"What medications are most commonly prescribed to diabetic patients over 65?"
"How many patients have been diagnosed with both diabetes and hypertensive disorder?"
```

The agent translates each question into SQL, runs it against a DuckDB database using the
OMOP CDM schema, self-corrects if the query fails, and narrates the result in plain language.

---

## Why This Project

This is my second portfolio project. The first — [DataScope](https://github.com/scottxinshi/datascope) — demonstrated breadth: many agents, many integrations.

ClinIQ demonstrates depth:
- One agent, one hard problem
- Domain fluency in OMOP CDM (the real standard behind Epic and major health systems)
- An evaluation harness that proves it works — not just that it demos well
- Measurable, iterative improvement from baseline to production-ready accuracy

---

## Architecture

```
User Question
     │
     ▼
Schema Router          ← selects only relevant OMOP tables (not all 30+)
     │
     ▼
SQL Generator          ← Groq (Llama 3.3 70B) generates DuckDB SQL
     │
     ▼
Executor               ← runs SQL against DuckDB OMOP database
     │
  error? ──────────────► Self-Corrector (up to 3 retries)
     │
     ▼
Narrator               ← converts result to plain clinical language
     │
     ▼
Answer + SQL + Tables Used
```

**Three depth features:**

1. **Schema-aware prompting** — OMOP has 30+ tables. The router injects only the relevant ones per question, reducing noise and token cost.

2. **SQL self-correction loop** — if a query fails or returns unexpected results, the agent reflects on the error and retries with a corrected prompt. Configurable max retries.

3. **Evaluation harness** — 25 benchmark question/SQL pairs scored against ground truth. Accuracy is measured, not assumed.

---

## Tech Stack

| Component | Tool |
|---|---|
| Orchestration | LangGraph |
| LLM | Groq — Llama 3.3 70B |
| Database | DuckDB + OMOP CDM schema |
| Vector store | ChromaDB (schema embeddings) |
| Data | Synthea synthetic patients (5,000) |
| API | FastAPI |
| Frontend | Streamlit |
| Containers | Docker |

Same stack as DataScope. The domain and the engineering depth are what's new.

---

## OMOP CDM

OMOP (Observational Medical Outcomes Partnership) Common Data Model is the standardized
database schema used by Epic, academic medical centers, and most major US health systems.
Knowing it by name signals domain fluency, not just AI generalism.

Key tables used in this project:

| Table | Contents |
|---|---|
| `person` | Patient demographics |
| `condition_occurrence` | Diagnoses (SNOMED codes) |
| `drug_exposure` | Medications (RxNorm codes) |
| `visit_occurrence` | Hospital and clinic visits |
| `measurement` | Lab results and vitals (LOINC codes) |
| `concept` | Vocabulary lookup — maps IDs to readable names |

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/scottxinshi/cliniq.git
cd cliniq

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Add your GROQ_API_KEY to .env

# 4. Generate synthetic patient data
python scripts/generate_omop_data.py

# 5. Run the app
streamlit run frontend/app.py
```

Or with Docker (one command):
```bash
docker-compose up
```

---

## Evaluation Harness

```bash
python eval/benchmark.py
```

Runs 10 clinical questions through the agent and scores each against ground truth SQL.
Results show pass/fail per question, retry count, and overall accuracy by difficulty.

---

## Data

5,000 synthetic patients generated using the OMOP CDM schema. Conditions include:
- Type 2 diabetes mellitus, Hypertensive disorder, Asthma, Heart failure
- Allergic rhinitis due to pollen, Atopic conjunctivitis, Blurred vision
- Atrial fibrillation, Chronic renal disease, Malignant neoplastic disease

No real patient data. No PHI. Safe for portfolio, demo, and public GitHub.

---

## Built By

**Scott Xin Shi** — Data Engineer with 10 years in financial services, building AI engineering
portfolio for healthcare roles.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/scott-xin-shi)
[![GitHub](https://img.shields.io/badge/GitHub-Portfolio-717171?style=flat&logo=github)](https://github.com/scottxinshi)

*Also see: [DataScope](https://github.com/scottxinshi/datascope) — multi-agent analytics system (breadth)*
