#!/usr/bin/env python3
"""Generate on-call runbook artifacts from operational failure patterns."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from revops_funnel.artifacts import write_json_artifact
from revops_funnel.oncall_runbooks import generate_oncall_runbook_report

DEFAULT_ONCALL_OUTPUT = os.getenv(
    "ONCALL_RUNBOOK_REPORT_PATH",
    "artifacts/runbooks/oncall_runbook_report.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--health-report",
        default=os.getenv("ONCALL_HEALTH_REPORT", "artifacts/monitoring/health_report.json"),
        help="Path to health report artifact.",
    )
    parser.add_argument(
        "--dashboard-report",
        default=os.getenv(
            "ONCALL_DASHBOARD_REPORT", "artifacts/monitoring/operational_dashboard.json"
        ),
        help="Path to operational dashboard artifact.",
    )
    parser.add_argument(
        "--rollback-report",
        default=os.getenv(
            "ONCALL_ROLLBACK_REPORT", "artifacts/promotions/deployment_rollback_execution.json"
        ),
        help="Path to rollback execution report artifact.",
    )
    parser.add_argument(
        "--incident-dispatch-report",
        default=os.getenv(
            "ONCALL_INCIDENT_DISPATCH_REPORT",
            "artifacts/promotions/rollback_incident_dispatch.json",
        ),
        help="Path to rollback incident dispatch report artifact.",
    )
    parser.add_argument(
        "--dead-letter-escalation-report",
        default=os.getenv(
            "ONCALL_DEAD_LETTER_ESCALATION_REPORT",
            "artifacts/promotions/rollback_dead_letter_escalation.json",
        ),
        help="Path to dead-letter escalation report artifact.",
    )
    parser.add_argument(
        "--primary-endpoint",
        default=os.getenv("ONCALL_PRIMARY_ENDPOINT", "pagerduty-primary"),
        help="Primary escalation endpoint identifier.",
    )
    parser.add_argument(
        "--secondary-endpoint",
        default=os.getenv("ONCALL_SECONDARY_ENDPOINT", "pagerduty-secondary"),
        help="Secondary escalation endpoint identifier.",
    )
    parser.add_argument(
        "--ticket-queue",
        default=os.getenv("ONCALL_TICKET_QUEUE", "revops-platform"),
        help="Incident ticket queue identifier.",
    )
    parser.add_argument(
        "--strict-artifacts",
        action="store_true",
        help="Fail when no runbook input artifacts are available.",
    )
    parser.add_argument(
        "--strict-quality-gate",
        action="store_true",
        help="Fail if runbook quality score does not meet threshold.",
    )
    parser.add_argument(
        "--quality-threshold",
        type=float,
        default=float(os.getenv("ONCALL_QUALITY_THRESHOLD", "0.8")),
        help="Minimum runbook quality score in strict mode.",
    )
    parser.add_argument(
        "--recent-patterns",
        default=os.getenv("ONCALL_RECENT_PATTERNS_PATH", "artifacts/runbooks/recent_patterns.json"),
        help="Path to recent pattern IDs used for flap suppression.",
    )
    parser.add_argument(
        "--flap-threshold",
        type=int,
        default=int(os.getenv("ONCALL_FLAP_THRESHOLD", "3")),
        help="Suppress patterns seen this many times in recent windows.",
    )
    parser.add_argument(
        "--last-game-day-utc",
        default=os.getenv("ONCALL_LAST_GAME_DAY_UTC"),
        help="Last game-day execution timestamp in ISO8601 UTC.",
    )
    parser.add_argument(
        "--game-day-cadence-days",
        type=int,
        default=int(os.getenv("ONCALL_GAME_DAY_CADENCE_DAYS", "30")),
        help="Expected cadence for game-day exercises.",
    )
    parser.add_argument(
        "--timeline-output",
        default=os.getenv("ONCALL_TIMELINE_OUTPUT", "artifacts/runbooks/incident_timeline.json"),
        help="Output path for incident timeline artifact.",
    )
    parser.add_argument(
        "--safe-commands-only",
        action="store_true",
        help="Fail if generated runbook commands contain unsafe operations.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_ONCALL_OUTPUT,
        help="Output path for on-call runbook report artifact.",
    )
    return parser.parse_args()


def _read_json(path: str) -> dict[str, Any] | None:
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


def _read_recent_patterns(path: str) -> list[str]:
    payload = _read_json(path)
    if not payload:
        return []
    values = payload.get("pattern_ids")
    if not isinstance(values, list):
        return []
    return [str(value) for value in values if value]


def _has_unsafe_commands(report_payload: dict[str, Any]) -> bool:
    unsafe_tokens = [" rm ", "drop ", "truncate ", "shutdown", "reboot"]
    actions = report_payload.get("recommended_actions", [])
    if not isinstance(actions, list):
        return False
    for action in actions:
        if not isinstance(action, dict):
            continue
        command = f" {str(action.get('command', '')).lower()} "
        if any(token in command for token in unsafe_tokens):
            return True
    return False


def main() -> int:
    args = parse_args()

    health_report = _read_json(args.health_report)
    dashboard_report = _read_json(args.dashboard_report)
    rollback_report = _read_json(args.rollback_report)
    incident_dispatch_report = _read_json(args.incident_dispatch_report)
    dead_letter_escalation_report = _read_json(args.dead_letter_escalation_report)
    recent_pattern_ids = _read_recent_patterns(args.recent_patterns)

    has_any_artifact = any(
        [
            health_report,
            dashboard_report,
            rollback_report,
            incident_dispatch_report,
            dead_letter_escalation_report,
        ]
    )
    if not has_any_artifact:
        if args.strict_artifacts:
            print("Error: no runbook artifacts found (--strict-artifacts enabled)")
            return 1

        skipped_payload: dict[str, Any] = {
            "overall_status": "skipped",
            "incident_required": False,
            "reason": "No runbook input artifacts found",
        }
        write_json_artifact(args.output, skipped_payload)
        print("Runbook generation skipped (no artifacts).")
        return 0

    report = generate_oncall_runbook_report(
        health_report=health_report,
        dashboard_report=dashboard_report,
        rollback_execution_report=rollback_report,
        incident_dispatch_report=incident_dispatch_report,
        dead_letter_escalation_report=dead_letter_escalation_report,
        primary_endpoint=args.primary_endpoint,
        secondary_endpoint=args.secondary_endpoint,
        ticket_queue=args.ticket_queue,
        recent_pattern_ids=recent_pattern_ids,
        flap_threshold=max(1, args.flap_threshold),
        strict_quality_threshold=max(0.0, args.quality_threshold),
        dependency_impact=(dashboard_report or {}).get("dependency_impact", {}),
        last_game_day_utc=args.last_game_day_utc,
        game_day_cadence_days=max(1, args.game_day_cadence_days),
    )
    report_payload = report.to_dict()
    artifact_path = write_json_artifact(args.output, report_payload)
    write_json_artifact(
        args.timeline_output,
        {"timeline": report_payload.get("incident_timeline", [])},
    )

    if args.safe_commands_only and _has_unsafe_commands(report_payload):
        print("Error: unsafe runbook command detected (--safe-commands-only enabled)")
        return 1

    if args.strict_quality_gate and not bool(report_payload.get("quality_gate_passed", False)):
        print("Error: runbook quality gate failed (--strict-quality-gate enabled)")
        return 1

    print(f"✓ On-call runbook generated: {artifact_path}")
    print(f"  Overall status: {report.overall_status}")
    print(f"  Incident required: {report.incident_required}")
    print(f"  Failure patterns: {len(report.failure_patterns)}")
    print(f"  Escalation steps: {len(report.escalation_steps)}")
    print(f"  Runbook quality score: {report.runbook_quality_score}")
    print(f"  Game-day due: {report.game_day_due}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
