"""Airflow DAG orchestrating the end-to-end RevOps pipeline."""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_ROOT = (
    "{{ var.value.project_root | default('/workspaces/revops-funnel-reconciliation-engine') }}"
)

DEFAULT_ARGS = {
    "owner": "revops-data-platform",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="revops_end_to_end_pipeline",
    description="Run the end-to-end RevOps pipeline with validation, cache refresh, and promotion",
    default_args=DEFAULT_ARGS,
    schedule="0 6 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["revops", "pipeline", "ci-cd", "operations"],
) as dag:
    init_warehouse = BashOperator(
        task_id="init_warehouse",
        bash_command=f"cd {PROJECT_ROOT} && make init-warehouse",
    )

    ingest_crm = BashOperator(
        task_id="ingest_crm",
        bash_command=f"cd {PROJECT_ROOT} && make ingest-crm",
    )

    poll_leads = BashOperator(
        task_id="poll_leads",
        bash_command=f"cd {PROJECT_ROOT} && make poll-leads",
    )

    ingest_leads = BashOperator(
        task_id="ingest_leads",
        bash_command=f"cd {PROJECT_ROOT} && make ingest-leads",
    )

    export_bronze = BashOperator(
        task_id="export_bronze",
        bash_command=f"cd {PROJECT_ROOT} && make export-bronze",
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"cd {PROJECT_ROOT} && make dbt-build-changed",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {PROJECT_ROOT} && make dbt-test-changed",
    )

    quality_gate = BashOperator(
        task_id="quality_gate",
        bash_command=f"cd {PROJECT_ROOT} && make quality-gate",
    )

    refresh_caches = BashOperator(
        task_id="refresh_caches",
        bash_command=f"cd {PROJECT_ROOT} && make refresh-caches",
    )

    release_readiness = BashOperator(
        task_id="release_readiness",
        bash_command=f"cd {PROJECT_ROOT} && make release-readiness-gate",
    )

    promote_deployment = BashOperator(
        task_id="promote_deployment",
        bash_command=f"cd {PROJECT_ROOT} && make promote-deployment",
    )

    init_warehouse >> ingest_crm
    init_warehouse >> poll_leads >> ingest_leads
    [ingest_crm, ingest_leads] >> export_bronze >> dbt_build >> dbt_test
    dbt_test >> quality_gate >> refresh_caches >> release_readiness >> promote_deployment
