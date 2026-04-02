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
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
}

TASK_TIMEOUT = timedelta(minutes=45)

with DAG(
    dag_id="revops_end_to_end_pipeline",
    description="Run deterministic end-to-end RevOps pipeline with reliability hardening",
    default_args=DEFAULT_ARGS,
    schedule="0 6 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=4),
    tags=["revops", "pipeline", "ci-cd", "operations"],
) as dag:
    preflight = BashOperator(
        task_id="preflight",
        bash_command=f"cd {PROJECT_ROOT} && make preflight",
        execution_timeout=TASK_TIMEOUT,
    )

    init_warehouse = BashOperator(
        task_id="init_warehouse",
        bash_command=f"cd {PROJECT_ROOT} && make init-warehouse",
        execution_timeout=TASK_TIMEOUT,
    )

    ingest_crm = BashOperator(
        task_id="ingest_crm",
        bash_command=f"cd {PROJECT_ROOT} && make ingest-crm",
        execution_timeout=TASK_TIMEOUT,
    )

    ingest_leads = BashOperator(
        task_id="ingest_leads",
        bash_command=f"cd {PROJECT_ROOT} && make ingest-leads",
        execution_timeout=TASK_TIMEOUT,
    )

    export_bronze = BashOperator(
        task_id="export_bronze",
        bash_command=f"cd {PROJECT_ROOT} && make export-bronze",
        execution_timeout=TASK_TIMEOUT,
    )

    check_freshness = BashOperator(
        task_id="check_freshness",
        bash_command=f"cd {PROJECT_ROOT} && make check-freshness",
        execution_timeout=TASK_TIMEOUT,
    )

    dbt_build_full = BashOperator(
        task_id="dbt_build_full",
        bash_command=f"cd {PROJECT_ROOT} && make dbt-build",
        execution_timeout=TASK_TIMEOUT,
    )

    dbt_test_full = BashOperator(
        task_id="dbt_test_full",
        bash_command=f"cd {PROJECT_ROOT} && make dbt-test",
        execution_timeout=TASK_TIMEOUT,
    )

    post_transform_checks = BashOperator(
        task_id="post_transform_checks",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            "make query-pack-validate && make quality-checks && make ge-validate"
        ),
        execution_timeout=TASK_TIMEOUT,
    )

    parity_report = BashOperator(
        task_id="parity_report",
        bash_command=f"cd {PROJECT_ROOT} && make metric-parity-check-report",
        execution_timeout=TASK_TIMEOUT,
    )

    refresh_caches = BashOperator(
        task_id="refresh_caches",
        bash_command=f"cd {PROJECT_ROOT} && make refresh-caches",
        execution_timeout=TASK_TIMEOUT,
    )

    release_readiness = BashOperator(
        task_id="release_readiness",
        bash_command=f"cd {PROJECT_ROOT} && make release-readiness-gate",
        execution_timeout=TASK_TIMEOUT,
    )

    promote_deployment = BashOperator(
        task_id="promote_deployment",
        bash_command=f"cd {PROJECT_ROOT} && make promote-deployment",
        execution_timeout=TASK_TIMEOUT,
    )

    preflight >> init_warehouse
    init_warehouse >> [ingest_crm, ingest_leads]
    [ingest_crm, ingest_leads] >> export_bronze >> check_freshness
    check_freshness >> dbt_build_full >> dbt_test_full >> post_transform_checks
    post_transform_checks >> parity_report >> refresh_caches >> release_readiness
    release_readiness >> promote_deployment
