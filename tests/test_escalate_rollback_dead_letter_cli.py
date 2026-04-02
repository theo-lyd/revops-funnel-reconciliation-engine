from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import requests


def _load_main():
    module_path = Path("scripts/ops/escalate_rollback_dead_letter.py")
    spec = importlib.util.spec_from_file_location("escalate_rollback_dead_letter", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise AssertionError("Unable to load escalate_rollback_dead_letter module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


def _write_dead_letter(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"release_id": "release-cli", "environment": "production"}),
        encoding="utf-8",
    )


def test_escalate_dead_letter_cli_non_strict_skip_no_dead_letter(
    tmp_path: Path,
    monkeypatch,
) -> None:
    main = _load_main()
    dead_letter = tmp_path / "missing_dead_letter.json"
    output = tmp_path / "rollback_dead_letter_escalation.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "escalate_rollback_dead_letter.py",
            "--dead-letter",
            str(dead_letter),
            "--output",
            str(output),
        ],
    )

    result = main()
    assert result == 0
    assert output.exists()


def test_escalate_dead_letter_cli_strict_fails_when_not_sent(
    tmp_path: Path,
    monkeypatch,
) -> None:
    main = _load_main()
    dead_letter = tmp_path / "rollback_incident_dead_letter.json"
    _write_dead_letter(dead_letter)

    monkeypatch.setattr(
        "sys.argv",
        [
            "escalate_rollback_dead_letter.py",
            "--dead-letter",
            str(dead_letter),
            "--strict",
        ],
    )

    try:
        main()
    except SystemExit as error:
        assert "strict mode failed" in str(error)
    else:  # pragma: no cover
        raise AssertionError("Expected strict mode to fail when escalation is not sent")


def test_escalation_cli_retries_then_succeeds_from_dead_letter(
    tmp_path: Path,
    monkeypatch,
) -> None:
    main = _load_main()
    dead_letter = tmp_path / "rollback_incident_dead_letter.json"
    output = tmp_path / "rollback_dead_letter_escalation.json"

    dead_letter.write_text(
        json.dumps(
            {
                "contract_version": "phase7.v2",
                "correlation_id": "corr-123",
                "release_id": "release-cli",
                "environment": "production",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "escalate_rollback_dead_letter.py",
            "--dead-letter",
            str(dead_letter),
            "--webhook-url",
            "https://example.com/escalation",
            "--max-attempts",
            "2",
            "--backoff-seconds",
            "0",
            "--output",
            str(output),
        ],
    )

    class _SuccessResponse:
        status_code = 200
        text = "ok"

    with patch(
        "revops_funnel.deployment_ops.requests.post",
        side_effect=[requests.RequestException("temporary"), _SuccessResponse()],
    ):
        assert main() == 0

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["escalation_status"] == "sent"
    assert report["attempt_count"] == 2
    assert report["correlation_id"] == "corr-123"
