#!/usr/bin/env python3
"""Forecast query cost budget and emit early-warning alerts for team budgets."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from revops_funnel.artifacts import write_json_artifact
from revops_funnel.cost_observability import _forecast_end_of_period_cost

DEFAULT_ATTRIBUTION = os.getenv(
    "COST_ATTRIBUTION_REPORT_PATH",
    "artifacts/performance/query_cost_attribution_report.json",
)
DEFAULT_OUTPUT = os.getenv(
    "COST_FORECAST_REPORT_PATH",
    "artifacts/performance/query_cost_forecast_report.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--attribution-report",
        default=DEFAULT_ATTRIBUTION,
        help="Current query-cost attribution report path.",
    )
    parser.add_argument(
        "--team-owner-tag-mapping",
        type=str,
        default=os.getenv("COST_TEAM_TAG_MAPPING", ""),
        help='JSON mapping of tag prefixes to team owners (e.g. \'{"crm_": "revenue-ops"}\')',
    )
    parser.add_argument(
        "--budget-threshold-pct",
        type=float,
        default=float(os.getenv("COST_BUDGET_THRESHOLD_PCT", "80")),
        help="Alert when trending toward N% of allocated budget.",
    )
    parser.add_argument(
        "--staging-to-prod-multiplier",
        type=float,
        default=float(os.getenv("STAGING_TO_PROD_COST_MULTIPLIER", "5.0")),
        help="Multiplier to extrapolate staging costs to production.",
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output path for forecast report.")
    return parser.parse_args()


def _parse_team_mapping(mapping_json: str) -> dict[str, str]:
    """Parse team owner tag mapping from JSON string."""
    if not mapping_json.strip():
        return {}
    try:
        raw_mapping = json.loads(mapping_json)
        if not isinstance(raw_mapping, dict):
            return {}
        return {str(k): str(v) for k, v in raw_mapping.items()}
    except json.JSONDecodeError:
        return {}


def _assign_team_owner(query_tag: str, team_mapping: dict[str, str]) -> str | None:
    """Assign team owner based on query tag prefix."""
    tag_lower = query_tag.lower()
    for prefix, team in team_mapping.items():
        if tag_lower.startswith(prefix.lower()):
            return team
    return None


def _read_json(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
        return {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _coerce_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def main() -> int:
    args = parse_args()

    report_path = Path(args.attribution_report)
    if not report_path.exists():
        skipped_report: dict[str, Any] = {
            "status": "skipped",
            "reason": f"Attribution report not found: {report_path}",
            "forecasts": [],
        }
        write_json_artifact(args.output, skipped_report)
        print(json.dumps(skipped_report, indent=2, sort_keys=True))
        return 0

    attribution = _read_json(report_path)
    team_mapping = _parse_team_mapping(args.team_owner_tag_mapping)

    raw_tag_rows = attribution.get("attribution_by_query_tag", [])
    tag_rows = raw_tag_rows if isinstance(raw_tag_rows, list) else []
    forecasts: list[dict[str, object]] = []

    for row in tag_rows:
        if not isinstance(row, dict):
            continue

        query_tag = str(row.get("query_tag", ""))
        current_monthly_burn = _coerce_float(row.get("credits_used", 0.0), 0.0)

        team_owner = _assign_team_owner(query_tag, team_mapping)
        forecast, confidence = _forecast_end_of_period_cost(current_monthly_burn, [], 15)

        if current_monthly_burn > 0:
            utilization_pct = forecast / current_monthly_burn * 100
        else:
            utilization_pct = 0.0
        alert = "trending-over-budget" if utilization_pct > args.budget_threshold_pct else "ok"

        forecast_dict: dict[str, object] = {
            "query_tag": query_tag,
            "team_owner": team_owner,
            "current_monthly_burn": round(current_monthly_burn, 2),
            "forecast_end_of_month": round(forecast, 2),
            "confidence": round(confidence, 2),
            "allocation_alert": alert,
        }

        forecasts.append(forecast_dict)

    total_forecast_credits = sum(
        _coerce_float(item.get("forecast_end_of_month", 0.0), 0.0) for item in forecasts
    )

    report_payload: dict[str, Any] = {
        "status": "ok",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "threshold_pct": args.budget_threshold_pct,
        "forecasts": forecasts,
        "total_forecast_credits": round(total_forecast_credits, 2),
    }

    write_json_artifact(args.output, report_payload)
    print(json.dumps(report_payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    exit(main())
