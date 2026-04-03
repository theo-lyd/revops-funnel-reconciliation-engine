from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from revops_funnel.defense_package import DefensePackagePolicy, generate_defense_package_report


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_generate_defense_package_report_ok_with_complete_inputs(tmp_path: Path) -> None:
    bundle_path = tmp_path / "release-evidence-bundle.md"
    bundle_path.write_text("# Release Evidence Bundle\n", encoding="utf-8")

    report = generate_defense_package_report(
        validation_report={"status": "ok", "correlation_id": "phase11-correlation"},
        incident_operations_report={
            "incident_open": False,
            "response_readiness": "ready",
            "correlation_id": "phase10-correlation",
        },
        runbook_report={
            "overall_status": "ok",
            "game_day_due": False,
            "failure_patterns": [],
            "incident_timeline": [{"event_type": "pattern_detected"}],
        },
        release_evidence_bundle_path=str(bundle_path),
        policy=DefensePackagePolicy(),
    )

    payload = report.to_dict()
    assert payload["status"] == "ok"
    assert payload["correlation_id"] == "phase11-correlation"
    assert payload["defense_summary"]["defense_readiness_score"] >= 0.75
    assert payload["handover_summary"]["handover_coverage"] == 1.0


def test_generate_defense_package_report_warning_for_missing_bundle_non_strict(
    tmp_path: Path,
) -> None:
    report = generate_defense_package_report(
        validation_report={"status": "warning"},
        incident_operations_report={"incident_open": True, "response_readiness": "degraded"},
        runbook_report={
            "game_day_due": True,
            "failure_patterns": [{"severity": "p1"}],
        },
        release_evidence_bundle_path=str(tmp_path / "missing.md"),
        policy=DefensePackagePolicy(min_defense_readiness_score=0.9),
        strict_validation=False,
    )

    payload = report.to_dict()
    assert payload["status"] == "warning"
    assert payload["strict_blockers"]


def test_run_defense_package_cli_strict_fails_when_blockers_present(tmp_path: Path) -> None:
    validation_path = tmp_path / "validation.json"
    incident_ops_path = tmp_path / "incident_ops.json"
    runbook_path = tmp_path / "runbook.json"
    output_path = tmp_path / "phase12_report.json"

    _write_json(validation_path, {"status": "error"})
    _write_json(incident_ops_path, {"incident_open": True, "response_readiness": "at-risk"})
    _write_json(
        runbook_path,
        {
            "game_day_due": True,
            "failure_patterns": [{"severity": "p1"}, {"severity": "p1"}],
        },
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/ops/run_defense_package.py",
            f"--validation-report={validation_path}",
            f"--incident-operations-report={incident_ops_path}",
            f"--runbook-report={runbook_path}",
            f"--release-evidence-bundle={tmp_path / 'missing.md'}",
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


def test_run_defense_package_cli_policy_contract_mismatch_fails(tmp_path: Path) -> None:
    validation_path = tmp_path / "validation.json"
    policy_path = tmp_path / "policy.json"
    output_path = tmp_path / "phase12_report.json"

    _write_json(validation_path, {"status": "ok"})
    _write_json(policy_path, {"contract_version": "phase12.policy.v0"})

    result = subprocess.run(
        [
            sys.executable,
            "scripts/ops/run_defense_package.py",
            f"--validation-report={validation_path}",
            f"--policy={policy_path}",
            f"--output={output_path}",
        ],
        cwd="/workspaces/revops-funnel-reconciliation-engine",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert (
        "policy contract mismatch" in result.stderr.lower()
        or "policy contract mismatch" in result.stdout.lower()
    )
