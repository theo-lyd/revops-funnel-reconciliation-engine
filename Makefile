PYTHON ?= python
PIP ?= pip
AIRFLOW_VERSION ?= 2.10.5
AIRFLOW_CONSTRAINTS ?= https://raw.githubusercontent.com/apache/airflow/constraints-$(AIRFLOW_VERSION)/constraints-3.10.txt
DBT_THREADS_LOCAL ?= 1
DBT_THREADS_PROD ?= 4
DBT_MAX_THREADS_LOCAL ?= 2
DBT_MAX_THREADS_PROD ?= 4
DBT_TIMEOUT_SECONDS_LOCAL ?= 900
DBT_TIMEOUT_SECONDS_PROD ?= 1800
DBT_BASE_REF ?= origin/master
DBT_PROD_SELECTOR ?= path:models/staging path:models/intermediate path:models/marts
COST_LOOKBACK_HOURS ?= 24
COST_MAX_QUERIES ?= 2000
COST_QUERY_TAG_PREFIX ?=
COST_BASELINE_REPORT_PATH ?= artifacts/performance/query_cost_attribution_baseline.json
COST_REGRESSION_REPORT_PATH ?= artifacts/performance/query_cost_regression_report.json
COST_MAX_CREDITS_REGRESSION_PCT ?= 20
COST_MAX_ELAPSED_REGRESSION_PCT ?= 25
COST_MAX_NEW_QUERY_TAGS ?= 0
PHASE82_ENABLE ?= false
PHASE82_TEAM_TAG_MAPPING ?=
PHASE82_BUDGET_THRESHOLD_PCT ?= 80
PHASE82_STAGING_TO_PROD_MULTIPLIER ?= 5.0
PHASE82_WAREHOUSE_DAILY_BUDGET_CREDITS ?= 100
PHASE82_WAREHOUSE_CURRENT_DAILY_BURN ?= 45.6
PHASE82_PROD_CURRENT_MONTHLY_COST ?= 0
HEALTH_MAX_FRESHNESS_HOURS ?= 24
HEALTH_MAX_JOB_DURATION_MINUTES ?= 120
HEALTH_REPORT_PATH ?= artifacts/monitoring/health_report.json
HEALTH_STRICT_METRICS ?= false
DASHBOARD_OUTPUT_PATH ?= artifacts/monitoring/operational_dashboard.json
DASHBOARD_HEALTH_REPORT ?= artifacts/monitoring/health_report.json
DASHBOARD_COST_REPORT ?= artifacts/monitoring/query_cost_attribution.json
DASHBOARD_PERFORMANCE_REPORT ?= artifacts/performance/dbt_build_prod_report.json
ONCALL_RUNBOOK_REPORT_PATH ?= artifacts/runbooks/oncall_runbook_report.json
ONCALL_HEALTH_REPORT ?= artifacts/monitoring/health_report.json
ONCALL_DASHBOARD_REPORT ?= artifacts/monitoring/operational_dashboard.json
ONCALL_ROLLBACK_REPORT ?= artifacts/promotions/deployment_rollback_execution.json
ONCALL_INCIDENT_DISPATCH_REPORT ?= artifacts/promotions/rollback_incident_dispatch.json
ONCALL_DEAD_LETTER_ESCALATION_REPORT ?= artifacts/promotions/rollback_dead_letter_escalation.json
ONCALL_PRIMARY_ENDPOINT ?= pagerduty-primary
ONCALL_SECONDARY_ENDPOINT ?= pagerduty-secondary
ONCALL_TICKET_QUEUE ?= revops-platform
INCIDENT_OPERATIONS_REPORT_PATH ?= artifacts/runbooks/incident_operations_report.json
INCIDENT_OPS_HEALTH_REPORT ?= artifacts/monitoring/health_report.json
INCIDENT_OPS_DASHBOARD_REPORT ?= artifacts/monitoring/operational_dashboard.json
INCIDENT_OPS_RUNBOOK_REPORT ?= artifacts/runbooks/oncall_runbook_report.json
INCIDENT_OPS_DISPATCH_REPORT ?= artifacts/promotions/rollback_incident_dispatch.json
INCIDENT_OPS_ESCALATION_REPORT ?= artifacts/promotions/rollback_dead_letter_escalation.json
INCIDENT_OPS_RECENT_PATTERNS ?= artifacts/runbooks/recent_patterns.json
INCIDENT_OPS_FATIGUE_REPEAT_THRESHOLD ?= 3
INCIDENT_OPS_FATIGUE_DECAY_HALF_LIFE_HOURS ?= 24
INCIDENT_OPS_POLICY_PATH ?=
INCIDENT_OPS_STRICT_MIN_EVIDENCE_COMPLETENESS ?= 0.8
INCIDENT_OPS_CORRELATION_ID ?=
PHASE11_VALIDATION_REPORT_PATH ?= artifacts/validation/validation_backtesting_report.json
PHASE11_CURRENT_COST_REPORT_PATH ?= artifacts/performance/query_cost_attribution_report.json
PHASE11_BASELINE_COST_REPORT_PATH ?= artifacts/performance/query_cost_attribution_baseline.json
PHASE11_REGRESSION_REPORT_PATH ?= artifacts/performance/query_cost_regression_report.json
PHASE11_FORECAST_REPORT_PATH ?= artifacts/performance/query_cost_forecast_report.json
PHASE11_CROSS_ENVIRONMENT_REPORT_PATH ?= artifacts/performance/cross_environment_forecast.json
PHASE11_PR_IMPACT_REPORT_PATH ?= artifacts/performance/pr_cost_impact_score.json
PHASE11_HEALTH_REPORT_PATH ?= artifacts/monitoring/health_report.json
PHASE11_DASHBOARD_REPORT_PATH ?= artifacts/monitoring/operational_dashboard.json
PHASE11_RUNBOOK_REPORT_PATH ?= artifacts/runbooks/oncall_runbook_report.json
PHASE11_INCIDENT_OPERATIONS_REPORT_PATH ?= artifacts/runbooks/incident_operations_report.json
PHASE11_MIN_ARTIFACT_COVERAGE ?= 0.8
PHASE11_MAX_CREDITS_REGRESSION_PCT ?= 20
PHASE11_MAX_ELAPSED_REGRESSION_PCT ?= 25
PHASE11_MIN_OPERATIONAL_READINESS_SCORE ?= 0.7
PHASE11_MAX_FORECAST_MISMATCH_PCT ?= 25
PHASE11_STRICT_VALIDATION ?= false
PHASE11_POLICY_PATH ?=
PHASE11_CORRELATION_ID ?=

