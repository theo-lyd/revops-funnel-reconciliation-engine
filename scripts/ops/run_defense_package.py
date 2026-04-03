#!/usr/bin/env python3
"""Run Phase 12 defense package, rehearsal, and handover generation."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from revops_funnel.artifacts import write_json_artifact
from revops_funnel.defense_package import (
    POLICY_CONTRACT_VERSION,
    DefensePackagePolicy,
    generate_defense_package_report,
)

DEFAULT_DEFENSE_REPORT_PATH = os.getenv(
    "PHASE12_DEFENSE_REPORT_PATH",
    "artifacts/release-evidence/phase12_defense_package_report.json",
)
DEFAULT_PHASE11_VALIDATION_REPORT = os.getenv(
    "PHASE12_VALIDATION_REPORT_PATH",
    "artifacts/validation/validation_backtesting_report.json",
)
DEFAULT_INCIDENT_OPS_REPORT = os.getenv(
    "PHASE12_INCIDENT_OPERATIONS_REPORT_PATH",
    "artifacts/runbooks/incident_operations_report.json",
)
DEFAULT_RUNBOOK_REPORT = os.getenv(
    "PHASE12_RUNBOOK_REPORT_PATH",
    "artifacts/runbooks/oncall_runbook_report.json",
)
DEFAULT_RELEASE_BUNDLE_PATH = os.getenv(
    "PHASE12_RELEASE_BUNDLE_PATH",
    "artifacts/release-evidence/release-evidence-bundle.md",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation-report", default=DEFAULT_PHASE11_VALIDATION_REPORT)
    parser.add_argument("--incident-operations-report", default=DEFAULT_INCIDENT_OPS_REPORT)
    parser.add_argument("--runbook-report", default=DEFAULT_RUNBOOK_REPORT)
    parser.add_argument("--release-evidence-bundle", default=DEFAULT_RELEASE_BUNDLE_PATH)
    parser.add_argument(
        "--min-defense-readiness-score",
        type=float,
        default=float(os.getenv("PHASE12_MIN_DEFENSE_READINESS_SCORE", "0.75")),
    )
    parser.add_argument(
        "--min-handover-coverage",
        type=float,
        default=float(os.getenv("PHASE12_MIN_HANDOVER_COVERAGE", "0.85")),
    )
    parser.add_argument(
        "--max-open-p1-failures",
        type=int,
        default=int(os.getenv("PHASE12_MAX_OPEN_P1_FAILURES", "0")),
    )
    parser.add_argument(
        "--require-rehearsal-not-due",
        action="store_true",
        default=os.getenv("PHASE12_REQUIRE_REHEARSAL_NOT_DUE", "true").lower() == "true",
    )
    parser.add_argument(
        "--policy",
        default=os.getenv("PHASE12_POLICY_PATH", ""),
        help="Optional JSON policy artifact path.",
    )
    parser.add_argument(
        "--correlation-id",
        default=os.getenv("PHASE12_CORRELATION_ID", "").strip(),
        help="Optional explicit correlation id for joining cross-phase artifacts.",
    )
    parser.add_argument(
        "--strict-validation",
        action="store_true",
        default=os.getenv("PHASE12_STRICT_VALIDATION", "false").lower() == "true",
        help="Fail when defense package blockers are detected.",
    )
    parser.add_argument("--output", default=DEFAULT_DEFENSE_REPORT_PATH)
    return parser.parse_args()


def _read_json(path: str) -> dict[str, object] | None:
    p = Path(path)
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _to_float(value: object, default: float) -> float:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _to_int(value: object, default: int) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _load_policy(path: str) -> tuple[dict[str, object] | None, str]:
    policy_path = path.strip()
    if not policy_path:
        return None, "default"

    payload = _read_json(policy_path)
    if payload is None:
        raise SystemExit(f"Phase 12 policy path unreadable: {policy_path}")

    version = str(payload.get("contract_version", ""))
    if version != POLICY_CONTRACT_VERSION:
        raise SystemExit(
            "Phase 12 policy contract mismatch: "
            f"expected {POLICY_CONTRACT_VERSION}, got '{version}'"
        )

    min_readiness = _to_float(payload.get("min_defense_readiness_score", 0.75), 0.75)
    min_coverage = _to_float(payload.get("min_handover_coverage", 0.85), 0.85)
    max_open_p1_failures = _to_int(payload.get("max_open_p1_failures", 0), 0)

    if not (0.0 <= min_readiness <= 1.0):
        raise SystemExit(
            "Phase 12 policy value out of range: min_defense_readiness_score must be 0..1"
        )
    if not (0.0 <= min_coverage <= 1.0):
        raise SystemExit("Phase 12 policy value out of range: min_handover_coverage must be 0..1")
    if max_open_p1_failures < 0:
        raise SystemExit("Phase 12 policy value out of range: max_open_p1_failures must be >= 0")

    return payload, "file"


def _emit_and_exit(output: str, payload: dict[str, object], code: int) -> int:
    write_json_artifact(output, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return code


def main() -> int:
    args = parse_args()

    validation_report = _read_json(args.validation_report)
    incident_operations_report = _read_json(args.incident_operations_report)
    runbook_report = _read_json(args.runbook_report)

    loaded_policy, policy_source = _load_policy(args.policy)

    min_defense_readiness_score = args.min_defense_readiness_score
    min_handover_coverage = args.min_handover_coverage
    max_open_p1_failures = args.max_open_p1_failures
    require_rehearsal_not_due = bool(args.require_rehearsal_not_due)

    if loaded_policy is not None:
        min_defense_readiness_score = _to_float(
            loaded_policy.get("min_defense_readiness_score", min_defense_readiness_score),
            min_defense_readiness_score,
        )
        min_handover_coverage = _to_float(
            loaded_policy.get("min_handover_coverage", min_handover_coverage),
            min_handover_coverage,
        )
        max_open_p1_failures = _to_int(
            loaded_policy.get("max_open_p1_failures", max_open_p1_failures),
            max_open_p1_failures,
        )
        require_rehearsal_not_due = bool(
            loaded_policy.get("require_rehearsal_not_due", require_rehearsal_not_due)
        )

    policy = DefensePackagePolicy(
        min_defense_readiness_score=max(0.0, min(1.0, min_defense_readiness_score)),
        min_handover_coverage=max(0.0, min(1.0, min_handover_coverage)),
        max_open_p1_failures=max(0, max_open_p1_failures),
        require_rehearsal_not_due=require_rehearsal_not_due,
    )

    report = generate_defense_package_report(
        validation_report=validation_report,
        incident_operations_report=incident_operations_report,
        runbook_report=runbook_report,
        release_evidence_bundle_path=args.release_evidence_bundle,
        policy=policy,
        explicit_correlation_id=(args.correlation_id or None),
        strict_validation=bool(args.strict_validation),
    )

    payload = report.to_dict()
    payload["strict_validation"] = bool(args.strict_validation)
    payload["policy_source"] = policy_source
    payload["policy"] = asdict(policy)
    payload["release_evidence_bundle_path"] = args.release_evidence_bundle

    status = str(payload.get("status", "unknown"))
    code = 1 if status == "error" else 0
    return _emit_and_exit(args.output, payload, code)


if __name__ == "__main__":
    raise SystemExit(main())
