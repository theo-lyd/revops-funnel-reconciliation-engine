"""Airflow DAG orchestrating Bronze ingestion and SLA monitoring."""

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
    dag_id="revops_bronze_ingestion",
    description="Ingest CRM and synthetic leads into Bronze layer with freshness checks",
    default_args=DEFAULT_ARGS,
    schedule="0 * * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["revops", "bronze", "ingestion"],
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

    freshness_check = BashOperator(
        task_id="freshness_check",
        bash_command=f"cd {PROJECT_ROOT} && make check-freshness",
    )

    init_warehouse >> ingest_crm
    init_warehouse >> poll_leads >> ingest_leads
    [ingest_crm, ingest_leads] >> export_bronze >> freshness_check
