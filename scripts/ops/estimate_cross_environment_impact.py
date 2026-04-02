#!/usr/bin/env python3
"""Estimate production cost from staging data with cross-environment normalization."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from revops_funnel.artifacts import write_json_artifact
from revops_funnel.cost_observability import _estimate_prod_cost_from_staging

DEFAULT_STAGING_REPORT = os.getenv(
    "STAGING_COST_ATTRIBUTION_PATH",
    "artifacts/performance/query_cost_attribution_staging.json",
)
DEFAULT_OUTPUT = os.getenv(
    "CROSS_ENVIRONMENT_FORECAST_PATH",
    "artifacts/performance/cross_environment_forecast.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--staging-report",
        default=DEFAULT_STAGING_REPORT,
        help="Staging environment cost attribution report.",
    )
    parser.add_argument(
        "--prod-current",
        type=float,
        default=float(os.getenv("PROD_CURRENT_MONTHLY_COST", "0")),
        help="Current production monthly cost (for comparison).",
    )
    parser.add_argument(
        "--staging-to-prod-multiplier",
        type=float,
        default=float(os.getenv("STAGING_TO_PROD_COST_MULTIPLIER", "5.0")),
        help="Multiplier to extrapolate staging→prod.",
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output path for forecast.")
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
        return {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def main() -> int:
    args = parse_args()

    report_path = Path(args.staging_report)
    if not report_path.exists():
        skipped_forecast: dict[str, Any] = {
            "status": "skipped",
            "reason": f"Staging report not found: {report_path}",
        }
        write_json_artifact(args.output, skipped_forecast)
        print(json.dumps(skipped_forecast, indent=2, sort_keys=True))
        return 0

    staging_report = _read_json(report_path)
    totals_obj = staging_report.get("totals", {})
    totals = totals_obj if isinstance(totals_obj, dict) else {}

    staging_monthly = float(totals.get("credits_used", 0.0))
    staging_trend = 0.5  # Placeholder: would compute from historical

    prod_estimate_today, prod_estimate_steady, confidence = _estimate_prod_cost_from_staging(
        staging_monthly,
        staging_trend,
        args.staging_to_prod_multiplier,
    )

    forecast_delta = prod_estimate_today - args.prod_current if args.prod_current > 0 else 0.0
    if args.prod_current > 0:
        forecast_delta_pct = forecast_delta / args.prod_current * 100
    else:
        forecast_delta_pct = 0.0

    forecast_payload: dict[str, Any] = {
        "status": "ok",
        "staging_current_monthly": round(staging_monthly, 2),
        "staging_to_prod_multiplier": args.staging_to_prod_multiplier,
        "estimated_prod_if_deployed_today": round(prod_estimate_today, 2),
        "estimated_prod_at_steady_state": round(prod_estimate_steady, 2),
        "actual_prod_current": round(args.prod_current, 2),
        "forecast_impact": round(forecast_delta, 2),
        "forecast_impact_pct": round(forecast_delta_pct, 1),
        "confidence": round(confidence, 2),
    }

    write_json_artifact(args.output, forecast_payload)
    print(json.dumps(forecast_payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    exit(main())
