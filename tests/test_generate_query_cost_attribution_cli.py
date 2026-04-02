from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from revops_funnel.cost_observability import QueryCostEntry


def _load_module():
    module_path = Path("scripts/ops/generate_query_cost_attribution.py")
    spec = importlib.util.spec_from_file_location("generate_query_cost_attribution", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise AssertionError("Unable to load generate_query_cost_attribution module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_generate_query_cost_attribution_cli_skipped_mode(tmp_path: Path, monkeypatch) -> None:
    module = _load_module()
    output = tmp_path / "query_cost_report.json"

    monkeypatch.setattr(
        module,
        "fetch_query_cost_entries",
        lambda args: ("skipped", [], "missing env"),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_query_cost_attribution.py",
            "--output",
            str(output),
        ],
    )

    result = module.main()
    assert result == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "skipped"


def test_generate_query_cost_attribution_cli_success_mode(tmp_path: Path, monkeypatch) -> None:
    module = _load_module()
    output = tmp_path / "query_cost_report.json"
    entries = [
        QueryCostEntry(
            query_id="q1",
            query_tag="dbt-build",
            warehouse_name="WH_XS",
            user_name="svc",
            elapsed_seconds=12.0,
            bytes_scanned=200,
            credits_used=0.8,
            started_at_utc="2026-04-02T00:00:00+00:00",
        )
    ]

    monkeypatch.setattr(
        module,
        "fetch_query_cost_entries",
        lambda args: ("ok", entries, ""),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_query_cost_attribution.py",
            "--output",
            str(output),
        ],
    )

    result = module.main()
    assert result == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "ok"
    assert payload["totals"]["query_count"] == 1
