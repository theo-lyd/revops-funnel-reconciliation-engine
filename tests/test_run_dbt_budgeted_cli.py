from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_module():
    module_path = Path("scripts/ops/run_dbt_budgeted.py")
    spec = importlib.util.spec_from_file_location("run_dbt_budgeted", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise AssertionError("Unable to load run_dbt_budgeted module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _Completed:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_run_dbt_budgeted_cli_applies_thread_cap(tmp_path: Path, monkeypatch) -> None:
    module = _load_module()
    output = tmp_path / "dbt_budget_report.json"

    captured: dict[str, object] = {}

    def _fake_run(command, cwd, check, capture_output, text, timeout):
        captured["command"] = command
        captured["cwd"] = cwd
        captured["timeout"] = timeout
        return _Completed(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(module.subprocess, "run", _fake_run)
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_dbt_budgeted.py",
            "--command",
            "build",
            "--environment",
            "production",
            "--threads",
            "9",
            "--max-threads-prod",
            "4",
            "--project-dir",
            ".",
            "--output",
            str(output),
        ],
    )

    result = module.main()
    assert result == 0
    assert output.exists()

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["effective_threads"] == 4
    assert payload["exit_code"] == 0
    assert captured["timeout"] == 1800
    assert "--threads" in captured["command"]


def test_run_dbt_budgeted_cli_timeout_exit_code(tmp_path: Path, monkeypatch) -> None:
    module = _load_module()
    output = tmp_path / "dbt_budget_report.json"

    def _timeout_run(command, cwd, check, capture_output, text, timeout):
        raise module.subprocess.TimeoutExpired(cmd=command, timeout=timeout)

    monkeypatch.setattr(module.subprocess, "run", _timeout_run)
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_dbt_budgeted.py",
            "--command",
            "test",
            "--environment",
            "local",
            "--project-dir",
            ".",
            "--output",
            str(output),
        ],
    )

    result = module.main()
    assert result == 124
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["timed_out"] is True
    assert payload["exit_code"] == 124
