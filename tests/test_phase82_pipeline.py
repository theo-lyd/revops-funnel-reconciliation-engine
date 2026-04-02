from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_module(relative_path: str, module_name: str):
    module_path = Path(relative_path)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise AssertionError(f"Unable to load module: {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_module(module, argv: list[str]) -> int:
    old_argv = sys.argv[:]
    sys.argv = argv
    try:
        return module.main()
    finally:
        sys.argv = old_argv


def test_phase82_artifact_pipeline_end_to_end(tmp_path: Path) -> None:
    attribution_path = tmp_path / "query_cost_attribution.json"
    forecast_path = tmp_path / "forecast.json"
    pattern_path = tmp_path / "pattern.json"
    runbooks_path = tmp_path / "runbooks.json"
    cross_env_path = tmp_path / "cross_env.json"
    pr_impact_path = tmp_path / "pr_impact.json"

    attribution_payload = {
        "status": "ok",
        "totals": {
            "query_count": 12,
            "elapsed_seconds": 420.0,
            "bytes_scanned": 900000,
            "credits_used": 42.0,
        },
        "attribution_by_query_tag": [
            {
                "query_tag": "crm_int_lead_matches",
                "query_count": 4,
                "elapsed_seconds": 120.0,
                "bytes_scanned": 200000,
                "credits_used": 18.0,
            },
            {
                "query_tag": "crm_stg_accounts",
                "query_count": 8,
                "elapsed_seconds": 300.0,
                "bytes_scanned": 700000,
                "credits_used": 24.0,
            },
        ],
        "attribution_by_warehouse": [],
        "attribution_by_transformation_layer": [],
        "top_expensive_queries": [
            {
                "query_id": "q1",
                "query_tag": "crm_int_lead_matches",
                "warehouse_name": "TRANSFORM_WH",
                "user_name": "svc",
                "elapsed_seconds": 120.0,
                "bytes_scanned": 200000,
                "credits_used": 18.0,
                "started_at_utc": "2026-04-02T00:00:00+00:00",
            }
        ],
    }
    attribution_path.write_text(json.dumps(attribution_payload), encoding="utf-8")

    forecast_module = _load_module(
        "scripts/ops/forecast_query_cost_budget.py", "forecast_query_cost_budget"
    )
    assert (
        _run_module(
            forecast_module,
            [
                "forecast_query_cost_budget.py",
                "--attribution-report",
                str(attribution_path),
                "--team-owner-tag-mapping",
                json.dumps({"crm_": "revenue-ops"}),
                "--budget-threshold-pct",
                "75",
                "--output",
                str(forecast_path),
            ],
        )
        == 0
    )
    forecast_payload = json.loads(forecast_path.read_text(encoding="utf-8"))
    assert forecast_payload["status"] == "ok"
    assert forecast_payload["forecasts"]
    assert forecast_payload["forecasts"][0]["team_owner"] == "revenue-ops"
    assert forecast_payload["forecasts"][0]["allocation_alert"] in {"ok", "trending-over-budget"}

    patterns_module = _load_module(
        "scripts/ops/analyze_query_patterns.py", "analyze_query_patterns"
    )
    assert (
        _run_module(
            patterns_module,
            [
                "analyze_query_patterns.py",
                "--attribution-report",
                str(attribution_path),
                "--output",
                str(pattern_path),
            ],
        )
        == 0
    )
    pattern_payload = json.loads(pattern_path.read_text(encoding="utf-8"))
    assert pattern_payload["status"] == "ok"
    assert pattern_payload["query_patterns"]
    assert pattern_payload["optimization_opportunities_by_roi"]

    runbooks_module = _load_module(
        "scripts/ops/generate_cost_optimization_runbooks.py", "generate_cost_optimization_runbooks"
    )
    assert (
        _run_module(
            runbooks_module,
            [
                "generate_cost_optimization_runbooks.py",
                "--pattern-analysis",
                str(pattern_path),
                "--runbook-approval-required",
                "--output",
                str(runbooks_path),
            ],
        )
        == 0
    )
    runbooks_payload = json.loads(runbooks_path.read_text(encoding="utf-8"))
    assert runbooks_payload["status"] == "ok"
    assert runbooks_payload["generated_count"] >= 1
    assert runbooks_payload["runbooks"][0]["status"] == "ready-for-review"

    cross_env_module = _load_module(
        "scripts/ops/estimate_cross_environment_impact.py", "estimate_cross_environment_impact"
    )
    assert (
        _run_module(
            cross_env_module,
            [
                "estimate_cross_environment_impact.py",
                "--staging-report",
                str(attribution_path),
                "--prod-current",
                "35",
                "--output",
                str(cross_env_path),
            ],
        )
        == 0
    )
    cross_env_payload = json.loads(cross_env_path.read_text(encoding="utf-8"))
    assert cross_env_payload["status"] == "ok"
    assert cross_env_payload["estimated_prod_if_deployed_today"] > 0

    pr_impact_module = _load_module(
        "scripts/ops/analyze_pr_cost_impact.py", "analyze_pr_cost_impact"
    )
    assert (
        _run_module(
            pr_impact_module,
            [
                "analyze_pr_cost_impact.py",
                "--added-models",
                "1",
                "--added-joins",
                "2",
                "--modified-predicates",
                "0",
                "--baseline-monthly-cost",
                "500",
                "--output",
                str(pr_impact_path),
            ],
        )
        == 0
    )
    pr_impact_payload = json.loads(pr_impact_path.read_text(encoding="utf-8"))
    assert pr_impact_payload["status"] == "ok"
    assert pr_impact_payload["cost_delta_monthly"] > 0
    assert pr_impact_payload["recommendations"]


def test_phase82_execution_phase_attribution_uses_budget_report(tmp_path: Path) -> None:
    budget_report_path = tmp_path / "dbt_budget_report.json"
    output_path = tmp_path / "execution_phase_attribution.json"

    budget_report_path.write_text(
        json.dumps(
            {
                "status": "ok",
                "duration_seconds": 100.0,
                "timed_out": False,
                "exit_code": 0,
            }
        ),
        encoding="utf-8",
    )

    module = _load_module(
        "scripts/ops/generate_execution_phase_attribution.py",
        "generate_execution_phase_attribution",
    )
    assert (
        _run_module(
            module,
            [
                "generate_execution_phase_attribution.py",
                "--dbt-budget-report",
                str(budget_report_path),
                "--output",
                str(output_path),
            ],
        )
        == 0
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["status"] == "ok"
    assert payload["primary_bottleneck"] == "query_execution"
    phase_names = {phase["phase"] for phase in payload["execution_phases"]}
    assert phase_names == {"parsing_and_compilation", "query_execution", "materialization"}
    assert sum(
        float(phase["elapsed_seconds"]) for phase in payload["execution_phases"]
    ) == pytest.approx(100.0)
