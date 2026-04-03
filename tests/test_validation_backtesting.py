from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from revops_funnel.validation_backtesting import (
    POLICY_CONTRACT_VERSION,
    ValidationBacktestingPolicy,
    generate_validation_backtesting_report,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_generate_validation_backtesting_report_aligns_signals() -> None:
    report = generate_validation_backtesting_report(
        current_cost_report={
            "status": "ok",
            "totals": {"credits_used": 12.0, "elapsed_seconds": 100.0},
        },
        baseline_cost_report={
            "status": "ok",
            "totals": {"credits_used": 9.0, "elapsed_seconds": 80.0},
        },
        regression_report={
            "status": "regression-detected",
            "thresholds": {
                "max_credits_regression_pct": 20.0,
                "max_elapsed_regression_pct": 20.0,
                "max_new_query_tags": 0,
            },
            "summary": {"blocked": True},
            "query_tag_regressions": [
                {"query_tag": "dbt-build", "metric": "credits_used"},
            ],
            "new_query_tags": [],
        },
        forecast_report={
            "status": "ok",
            "forecasts": [
                {"query_tag": "dbt-build", "allocation_alert": "trending-over-budget"},
                {"query_tag": "dbt-test", "allocation_alert": "ok"},
            ],
        },
        cross_environment_report={"status": "ok", "forecast_impact": 4.0},
        pr_impact_report={"status": "ok", "cost_delta_monthly": 6.0},
        health_report={"overall_status": "ok"},
        dashboard_report={"operational_status": "ok"},
        runbook_report={"quality_gate_passed": True},
        incident_operations_report={
            "incident_open": False,
            "strict_blockers": [],
            "evidence_completeness_score": 1.0,
        },
        policy=ValidationBacktestingPolicy(),
    )

    payload = report.to_dict()
    assert payload["status"] == "ok"
    assert payload["validation_coverage_pct"] == 1.0
    assert payload["backtest_summary"]["regression_alignment"] is True
    assert payload["backtest_summary"]["forecast_precision_pct"] == 100.0
    assert payload["impact_summary"]["operational_readiness"]["overall_score"] >= 0.75


def test_generate_validation_backtesting_report_flags_mismatched_alignment() -> None:
    report = generate_validation_backtesting_report(
        current_cost_report={
            "status": "ok",
            "totals": {"credits_used": 15.0, "elapsed_seconds": 100.0},
        },
        baseline_cost_report={
            "status": "ok",
            "totals": {"credits_used": 10.0, "elapsed_seconds": 90.0},
        },
        regression_report={
            "status": "ok",
            "thresholds": {
                "max_credits_regression_pct": 20.0,
                "max_elapsed_regression_pct": 20.0,
                "max_new_query_tags": 0,
            },
            "summary": {"blocked": False},
            "query_tag_regressions": [],
            "new_query_tags": [],
        },
        forecast_report={"status": "ok", "forecasts": []},
        cross_environment_report=None,
        pr_impact_report=None,
        health_report={"overall_status": "degraded"},
        dashboard_report={"operational_status": "degraded"},
        runbook_report={"quality_gate_passed": False},
        incident_operations_report={
            "incident_open": True,
            "strict_blockers": ["dispatch_status=missing"],
            "evidence_completeness_score": 0.5,
        },
        policy=ValidationBacktestingPolicy(min_operational_readiness_score=0.9),
    )

    payload = report.to_dict()
    assert payload["status"] == "warning"
    assert payload["strict_blockers"]
    assert payload["backtest_summary"]["regression_alignment"] is False


def test_run_validation_backtesting_cli_strict_fails(tmp_path: Path) -> None:
    current_path = tmp_path / "current.json"
    baseline_path = tmp_path / "baseline.json"
    regression_path = tmp_path / "regression.json"
    forecast_path = tmp_path / "forecast.json"
    health_path = tmp_path / "health.json"
    dashboard_path = tmp_path / "dashboard.json"
    runbook_path = tmp_path / "runbook.json"
    incident_ops_path = tmp_path / "incident_ops.json"
    output_path = tmp_path / "validation_backtesting.json"

    _write_json(
        current_path,
        {"status": "ok", "totals": {"credits_used": 15.0, "elapsed_seconds": 100.0}},
    )
    _write_json(
        baseline_path,
        {"status": "ok", "totals": {"credits_used": 10.0, "elapsed_seconds": 90.0}},
    )
    _write_json(
        regression_path,
        {
            "status": "ok",
            "thresholds": {
                "max_credits_regression_pct": 20.0,
                "max_elapsed_regression_pct": 20.0,
                "max_new_query_tags": 0,
            },
            "summary": {"blocked": False},
            "query_tag_regressions": [],
            "new_query_tags": [],
        },
    )
    _write_json(
        forecast_path,
        {
            "status": "ok",
            "forecasts": [{"query_tag": "dbt-build", "allocation_alert": "trending-over-budget"}],
        },
    )
    _write_json(health_path, {"overall_status": "degraded"})
    _write_json(dashboard_path, {"operational_status": "degraded"})
    _write_json(runbook_path, {"quality_gate_passed": False})
    _write_json(
        incident_ops_path,
        {
            "incident_open": True,
            "strict_blockers": ["dispatch_status=missing"],
            "evidence_completeness_score": 0.5,
        },
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/ops/run_validation_backtesting.py",
            f"--current-cost-report={current_path}",
            f"--baseline-cost-report={baseline_path}",
            f"--regression-report={regression_path}",
            f"--forecast-report={forecast_path}",
            f"--health-report={health_path}",
            f"--dashboard-report={dashboard_path}",
            f"--runbook-report={runbook_path}",
            f"--incident-operations-report={incident_ops_path}",
            "--strict-validation",
            f"--output={output_path}",
        ],
        cwd="/workspaces/revops-funnel-reconciliation-engine",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["status"] == "error"
    assert payload["strict_blockers"]


def test_run_validation_backtesting_cli_safe_mode_skips_missing_inputs(tmp_path: Path) -> None:
    output_path = tmp_path / "validation_backtesting.json"
    current_path = tmp_path / "current.json"
    current_path.write_text(
        json.dumps({"status": "ok", "totals": {"credits_used": 1.0}}),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/ops/run_validation_backtesting.py",
            f"--current-cost-report={current_path}",
            f"--output={output_path}",
        ],
        cwd="/workspaces/revops-funnel-reconciliation-engine",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["status"] in {"warning", "skipped"}
    assert payload["validation_summary"]["missing_required_artifacts"]


def test_run_validation_backtesting_cli_policy_file(tmp_path: Path) -> None:
    current_path = tmp_path / "current.json"
    baseline_path = tmp_path / "baseline.json"
    regression_path = tmp_path / "regression.json"
    forecast_path = tmp_path / "forecast.json"
    health_path = tmp_path / "health.json"
    dashboard_path = tmp_path / "dashboard.json"
    runbook_path = tmp_path / "runbook.json"
    incident_ops_path = tmp_path / "incident_ops.json"
    policy_path = tmp_path / "policy.json"
    output_path = tmp_path / "validation_backtesting.json"

    _write_json(
        current_path,
        {"status": "ok", "totals": {"credits_used": 8.0, "elapsed_seconds": 50.0}},
    )
    _write_json(
        baseline_path,
        {"status": "ok", "totals": {"credits_used": 8.0, "elapsed_seconds": 50.0}},
    )
    _write_json(
        regression_path,
        {
            "status": "ok",
            "thresholds": {
                "max_credits_regression_pct": 20.0,
                "max_elapsed_regression_pct": 20.0,
                "max_new_query_tags": 0,
            },
            "summary": {"blocked": False},
            "query_tag_regressions": [],
            "new_query_tags": [],
        },
    )
    _write_json(forecast_path, {"status": "ok", "forecasts": []})
    _write_json(health_path, {"overall_status": "ok"})
    _write_json(dashboard_path, {"operational_status": "ok"})
    _write_json(runbook_path, {"quality_gate_passed": True})
    _write_json(
        incident_ops_path,
        {
            "incident_open": False,
            "strict_blockers": [],
            "evidence_completeness_score": 1.0,
            "correlation_id": "phase10-correlation",
        },
    )
    _write_json(
        policy_path,
        {
            "contract_version": POLICY_CONTRACT_VERSION,
            "min_artifact_coverage": 0.5,
            "max_credits_regression_pct": 20.0,
            "max_elapsed_regression_pct": 20.0,
            "min_operational_readiness_score": 0.6,
            "max_forecast_mismatch_pct": 30.0,
        },
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/ops/run_validation_backtesting.py",
            f"--current-cost-report={current_path}",
            f"--baseline-cost-report={baseline_path}",
            f"--regression-report={regression_path}",
            f"--forecast-report={forecast_path}",
            f"--health-report={health_path}",
            f"--dashboard-report={dashboard_path}",
            f"--runbook-report={runbook_path}",
            f"--incident-operations-report={incident_ops_path}",
            f"--policy={policy_path}",
            "--correlation-id=phase11-explicit-correlation",
            f"--output={output_path}",
        ],
        cwd="/workspaces/revops-funnel-reconciliation-engine",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["status"] == "ok"
    assert payload["policy_source"] == "file"
    assert payload["correlation_id"] == "phase11-explicit-correlation"
