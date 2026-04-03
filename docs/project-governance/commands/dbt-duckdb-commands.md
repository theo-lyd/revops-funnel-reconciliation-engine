# dbt and DuckDB Command Log (5Ws and H)

This file records local DuckDB prep and dbt transformation commands.

## Entry format
- What
- Why
- Who
- When
- Where
- How
- Line-numbered example

## DuckDB and warehouse commands

### DD-001
- What: `python scripts/init_warehouse.py`
- Why: initialize local DuckDB schemas and baseline objects
- Who: project maintainer
- When: setup and environment repair
- Where: repository root
- How:
  - Preconditions: writable warehouse path and valid imports
  - Alternatives: `make init-warehouse`
  - Expected output: initialization confirmation
  - Recovery: verify permissions and rerun
- Line-numbered example:
  1. `python scripts/init_warehouse.py`

### DD-002
- What: `python scripts/ingest/load_crm_csv_to_duckdb.py`
- Why: load CRM CSV data into DuckDB
- Who: project maintainer
- When: ingestion refreshes
- Where: repository root
- How:
  - Preconditions: CRM files present in data/raw
  - Alternatives: `make ingest-crm`
  - Expected output: table load summary
  - Recovery: validate file paths and schema mapping
- Line-numbered example:
  1. `python scripts/ingest/load_crm_csv_to_duckdb.py`

### DD-003
- What: `python scripts/ingest/load_leads_jsonl_to_duckdb.py`
- Why: load leads JSONL into DuckDB
- Who: project maintainer
- When: ingestion and quality-gate setup
- Where: repository root
- How:
  - Preconditions: marketing JSONL exists
  - Alternatives: `make ingest-leads`
  - Expected output: lead-row ingest summary
  - Recovery: fetch/generate missing source data and rerun
- Line-numbered example:
  1. `python scripts/ingest/load_leads_jsonl_to_duckdb.py`

## dbt commands

### DD-004
- What: `cd dbt && dbt deps`
- Why: install dbt package dependencies
- Who: project maintainer
- When: setup and package updates
- Where: dbt directory
- How:
  - Preconditions: dbt profile configured
  - Alternatives: `make dbt-deps`
  - Expected output: package install summary
  - Recovery: resolve network/version issues and rerun
- Line-numbered example:
  1. `cd dbt`
  2. `dbt deps`

### DD-005
- What: `cd dbt && dbt build --profiles-dir profiles`
- Why: build model graph with tests/snapshots
- Who: project maintainer
- When: transformation validation
- Where: dbt directory
- How:
  - Preconditions: sources available and profile valid
  - Alternatives: `make dbt-build`; add `--select` for scoped runs
  - Expected output: build summary with pass/fail totals
  - Recovery: fix failing nodes and rerun
- Line-numbered example:
  1. `cd dbt`
  2. `dbt build --profiles-dir profiles`

### DD-006
- What: `cd dbt && dbt test --profiles-dir profiles --threads 1`
- Why: run stable data tests in constrained environments
- Who: project maintainer
- When: quality checks and release prep
- Where: dbt directory
- How:
  - Preconditions: models built
  - Alternatives: `make dbt-test`; increase threads in stronger environments
  - Expected output: test pass/fail summary
  - Recovery: inspect failing compiled SQL and rerun
- Line-numbered example:
  1. `cd dbt`
  2. `dbt test --profiles-dir profiles --threads 1`

### DD-007
- What: `cd dbt && dbt snapshot --profiles-dir profiles`
- Why: generate snapshot history tables
- Who: project maintainer
- When: snapshot refresh windows
- Where: dbt directory
- How:
  - Preconditions: snapshot configs and sources valid
  - Alternatives: `make dbt-snapshot`; `dbt snapshot --target prod`
  - Expected output: snapshot execution summary
  - Recovery: correct source/snapshot config and rerun
- Line-numbered example:
  1. `cd dbt`
  2. `dbt snapshot --profiles-dir profiles`

### DD-008
- What: `cd dbt && dbt source freshness --profiles-dir profiles --threads 1`
- Why: validate source freshness SLAs
- Who: project maintainer
- When: reliability checks and stop-gates
- Where: dbt directory
- How:
  - Preconditions: freshness checks defined
  - Alternatives: `make dbt-source-freshness`
  - Expected output: freshness report by source
  - Recovery: verify source schedules and credentials
- Line-numbered example:
  1. `cd dbt`
  2. `dbt source freshness --profiles-dir profiles --threads 1`
