#!/usr/bin/env python3
"""Check query-cost attribution artifacts for regression against a baseline."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from revops_funnel.artifacts import write_json_artifact
from revops_funnel.cost_observability import (
    CostRegressionThresholds,
    detect_query_cost_regressions,
)

DEFAULT_CURRENT_REPORT = os.getenv(
    "COST_ATTRIBUTION_REPORT_PATH",
    "artifacts/performance/query_cost_attribution_report.json",
)
DEFAULT_BASELINE_REPORT = os.getenv(
    "COST_BASELINE_REPORT_PATH",
    "artifacts/performance/query_cost_attribution_baseline.json",
)
DEFAULT_OUTPUT = os.getenv(
    "COST_REGRESSION_REPORT_PATH",
    "artifacts/performance/query_cost_regression_report.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--current-report",
        default=DEFAULT_CURRENT_REPORT,
        help="Current query-cost attribution report path.",
    )
    parser.add_argument(
        "--baseline-report",
        default=DEFAULT_BASELINE_REPORT,
        help="Baseline query-cost attribution report path.",
    )
    parser.add_argument(
        "--max-credits-regression-pct",
        type=float,
        default=float(os.getenv("COST_MAX_CREDITS_REGRESSION_PCT", "20")),
        help="Allowed percentage increase in credits_used before failing.",
    )
    parser.add_argument(
        "--max-elapsed-regression-pct",
        type=float,
        default=float(os.getenv("COST_MAX_ELAPSED_REGRESSION_PCT", "25")),
        help="Allowed percentage increase in elapsed_seconds before failing.",
    )
    parser.add_argument(
        "--strict-baseline",
        action="store_true",
        help="Fail when baseline report is missing or unusable.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Output path for query-cost regression report.",
    )
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object JSON payload in {path}")
    return payload


def _emit_and_exit(output: str, payload: dict[str, object], code: int) -> int:
    write_json_artifact(output, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return code


def main() -> int:
    args = parse_args()

    current_path = Path(args.current_report)
    baseline_path = Path(args.baseline_report)

    if not current_path.exists():
        return _emit_and_exit(
            args.output,
            {
                "status": "error",
                "detail": f"current report not found: {current_path}",
                "strict_baseline": bool(args.strict_baseline),
            },
            1,
        )

    current_report = _read_json(current_path)
    current_status = str(current_report.get("status", ""))
    if current_status and current_status != "ok":
        return _emit_and_exit(
            args.output,
            {
                "status": "skipped",
                "detail": f"current report status is '{current_status}'",
                "strict_baseline": bool(args.strict_baseline),
            },
            0,
        )

    if not baseline_path.exists():
        status = "error" if args.strict_baseline else "skipped"
        code = 1 if args.strict_baseline else 0
        return _emit_and_exit(
            args.output,
            {
                "status": status,
                "detail": f"baseline report not found: {baseline_path}",
                "strict_baseline": bool(args.strict_baseline),
            },
            code,
        )

    baseline_report = _read_json(baseline_path)
    baseline_status = str(baseline_report.get("status", ""))
    if baseline_status and baseline_status != "ok":
        status = "error" if args.strict_baseline else "skipped"
        code = 1 if args.strict_baseline else 0
        return _emit_and_exit(
            args.output,
            {
                "status": status,
                "detail": f"baseline report status is '{baseline_status}'",
                "strict_baseline": bool(args.strict_baseline),
            },
            code,
        )

    thresholds = CostRegressionThresholds(
        max_credits_regression_pct=max(0.0, args.max_credits_regression_pct),
        max_elapsed_regression_pct=max(0.0, args.max_elapsed_regression_pct),
    )

    comparison = detect_query_cost_regressions(current_report, baseline_report, thresholds)
    payload = {
        "status": comparison.get("status", "error"),
        "detail": comparison.get("detail", ""),
        "strict_baseline": bool(args.strict_baseline),
        "current_report": str(current_path),
        "baseline_report": str(baseline_path),
        "comparison": comparison,
    }

    status = str(payload["status"])
    code = 1 if status in {"error", "regression-detected"} else 0
    return _emit_and_exit(args.output, payload, code)


if __name__ == "__main__":
    raise SystemExit(main())
