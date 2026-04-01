# Other Commands Log (5Ws and H)

This file captures commands that do not fit Git, shell, Make, or Python/dbt/DuckDB categories.

## Entry format
- What
- Why
- Who
- When
- Where
- How

## Entries

### OTH-001
- What: pre-commit install
- Why: install local hook scripts for quality and security guardrails
- Who: project maintainer
- When: initial setup and environment rebuilds
- Where: repository root
- How:
  - Preconditions: pre-commit available in environment
  - Expected output: hook installation confirmation
  - Recovery: reinstall after Python environment recreation

### OTH-002
- What: AIRFLOW_HOME=.airflow airflow db migrate
- Why: initialize Airflow metadata database
- Who: project maintainer
- When: orchestration setup
- Where: repository root
- How:
  - Preconditions: Airflow installed and AIRFLOW_HOME writable
  - Expected output: migration completion summary
  - Recovery: inspect Airflow logs for migration issues

### OTH-003
- What: AIRFLOW_HOME=.airflow airflow users create ...
- Why: create administrative user for Airflow standalone operations
- Who: project maintainer
- When: orchestration setup
- Where: repository root
- How:
  - Preconditions: admin username, email, and password environment values set
  - Expected output: user creation confirmation
  - Recovery: rerun with corrected credentials and role values

### OTH-004
- What: AIRFLOW_HOME=.airflow airflow standalone
- Why: start local Airflow stack for orchestration testing
- Who: project maintainer
- When: integration runs and demos
- Where: repository root
- How:
  - Preconditions: initialization completed
  - Expected output: webserver and scheduler startup logs
  - Recovery: check port conflicts and metadata DB health