.PHONY: setup lint test format airflow-init airflow-start init-warehouse dbt-deps dbt-build dbt-build-prod dbt-build-changed dbt-source-freshness dbt-snapshot dbt-snapshot-prod dbt-test dbt-test-prod dbt-test-changed dbt-deploy-prod metric-parity-check metric-parity-check-strict metric-parity-check-report release-readiness-gate release-readiness-gate-strict release-evidence-bundle refresh-caches promote-deployment rollback-deployment production-stop-gate production-stop-gate-strict query-cost-attribution query-cost-attribution-strict query-cost-regression query-cost-regression-strict phase82-cost-forecast phase82-pattern-analysis phase82-phase-attribution phase82-cross-env-impact phase82-pr-impact phase82-warehouse-preflight phase82-runbook-gen phase82-suite health-checks health-checks-strict dashboards dashboards-strict oncall-runbooks oncall-runbooks-strict incident-ops incident-ops-strict phase11-validation phase11-validation-strict query-pack-validate ge-validate quality-checks quality-gate preflight ingest-crm poll-leads ingest-leads export-bronze check-freshness metabase-setup streamlit-dev anomaly-check insights-generate reporting-pack

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
	$(PYTHON) scripts/ops/run_dbt_budgeted.py --command build --environment production --project-dir dbt --profiles-dir profiles --target prod --select "$(DBT_PROD_SELECTOR)" --threads $(DBT_THREADS_PROD) --max-threads-local $(DBT_MAX_THREADS_LOCAL) --max-threads-prod $(DBT_MAX_THREADS_PROD) --timeout-seconds-local $(DBT_TIMEOUT_SECONDS_LOCAL) --timeout-seconds-prod $(DBT_TIMEOUT_SECONDS_PROD) --output artifacts/performance/dbt_build_prod_report.json

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
	$(PYTHON) scripts/ops/run_dbt_budgeted.py --command test --environment production --project-dir dbt --profiles-dir profiles --target prod --select "$(DBT_PROD_SELECTOR)" --threads $(DBT_THREADS_PROD) --max-threads-local $(DBT_MAX_THREADS_LOCAL) --max-threads-prod $(DBT_MAX_THREADS_PROD) --timeout-seconds-local $(DBT_TIMEOUT_SECONDS_LOCAL) --timeout-seconds-prod $(DBT_TIMEOUT_SECONDS_PROD) --output artifacts/performance/dbt_test_prod_report.json

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

