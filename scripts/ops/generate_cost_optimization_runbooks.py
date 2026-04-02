#!/usr/bin/env python3
"""Generate executable cost optimization runbooks from pattern analysis."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from revops_funnel.artifacts import write_json_artifact

DEFAULT_PATTERN_ANALYSIS = os.getenv(
    "COST_PATTERN_ANALYSIS_PATH",
    "artifacts/performance/query_pattern_analysis.json",
)
DEFAULT_OUTPUT = os.getenv(
    "COST_OPTIMIZATION_RUNBOOKS_PATH",
    "artifacts/performance/optimization_runbooks.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pattern-analysis",
        default=DEFAULT_PATTERN_ANALYSIS,
        help="Query pattern analysis report.",
    )
    parser.add_argument(
        "--runbook-approval-required",
        action="store_true",
        help="Mark runbooks as requiring manual approval before execution.",
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output path for runbooks.")
    return parser.parse_args()


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

    analysis_path = Path(args.pattern_analysis)
    if not analysis_path.exists():
        runbooks = {
            "status": "skipped",
            "reason": f"Pattern analysis not found: {analysis_path}",
            "runbooks": [],
        }
        write_json_artifact(args.output, runbooks)
        print(json.dumps(runbooks, indent=2, sort_keys=True))
        return 0

    analysis = _read_json(analysis_path)
    raw_patterns = analysis.get("query_patterns", [])
    patterns = raw_patterns if isinstance(raw_patterns, list) else []

    runbooks_list: list[dict[str, object]] = []

    for pattern in patterns:
        if not isinstance(pattern, dict):
            continue

        query_id = str(pattern.get("query_id", ""))
        query_tag = str(pattern.get("query_tag", ""))
        raw_hints = pattern.get("optimization_hints", [])
        hints = raw_hints if isinstance(raw_hints, list) else []

        for hint in hints:
            if not isinstance(hint, dict):
                continue

            hint_text = str(hint.get("hint", ""))
            estimated_savings = _coerce_float(hint.get("estimated_credits_saved_monthly", 0.0), 0.0)
            effort_hours = _coerce_float(hint.get("effort_hours", 1.0), 1.0)

            runbook: dict[str, object] = {
                "query_id": query_id,
                "query_tag": query_tag,
                "problem": hint_text,
                "proposed_fix": f"-- Add filter to {query_tag}",
                "expected_savings_monthly": round(estimated_savings, 2),
                "effort_hours": effort_hours,
                "roi": round(estimated_savings / max(effort_hours, 1.0), 2),
                "status": "ready-for-review" if args.runbook_approval_required else "draft",
                "testing_checklist": [
                    "Row count matches baseline",
                    "Regression tests pass",
                    "Query plan shows improvement",
                ],
            }

            runbooks_list.append(runbook)

    sorted_runbooks: list[dict[str, object]] = sorted(
        runbooks_list,
        key=lambda x: _coerce_float(x.get("roi", 0.0), 0.0),
        reverse=True,
    )

    total_savings = sum(
        _coerce_float(item.get("expected_savings_monthly", 0.0), 0.0) for item in sorted_runbooks
    )

    runbooks_output: dict[str, Any] = {
        "status": "ok",
        "generated_count": len(sorted_runbooks),
        "total_potential_savings_monthly": round(total_savings, 2),
        "runbooks": sorted_runbooks,
    }

    write_json_artifact(args.output, runbooks_output)
    print(json.dumps(runbooks_output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    exit(main())
