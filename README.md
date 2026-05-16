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
| v3 | Added OR parentheses + no-date rule | 100% (10/10) |
| v4 | Expanded to 25 questions; added stem matching, visit/age/join rules | **100% (25/25)** |

25 curated clinical questions scored against ground truth SQL across three difficulty levels.
Each improvement was driven by a specific failure the benchmark caught — not guesswork.

---

## What It Does

ClinIQ has two modes:

### Tab 1 — Population Query
Ask plain English questions about your patient population. The agent shows its work at every step.

```
"How many patients have been diagnosed with both diabetes and hypertension?"
"What medications are most commonly prescribed to diabetic patients?"
"How many patients had an emergency room visit?"
```

The agent translates each question into SQL, runs it against a DuckDB OMOP database,
self-corrects if the query fails, and narrates the result in plain language. Each response
shows which OMOP tables were selected and the SQL that was generated — no black box.

### Tab 2 — Patient Timeline
Pull up any individual patient's full clinical record in one view.

- **Search** by name, phone number, or email address
- **Filter** by gender, age range, race, or US state
- **See at a glance:** AI-generated clinical summary, active conditions with diagnosis dates,
  current medications, full visit history, and recent lab results (glucose, blood pressure,
  A1c, kidney function, and more)

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

### Agent Pipeline (Tab 1)

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

### Patient Timeline (Tab 2)

```
Patient Search / Filters
     │
     ▼
DuckDB OMOP Queries    ← demographics, conditions, medications, visits, measurements
     │
     ▼
Groq LLM Narrator      ← generates 3-5 sentence clinical summary
     │
     ▼
Full Patient View
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
| Data | Synthetic patients (5,000) — OMOP-compatible |
| Frontend | Streamlit |
| Containers | Docker |
| CI | GitHub Actions |

Same stack as DataScope. The domain and the engineering depth are what's new.

---

## OMOP CDM

OMOP (Observational Medical Outcomes Partnership) Common Data Model is the standardized
database schema used by Epic, academic medical centers, and most major US health systems.
Knowing it by name signals domain fluency, not just AI generalism.

Key tables used in this project:

| Table | Contents |
|---|---|
| `person` | Patient demographics (name, age, gender, race, contact info) |
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

Runs 25 clinical questions through the agent and scores each against ground truth SQL.
Results show pass/fail per question, retry count, and overall accuracy by difficulty.

| Difficulty | Count | Score |
|---|---|---|
| Easy | 10 | 10/10 |
| Medium | 10 | 10/10 |
| Hard | 5 | 5/5 |
| **Total** | **25** | **25/25** |

---

## Data

5,000 synthetic patients generated using Python's Faker library and the OMOP CDM schema.

Conditions include: Type 2 diabetes mellitus, Hypertensive disorder, Asthma, Heart failure,
Allergic rhinitis due to pollen, Atopic conjunctivitis, Atrial fibrillation, Chronic renal
disease, Coronary arteriosclerosis, Malignant neoplastic disease.

Drug assignment is condition-aware — allergy patients receive allergy medications,
asthma patients receive inhalers.

No real patient data. No PHI. Safe for portfolio, demo, and public GitHub.

---

## Built By

**Scott Xin Shi** — Data Engineer with 10 years in financial services, building AI engineering
portfolio for healthcare roles.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/scott-xin-shi)
[![GitHub](https://img.shields.io/badge/GitHub-Portfolio-717171?style=flat&logo=github)](https://github.com/scottxinshi)

*Also see: [DataScope](https://github.com/scottxinshi/datascope) — multi-agent analytics system (breadth)*