performance-gate:
	$(PYTHON) scripts/ops/run_dbt_budgeted.py --command build --environment local --project-dir dbt --profiles-dir profiles --threads $(DBT_THREADS_LOCAL) --max-threads-local $(DBT_MAX_THREADS_LOCAL) --max-threads-prod $(DBT_MAX_THREADS_PROD) --timeout-seconds-local $(DBT_TIMEOUT_SECONDS_LOCAL) --timeout-seconds-prod $(DBT_TIMEOUT_SECONDS_PROD) --output artifacts/performance/dbt_build_local_report.json

query-cost-attribution:
	$(PYTHON) scripts/ops/generate_query_cost_attribution.py --lookback-hours $(COST_LOOKBACK_HOURS) --max-queries $(COST_MAX_QUERIES) --query-tag-prefix "$(COST_QUERY_TAG_PREFIX)" --output artifacts/performance/query_cost_attribution_report.json

query-cost-attribution-strict:
	$(PYTHON) scripts/ops/generate_query_cost_attribution.py --strict-snowflake --lookback-hours $(COST_LOOKBACK_HOURS) --max-queries $(COST_MAX_QUERIES) --query-tag-prefix "$(COST_QUERY_TAG_PREFIX)" --output artifacts/performance/query_cost_attribution_report.json

query-cost-regression:
	$(PYTHON) scripts/ops/check_query_cost_regression.py --current-report artifacts/performance/query_cost_attribution_report.json --baseline-report $(COST_BASELINE_REPORT_PATH) --max-credits-regression-pct $(COST_MAX_CREDITS_REGRESSION_PCT) --max-elapsed-regression-pct $(COST_MAX_ELAPSED_REGRESSION_PCT) --max-new-query-tags $(COST_MAX_NEW_QUERY_TAGS) --output $(COST_REGRESSION_REPORT_PATH)

query-cost-regression-strict:
	$(PYTHON) scripts/ops/check_query_cost_regression.py --strict-baseline --current-report artifacts/performance/query_cost_attribution_report.json --baseline-report $(COST_BASELINE_REPORT_PATH) --max-credits-regression-pct $(COST_MAX_CREDITS_REGRESSION_PCT) --max-elapsed-regression-pct $(COST_MAX_ELAPSED_REGRESSION_PCT) --max-new-query-tags $(COST_MAX_NEW_QUERY_TAGS) --output $(COST_REGRESSION_REPORT_PATH)

phase82-cost-forecast:
	$(PYTHON) scripts/ops/forecast_query_cost_budget.py --attribution-report artifacts/performance/query_cost_attribution_report.json --team-owner-tag-mapping '$(PHASE82_TEAM_TAG_MAPPING)' --budget-threshold-pct $(PHASE82_BUDGET_THRESHOLD_PCT) --staging-to-prod-multiplier $(PHASE82_STAGING_TO_PROD_MULTIPLIER) --output artifacts/performance/query_cost_forecast_report.json

phase82-pattern-analysis:
	$(PYTHON) scripts/ops/analyze_query_patterns.py --attribution-report artifacts/performance/query_cost_attribution_report.json --output artifacts/performance/query_pattern_analysis.json

phase82-phase-attribution:
	$(PYTHON) scripts/ops/generate_execution_phase_attribution.py --dbt-budget-report artifacts/performance/dbt_build_prod_report.json --output artifacts/performance/execution_phase_attribution.json

phase82-cross-env-impact:
	$(PYTHON) scripts/ops/estimate_cross_environment_impact.py --staging-report artifacts/performance/query_cost_attribution_report.json --prod-current $(PHASE82_PROD_CURRENT_MONTHLY_COST) --staging-to-prod-multiplier $(PHASE82_STAGING_TO_PROD_MULTIPLIER) --output artifacts/performance/cross_environment_forecast.json

phase82-pr-impact:
	$(PYTHON) scripts/ops/analyze_pr_cost_impact.py --baseline-monthly-cost $${BASELINE_MONTHLY_COST:-500} --output artifacts/performance/pr_cost_impact_score.json

phase82-warehouse-preflight:
	$(PYTHON) scripts/ops/emit_warehouse_cost_estimate.py --daily-budget-credits $(PHASE82_WAREHOUSE_DAILY_BUDGET_CREDITS) --current-daily-burn $(PHASE82_WAREHOUSE_CURRENT_DAILY_BURN) --output artifacts/performance/warehouse_cost_estimate.json

phase82-runbook-gen:
	$(PYTHON) scripts/ops/generate_cost_optimization_runbooks.py --pattern-analysis artifacts/performance/query_pattern_analysis.json --runbook-approval-required --output artifacts/performance/optimization_runbooks.json

