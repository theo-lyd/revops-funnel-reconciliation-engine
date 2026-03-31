"""Freshness SLA checks for Bronze source arrivals."""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-delay-hours",
        type=float,
        default=2.0,
        help="Maximum allowed delay in hours before alerting.",
    )
    return parser.parse_args()


def age_hours(path: Path) -> float:
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return (datetime.now(timezone.utc) - mtime) / timedelta(hours=1)


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
        "CRM pipeline file": Path("data/raw/crm/sales_pipeline.csv"),
        "Marketing leads landing file": Path("data/raw/marketing/leads_raw.jsonl"),
    }

    breaches: list[str] = []
    for label, file_path in checks.items():
        if not file_path.exists():
            breaches.append(f"{label} missing: {file_path}")
            continue

        delay = age_hours(file_path)
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
