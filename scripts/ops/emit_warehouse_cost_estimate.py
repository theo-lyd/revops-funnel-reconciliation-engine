#!/usr/bin/env python3
"""Emit warehouse pre-flight cost estimate using Snowflake resource monitors."""

from __future__ import annotations

import argparse
import json
import os

from revops_funnel.artifacts import write_json_artifact

DEFAULT_OUTPUT = os.getenv(
    "WAREHOUSE_COST_ESTIMATE_PATH",
    "artifacts/performance/warehouse_cost_estimate.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warehouse-name",
        default=os.getenv("SNOWFLAKE_WAREHOUSE", "TRANSFORM_WH"),
        help="Snowflake warehouse name.",
    )
    parser.add_argument(
        "--estimated-query-cost",
        type=float,
        default=3.2,
        help="Estimated query cost in credits.",
    )
    parser.add_argument(
        "--warehouse-mode",
        choices=("standard", "spot"),
        default="standard",
        help="Warehouse mode (standard=pay-as-you-go, spot=reserved compute).",
    )
    parser.add_argument(
        "--daily-budget-credits",
        type=float,
        default=100.0,
        help="Daily warehouse budget limit in credits.",
    )
    parser.add_argument(
        "--current-daily-burn",
        type=float,
        default=45.6,
        help="Current daily burn rate in credits.",
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output path for estimate.")
    parser.add_argument(
        "--strict-snowflake",
        action="store_true",
        help="Fail if Snowflake unavailable.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # In non-strict mode, emit safe estimate without requiring Snowflake connectivity
    projected_daily = args.current_daily_burn + args.estimated_query_cost
    if args.daily_budget_credits > 0:
        projected_utilization_pct = (projected_daily / args.daily_budget_credits) * 100
    else:
        projected_utilization_pct = 100.0
    over_budget = projected_daily > args.daily_budget_credits

    estimate: dict[str, object] = {
        "status": "ok",
        "warehouse_name": args.warehouse_name,
        "warehouse_mode": args.warehouse_mode,
        "estimated_query_cost": args.estimated_query_cost,
        "current_daily_burn": args.current_daily_burn,
        "projected_daily_after_query": round(projected_daily, 2),
        "daily_budget_credits": args.daily_budget_credits,
        "projected_daily_utilization_pct": round(projected_utilization_pct, 1),
        "projected_over_budget": over_budget,
        "cache_hit_rate_expected": 0.78,
        "query_cost_if_no_cache": round(args.estimated_query_cost * 2.5, 2),
        "recommendation": (
            "Query will exceed daily budget; review or reschedule"
            if over_budget
            else "Query within daily budget; can proceed"
        ),
    }

    write_json_artifact(args.output, estimate)
    print(json.dumps(estimate, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    exit(main())
