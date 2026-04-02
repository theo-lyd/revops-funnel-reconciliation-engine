PYTHON ?= python
PIP ?= pip
AIRFLOW_VERSION ?= 2.10.5
AIRFLOW_CONSTRAINTS ?= https://raw.githubusercontent.com/apache/airflow/constraints-$(AIRFLOW_VERSION)/constraints-3.10.txt
DBT_THREADS_LOCAL ?= 1
DBT_THREADS_PROD ?= 4
DBT_BASE_REF ?= origin/master

.PHONY: setup lint test format airflow-init airflow-start init-warehouse dbt-deps dbt-build dbt-build-prod dbt-build-changed dbt-source-freshness dbt-snapshot dbt-snapshot-prod dbt-test dbt-test-prod dbt-test-changed dbt-deploy-prod metric-parity-check metric-parity-check-strict metric-parity-check-report release-readiness-gate release-readiness-gate-strict release-evidence-bundle refresh-caches promote-deployment rollback-deployment production-stop-gate production-stop-gate-strict query-pack-validate ge-validate quality-checks quality-gate preflight ingest-crm poll-leads ingest-leads export-bronze check-freshness metabase-setup streamlit-dev anomaly-check insights-generate

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

dbt-build-changed:
	$(PYTHON) scripts/ops/run_changed_model_dbt.py build --base-ref $(DBT_BASE_REF)

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

dbt-test-changed:
	$(PYTHON) scripts/ops/run_changed_model_dbt.py test --base-ref $(DBT_BASE_REF)

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

release-evidence-bundle:
	@test -n "$$RELEASE_ID" || (echo "RELEASE_ID is required" && exit 1)
	$(PYTHON) scripts/governance/generate_release_evidence_bundle.py --release-id "$$RELEASE_ID"

refresh-caches:
	$(PYTHON) scripts/ops/refresh_runtime_caches.py

promote-deployment:
	$(PYTHON) scripts/ops/promote_deployment.py

rollback-deployment:
	$(PYTHON) scripts/ops/rollback_deployment.py

execute-rollback-playbook:
	$(PYTHON) scripts/ops/execute_rollback_playbook.py --rollback-report artifacts/promotions/deployment_rollback.json

dispatch-rollback-incident:
	$(PYTHON) scripts/ops/dispatch_rollback_incident.py --incident-payload artifacts/promotions/rollback_incident_payload.json --max-attempts $${ROLLBACK_INCIDENT_MAX_ATTEMPTS:-3} --backoff-seconds $${ROLLBACK_INCIDENT_BACKOFF_SECONDS:-2} --dead-letter-output artifacts/promotions/rollback_incident_dead_letter.json

escalate-rollback-dead-letter:
	$(PYTHON) scripts/ops/escalate_rollback_dead_letter.py --dead-letter artifacts/promotions/rollback_incident_dead_letter.json --max-attempts $${ROLLBACK_ESCALATION_MAX_ATTEMPTS:-2} --backoff-seconds $${ROLLBACK_ESCALATION_BACKOFF_SECONDS:-3}

production-stop-gate:
	$(MAKE) quality-gate
	$(MAKE) metric-parity-check-report
	$(MAKE) release-readiness-gate

production-stop-gate-strict:
	$(MAKE) quality-gate
	$(MAKE) metric-parity-check-strict
	$(MAKE) release-readiness-gate-strict
	$(MAKE) release-evidence-bundle

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

# Phase 5: Analytics and Visualization targets

metabase-setup:
	@echo "Setting up Metabase for Phase 5 dashboards..."
	$(PYTHON) scripts/analytics/setup_metabase.py --host $(METABASE_HOST) --port $(METABASE_PORT)

streamlit-dev:
	@echo "Starting Streamlit app on port $${STREAMLIT_SERVER_PORT:-8501}..."
	streamlit run scripts/analytics/streamlit_app.py --server.port $${STREAMLIT_SERVER_PORT:-8501}

anomaly-check:
	@echo "Running Batch 5.4 anomaly monitoring check..."
	$(PYTHON) scripts/analytics/anomaly_monitor.py --source duckdb --output-json $(ANOMALY_REPORT_PATH) --output-markdown $(ANOMALY_MARKDOWN_PATH)

insights-generate:
	@echo "Generating Batch 5.4 monitoring insights..."
	$(PYTHON) scripts/analytics/anomaly_monitor.py --source duckdb --output-json $(ANOMALY_REPORT_PATH) --output-markdown $(ANOMALY_MARKDOWN_PATH)
