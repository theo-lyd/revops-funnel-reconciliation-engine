#!/usr/bin/env python3
"""Analyze PR/commit cost impact and score complexity delta."""

from __future__ import annotations

import argparse
import json
import os

from revops_funnel.artifacts import write_json_artifact

DEFAULT_OUTPUT = os.getenv("PR_COST_IMPACT_PATH", "artifacts/performance/pr_cost_impact_score.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--added-models",
        type=int,
        default=0,
        help="Number of new models added in commit.",
    )
    parser.add_argument(
        "--removed-models",
        type=int,
        default=0,
        help="Number of models removed/deprecated.",
    )
    parser.add_argument(
        "--added-joins",
        type=int,
        default=0,
        help="Number of new joins added.",
    )
    parser.add_argument(
        "--modified-predicates",
        type=int,
        default=0,
        help="Number of predicates modified (filter changes).",
    )
    parser.add_argument(
        "--baseline-monthly-cost",
        type=float,
        default=float(os.getenv("BASELINE_MONTHLY_COST", "500")),
        help="Current baseline monthly cost.",
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output path for impact score.")
    return parser.parse_args()


def _compute_cost_impact_score(
    added_models: int,
    removed_models: int,
    added_joins: int,
    modified_predicates: int,
    baseline_cost: float,
) -> tuple[float, str]:
    """Compute cost impact score (1–10) and confidence level."""
    score = 0.0

    # New models add complexity (assume 50-100 credits each)
    score += added_models * 75 * 12  # monthly impact

    # Removed models reduce cost
    score -= removed_models * 75 * 12

    # New joins can 2-3x cost (assume 30 credits per join)
    score += added_joins * 30 * 12

    # Predicate changes can reduce by up to 70%
    score -= modified_predicates * baseline_cost * 0.1

    # Score on 1-10 scale
    impact_pct = (abs(score) / baseline_cost) * 100

    if impact_pct > 50:
        confidence = "high"
    elif impact_pct > 10:
        confidence = "medium"
    else:
        confidence = "low"

    return (round(score, 2), confidence)


def main() -> int:
    args = parse_args()

    cost_delta, confidence = _compute_cost_impact_score(
        args.added_models,
        args.removed_models,
        args.added_joins,
        args.modified_predicates,
        args.baseline_monthly_cost,
    )

    if args.baseline_monthly_cost > 0:
        impact_pct = cost_delta / args.baseline_monthly_cost * 100
    else:
        impact_pct = 0.0

    impact_report = {
        "status": "ok",
        "cost_delta_monthly": cost_delta,
        "cost_delta_pct": round(impact_pct, 1),
        "confidence": confidence,
        "model_changes": {
            "added": args.added_models,
            "removed": args.removed_models,
        },
        "query_complexity_changes": {
            "added_joins": args.added_joins,
            "modified_predicates": args.modified_predicates,
        },
        "recommendations": [],
    }

    if cost_delta > 0 and args.baseline_monthly_cost > 0 and impact_pct > 10:
        msg = (
            f"Cost increase of ~${abs(cost_delta):.0f}/month detected; "
            "recommend cost review before merge"
        )
        impact_report["recommendations"].append(
            {
                "type": "cost-review",
                "message": msg,
            }
        )

    write_json_artifact(args.output, impact_report)
    print(json.dumps(impact_report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    exit(main())
