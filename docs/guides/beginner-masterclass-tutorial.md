# Beginner Masterclass Tutorial: RevOps Funnel Reconciliation Engine

## Who This Tutorial Is For
This tutorial is written for complete beginners who want to understand, operate, and explain this project with confidence.

You do not need prior expertise in Airflow, dbt, or analytics engineering. You do need patience and a willingness to connect business questions to data pipelines.

## What This Project Is
The RevOps Funnel Reconciliation Engine is a production-grade analytics engineering system that answers a core business question:

- Where is revenue leaking between lead capture and deal close, and what should the business do next?

It combines:
- Ingestion and standardization of CRM + marketing data.
- Historical tracking and reconciliation logic.
- Governed semantic models in dbt.
- BI surfaces (Streamlit and Metabase) for decision-making.
- Operational quality gates (lint, tests, data quality checks, CI).

## Why This Project Matters
Most organizations have fragmented RevOps data:
- Marketing sees leads.
- Sales sees opportunities.
- Finance sees revenue.
- Leadership sees inconsistent metrics.

This project creates one reliable analytical path from raw source events to executive-ready metrics.

## Learning Outcomes
By the end, you should be able to:
- Explain the architecture from raw sources to executive dashboards.
- Describe why data contracts and quality checks are non-negotiable.
- Run and validate the local workflow.
- Defend modeling and governance decisions in interviews.
- Translate technical outputs into business decisions.

## Big-Picture Architecture

### Layer 1: Raw Data Inputs
The project ingests source records such as:
- CRM accounts, products, pipeline, sales teams.
- Marketing lead data.

Raw files are in project data folders and are loaded into DuckDB for local development.

### Layer 2: Bronze Standardization
Bronze ensures source data is loaded and standardized consistently.

Main goal:
- Keep source fidelity while applying minimal normalization.

### Layer 3: Silver Reconciliation and Harmonization
Silver adds business logic and cross-source linkage:
- Lead-to-account fuzzy candidates and matches.
- Lead-to-opportunity base modeling.
- Opportunity enrichment.

Main goal:
- Connect entities so funnel analysis reflects real business flow.

### Layer 4: Gold and BI Consumption
Gold models expose decision-ready metrics and views, including executive funnel analytics.

Main goal:
- Provide governed, reusable metrics for dashboards and reporting.

### Layer 5: Interface + Operations
- Streamlit: guided analytics explorer with KPI and trend views.
- Metabase: executive BI dashboards and reusable cards.
- Airflow: orchestration for repeatable batch operation.
- CI/CD and quality gates: reliability, consistency, safety.

## Repository Map for Beginners
Start with these folders first:
- `README.md`: quick start, high-level context.
- `dbt/models/`: transformation logic.
- `scripts/`: ingestion, setup, quality operations.
- `dags/`: orchestration flow.
- `src/revops_funnel/`: reusable logic and utilities.
- `docs/reports/`: phase-by-phase delivery evidence.
- `docs/runbooks/`: operational execution and standards.

## Step-by-Step Learning Path

### Step 1: Understand the Business Question Before Code
Write down the core KPI questions:
- How many opportunities are entering the funnel monthly?
- What percentage wins?
- Where is leakage highest by office?
- Is cycle time improving or worsening?

If a model or dashboard cannot answer these, it is not complete.

### Step 2: Understand Data Contracts
Review source contracts and expected column types.

Why this matters:
- If schema assumptions fail, metrics silently drift.
- Contract tests prevent hidden breakage.

### Step 3: Learn the dbt Mental Model
dbt creates a DAG of SQL models.

Key beginner ideas:
- `stg_*` models: cleaned source tables.
- `int_*` models: intermediate business logic.
- `fct_*`, `dim_*`, `bi_*`: mart and BI consumption outputs.
- tests + snapshots = trust and historical traceability.

### Step 4: Learn Operational Gates
The project intentionally blocks low-quality changes.

Typical sequence:
- lint and type checks.
- unit/integration tests.
- dbt build and dbt tests.
- quality checks and Great Expectations.

The goal is deterministic quality, not heroics.

### Step 5: Understand Dashboard Limits
Dashboards are only as good as their underlying data.

If you only have one month of data, trend tabs cannot provide directional insight. This is expected and should be communicated explicitly.

### Step 6: Understand Minimum Viable Backfill
Study:
- `docs/runbooks/minimum-viable-data-backfill-spec.md`

This defines exact columns and monthly coverage thresholds required to produce meaningful trends.

## Practical Walkthrough of the Data Journey

### Ingestion
Scripts in `scripts/ingest/` load source files and API records into local warehouse storage.

### Transformation
dbt models in `dbt/models/` perform:
- normalization,
- relationship resolution,
- metric derivation,
- BI view generation.

### Validation
Tests in `dbt/tests/` and `tests/` verify:
- logical constraints,
- metric ranges,
- temporal consistency,
- non-negative velocity metrics.

### Consumption
- Streamlit app uses governed query templates.
- Metabase uses curated SQL/query packs and data-source setup automation.

## How to Read a Phase Report
Use this pattern for every phase:
- objective,
- what was implemented,
- what was validated,
- risks and tradeoffs,
- production implications.

Good starting points:
- `docs/reports/phase-4/phase-4-end-report.md`
- `docs/reports/phase-5/phase-5-end-report.md`
- `docs/reports/phase-12/phase-12-end-report.md`

## Common Beginner Misconceptions
- "If chart loads, insight exists." False. Insight requires sufficient history and quality.
- "AI-generated SQL means governance is unnecessary." False. Governance is more important with AI.
- "Passing tests means business trust is guaranteed." False. You still need semantic clarity and stakeholder validation.

## How This Project Demonstrates Engineering Maturity
- Contract-first thinking.
- Multi-layer model architecture.
- Deterministic quality gates.
- Operational runbooks.
- Artifact-driven governance and release readiness.

## Suggested 14-Day Study Plan
Day 1-2:
- Read `README.md` and project-governance docs.

Day 3-4:
- Trace one source field from raw to BI output.

Day 5-6:
- Study reconciliation models in `dbt/models/intermediate/`.

Day 7-8:
- Study Phase 4 and Phase 5 end reports.

Day 9-10:
- Study tests and quality gates.

Day 11-12:
- Study Phase 11 and Phase 12 defense/reporting artifacts.

Day 13:
- Write your own architecture explanation from memory.

Day 14:
- Rehearse an interview answer: "How does this system prevent misleading funnel decisions?"

## Interview Prep Checklist From This Tutorial
You should be able to answer:
- Why dbt over ad hoc SQL scripts?
- Why snapshots are needed for RevOps history.
- How you control AI assistant risk in analytics interfaces.
- Why one-month data cannot support trend decisions.
- How CI gates protect business trust.

## Final Beginner Advice
Treat this project as both:
- a technical platform, and
- a decision system.

If code is correct but decisions are still weak, improve data quality and semantic coverage first.