phase82-suite:
	$(MAKE) phase82-cost-forecast
	$(MAKE) phase82-pattern-analysis
	$(MAKE) phase82-phase-attribution
	$(MAKE) phase82-cross-env-impact
	$(MAKE) phase82-pr-impact
	$(MAKE) phase82-warehouse-preflight
	$(MAKE) phase82-runbook-gen

health-checks:
	$(PYTHON) scripts/ops/run_health_checks.py --max-freshness-hours $(HEALTH_MAX_FRESHNESS_HOURS) --max-job-duration-minutes $(HEALTH_MAX_JOB_DURATION_MINUTES) --output $(HEALTH_REPORT_PATH)

health-checks-strict:
	$(PYTHON) scripts/ops/run_health_checks.py --strict-metrics --max-freshness-hours $(HEALTH_MAX_FRESHNESS_HOURS) --max-job-duration-minutes $(HEALTH_MAX_JOB_DURATION_MINUTES) --output $(HEALTH_REPORT_PATH)

dashboards:
	$(PYTHON) scripts/ops/generate_operational_dashboards.py --health-report $(DASHBOARD_HEALTH_REPORT) --cost-report $(DASHBOARD_COST_REPORT) --performance-report $(DASHBOARD_PERFORMANCE_REPORT) --output $(DASHBOARD_OUTPUT_PATH)

dashboards-strict:
	$(PYTHON) scripts/ops/generate_operational_dashboards.py --strict-metrics --health-report $(DASHBOARD_HEALTH_REPORT) --cost-report $(DASHBOARD_COST_REPORT) --performance-report $(DASHBOARD_PERFORMANCE_REPORT) --output $(DASHBOARD_OUTPUT_PATH)

oncall-runbooks:
	$(PYTHON) scripts/ops/run_oncall_runbooks.py --health-report $(ONCALL_HEALTH_REPORT) --dashboard-report $(ONCALL_DASHBOARD_REPORT) --rollback-report $(ONCALL_ROLLBACK_REPORT) --incident-dispatch-report $(ONCALL_INCIDENT_DISPATCH_REPORT) --dead-letter-escalation-report $(ONCALL_DEAD_LETTER_ESCALATION_REPORT) --primary-endpoint "$(ONCALL_PRIMARY_ENDPOINT)" --secondary-endpoint "$(ONCALL_SECONDARY_ENDPOINT)" --ticket-queue "$(ONCALL_TICKET_QUEUE)" --output $(ONCALL_RUNBOOK_REPORT_PATH)

oncall-runbooks-strict:
	$(PYTHON) scripts/ops/run_oncall_runbooks.py --strict-artifacts --health-report $(ONCALL_HEALTH_REPORT) --dashboard-report $(ONCALL_DASHBOARD_REPORT) --rollback-report $(ONCALL_ROLLBACK_REPORT) --incident-dispatch-report $(ONCALL_INCIDENT_DISPATCH_REPORT) --dead-letter-escalation-report $(ONCALL_DEAD_LETTER_ESCALATION_REPORT) --primary-endpoint "$(ONCALL_PRIMARY_ENDPOINT)" --secondary-endpoint "$(ONCALL_SECONDARY_ENDPOINT)" --ticket-queue "$(ONCALL_TICKET_QUEUE)" --output $(ONCALL_RUNBOOK_REPORT_PATH)

incident-ops:
	$(PYTHON) scripts/ops/run_incident_operations.py --health-report $(INCIDENT_OPS_HEALTH_REPORT) --dashboard-report $(INCIDENT_OPS_DASHBOARD_REPORT) --runbook-report $(INCIDENT_OPS_RUNBOOK_REPORT) --dispatch-report $(INCIDENT_OPS_DISPATCH_REPORT) --escalation-report $(INCIDENT_OPS_ESCALATION_REPORT) --recent-patterns $(INCIDENT_OPS_RECENT_PATTERNS) --fatigue-repeat-threshold $(INCIDENT_OPS_FATIGUE_REPEAT_THRESHOLD) --fatigue-decay-half-life-hours $(INCIDENT_OPS_FATIGUE_DECAY_HALF_LIFE_HOURS) --policy "$(INCIDENT_OPS_POLICY_PATH)" --correlation-id "$(INCIDENT_OPS_CORRELATION_ID)" --output $(INCIDENT_OPERATIONS_REPORT_PATH)

