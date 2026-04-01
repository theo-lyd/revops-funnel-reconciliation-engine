# revops-funnel-reconciliation-engine
A production-grade Revenue Operations framework for identifying mid-funnel friction and revenue leakage. Built with the Modern Data Stack (Snowflake, dbt, Airflow) and featuring an LLM-powered analytical interface.

## Quick Start

### 1) Open in GitHub Codespaces
The repository includes a devcontainer with Python 3.10, dbt tooling, and development extensions.

### 2) Bootstrap locally
```bash
./scripts/bootstrap.sh
make preflight
```

### 3) Run checks
```bash
make lint
make test
make quality-gate
```

### 4) Initialize local warehouse
```bash
make init-warehouse
```

### 5) Configure dbt profile
```bash
cp dbt/profiles/profiles.yml.example dbt/profiles/profiles.yml
make dbt-deps
make dbt-snapshot
```

### 6) Load Bronze data
```bash
make ingest-crm
# In a separate terminal, run the synthetic API server first, then:
make poll-leads
make ingest-leads
make export-bronze
make check-freshness
make quality-checks
```

### 7) Orchestrate with Airflow
```bash
export AIRFLOW_ADMIN_USERNAME=admin
export AIRFLOW_ADMIN_EMAIL=admin@example.com
export AIRFLOW_ADMIN_PASSWORD='<set-a-strong-password>'
make airflow-init
make airflow-start
```

### 8) Align with Snowflake production target
```bash
cp dbt/profiles/profiles.yml.example dbt/profiles/profiles.yml
export SNOWFLAKE_ACCOUNT='<your-account>'
export SNOWFLAKE_USER='<your-user>'
export SNOWFLAKE_PASSWORD='<your-password>'
export SNOWFLAKE_ROLE='TRANSFORMER'
export SNOWFLAKE_DATABASE='REVOPS'
export SNOWFLAKE_WAREHOUSE='TRANSFORMING'

# Build/test against Snowflake target
make dbt-build-prod
make dbt-test-prod

# Optional parity check between local DuckDB and Snowflake metrics
make metric-parity-check

# Generate machine-readable parity report artifact
make metric-parity-check-report

# End-to-end production readiness gate (local-safe skip without Snowflake env)
make release-readiness-gate

# Strict production gate for CI/CD with full Snowflake credentials
make release-readiness-gate-strict

# Full production stop-gate sequence (local-safe)
make production-stop-gate

# Strict production stop-gate sequence (requires Snowflake env + RELEASE_ID)
RELEASE_ID=phase4-hardening-block4 make production-stop-gate-strict

# Generate release evidence bundle artifact
RELEASE_ID=phase4-hardening-block4 make release-evidence-bundle
```

## Repository Layout

- `.devcontainer/`: Reproducible Codespaces configuration
- `data/raw/crm/`: Raw CRM source files (batch source)
- `dbt/`: Analytics engineering models and macros
- `dags/`: Airflow orchestration DAGs
- `docs/reports/`: Batch and phase implementation reports
- `requirements/`: Runtime and development dependency manifests
- `scripts/`: Utility scripts (bootstrap, loaders, checks)
- `src/revops_funnel/`: Core Python package
- `tests/`: Automated tests

## Documentation

### Phase 4: Semantic Layer and Gold Layer
Phase 4 delivery includes four batches plus optional post-phase hardening:

1. **Batch 4.1**: [Gold marts foundation](docs/reports/phase-4/batch-4.1-gold-marts-foundation.md)
2. **Batch 4.2**: [Semantic metric contract and governed glossary](docs/reports/phase-4/batch-4.2-semantic-metric-contract-and-governed-glossary.md)
3. **Batch 4.3**: [BI readiness layer](docs/reports/phase-4/batch-4.3-bi-readiness-layer.md)
4. **Batch 4.4**: [Snowflake production alignment and deployment governance](docs/reports/phase-4/batch-4.4-snowflake-production-alignment-and-deployment-governance.md)

### Post-Phase 4 Hardening (Optional, Completed)
Four optional hardening blocks strengthen production deployment and governance:

- **Block 1**: [Governance and security hardening](docs/reports/phase-4/post-phase-4-block-1-governance-and-security-hardening.md)
- **Block 2**: [Observability and reliability hardening](docs/reports/phase-4/post-phase-4-block-2-observability-and-reliability.md)
- **Block 3**: [Production readiness and parity enforcement](docs/reports/phase-4/post-phase-4-block-3-production-readiness-and-parity-enforcement.md)
- **Block 4**: [Governance automation and stop-gate orchestration](docs/reports/phase-4/post-phase-4-block-4-governance-automation-and-stop-gate-orchestration.md)
- **Summary**: [Post-phase-4-hardening complete summary](docs/reports/phase-4/post-phase-4-hardening-complete-summary.md)

### Phase 5: AI-Driven Analytics and Visualization
Phase 5 delivery currently includes planning and first two batches:

1. **Plan**: [Phase 5 implementation plan](docs/reports/phase-5/PHASE-5-PLAN.md)
2. **Batch 5.1**: [Dashboard foundation and BI layer integration](docs/reports/phase-5/batch-5.1-dashboard-foundation.md)
3. **Batch 5.2**: [Streamlit application and query templates](docs/reports/phase-5/batch-5.2-streamlit-application-and-query-templates.md)
4. **Batch 5.3**: [LLM integration and AI-driven query generation](docs/reports/phase-5/batch-5.3-llm-integration-and-ai-driven-query-generation.md)
5. **Batch 5.4**: [Analytics insights and anomaly detection](docs/reports/phase-5/batch-5.4-analytics-insights-and-anomaly-detection.md)
6. **Post-Phase 5 Hardening**: [Shared modules and validation](docs/reports/phase-5/post-phase-5-hardening-shared-modules-and-validation.md)
7. **Hardening Summary**: [Final hardening summary](docs/reports/phase-5/PHASE-5-HARDENING-FINAL-SUMMARY.md)
8. **End Report**: [Phase 5 end report](docs/reports/phase-5/phase-5-end-report.md)

### Phase 6: Monitoring Delivery and Alert Transport
Phase 6 extends monitoring from artifact generation into optional notification delivery:

1. **Plan**: [Phase 6 implementation plan](docs/reports/phase-6/PHASE-6-PLAN.md)
2. **Batch 6.1**: [Monitoring email delivery](docs/reports/phase-6/batch-6.1-monitoring-email-delivery.md)
3. **End Report**: [Phase 6 end report](docs/reports/phase-6/phase-6-end-report.md)

### Project Governance
- [Standing instructions and process documentation](docs/project-governance/standing-instructions.md)
- [Phase completion checklist and stop-gate workflow](docs/project-governance/phase-completion-checklist.md)
- [Issues and resolution log](docs/project-governance/issues-log.md)
- [Command ledgers (git, make, python, dbt, etc.)](docs/project-governance/commands/)
