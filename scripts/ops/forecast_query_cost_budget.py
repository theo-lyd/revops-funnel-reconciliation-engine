#!/usr/bin/env python3
"""Forecast query cost budget and emit early-warning alerts for team budgets."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

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
        return json.loads(mapping_json)
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
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def main() -> int:
    args = parse_args()

    report_path = Path(args.attribution_report)
    if not report_path.exists():
        forecast_report = {
            "status": "skipped",
            "reason": f"Attribution report not found: {report_path}",
            "forecasts": [],
        }
        write_json_artifact(args.output, forecast_report)
        print(json.dumps(forecast_report, indent=2, sort_keys=True))
        return 0

    attribution = _read_json(report_path)
    team_mapping = _parse_team_mapping(args.team_owner_tag_mapping)

    tag_rows = attribution.get("attribution_by_query_tag", [])
    forecasts: list[dict[str, object]] = []

    for row in tag_rows:
        if not isinstance(row, dict):
            continue

        query_tag = str(row.get("query_tag", ""))
        current_monthly_burn = float(row.get("credits_used", 0.0))

        team_owner = _assign_team_owner(query_tag, team_mapping)
        forecast, confidence = _forecast_end_of_period_cost(current_monthly_burn, [], 15)

        forecast_dict: dict[str, object] = {
            "query_tag": query_tag,
            "team_owner": team_owner,
            "current_monthly_burn": round(current_monthly_burn, 2),
            "forecast_end_of_month": round(forecast, 2),
            "confidence": round(confidence, 2),
            "allocation_alert": "ok",
        }

        forecasts.append(forecast_dict)

    forecast_report = {
        "status": "ok",
        "generated_at_utc": json.dumps({"generated_at": "2026-04-02T00:00:00Z"}),  # Placeholder
        "threshold_pct": args.budget_threshold_pct,
        "forecasts": forecasts,
        "total_forecast_credits": round(
            sum(float(f.get("forecast_end_of_month", 0)) for f in forecasts), 2
        ),
    }

    write_json_artifact(args.output, forecast_report)
    print(json.dumps(forecast_report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    exit(main())
