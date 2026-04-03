#!/usr/bin/env python3
"""Generate reliability engineering and incident operations command-center report."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from revops_funnel.artifacts import write_json_artifact
from revops_funnel.incident_operations import (
    POLICY_CONTRACT_VERSION,
    IncidentOperationsPolicy,
    generate_incident_operations_report,
)

DEFAULT_INCIDENT_OPS_OUTPUT = os.getenv(
    "INCIDENT_OPERATIONS_REPORT_PATH",
    "artifacts/runbooks/incident_operations_report.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--health-report",
        default=os.getenv("INCIDENT_OPS_HEALTH_REPORT", "artifacts/monitoring/health_report.json"),
        help="Path to health report artifact.",
    )
    parser.add_argument(
        "--dashboard-report",
        default=os.getenv(
            "INCIDENT_OPS_DASHBOARD_REPORT", "artifacts/monitoring/operational_dashboard.json"
        ),
        help="Path to operational dashboard artifact.",
    )
    parser.add_argument(
        "--runbook-report",
        default=os.getenv(
            "INCIDENT_OPS_RUNBOOK_REPORT", "artifacts/runbooks/oncall_runbook_report.json"
        ),
        help="Path to on-call runbook artifact.",
    )
    parser.add_argument(
        "--dispatch-report",
        default=os.getenv(
            "INCIDENT_OPS_DISPATCH_REPORT", "artifacts/promotions/rollback_incident_dispatch.json"
        ),
        help="Path to incident dispatch report.",
    )
    parser.add_argument(
        "--escalation-report",
        default=os.getenv(
            "INCIDENT_OPS_ESCALATION_REPORT",
            "artifacts/promotions/rollback_dead_letter_escalation.json",
        ),
        help="Path to dead-letter escalation report.",
    )
    parser.add_argument(
        "--recent-patterns",
        default=os.getenv(
            "INCIDENT_OPS_RECENT_PATTERNS", "artifacts/runbooks/recent_patterns.json"
        ),
        help="Path to recent pattern IDs JSON for fatigue scoring.",
    )
    parser.add_argument(
        "--fatigue-repeat-threshold",
        type=int,
        default=int(os.getenv("INCIDENT_OPS_FATIGUE_REPEAT_THRESHOLD", "3")),
        help="Repeat threshold for counting alert fatigue.",
    )
    parser.add_argument(
        "--fatigue-decay-half-life-hours",
        type=float,
        default=float(os.getenv("INCIDENT_OPS_FATIGUE_DECAY_HALF_LIFE_HOURS", "24")),
        help="Half-life in hours for fatigue v2 time-decay weighting.",
    )
    parser.add_argument(
        "--policy",
        default=os.getenv("INCIDENT_OPS_POLICY_PATH", ""),
        help="Optional path to policy JSON artifact (opt-in).",
    )
    parser.add_argument(
        "--strict-min-evidence-completeness",
        type=float,
        default=float(os.getenv("INCIDENT_OPS_STRICT_MIN_EVIDENCE_COMPLETENESS", "0.8")),
        help="Minimum evidence completeness required before strict blockers can fail execution.",
    )
    parser.add_argument(
        "--correlation-id",
        default=os.getenv("INCIDENT_OPS_CORRELATION_ID", ""),
        help="Optional correlation ID override for idempotent joins across artifacts.",
    )
    parser.add_argument(
        "--require-dispatch-sent",
        action="store_true",
        help="Require dispatch status to be sent in strict mode.",
    )
    parser.add_argument(
        "--require-escalation-sent",
        action="store_true",
        help="Require escalation status to be sent (or skipped-no-dead-letter) in strict mode.",
    )
    parser.add_argument(
        "--strict-operations",
        action="store_true",
        help="Fail when strict blockers are detected for an open incident.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_INCIDENT_OPS_OUTPUT,
        help="Output path for incident operations report artifact.",
    )
    return parser.parse_args()


def _read_json(path: str) -> dict[str, Any] | None:
    if not path:
        return None

    artifact_path = Path(path)
    if not artifact_path.exists():
        return None

    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    if not isinstance(payload, dict):
        return None
    return payload


def _read_recent_pattern_ids(path: str) -> list[str]:
    payload = _read_json(path)
    if not payload:
        return []

    values = payload.get("pattern_ids")
    if not isinstance(values, list):
        return []
    return [str(value) for value in values if value]


def _read_recent_pattern_events(path: str) -> list[dict[str, Any]]:
    payload = _read_json(path)
    if not payload:
        return []

    values = payload.get("events")
    if not isinstance(values, list):
        return []

    events: list[dict[str, Any]] = []
    for value in values:
        if isinstance(value, dict):
            events.append(value)
    return events


def _load_policy(path: str) -> dict[str, Any]:
    payload = _read_json(path)
    if not payload:
        return {}

    contract_version = str(payload.get("contract_version", ""))
    if contract_version and contract_version != POLICY_CONTRACT_VERSION:
        print(
            "Warning: unsupported policy contract_version="
            f"{contract_version}; expected {POLICY_CONTRACT_VERSION}. Ignoring policy."
        )
        return {}
    return payload


def main() -> int:
    args = parse_args()

    health_report = _read_json(args.health_report)
    dashboard_report = _read_json(args.dashboard_report)
    runbook_report = _read_json(args.runbook_report)
    dispatch_report = _read_json(args.dispatch_report)
    escalation_report = _read_json(args.escalation_report)
    recent_pattern_ids = _read_recent_pattern_ids(args.recent_patterns)
    recent_pattern_events = _read_recent_pattern_events(args.recent_patterns)
    policy_payload = _load_policy(args.policy)

    require_dispatch_sent = bool(policy_payload.get("require_dispatch_sent", False)) or bool(
        args.require_dispatch_sent
    )
    require_escalation_sent = bool(policy_payload.get("require_escalation_sent", False)) or bool(
        args.require_escalation_sent
    )
    fatigue_repeat_threshold = int(
        policy_payload.get("fatigue_pattern_repeat_threshold", args.fatigue_repeat_threshold)
    )
    fatigue_decay_half_life_hours = float(
        policy_payload.get(
            "fatigue_decay_half_life_hours",
            args.fatigue_decay_half_life_hours,
        )
    )
    min_evidence_completeness = float(
        policy_payload.get(
            "min_evidence_completeness",
            args.strict_min_evidence_completeness,
        )
    )

    policy = IncidentOperationsPolicy(
        require_dispatch_sent=require_dispatch_sent,
        require_escalation_sent=require_escalation_sent,
        fatigue_pattern_repeat_threshold=max(1, fatigue_repeat_threshold),
        fatigue_decay_half_life_hours=max(1.0, fatigue_decay_half_life_hours),
        min_evidence_completeness=max(0.0, min(1.0, min_evidence_completeness)),
        policy_contract_version=str(
            policy_payload.get("contract_version", POLICY_CONTRACT_VERSION)
        ),
    )

    report = generate_incident_operations_report(
        health_report=health_report,
        dashboard_report=dashboard_report,
        runbook_report=runbook_report,
        dispatch_report=dispatch_report,
        escalation_report=escalation_report,
        recent_pattern_ids=recent_pattern_ids,
        recent_pattern_events=recent_pattern_events,
        policy=policy,
        explicit_correlation_id=args.correlation_id or None,
    )
    payload = report.to_dict()
    payload["policy_contract_version"] = policy.policy_contract_version
    payload["policy_source"] = "file" if policy_payload else "defaults+args"

    strict_blockers = bool(payload["incident_open"] and payload["strict_blockers"])
    evidence_score = float(payload.get("evidence_completeness_score", 0.0))
    strict_enforcement_suppressed = False

    if (
        args.strict_operations
        and strict_blockers
        and evidence_score < policy.min_evidence_completeness
    ):
        strict_enforcement_suppressed = True
        payload["strict_enforcement_suppressed"] = True

    write_json_artifact(args.output, payload)

    print(json.dumps(payload, indent=2, sort_keys=True))

    if args.strict_operations and strict_blockers and not strict_enforcement_suppressed:
        print("Error: strict incident operations blockers detected")
        return 1

    if args.strict_operations and strict_enforcement_suppressed:
        print(
            "Warning: strict blockers detected but enforcement suppressed due to low evidence "
            f"completeness ({evidence_score:.3f} < {policy.min_evidence_completeness:.3f})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