incident-ops-strict:
	$(PYTHON) scripts/ops/run_incident_operations.py --strict-operations --require-dispatch-sent --require-escalation-sent --strict-min-evidence-completeness $(INCIDENT_OPS_STRICT_MIN_EVIDENCE_COMPLETENESS) --health-report $(INCIDENT_OPS_HEALTH_REPORT) --dashboard-report $(INCIDENT_OPS_DASHBOARD_REPORT) --runbook-report $(INCIDENT_OPS_RUNBOOK_REPORT) --dispatch-report $(INCIDENT_OPS_DISPATCH_REPORT) --escalation-report $(INCIDENT_OPS_ESCALATION_REPORT) --recent-patterns $(INCIDENT_OPS_RECENT_PATTERNS) --fatigue-repeat-threshold $(INCIDENT_OPS_FATIGUE_REPEAT_THRESHOLD) --fatigue-decay-half-life-hours $(INCIDENT_OPS_FATIGUE_DECAY_HALF_LIFE_HOURS) --policy "$(INCIDENT_OPS_POLICY_PATH)" --correlation-id "$(INCIDENT_OPS_CORRELATION_ID)" --output $(INCIDENT_OPERATIONS_REPORT_PATH)

phase11-validation:
	$(PYTHON) scripts/ops/run_validation_backtesting.py --current-cost-report $(PHASE11_CURRENT_COST_REPORT_PATH) --baseline-cost-report $(PHASE11_BASELINE_COST_REPORT_PATH) --regression-report $(PHASE11_REGRESSION_REPORT_PATH) --forecast-report $(PHASE11_FORECAST_REPORT_PATH) --cross-environment-report $(PHASE11_CROSS_ENVIRONMENT_REPORT_PATH) --pr-impact-report $(PHASE11_PR_IMPACT_REPORT_PATH) --health-report $(PHASE11_HEALTH_REPORT_PATH) --dashboard-report $(PHASE11_DASHBOARD_REPORT_PATH) --runbook-report $(PHASE11_RUNBOOK_REPORT_PATH) --incident-operations-report $(PHASE11_INCIDENT_OPERATIONS_REPORT_PATH) --policy "$(PHASE11_POLICY_PATH)" --correlation-id "$(PHASE11_CORRELATION_ID)" --min-artifact-coverage $(PHASE11_MIN_ARTIFACT_COVERAGE) --max-credits-regression-pct $(PHASE11_MAX_CREDITS_REGRESSION_PCT) --max-elapsed-regression-pct $(PHASE11_MAX_ELAPSED_REGRESSION_PCT) --min-operational-readiness-score $(PHASE11_MIN_OPERATIONAL_READINESS_SCORE) --max-forecast-mismatch-pct $(PHASE11_MAX_FORECAST_MISMATCH_PCT) --output $(PHASE11_VALIDATION_REPORT_PATH)

phase11-validation-strict:
	$(PYTHON) scripts/ops/run_validation_backtesting.py --strict-validation --current-cost-report $(PHASE11_CURRENT_COST_REPORT_PATH) --baseline-cost-report $(PHASE11_BASELINE_COST_REPORT_PATH) --regression-report $(PHASE11_REGRESSION_REPORT_PATH) --forecast-report $(PHASE11_FORECAST_REPORT_PATH) --cross-environment-report $(PHASE11_CROSS_ENVIRONMENT_REPORT_PATH) --pr-impact-report $(PHASE11_PR_IMPACT_REPORT_PATH) --health-report $(PHASE11_HEALTH_REPORT_PATH) --dashboard-report $(PHASE11_DASHBOARD_REPORT_PATH) --runbook-report $(PHASE11_RUNBOOK_REPORT_PATH) --incident-operations-report $(PHASE11_INCIDENT_OPERATIONS_REPORT_PATH) --policy "$(PHASE11_POLICY_PATH)" --correlation-id "$(PHASE11_CORRELATION_ID)" --min-artifact-coverage $(PHASE11_MIN_ARTIFACT_COVERAGE) --max-credits-regression-pct $(PHASE11_MAX_CREDITS_REGRESSION_PCT) --max-elapsed-regression-pct $(PHASE11_MAX_ELAPSED_REGRESSION_PCT) --min-operational-readiness-score $(PHASE11_MIN_OPERATIONAL_READINESS_SCORE) --max-forecast-mismatch-pct $(PHASE11_MAX_FORECAST_MISMATCH_PCT) --output $(PHASE11_VALIDATION_REPORT_PATH)

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

reporting-pack:
	@echo "Generating Public-Sector and Executive Reporting Pack..."
	$(PYTHON) scripts/analytics/generate_reporting_pack.py --output $${REPORTING_PACK_OUTPUT_PATH:-artifacts/reports/public_sector_executive_reporting_pack.json}
