PYTHON ?= python
PIP ?= pip

.PHONY: setup lint test format airflow-init airflow-start init-warehouse dbt-deps dbt-build preflight ingest-crm poll-leads ingest-leads

setup:
	$(PIP) install -r requirements/base.txt -r requirements/dev.txt
	pre-commit install

lint:
	ruff check .
	mypy src

test:
	pytest -q

format:
	ruff check . --fix
	ruff format .

airflow-init:
	AIRFLOW_HOME=.airflow airflow db migrate
	AIRFLOW_HOME=.airflow airflow users create --username admin --firstname RevOps --lastname Admin --role Admin --email admin@example.com --password admin

airflow-start:
	AIRFLOW_HOME=.airflow airflow standalone

init-warehouse:
	$(PYTHON) scripts/init_warehouse.py

dbt-deps:
	cd dbt && dbt deps

dbt-build:
	cd dbt && dbt build --profiles-dir profiles

preflight:
	$(PYTHON) scripts/preflight_check.py

ingest-crm:
	$(PYTHON) scripts/ingest/load_crm_csv_to_duckdb.py

poll-leads:
	$(PYTHON) scripts/ingest/poll_synthetic_leads_api.py

ingest-leads:
	$(PYTHON) scripts/ingest/load_leads_jsonl_to_duckdb.py
