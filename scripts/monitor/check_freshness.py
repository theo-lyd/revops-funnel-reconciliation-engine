"""Freshness SLA checks for Bronze source arrivals."""

from __future__ import annotations

import argparse
import importlib
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from revops_funnel.config import get_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-delay-hours",
        type=float,
        default=2.0,
        help="Maximum allowed delay in hours before alerting.",
    )
    return parser.parse_args()


def age_hours(loaded_at: datetime) -> float:
    return (datetime.now(timezone.utc) - loaded_at) / timedelta(hours=1)


def latest_success_timestamp(source_name: str) -> datetime | None:
    settings = get_settings()
    duckdb = importlib.import_module("duckdb")
    conn = duckdb.connect(settings.duckdb_path, read_only=True)
    try:
        row = conn.execute(
            """
            SELECT max(loaded_at)
            FROM observability.ingestion_audit
            WHERE source_name = ?
              AND status = 'success'
            """,
            [source_name],
        ).fetchone()
    except Exception:
        conn.close()
        return None
    conn.close()
    if not row or row[0] is None:
        return None
    value: Any = row[0]
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    return None


def post_slack(message: str) -> None:
    webhook = os.getenv("SLACK_WEBHOOK_URL", "")
    if not webhook:
        print("SLACK_WEBHOOK_URL not set; skipping Slack alert")
        return

    response = requests.post(webhook, json={"text": message}, timeout=10)
    response.raise_for_status()


def main() -> None:
    args = parse_args()
    max_delay = args.max_delay_hours

    checks = {
        "CRM pipeline ingestion": "crm_sales_pipeline",
        "Marketing leads ingestion": "marketing_leads",
    }

    breaches: list[str] = []
    for label, source_name in checks.items():
        latest_loaded_at = latest_success_timestamp(source_name)
        if latest_loaded_at is None:
            breaches.append(f"{label} missing successful audit event for source={source_name}")
            continue

        delay = age_hours(latest_loaded_at)
        print(f"{label}: {delay:.2f}h old")
        if delay > max_delay:
            breaches.append(f"{label} is stale ({delay:.2f}h > {max_delay:.2f}h)")

    if breaches:
        message = "Freshness SLA breach:\n" + "\n".join(f"- {item}" for item in breaches)
        print(message)
        post_slack(message)
        raise SystemExit(1)

    print("Freshness SLA checks passed.")


if __name__ == "__main__":
    main()
