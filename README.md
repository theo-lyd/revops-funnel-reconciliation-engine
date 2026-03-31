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
