"""Phase 12 defense package, rehearsal, and handover reporting helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_DNS, uuid5

CONTRACT_VERSION = "phase12.v1"
POLICY_CONTRACT_VERSION = "phase12.policy.v1"


class SignalStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class DefensePackagePolicy:
    min_defense_readiness_score: float = 0.75
    min_handover_coverage: float = 0.85
    max_open_p1_failures: int = 0
    require_rehearsal_not_due: bool = True
    policy_contract_version: str = POLICY_CONTRACT_VERSION


@dataclass(frozen=True)
class DefensePackageReport:
    contract_version: str
    generated_at_utc: str
    status: SignalStatus
    correlation_id: str
    correlation_source: str
    defense_summary: dict[str, Any]
    rehearsal_summary: dict[str, Any]
    handover_summary: dict[str, Any]
    recommendations: list[dict[str, Any]]
    strict_blockers: list[str]
    gate_eligibility: dict[str, Any]
    evidence_paths: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


def _safe_str(payload: dict[str, Any] | None, key: str, default: str = "") -> str:
    if not payload:
        return default
    value = payload.get(key, default)
    return str(value) if value is not None else default


def _safe_float(payload: dict[str, Any] | None, key: str, default: float = 0.0) -> float:
    if not payload:
        return default
    value = payload.get(key, default)
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _parse_iso_time(raw: str | None) -> datetime | None:
    if not raw:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _resolve_correlation(
    validation_report: dict[str, Any] | None,
    incident_operations_report: dict[str, Any] | None,
    runbook_report: dict[str, Any] | None,
    explicit_correlation_id: str | None,
) -> tuple[str, str]:
    if explicit_correlation_id:
        return explicit_correlation_id, "explicit"

    phase11_correlation = _safe_str(validation_report, "correlation_id", "")
    if phase11_correlation:
        return phase11_correlation, "phase11"

    incident_correlation = _safe_str(incident_operations_report, "correlation_id", "")
    if incident_correlation:
        return incident_correlation, "incident-ops"

    runbook_correlation = _safe_str(runbook_report, "correlation_id", "")
    if runbook_correlation:
        return runbook_correlation, "runbook"

    fingerprint = ":".join(
        [
            _safe_str(validation_report, "status", "missing"),
            _safe_str(incident_operations_report, "incident_state", "missing"),
            _safe_str(runbook_report, "overall_status", "missing"),
        ]
    )
    return str(uuid5(NAMESPACE_DNS, f"phase12:{fingerprint}")), "generated"


def _readiness_score(validation_report: dict[str, Any] | None) -> float:
    if not validation_report:
        return 0.0

    status = _safe_str(validation_report, "status", "")
    if status == "ok":
        return 1.0
    if status == "warning":
        return 0.7
    if status == "skipped":
        return 0.4
    return 0.2


def _bundle_present_score(
    release_evidence_bundle_path: str,
    bundle_exists: bool,
) -> tuple[float, str]:
    if bundle_exists:
        return 1.0, "present"
    if release_evidence_bundle_path.strip():
        return 0.0, "missing"
    return 0.0, "not_configured"


def _incident_response_score(incident_operations_report: dict[str, Any] | None) -> float:
    if not incident_operations_report:
        return 0.0

    response_readiness = _safe_str(incident_operations_report, "response_readiness", "")
    incident_open = bool((incident_operations_report or {}).get("incident_open", False))
    if not incident_open:
        return 1.0
    if response_readiness == "ready":
        return 1.0
    if response_readiness == "degraded":
        return 0.6
    return 0.2


def _count_open_p1_failures(runbook_report: dict[str, Any] | None) -> int:
    if not runbook_report:
        return 0

    patterns = runbook_report.get("failure_patterns", [])
    if not isinstance(patterns, list):
        return 0

    total = 0
    for item in patterns:
        if not isinstance(item, dict):
            continue
        if str(item.get("severity", "")).lower() == "p1":
            total += 1
    return total


def _build_handover_summary(
    validation_report: dict[str, Any] | None,
    incident_operations_report: dict[str, Any] | None,
    runbook_report: dict[str, Any] | None,
    release_bundle_exists: bool,
) -> dict[str, Any]:
    checks = {
        "phase11_validation_report": validation_report is not None,
        "incident_operations_report": incident_operations_report is not None,
        "oncall_runbook_report": runbook_report is not None,
        "release_evidence_bundle": release_bundle_exists,
    }
    present = sum(1 for ok in checks.values() if ok)
    coverage = present / len(checks)

    return {
        "packet_checks": checks,
        "handover_coverage": round(coverage, 3),
        "missing_packets": sorted([name for name, ok in checks.items() if not ok]),
    }


def _build_rehearsal_summary(runbook_report: dict[str, Any] | None) -> dict[str, Any]:
    if not runbook_report:
        return {
            "rehearsal_available": False,
            "game_day_due": True,
            "days_since_last_game_day": None,
            "timeline_event_count": 0,
        }

    game_day_due = bool(runbook_report.get("game_day_due", False))
    timeline = runbook_report.get("incident_timeline", [])
    timeline_count = len(timeline) if isinstance(timeline, list) else 0

    days_since = None
    generated_at = _parse_iso_time(_safe_str(runbook_report, "generated_at_utc", ""))
    last_game_day = _parse_iso_time(_safe_str(runbook_report, "last_game_day_utc", ""))
    if generated_at is not None and last_game_day is not None and generated_at >= last_game_day:
        days_since = round((generated_at - last_game_day).total_seconds() / 86400.0, 3)

    return {
        "rehearsal_available": True,
        "game_day_due": game_day_due,
        "days_since_last_game_day": days_since,
        "timeline_event_count": timeline_count,
    }


def generate_defense_package_report(
    validation_report: dict[str, Any] | None,
    incident_operations_report: dict[str, Any] | None,
    runbook_report: dict[str, Any] | None,
    release_evidence_bundle_path: str,
    policy: DefensePackagePolicy,
    explicit_correlation_id: str | None = None,
    strict_validation: bool = False,
) -> DefensePackageReport:
    release_bundle_exists = Path(release_evidence_bundle_path).is_file()

    validation_component = _readiness_score(validation_report)
    bundle_component, bundle_state = _bundle_present_score(
        release_evidence_bundle_path,
        release_bundle_exists,
    )
    incident_component = _incident_response_score(incident_operations_report)

    defense_readiness_score = (
        validation_component * 0.45 + bundle_component * 0.25 + incident_component * 0.30
    )

    defense_summary = {
        "phase11_signal_status": _safe_str(validation_report, "status", "missing"),
        "release_evidence_bundle_state": bundle_state,
        "incident_response_readiness": _safe_str(
            incident_operations_report,
            "response_readiness",
            "missing",
        ),
        "components": {
            "phase11_validation": round(validation_component, 3),
            "release_evidence_bundle": round(bundle_component, 3),
            "incident_response": round(incident_component, 3),
        },
        "defense_readiness_score": round(defense_readiness_score, 3),
    }

    rehearsal_summary = _build_rehearsal_summary(runbook_report)
    handover_summary = _build_handover_summary(
        validation_report,
        incident_operations_report,
        runbook_report,
        release_bundle_exists,
    )

    open_p1_failures = _count_open_p1_failures(runbook_report)

    strict_blockers: list[str] = []
    recommendations: list[dict[str, Any]] = []

    if defense_readiness_score < policy.min_defense_readiness_score:
        strict_blockers.append(
            "defense_readiness_score="
            f"{defense_readiness_score:.3f}<min={policy.min_defense_readiness_score:.3f}"
        )
        recommendations.append(
            {
                "type": "defense-readiness",
                "message": (
                    "Improve Phase 11 quality, release evidence completeness, "
                    "or response readiness."
                ),
            }
        )

    coverage = _safe_float(handover_summary, "handover_coverage", 0.0)
    if coverage < policy.min_handover_coverage:
        strict_blockers.append(
            f"handover_coverage={coverage:.3f}<min={policy.min_handover_coverage:.3f}"
        )
        recommendations.append(
            {
                "type": "handover-completeness",
                "message": "Complete the missing handover packet artifacts before sign-off.",
                "missing_packets": handover_summary.get("missing_packets", []),
            }
        )

    if open_p1_failures > policy.max_open_p1_failures:
        strict_blockers.append(
            f"open_p1_failures={open_p1_failures}>max={policy.max_open_p1_failures}"
        )
        recommendations.append(
            {
                "type": "failure-patterns",
                "message": "Resolve P1 failure patterns before handover finalization.",
                "open_p1_failures": open_p1_failures,
            }
        )

    rehearsal_due = bool(rehearsal_summary.get("game_day_due", True))
    if policy.require_rehearsal_not_due and rehearsal_due:
        strict_blockers.append("rehearsal_due=true")
        recommendations.append(
            {
                "type": "rehearsal",
                "message": "Schedule or complete game-day rehearsal before release handover.",
            }
        )

    phase11_status = _safe_str(validation_report, "status", "missing")
    if phase11_status == "error":
        strict_blockers.append("phase11_status=error")

    any_inputs = any(
        item is not None
        for item in (
            validation_report,
            incident_operations_report,
            runbook_report,
        )
    )

    if not any_inputs:
        status = SignalStatus.SKIPPED
    elif strict_blockers:
        status = SignalStatus.ERROR if strict_validation else SignalStatus.WARNING
    elif phase11_status == "warning":
        status = SignalStatus.WARNING
    else:
        status = SignalStatus.OK

    gate_eligibility = {
        "safe_mode_eligible": status
        in {
            SignalStatus.OK,
            SignalStatus.WARNING,
            SignalStatus.SKIPPED,
        },
        "strict_mode_eligible": bool(any_inputs) and not strict_blockers,
        "blocking_issue_count": len(strict_blockers),
        "open_p1_failures": open_p1_failures,
    }

    correlation_id, correlation_source = _resolve_correlation(
        validation_report,
        incident_operations_report,
        runbook_report,
        explicit_correlation_id,
    )

    evidence_paths = {
        "phase11_validation_report": "artifacts/validation/validation_backtesting_report.json",
        "incident_operations_report": "artifacts/runbooks/incident_operations_report.json",
        "oncall_runbook_report": "artifacts/runbooks/oncall_runbook_report.json",
        "release_evidence_bundle": "artifacts/release-evidence/release-evidence-bundle.md",
    }

    return DefensePackageReport(
        contract_version=CONTRACT_VERSION,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        status=status,
        correlation_id=correlation_id,
        correlation_source=correlation_source,
        defense_summary=defense_summary,
        rehearsal_summary=rehearsal_summary,
        handover_summary=handover_summary,
        recommendations=recommendations,
        strict_blockers=strict_blockers,
        gate_eligibility=gate_eligibility,
        evidence_paths=evidence_paths,
    )
