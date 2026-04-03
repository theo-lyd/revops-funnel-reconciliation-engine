#!/usr/bin/env python3
"""Run Phase 11 validation, backtesting, and impact measurement."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from revops_funnel.artifacts import write_json_artifact
from revops_funnel.validation_backtesting import (
    POLICY_CONTRACT_VERSION,
    ValidationBacktestingPolicy,
    generate_validation_backtesting_report,
)

DEFAULT_VALIDATION_REPORT = os.getenv(
    "PHASE11_VALIDATION_REPORT_PATH",
    "artifacts/validation/validation_backtesting_report.json",
)
DEFAULT_CURRENT_COST_REPORT = os.getenv(
    "PHASE11_CURRENT_COST_REPORT_PATH",
    "artifacts/performance/query_cost_attribution_report.json",
)
DEFAULT_BASELINE_COST_REPORT = os.getenv(
    "PHASE11_BASELINE_COST_REPORT_PATH",
    "artifacts/performance/query_cost_attribution_baseline.json",
)
DEFAULT_REGRESSION_REPORT = os.getenv(
    "PHASE11_REGRESSION_REPORT_PATH",
    "artifacts/performance/query_cost_regression_report.json",
)
DEFAULT_FORECAST_REPORT = os.getenv(
    "PHASE11_FORECAST_REPORT_PATH",
    "artifacts/performance/query_cost_forecast_report.json",
)
DEFAULT_CROSS_ENVIRONMENT_REPORT = os.getenv(
    "PHASE11_CROSS_ENVIRONMENT_REPORT_PATH",
    "artifacts/performance/cross_environment_forecast.json",
)
DEFAULT_PR_IMPACT_REPORT = os.getenv(
    "PHASE11_PR_IMPACT_REPORT_PATH",
    "artifacts/performance/pr_cost_impact_score.json",
)
DEFAULT_HEALTH_REPORT = os.getenv(
    "PHASE11_HEALTH_REPORT_PATH",
    "artifacts/monitoring/health_report.json",
)
DEFAULT_DASHBOARD_REPORT = os.getenv(
    "PHASE11_DASHBOARD_REPORT_PATH",
    "artifacts/monitoring/operational_dashboard.json",
)
DEFAULT_RUNBOOK_REPORT = os.getenv(
    "PHASE11_RUNBOOK_REPORT_PATH",
    "artifacts/runbooks/oncall_runbook_report.json",
)
DEFAULT_INCIDENT_OPERATIONS_REPORT = os.getenv(
    "PHASE11_INCIDENT_OPERATIONS_REPORT_PATH",
    "artifacts/runbooks/incident_operations_report.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current-cost-report", default=DEFAULT_CURRENT_COST_REPORT)
    parser.add_argument("--baseline-cost-report", default=DEFAULT_BASELINE_COST_REPORT)
    parser.add_argument("--regression-report", default=DEFAULT_REGRESSION_REPORT)
    parser.add_argument("--forecast-report", default=DEFAULT_FORECAST_REPORT)
    parser.add_argument("--cross-environment-report", default=DEFAULT_CROSS_ENVIRONMENT_REPORT)
    parser.add_argument("--pr-impact-report", default=DEFAULT_PR_IMPACT_REPORT)
    parser.add_argument("--health-report", default=DEFAULT_HEALTH_REPORT)
    parser.add_argument("--dashboard-report", default=DEFAULT_DASHBOARD_REPORT)
    parser.add_argument("--runbook-report", default=DEFAULT_RUNBOOK_REPORT)
    parser.add_argument("--incident-operations-report", default=DEFAULT_INCIDENT_OPERATIONS_REPORT)
    parser.add_argument(
        "--min-artifact-coverage",
        type=float,
        default=float(os.getenv("PHASE11_MIN_ARTIFACT_COVERAGE", "0.8")),
    )
    parser.add_argument(
        "--max-credits-regression-pct",
        type=float,
        default=float(os.getenv("PHASE11_MAX_CREDITS_REGRESSION_PCT", "20")),
    )
    parser.add_argument(
        "--max-elapsed-regression-pct",
        type=float,
        default=float(os.getenv("PHASE11_MAX_ELAPSED_REGRESSION_PCT", "25")),
    )
    parser.add_argument(
        "--min-operational-readiness-score",
        type=float,
        default=float(os.getenv("PHASE11_MIN_OPERATIONAL_READINESS_SCORE", "0.7")),
    )
    parser.add_argument(
        "--max-forecast-mismatch-pct",
        type=float,
        default=float(os.getenv("PHASE11_MAX_FORECAST_MISMATCH_PCT", "25")),
    )
    parser.add_argument(
        "--policy",
        default=os.getenv("PHASE11_POLICY_PATH", ""),
        help="Optional JSON policy artifact path.",
    )
    parser.add_argument(
        "--correlation-id",
        default=os.getenv("PHASE11_CORRELATION_ID", "").strip(),
        help="Optional explicit correlation id for joining cross-phase artifacts.",
    )
    parser.add_argument(
        "--strict-validation",
        action="store_true",
        default=os.getenv("PHASE11_STRICT_VALIDATION", "false").lower() == "true",
        help="Fail when validation or backtest blockers are detected.",
    )
    parser.add_argument("--output", default=DEFAULT_VALIDATION_REPORT)
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _emit_and_exit(output: str, payload: dict[str, object], code: int) -> int:
    write_json_artifact(output, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return code


def _load_policy(path: str) -> tuple[dict[str, object] | None, str]:
    policy_path = path.strip()
    if not policy_path:
        return None, "default"

    payload = _read_json(Path(policy_path))
    if payload is None:
        raise SystemExit(f"Phase 11 policy path unreadable: {policy_path}")

    version = str(payload.get("contract_version", ""))
    if version != POLICY_CONTRACT_VERSION:
        raise SystemExit(
            "Phase 11 policy contract mismatch: "
            f"expected {POLICY_CONTRACT_VERSION}, got '{version}'"
        )
    return payload, "file"


def main() -> int:
    args = parse_args()

    current_cost_report = _read_json(Path(args.current_cost_report))
    baseline_cost_report = _read_json(Path(args.baseline_cost_report))
    regression_report = _read_json(Path(args.regression_report))
    forecast_report = _read_json(Path(args.forecast_report))
    cross_environment_report = _read_json(Path(args.cross_environment_report))
    pr_impact_report = _read_json(Path(args.pr_impact_report))
    health_report = _read_json(Path(args.health_report))
    dashboard_report = _read_json(Path(args.dashboard_report))
    runbook_report = _read_json(Path(args.runbook_report))
    incident_operations_report = _read_json(Path(args.incident_operations_report))

    loaded_policy, policy_source = _load_policy(args.policy)
    min_artifact_coverage = args.min_artifact_coverage
    max_credits_regression_pct = args.max_credits_regression_pct
    max_elapsed_regression_pct = args.max_elapsed_regression_pct
    min_operational_readiness_score = args.min_operational_readiness_score
    max_forecast_mismatch_pct = args.max_forecast_mismatch_pct
    if loaded_policy is not None:
        min_artifact_coverage = float(
            loaded_policy.get("min_artifact_coverage", min_artifact_coverage)
        )
        max_credits_regression_pct = float(
            loaded_policy.get("max_credits_regression_pct", max_credits_regression_pct)
        )
        max_elapsed_regression_pct = float(
            loaded_policy.get("max_elapsed_regression_pct", max_elapsed_regression_pct)
        )
        min_operational_readiness_score = float(
            loaded_policy.get(
                "min_operational_readiness_score",
                min_operational_readiness_score,
            )
        )
        max_forecast_mismatch_pct = float(
            loaded_policy.get("max_forecast_mismatch_pct", max_forecast_mismatch_pct)
        )

    policy = ValidationBacktestingPolicy(
        min_artifact_coverage=max(0.0, min(1.0, min_artifact_coverage)),
        max_credits_regression_pct=max(0.0, max_credits_regression_pct),
        max_elapsed_regression_pct=max(0.0, max_elapsed_regression_pct),
        min_operational_readiness_score=max(0.0, min(1.0, min_operational_readiness_score)),
        max_forecast_mismatch_pct=max(0.0, max_forecast_mismatch_pct),
    )

    report = generate_validation_backtesting_report(
        current_cost_report=current_cost_report,
        baseline_cost_report=baseline_cost_report,
        regression_report=regression_report,
        forecast_report=forecast_report,
        cross_environment_report=cross_environment_report,
        pr_impact_report=pr_impact_report,
        health_report=health_report,
        dashboard_report=dashboard_report,
        runbook_report=runbook_report,
        incident_operations_report=incident_operations_report,
        policy=policy,
        explicit_correlation_id=(args.correlation_id or None),
        strict_validation=bool(args.strict_validation),
    )

    payload = report.to_dict()
    payload["strict_validation"] = bool(args.strict_validation)
    payload["policy_source"] = policy_source
    payload["policy"] = asdict(policy)

    status = str(payload["status"])
    code = 1 if status == "error" else 0
    return _emit_and_exit(args.output, payload, code)


if __name__ == "__main__":
    raise SystemExit(main())
