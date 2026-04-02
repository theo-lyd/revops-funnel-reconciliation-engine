from __future__ import annotations

import importlib.util
import json
from pathlib import Path


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
