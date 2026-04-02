from __future__ import annotations

from pathlib import Path

from revops_funnel.deployment_ops import (
    build_dbt_selector,
    create_deployment_promotion_report,
    refresh_runtime_caches,
    write_cache_refresh_report,
)


def test_build_dbt_selector_expands_downstream_layers() -> None:
    selector = build_dbt_selector([Path("dbt/models/staging/crm/example.sql")])
    assert selector == "path:models/staging path:models/intermediate path:models/marts"


def test_build_dbt_selector_defaults_when_no_dbt_changes() -> None:
    selector = build_dbt_selector([Path("README.md")])
    assert selector == "path:models/staging path:models/intermediate path:models/marts"


def test_refresh_runtime_caches_recreates_directories(tmp_path: Path) -> None:
    cache_a = tmp_path / "streamlit-cache"
    cache_b = tmp_path / "artifact-cache"
    cache_a.mkdir()
    cache_b.mkdir()
    (cache_a / "stale.txt").write_text("stale", encoding="utf-8")

    report = refresh_runtime_caches([cache_a, cache_b])

    assert cache_a.exists()
    assert cache_b.exists()
    assert report.refreshed_paths == [str(cache_a), str(cache_b)]


def test_create_deployment_promotion_report_requires_passed_parity(tmp_path: Path) -> None:
    parity_report = tmp_path / "parity.json"
    cache_report = tmp_path / "cache.json"
    output = tmp_path / "promotion.json"
    parity_report.write_text('{"status": "passed"}', encoding="utf-8")
    cache_report.write_text(
        (
            '{"refreshed_at_utc": "2026-04-01T00:00:00+00:00", '
            '"refreshed_paths": [".streamlit/cache"]}'
        ),
        encoding="utf-8",
    )

    report = create_deployment_promotion_report(
        release_id="release-123",
        selector="path:models/marts",
        parity_report_path=parity_report,
        cache_refresh_report_path=cache_report,
        source_base_ref="origin/master",
        git_commit_sha="abc123",
        workflow_run_id="run-99",
        output_path=output,
    )

    assert output.exists()
    assert report.release_id == "release-123"
    assert report.parity_status == "passed"
    assert report.git_commit_sha == "abc123"
    assert report.workflow_run_id == "run-99"
    assert report.release_gate_status == "passed"
    assert report.parity_report_sha256
    assert report.cache_refresh_report_sha256


def test_write_cache_refresh_report_creates_json(tmp_path: Path) -> None:
    cache_a = tmp_path / "cache-a"
    cache_b = tmp_path / "cache-b"
    report = refresh_runtime_caches([cache_a, cache_b])
    output = tmp_path / "cache-refresh.json"

    write_cache_refresh_report(report, output)

    assert output.exists()
