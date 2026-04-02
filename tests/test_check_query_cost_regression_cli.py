from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_module():
    module_path = Path("scripts/ops/check_query_cost_regression.py")
    spec = importlib.util.spec_from_file_location("check_query_cost_regression", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise AssertionError("Unable to load check_query_cost_regression module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_check_query_cost_regression_skips_without_baseline(tmp_path: Path, monkeypatch) -> None:
    module = _load_module()
    current = tmp_path / "current.json"
    output = tmp_path / "regression.json"

    current.write_text(
        json.dumps({"status": "ok", "totals": {"credits_used": 1.0, "elapsed_seconds": 1.0}}),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "check_query_cost_regression.py",
            "--current-report",
            str(current),
            "--baseline-report",
            str(tmp_path / "missing_baseline.json"),
            "--output",
            str(output),
        ],
    )

    result = module.main()
    assert result == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "skipped"


def test_check_query_cost_regression_fails_on_detected_regression(
    tmp_path: Path, monkeypatch
) -> None:
    module = _load_module()
    current = tmp_path / "current.json"
    baseline = tmp_path / "baseline.json"
    output = tmp_path / "regression.json"

    current.write_text(
        json.dumps(
            {
                "status": "ok",
                "totals": {"credits_used": 11.0, "elapsed_seconds": 90.0},
                "attribution_by_query_tag": [
                    {
                        "query_tag": "dbt-build",
                        "credits_used": 8.0,
                        "elapsed_seconds": 60.0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    baseline.write_text(
        json.dumps(
            {
                "status": "ok",
                "totals": {"credits_used": 8.0, "elapsed_seconds": 70.0},
                "attribution_by_query_tag": [
                    {
                        "query_tag": "dbt-build",
                        "credits_used": 5.0,
                        "elapsed_seconds": 45.0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "check_query_cost_regression.py",
            "--current-report",
            str(current),
            "--baseline-report",
            str(baseline),
            "--max-credits-regression-pct",
            "20",
            "--max-elapsed-regression-pct",
            "20",
            "--output",
            str(output),
        ],
    )

    result = module.main()
    assert result == 1
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "regression-detected"
