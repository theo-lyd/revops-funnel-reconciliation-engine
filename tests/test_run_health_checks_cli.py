from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_module():
    module_path = Path("scripts/ops/run_health_checks.py")
    spec = importlib.util.spec_from_file_location("run_health_checks", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise AssertionError("Unable to load run_health_checks module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_run_health_checks_skipped_no_telemetry(tmp_path: Path, monkeypatch) -> None:
    module = _load_module()
    output = tmp_path / "health_report.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_health_checks.py",
            "--output",
            str(output),
        ],
    )

    result = module.main()
    assert result == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "ok"


def test_run_health_checks_fails_strict_without_telemetry(tmp_path: Path, monkeypatch) -> None:
    module = _load_module()
    output = tmp_path / "health_report.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_health_checks.py",
            "--strict-metrics",
            "--output",
            str(output),
        ],
    )

    result = module.main()
    assert result == 1
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "error"
    assert payload["strict_metrics"] is True


def test_run_health_checks_fails_strict_error_budget(tmp_path: Path, monkeypatch) -> None:
    module = _load_module()
    output = tmp_path / "health_report.json"

    monkeypatch.setattr(
        module,
        "fetch_table_freshness",
        lambda _: ("ok", "2020-01-01T00:00:00+00:00"),
    )
    monkeypatch.setattr(module, "fetch_job_metrics", lambda _: ("ok", 500.0))
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_health_checks.py",
            "--strict-error-budget",
            "--burn-rate-critical",
            "0.5",
            "--output",
            str(output),
        ],
    )

    result = module.main()
    assert result == 1
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["strict_error_budget"] is True
    assert payload["report"]["error_budget"]["status"] == "critical"
