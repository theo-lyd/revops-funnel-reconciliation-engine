from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_main():
    module_path = Path("scripts/ops/execute_rollback_playbook.py")
    spec = importlib.util.spec_from_file_location("execute_rollback_playbook", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise AssertionError("Unable to load execute_rollback_playbook module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


def _write_rollback_report(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "release_id": "release-cli",
                "rollback_actions": ["Disable promotion flag for subsequent runs"],
            }
        ),
        encoding="utf-8",
    )


def test_execute_rollback_playbook_cli_allows_authorized_actor(
    tmp_path: Path,
    monkeypatch,
) -> None:
    main = _load_main()
    rollback_report = tmp_path / "deployment_rollback.json"
    output = tmp_path / "deployment_rollback_execution.json"
    _write_rollback_report(rollback_report)

    monkeypatch.setenv("ROLLBACK_ALLOWED_ACTORS", "alice,bob")
    monkeypatch.setenv("GITHUB_ACTOR", "alice")
    monkeypatch.setattr(
        "sys.argv",
        [
            "execute_rollback_playbook.py",
            "--rollback-report",
            str(rollback_report),
            "--output",
            str(output),
            "--require-release-access",
        ],
    )

    result = main()
    assert result == 0
    assert output.exists()


def test_execute_rollback_playbook_cli_blocks_unauthorized_actor(
    tmp_path: Path,
    monkeypatch,
) -> None:
    main = _load_main()
    rollback_report = tmp_path / "deployment_rollback.json"
    _write_rollback_report(rollback_report)

    monkeypatch.setenv("ROLLBACK_ALLOWED_ACTORS", "alice,bob")
    monkeypatch.setenv("GITHUB_ACTOR", "mallory")
    monkeypatch.setattr(
        "sys.argv",
        [
            "execute_rollback_playbook.py",
            "--rollback-report",
            str(rollback_report),
            "--require-release-access",
        ],
    )

    try:
        main()
    except SystemExit as error:
        assert "blocked" in str(error)
    else:  # pragma: no cover
        raise AssertionError("Expected unauthorized actor to be blocked")
