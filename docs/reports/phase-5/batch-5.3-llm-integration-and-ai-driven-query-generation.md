# Batch 5.3: LLM Integration and AI-Driven Query Generation

## Objective
Add natural-language analytics routing with strict governance controls so users can ask business questions while the system executes only approved query templates.

## Deliverables
1. LLM-powered intent-to-template routing in Streamlit.
2. Session-level rate limiting for AI requests.
3. Audit logging of prompts and resolved template decisions.
4. Validation guard rails restricting output to approved templates and known office filters.

## Files Updated
- scripts/analytics/streamlit_app.py
- requirements/base.txt
- .env.example
- .gitignore

## What Was Implemented

### 1) AI Assistant UX in Streamlit
- Added an AI panel in the sidebar with:
  - Natural-language input text area.
  - Generate with AI action.
- AI routing can pre-select:
  - Query template.
  - Regional office filters.
- Then auto-executes query against selected source (DuckDB or Snowflake).

### 2) Intent Routing with Hard Guardrails
- Added a resolution layer that maps prompts to the approved template catalog only.
- Supported modes:
  - llm: uses OpenAI chat completion when API key and package are available.
  - heuristic: deterministic keyword fallback when LLM is unavailable.
- Enforced constraints:
  - template_key must be one of the existing templates.
  - offices list must be a subset of known regional offices.
  - no arbitrary SQL is accepted from user input.

### 3) Rate Limiting and Auditability
- Session rate limiting using environment-configured threshold:
  - LLM_RATE_LIMIT_PER_MINUTE
- Audit logging to JSONL:
  - default path: artifacts/ai/llm_query_audit.jsonl
- Logged fields include timestamp, source, prompt, selected template, office filters, date range, mode, and explanation.

### 4) Environment and Dependency Support
- Added OpenAI SDK dependency in requirements/base.txt.
- Added environment variables:
  - OPENAI_API_KEY
  - OPENAI_MODEL
  - LLM_MAX_TOKENS
  - LLM_RATE_LIMIT_PER_MINUTE
  - LLM_AUDIT_LOG_PATH
- Added artifacts/ai/ to gitignore for runtime audit artifacts.

## Governance and Safety Posture
- Query execution remains template-governed and schema-scoped.
- AI layer only chooses from sanctioned analytical paths.
- Missing credentials or unavailable SDK never blocks app usage:
  - app falls back to deterministic routing.
- Audit logs create reproducibility and reviewability for AI-mediated analytics decisions.

## Validation
- make lint: passed (Ruff + mypy)
- make test: passed

## Exit Criteria Status
- AI input pathway implemented: met.
- Guardrails on template and office selection: met.
- Session rate limiting and audit log: met.
- No regression in existing quality checks: met.

## Notes for Batch 5.4
- Use audit stream for anomaly narrative enrichment.
- Add monitoring/alerts for repeated high-risk prompt patterns.
