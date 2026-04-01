PYTHON ?= python
PIP ?= pip
AIRFLOW_VERSION ?= 2.10.5
AIRFLOW_CONSTRAINTS ?= https://raw.githubusercontent.com/apache/airflow/constraints-$(AIRFLOW_VERSION)/constraints-3.10.txt

.PHONY: setup lint test format airflow-init airflow-start init-warehouse dbt-deps dbt-build dbt-build-prod dbt-snapshot dbt-snapshot-prod dbt-test dbt-test-prod dbt-deploy-prod ge-validate quality-checks quality-gate preflight ingest-crm poll-leads ingest-leads export-bronze check-freshness

setup:
	$(PIP) install "apache-airflow==$(AIRFLOW_VERSION)" --constraint "$(AIRFLOW_CONSTRAINTS)"
	$(PIP) install -r requirements/base.txt -r requirements/dev.txt
	pre-commit install

lint:
	ruff check .
	mypy src scripts dags

test:
	pytest -q

format:
	ruff check . --fix
	ruff format .

airflow-init:
	@test -n "$$AIRFLOW_ADMIN_PASSWORD" || (echo "AIRFLOW_ADMIN_PASSWORD is required" && exit 1)
	@test -n "$$AIRFLOW_ADMIN_USERNAME" || (echo "AIRFLOW_ADMIN_USERNAME is required" && exit 1)
	@test -n "$$AIRFLOW_ADMIN_EMAIL" || (echo "AIRFLOW_ADMIN_EMAIL is required" && exit 1)
	AIRFLOW_HOME=.airflow airflow db migrate
	AIRFLOW_HOME=.airflow airflow users create --username "$$AIRFLOW_ADMIN_USERNAME" --firstname RevOps --lastname Admin --role Admin --email "$$AIRFLOW_ADMIN_EMAIL" --password "$$AIRFLOW_ADMIN_PASSWORD"

airflow-start:
	AIRFLOW_HOME=.airflow airflow standalone

init-warehouse:
	$(PYTHON) scripts/init_warehouse.py

dbt-deps:
	cd dbt && dbt deps

dbt-build:
	cd dbt && dbt build --profiles-dir profiles --threads 1

dbt-build-prod:
	cd dbt && dbt build --profiles-dir profiles --target prod --threads 4

dbt-snapshot:
	cd dbt && dbt snapshot --profiles-dir profiles

dbt-snapshot-prod:
	cd dbt && dbt snapshot --profiles-dir profiles --target prod

dbt-test:
	cd dbt && dbt test --profiles-dir profiles --threads 1

dbt-test-prod:
	cd dbt && dbt test --profiles-dir profiles --target prod --threads 4

dbt-deploy-prod:
	$(MAKE) dbt-build-prod
	$(MAKE) dbt-test-prod

ge-validate:
	$(PYTHON) scripts/quality/run_great_expectations.py

quality-checks:
	$(PYTHON) scripts/quality/run_data_quality_checks.py

quality-gate:
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) dbt-test
	$(MAKE) quality-checks
	$(MAKE) ge-validate

preflight:
	$(PYTHON) scripts/preflight_check.py

ingest-crm:
	$(PYTHON) scripts/ingest/load_crm_csv_to_duckdb.py

poll-leads:
	$(PYTHON) scripts/ingest/poll_synthetic_leads_api.py

ingest-leads:
	$(PYTHON) scripts/ingest/load_leads_jsonl_to_duckdb.py

export-bronze:
	$(PYTHON) scripts/transform/export_bronze_parquet.py

check-freshness:
	$(PYTHON) scripts/monitor/check_freshness.py --max-delay-hours 2
