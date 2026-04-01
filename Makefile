PYTHON ?= python
PIP ?= pip
AIRFLOW_VERSION ?= 2.10.5
AIRFLOW_CONSTRAINTS ?= https://raw.githubusercontent.com/apache/airflow/constraints-$(AIRFLOW_VERSION)/constraints-3.10.txt
DBT_THREADS_LOCAL ?= 1
DBT_THREADS_PROD ?= 4

.PHONY: setup lint test format airflow-init airflow-start init-warehouse dbt-deps dbt-build dbt-build-prod dbt-source-freshness dbt-snapshot dbt-snapshot-prod dbt-test dbt-test-prod dbt-deploy-prod metric-parity-check metric-parity-check-strict metric-parity-check-report release-readiness-gate release-readiness-gate-strict query-pack-validate ge-validate quality-checks quality-gate preflight ingest-crm poll-leads ingest-leads export-bronze check-freshness

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
	cd dbt && dbt build --profiles-dir profiles --threads $(DBT_THREADS_LOCAL)

dbt-build-prod:
	cd dbt && dbt build --profiles-dir profiles --target prod --threads $(DBT_THREADS_PROD)

dbt-source-freshness:
	cd dbt && dbt source freshness --profiles-dir profiles --threads $(DBT_THREADS_LOCAL)

dbt-snapshot:
	cd dbt && dbt snapshot --profiles-dir profiles

dbt-snapshot-prod:
	cd dbt && dbt snapshot --profiles-dir profiles --target prod

dbt-test:
	cd dbt && dbt test --profiles-dir profiles --threads $(DBT_THREADS_LOCAL)

dbt-test-prod:
	cd dbt && dbt test --profiles-dir profiles --target prod --threads $(DBT_THREADS_PROD)

dbt-deploy-prod:
	$(MAKE) dbt-build-prod
	$(MAKE) dbt-test-prod

metric-parity-check:
	$(PYTHON) scripts/quality/run_metric_parity_check.py

metric-parity-check-strict:
	$(PYTHON) scripts/quality/run_metric_parity_check.py --strict-snowflake

metric-parity-check-report:
	$(PYTHON) scripts/quality/run_metric_parity_check.py --output-json artifacts/parity/metric_parity_report.json

release-readiness-gate:
	$(PYTHON) scripts/quality/run_release_readiness_gate.py

release-readiness-gate-strict:
	$(PYTHON) scripts/quality/run_release_readiness_gate.py --strict

query-pack-validate:
	$(PYTHON) scripts/quality/run_query_pack_validation.py

ge-validate:
	$(PYTHON) scripts/quality/run_great_expectations.py

quality-checks:
	$(PYTHON) scripts/quality/run_data_quality_checks.py

quality-gate:
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) dbt-build
	$(MAKE) dbt-test
	$(MAKE) query-pack-validate
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
