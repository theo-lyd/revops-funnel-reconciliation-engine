from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import requests


def _load_main():
    module_path = Path("scripts/ops/dispatch_rollback_incident.py")
    spec = importlib.util.spec_from_file_location("dispatch_rollback_incident", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise AssertionError("Unable to load dispatch_rollback_incident module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


def _write_incident_payload(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"release_id": "release-cli", "environment": "production"}),
        encoding="utf-8",
    )


def _load_execute_main():
    module_path = Path("scripts/ops/execute_rollback_playbook.py")
    spec = importlib.util.spec_from_file_location("execute_rollback_playbook", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise AssertionError("Unable to load execute_rollback_playbook module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


def test_dispatch_rollback_incident_cli_non_strict_skip(
    tmp_path: Path,
    monkeypatch,
) -> None:
    main = _load_main()
    payload = tmp_path / "rollback_incident_payload.json"
    output = tmp_path / "rollback_incident_dispatch.json"
    dead_letter = tmp_path / "rollback_incident_dead_letter.json"
    _write_incident_payload(payload)

    monkeypatch.setattr(
        "sys.argv",
        [
            "dispatch_rollback_incident.py",
            "--incident-payload",
            str(payload),
            "--output",
            str(output),
            "--dead-letter-output",
            str(dead_letter),
        ],
    )

    result = main()
    assert result == 0
    assert output.exists()
    assert dead_letter.exists() is False


def test_dispatch_rollback_incident_cli_strict_fails_on_skip(
    tmp_path: Path,
    monkeypatch,
) -> None:
    main = _load_main()
    payload = tmp_path / "rollback_incident_payload.json"
    _write_incident_payload(payload)

    monkeypatch.setattr(
        "sys.argv",
        [
            "dispatch_rollback_incident.py",
            "--incident-payload",
            str(payload),
            "--strict",
        ],
    )

    try:
        main()
    except SystemExit as error:
        assert "strict mode failed" in str(error)
    else:  # pragma: no cover
        raise AssertionError("Expected strict mode to fail when dispatch is skipped")


def test_cli_artifact_lifecycle_rollback_to_dead_letter(
    tmp_path: Path,
    monkeypatch,
) -> None:
    execute_main = _load_execute_main()
    dispatch_main = _load_main()

    monkeypatch.chdir(tmp_path)
    rollback_report = tmp_path / "deployment_rollback.json"
    rollback_report.write_text(
        json.dumps(
            {
                "release_id": "release-lifecycle",
                "environment": "production",
                "rollback_actions": [
                    "Disable promotion flag for subsequent runs",
                    "Attach rollback report to incident channel/ticket",
                ],
            }
        ),
        encoding="utf-8",
    )

    rollback_execution = tmp_path / "deployment_rollback_execution.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "execute_rollback_playbook.py",
            "--rollback-report",
            str(rollback_report),
            "--execute",
            "--output",
            str(rollback_execution),
        ],
    )
    assert execute_main() == 0

    incident_payload = tmp_path / "artifacts/promotions/rollback_incident_payload.json"
    dispatch_output = tmp_path / "rollback_incident_dispatch.json"
    dead_letter = tmp_path / "rollback_incident_dead_letter.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "dispatch_rollback_incident.py",
            "--incident-payload",
            str(incident_payload),
            "--webhook-url",
            "https://example.com/webhook",
            "--max-attempts",
            "2",
            "--backoff-seconds",
            "0",
            "--dead-letter-output",
            str(dead_letter),
            "--output",
            str(dispatch_output),
        ],
    )

    with patch(
        "revops_funnel.deployment_ops.requests.post",
        side_effect=requests.RequestException("forced failure"),
    ):
        assert dispatch_main() == 0

    dispatch_payload = json.loads(dispatch_output.read_text(encoding="utf-8"))
    dead_letter_payload = json.loads(dead_letter.read_text(encoding="utf-8"))
    assert dispatch_payload["dispatch_status"] == "failed"
    assert dead_letter_payload["incident_webhook_url"] == "redacted"
    assert dead_letter_payload["correlation_id"]
