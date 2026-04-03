"""Validation, backtesting, and impact measurement helpers for Phase 11."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import NAMESPACE_DNS, uuid5

CONTRACT_VERSION = "phase11.v1"
POLICY_CONTRACT_VERSION = "phase11.policy.v1"


class SignalStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class ValidationBacktestingPolicy:
    min_artifact_coverage: float = 0.8
    max_credits_regression_pct: float = 20.0
    max_elapsed_regression_pct: float = 25.0
    min_operational_readiness_score: float = 0.7
    max_forecast_mismatch_pct: float = 25.0
    readiness_weights: dict[str, float] | None = None
    policy_contract_version: str = POLICY_CONTRACT_VERSION


@dataclass(frozen=True)
class ValidationBacktestingReport:
    contract_version: str
    generated_at_utc: str
    status: SignalStatus
    correlation_id: str
    correlation_source: str
    validation_coverage_pct: float
    validation_summary: dict[str, Any]
    backtest_summary: dict[str, Any]
    impact_summary: dict[str, Any]
    recommendations: list[dict[str, Any]]
    strict_blockers: list[str]
    strict_blockers_detailed: list[dict[str, Any]]
    status_reason: str
    gate_eligibility: dict[str, Any]
    schema_validation: dict[str, Any]
    evidence_paths: dict[str, str]
    artifact_provenance: dict[str, dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


def _safe_float(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


def _safe_bool(payload: dict[str, Any] | None, key: str, default: bool = False) -> bool:
    if not payload:
        return default
    value = payload.get(key, default)
    return bool(value)


def _safe_str(payload: dict[str, Any] | None, key: str, default: str = "") -> str:
    if not payload:
        return default
    value = payload.get(key, default)
    return str(value) if value is not None else default


def _percent_change(current: float, baseline: float) -> float | None:
    if baseline <= 0:
        return None
    return ((current - baseline) / baseline) * 100.0


def _wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float] | None:
    if trials <= 0:
        return None

    n = float(trials)
    p = successes / n
    z2 = z**2
    denominator = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denominator
    margin = z * ((p * (1.0 - p) / n) + (z2 / (4.0 * (n**2)))) ** 0.5 / denominator
    return (max(0.0, center - margin), min(1.0, center + margin))


def _normalize_weights(weights: dict[str, float] | None) -> dict[str, float]:
    default_weights = {
        "health": 0.25,
        "dashboard": 0.25,
        "runbook": 0.25,
        "incident_operations": 0.25,
    }
    if not weights:
        return default_weights

    normalized: dict[str, float] = {}
    for key, default_weight in default_weights.items():
        value = _safe_float(weights.get(key, default_weight))
        normalized[key] = max(0.0, value)

    total = sum(normalized.values())
    if total <= 0:
        return default_weights

    return {key: (value / total) for key, value in normalized.items()}


def _schema_issue(
    artifact: str,
    code: str,
    severity: str,
    message: str,
) -> dict[str, str]:
    return {
        "artifact": artifact,
        "code": code,
        "severity": severity,
        "message": message,
    }


def _validate_artifact_schemas(
    required_artifacts: dict[str, dict[str, Any] | None],
    optional_artifacts: dict[str, dict[str, Any] | None],
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    required_keys: dict[str, list[str]] = {
        "current_cost_report": ["status", "totals"],
        "baseline_cost_report": ["status", "totals"],
        "regression_report": ["status", "summary"],
        "forecast_report": ["status", "forecasts"],
        "health_report": ["overall_status"],
        "dashboard_report": ["operational_status"],
        "runbook_report": ["quality_gate_passed"],
        "incident_operations_report": ["contract_version", "incident_open", "strict_blockers"],
    }

    for artifact, payload in required_artifacts.items():
        if payload is None:
            issues.append(
                _schema_issue(
                    artifact,
                    "artifact_missing",
                    "critical",
                    "Required artifact payload is missing.",
                )
            )
            continue

        if not isinstance(payload, dict):
            issues.append(
                _schema_issue(
                    artifact,
                    "artifact_not_object",
                    "critical",
                    "Artifact payload must be a JSON object.",
                )
            )
            continue

        for key in required_keys.get(artifact, []):
            if key not in payload:
                issues.append(
                    _schema_issue(
                        artifact,
                        f"missing_{key}",
                        "critical",
                        f"Missing required key '{key}'.",
                    )
                )

        if artifact == "incident_operations_report":
            version = str(payload.get("contract_version", ""))
            if version and not version.startswith("phase10."):
                issues.append(
                    _schema_issue(
                        artifact,
                        "unexpected_contract_version",
                        "critical",
                        f"Unexpected contract_version '{version}' for incident operations report.",
                    )
                )

    for artifact, payload in optional_artifacts.items():
        if payload is None:
            continue
        if not isinstance(payload, dict):
            issues.append(
                _schema_issue(
                    artifact,
                    "artifact_not_object",
                    "advisory",
                    "Optional artifact payload should be a JSON object.",
                )
            )

    return issues


def _score_status(value: str, healthy_values: set[str], degraded_values: set[str]) -> float:
    normalized = value.strip().lower()
    if normalized in healthy_values:
        return 1.0
    if normalized in degraded_values:
        return 0.5
    if not normalized:
        return 0.0
    return 0.0


def _extract_totals(report: dict[str, Any] | None) -> dict[str, float]:
    if not report:
        return {"credits_used": 0.0, "elapsed_seconds": 0.0, "query_count": 0.0}
    totals_obj = report.get("totals", {})
    totals = totals_obj if isinstance(totals_obj, dict) else {}
    return {
        "credits_used": _safe_float(totals.get("credits_used", 0.0)),
        "elapsed_seconds": _safe_float(totals.get("elapsed_seconds", 0.0)),
        "query_count": _safe_float(totals.get("query_count", 0.0)),
    }


def _extract_forecast_alert_tags(report: dict[str, Any] | None) -> set[str]:
    if not report:
        return set()
    forecasts = report.get("forecasts", [])
    if not isinstance(forecasts, list):
        return set()

    alert_tags: set[str] = set()
    for row in forecasts:
        if not isinstance(row, dict):
            continue
        if str(row.get("allocation_alert", "")).strip() != "trending-over-budget":
            continue
        tag = str(row.get("query_tag", "")).strip()
        if tag:
            alert_tags.add(tag)
    return alert_tags


def _extract_regression_tags(report: dict[str, Any] | None) -> set[str]:
    if not report:
        return set()

    tags: set[str] = set()
    for key in ("query_tag_regressions", "new_query_tags"):
        rows = report.get(key, [])
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict):
                tag = str(row.get("query_tag", row.get("tag", ""))).strip()
            else:
                tag = str(row).strip()
            if tag:
                tags.add(tag)
    return tags


def _operational_readiness_score(
    health_report: dict[str, Any] | None,
    dashboard_report: dict[str, Any] | None,
    runbook_report: dict[str, Any] | None,
    incident_operations_report: dict[str, Any] | None,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    health_score = _score_status(
        _safe_str(health_report, "overall_status", ""),
        {"ok", "healthy"},
        {"degraded"},
    )
    dashboard_score = _score_status(
        _safe_str(dashboard_report, "operational_status", ""),
        {"ok", "healthy"},
        {"degraded"},
    )
    runbook_score = 1.0 if _safe_bool(runbook_report, "quality_gate_passed", True) else 0.0

    incident_score = 0.0
    if incident_operations_report:
        incident_open = bool(incident_operations_report.get("incident_open", False))
        strict_blockers = incident_operations_report.get("strict_blockers", [])
        evidence_score = _safe_float(
            incident_operations_report.get("evidence_completeness_score", 0.0)
        )
        if not incident_open and not strict_blockers:
            incident_score = 1.0
        elif evidence_score >= 0.8:
            incident_score = 0.75
        else:
            incident_score = 0.5

    effective_weights = _normalize_weights(weights)
    weighted_score = (
        health_score * effective_weights["health"]
        + dashboard_score * effective_weights["dashboard"]
        + runbook_score * effective_weights["runbook"]
        + incident_score * effective_weights["incident_operations"]
    )

    values = [health_score, dashboard_score, runbook_score, incident_score]
    return {
        "health_score": round(health_score, 3),
        "dashboard_score": round(dashboard_score, 3),
        "runbook_score": round(runbook_score, 3),
        "incident_operations_score": round(incident_score, 3),
        "overall_score": round(weighted_score, 3),
        "unweighted_overall_score": round(sum(values) / len(values), 3),
        "weights": {
            "health": round(effective_weights["health"], 4),
            "dashboard": round(effective_weights["dashboard"], 4),
            "runbook": round(effective_weights["runbook"], 4),
            "incident_operations": round(effective_weights["incident_operations"], 4),
        },
    }


def _resolve_correlation(
    runbook_report: dict[str, Any] | None,
    incident_operations_report: dict[str, Any] | None,
    current_cost_report: dict[str, Any] | None,
    baseline_cost_report: dict[str, Any] | None,
    explicit_correlation_id: str | None,
) -> tuple[str, str]:
    if explicit_correlation_id:
        return explicit_correlation_id, "explicit"

    incident_correlation = _safe_str(incident_operations_report, "correlation_id", "")
    if incident_correlation:
        return incident_correlation, "incident-ops"

    runbook_correlation = _safe_str(runbook_report, "correlation_id", "")
    if runbook_correlation:
        return runbook_correlation, "runbook"

    fingerprint = ":".join(
        [
            _safe_str(current_cost_report, "status", "missing"),
            _safe_str(baseline_cost_report, "status", "missing"),
            _safe_str(runbook_report, "quality_gate_passed", "unknown"),
            _safe_str(incident_operations_report, "incident_state", "unknown"),
        ]
    )
    return str(uuid5(NAMESPACE_DNS, f"phase11:{fingerprint}")), "generated"


def generate_validation_backtesting_report(
    current_cost_report: dict[str, Any] | None,
    baseline_cost_report: dict[str, Any] | None,
    regression_report: dict[str, Any] | None,
    forecast_report: dict[str, Any] | None,
    cross_environment_report: dict[str, Any] | None,
    pr_impact_report: dict[str, Any] | None,
    health_report: dict[str, Any] | None,
    dashboard_report: dict[str, Any] | None,
    runbook_report: dict[str, Any] | None,
    incident_operations_report: dict[str, Any] | None,
    historical_cost_reports: list[dict[str, Any]] | None,
    artifact_provenance: dict[str, dict[str, Any]] | None,
    policy: ValidationBacktestingPolicy,
    explicit_correlation_id: str | None = None,
    strict_validation: bool = False,
) -> ValidationBacktestingReport:
    required_artifacts = {
        "current_cost_report": current_cost_report,
        "baseline_cost_report": baseline_cost_report,
        "regression_report": regression_report,
        "forecast_report": forecast_report,
        "health_report": health_report,
        "dashboard_report": dashboard_report,
        "runbook_report": runbook_report,
        "incident_operations_report": incident_operations_report,
    }
    optional_artifacts = {
        "cross_environment_report": cross_environment_report,
        "pr_impact_report": pr_impact_report,
    }

    schema_issues = _validate_artifact_schemas(required_artifacts, optional_artifacts)

    present_required = [name for name, payload in required_artifacts.items() if payload is not None]
    missing_required = [name for name, payload in required_artifacts.items() if payload is None]
    present_optional = [name for name, payload in optional_artifacts.items() if payload is not None]
    coverage_pct = len(present_required) / len(required_artifacts) if required_artifacts else 0.0

    current_totals = _extract_totals(current_cost_report)
    baseline_totals = _extract_totals(baseline_cost_report)

    backtest_mode = "point-in-time"
    history_window_count = 0
    effective_baseline_totals = dict(baseline_totals)
    valid_history_totals: list[dict[str, float]] = []
    for history_report in historical_cost_reports or []:
        if not isinstance(history_report, dict):
            continue
        if str(history_report.get("status", "")) not in {"", "ok"}:
            continue
        totals = _extract_totals(history_report)
        if totals["credits_used"] <= 0 and totals["elapsed_seconds"] <= 0:
            continue
        valid_history_totals.append(totals)

    if valid_history_totals:
        history_window_count = len(valid_history_totals)
        backtest_mode = "rolling-window"
        effective_baseline_totals = {
            "credits_used": sum(x["credits_used"] for x in valid_history_totals)
            / history_window_count,
            "elapsed_seconds": sum(x["elapsed_seconds"] for x in valid_history_totals)
            / history_window_count,
            "query_count": (
                sum(x["query_count"] for x in valid_history_totals) / history_window_count
            ),
        }
    current_status = _safe_str(current_cost_report, "status", "")
    baseline_status = _safe_str(baseline_cost_report, "status", "")
    regression_status = _safe_str(regression_report, "status", "")
    forecast_status = _safe_str(forecast_report, "status", "")

    actual_credits_delta = (
        current_totals["credits_used"] - effective_baseline_totals["credits_used"]
    )
    actual_elapsed_delta = (
        current_totals["elapsed_seconds"] - effective_baseline_totals["elapsed_seconds"]
    )
    actual_credits_delta_pct = _percent_change(
        current_totals["credits_used"], effective_baseline_totals["credits_used"]
    )
    actual_elapsed_delta_pct = _percent_change(
        current_totals["elapsed_seconds"], effective_baseline_totals["elapsed_seconds"]
    )

    regression_thresholds_obj = regression_report.get("thresholds", {}) if regression_report else {}
    regression_thresholds = (
        regression_thresholds_obj if isinstance(regression_thresholds_obj, dict) else {}
    )
    max_credits_regression_pct = _safe_float(
        regression_thresholds.get("max_credits_regression_pct", policy.max_credits_regression_pct)
    )
    max_elapsed_regression_pct = _safe_float(
        regression_thresholds.get("max_elapsed_regression_pct", policy.max_elapsed_regression_pct)
    )
    expected_blocked = False
    if (
        actual_credits_delta_pct is not None
        and actual_credits_delta_pct > max_credits_regression_pct
    ):
        expected_blocked = True
    if (
        actual_elapsed_delta_pct is not None
        and actual_elapsed_delta_pct > max_elapsed_regression_pct
    ):
        expected_blocked = True

    regression_summary_obj = regression_report.get("summary", {}) if regression_report else {}
    regression_summary = regression_summary_obj if isinstance(regression_summary_obj, dict) else {}
    observed_blocked = bool(regression_summary.get("blocked", False)) or (
        regression_status == "regression-detected"
    )
    regression_alignment = (
        observed_blocked == expected_blocked
        if regression_report
        and current_cost_report
        and (baseline_cost_report or valid_history_totals)
        else None
    )

    forecast_alert_tags = _extract_forecast_alert_tags(forecast_report)
    regression_tags = _extract_regression_tags(regression_report)
    forecast_alignment_tags = sorted(forecast_alert_tags & regression_tags)
    forecast_false_positive_tags = sorted(forecast_alert_tags - regression_tags)
    forecast_missed_tags = sorted(regression_tags - forecast_alert_tags)

    forecast_precision = None
    if forecast_alert_tags:
        forecast_precision = len(forecast_alignment_tags) / len(forecast_alert_tags)

    forecast_recall = None
    if regression_tags:
        forecast_recall = len(forecast_alignment_tags) / len(regression_tags)

    forecast_precision_band = _wilson_interval(
        len(forecast_alignment_tags), len(forecast_alert_tags)
    )
    forecast_recall_band = _wilson_interval(len(forecast_alignment_tags), len(regression_tags))

    forecast_alignment_gap_pct = None
    if forecast_precision is not None and forecast_recall is not None:
        forecast_alignment_gap_pct = round(
            (1.0 - min(forecast_precision, forecast_recall)) * 100.0,
            3,
        )

    operational_scores = _operational_readiness_score(
        health_report,
        dashboard_report,
        runbook_report,
        incident_operations_report,
        policy.readiness_weights,
    )

    pr_impact_delta = None
    if pr_impact_report:
        pr_impact_delta = _safe_float(pr_impact_report.get("cost_delta_monthly", 0.0))

    cross_environment_forecast = None
    if cross_environment_report:
        cross_environment_forecast = _safe_float(
            cross_environment_report.get("forecast_impact", 0.0)
        )

    validation_summary = {
        "required_artifacts": sorted(required_artifacts.keys()),
        "present_required_artifacts": sorted(present_required),
        "missing_required_artifacts": sorted(missing_required),
        "optional_artifacts_present": sorted(present_optional),
        "current_status": current_status,
        "baseline_status": baseline_status,
        "regression_status": regression_status,
        "forecast_status": forecast_status,
    }

    backtest_summary = {
        "backtest_mode": backtest_mode,
        "history_window_sample_size": history_window_count,
        "actual_credits_delta_monthly": round(actual_credits_delta, 3),
        "actual_credits_delta_pct": round(actual_credits_delta_pct, 3)
        if actual_credits_delta_pct is not None
        else None,
        "actual_elapsed_delta_seconds": round(actual_elapsed_delta, 3),
        "actual_elapsed_delta_pct": round(actual_elapsed_delta_pct, 3)
        if actual_elapsed_delta_pct is not None
        else None,
        "expected_regression_blocked": expected_blocked,
        "observed_regression_blocked": observed_blocked,
        "regression_alignment": regression_alignment,
        "forecast_alert_tags": sorted(forecast_alert_tags),
        "forecast_alignment_tags": forecast_alignment_tags,
        "forecast_false_positive_tags": forecast_false_positive_tags,
        "forecast_missed_tags": forecast_missed_tags,
        "forecast_precision_pct": round(forecast_precision * 100.0, 3)
        if forecast_precision is not None
        else None,
        "forecast_precision_sample_size": len(forecast_alert_tags),
        "forecast_precision_confidence_band_pct": [
            round(forecast_precision_band[0] * 100.0, 3),
            round(forecast_precision_band[1] * 100.0, 3),
        ]
        if forecast_precision_band is not None
        else None,
        "forecast_recall_pct": round(forecast_recall * 100.0, 3)
        if forecast_recall is not None
        else None,
        "forecast_recall_sample_size": len(regression_tags),
        "forecast_recall_confidence_band_pct": [
            round(forecast_recall_band[0] * 100.0, 3),
            round(forecast_recall_band[1] * 100.0, 3),
        ]
        if forecast_recall_band is not None
        else None,
        "forecast_alignment_gap_pct": forecast_alignment_gap_pct,
        "cross_environment_forecast_monthly": round(cross_environment_forecast, 3)
        if cross_environment_forecast is not None
        else None,
        "pr_impact_cost_delta_monthly": round(pr_impact_delta, 3)
        if pr_impact_delta is not None
        else None,
    }

    strict_blockers_detailed: list[dict[str, Any]] = []

    for issue in schema_issues:
        strict_blockers_detailed.append(
            {
                "code": f"schema::{issue['artifact']}::{issue['code']}",
                "severity": issue["severity"],
                "artifact": issue["artifact"],
                "message": issue["message"],
            }
        )

    if coverage_pct < policy.min_artifact_coverage:
        strict_blockers_detailed.append(
            {
                "code": "artifact_coverage_threshold",
                "severity": "critical",
                "artifact": "phase11",
                "message": (
                    f"artifact_coverage={coverage_pct:.3f}<min={policy.min_artifact_coverage:.3f}"
                ),
            }
        )
    if regression_alignment is False:
        strict_blockers_detailed.append(
            {
                "code": "regression_backtest_mismatch",
                "severity": "critical",
                "artifact": "regression_report",
                "message": "Regression backtest mismatch between expected and observed blocking.",
            }
        )
    if (
        forecast_alignment_gap_pct is not None
        and forecast_alignment_gap_pct > policy.max_forecast_mismatch_pct
    ):
        strict_blockers_detailed.append(
            {
                "code": "forecast_alignment_gap_threshold",
                "severity": "advisory",
                "artifact": "forecast_report",
                "message": (
                    f"forecast_alignment_gap_pct={forecast_alignment_gap_pct:.3f}>max={policy.max_forecast_mismatch_pct:.3f}"
                ),
            }
        )
    if operational_scores["overall_score"] < policy.min_operational_readiness_score:
        strict_blockers_detailed.append(
            {
                "code": "operational_readiness_threshold",
                "severity": "critical",
                "artifact": "phase11",
                "message": (
                    "operational_readiness="
                    f"{operational_scores['overall_score']:.3f}"
                    f"<min={policy.min_operational_readiness_score:.3f}"
                ),
            }
        )

    strict_blockers = [
        item["message"]
        for item in strict_blockers_detailed
        if str(item.get("severity", "")).lower() == "critical"
    ]

    recommendations: list[dict[str, Any]] = []
    if missing_required:
        recommendations.append(
            {
                "type": "artifact-coverage",
                "message": (
                    "Materialize the missing validation inputs before treating "
                    "the backtest as authoritative."
                ),
                "missing_required_artifacts": sorted(missing_required),
            }
        )
    if schema_issues:
        recommendations.append(
            {
                "type": "schema-validation",
                "message": (
                    "Resolve artifact schema/version validation issues before "
                    "trusting this scorecard."
                ),
                "issue_count": len(schema_issues),
            }
        )
    if regression_alignment is False:
        recommendations.append(
            {
                "type": "signal-alignment",
                "message": (
                    "Tune regression thresholds or expand the backtest window so "
                    "blocked regressions match observed drift."
                ),
            }
        )
    if (
        forecast_alignment_gap_pct is not None
        and forecast_alignment_gap_pct > policy.max_forecast_mismatch_pct
    ):
        recommendations.append(
            {
                "type": "forecast-calibration",
                "message": (
                    "Refine forecast alert thresholds; forecast backtests are "
                    "missing too many realized regressions."
                ),
            }
        )
    if operational_scores["overall_score"] < policy.min_operational_readiness_score:
        recommendations.append(
            {
                "type": "operational-readiness",
                "message": (
                    "Resolve health, dashboard, runbook, or incident-ops gaps "
                    "before using this release signal as a gate."
                ),
            }
        )

    if not present_required:
        status = SignalStatus.SKIPPED
        status_reason = "insufficient_required_artifacts"
    elif strict_blockers:
        status = SignalStatus.ERROR if strict_validation else SignalStatus.WARNING
        status_reason = (
            "strict_blockers_detected"
            if strict_validation
            else "critical_issues_detected_non_strict_mode"
        )
    elif schema_issues:
        status = SignalStatus.WARNING
        status_reason = "schema_or_version_issues_detected"
    else:
        status = SignalStatus.OK
        status_reason = "all_checks_passed"

    advisory_issue_count = sum(
        1
        for item in strict_blockers_detailed
        if str(item.get("severity", "")).lower() == "advisory"
    )
    gate_eligibility = {
        "safe_mode_eligible": status
        in {SignalStatus.OK, SignalStatus.WARNING, SignalStatus.SKIPPED},
        "strict_mode_eligible": bool(present_required) and not strict_blockers,
        "blocking_issue_count": len(strict_blockers),
        "advisory_issue_count": advisory_issue_count,
    }

    correlation_id, correlation_source = _resolve_correlation(
        runbook_report,
        incident_operations_report,
        current_cost_report,
        baseline_cost_report,
        explicit_correlation_id,
    )

    evidence_paths = {
        "current_cost_report": "artifacts/performance/query_cost_attribution_report.json",
        "baseline_cost_report": "artifacts/performance/query_cost_attribution_baseline.json",
        "regression_report": "artifacts/performance/query_cost_regression_report.json",
        "forecast_report": "artifacts/performance/query_cost_forecast_report.json",
        "cross_environment_report": "artifacts/performance/cross_environment_forecast.json",
        "pr_impact_report": "artifacts/performance/pr_cost_impact_score.json",
        "health_report": "artifacts/monitoring/health_report.json",
        "dashboard_report": "artifacts/monitoring/operational_dashboard.json",
        "runbook_report": "artifacts/runbooks/oncall_runbook_report.json",
        "incident_operations_report": "artifacts/runbooks/incident_operations_report.json",
    }

    return ValidationBacktestingReport(
        contract_version=CONTRACT_VERSION,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        status=status,
        correlation_id=correlation_id,
        correlation_source=correlation_source,
        validation_coverage_pct=round(coverage_pct, 3),
        validation_summary=validation_summary,
        backtest_summary=backtest_summary,
        impact_summary={
            "current_totals": current_totals,
            "baseline_totals": baseline_totals,
            "effective_baseline_totals": {
                "credits_used": round(effective_baseline_totals["credits_used"], 3),
                "elapsed_seconds": round(effective_baseline_totals["elapsed_seconds"], 3),
                "query_count": round(effective_baseline_totals["query_count"], 3),
            },
            "operational_readiness": operational_scores,
            "pr_impact_cost_delta_monthly": round(pr_impact_delta, 3)
            if pr_impact_delta is not None
            else None,
            "cross_environment_forecast_monthly": round(cross_environment_forecast, 3)
            if cross_environment_forecast is not None
            else None,
        },
        recommendations=recommendations,
        strict_blockers=strict_blockers,
        strict_blockers_detailed=strict_blockers_detailed,
        status_reason=status_reason,
        gate_eligibility=gate_eligibility,
        schema_validation={
            "issue_count": len(schema_issues),
            "issues": schema_issues,
        },
        evidence_paths=evidence_paths,
        artifact_provenance=artifact_provenance or {},
    )
