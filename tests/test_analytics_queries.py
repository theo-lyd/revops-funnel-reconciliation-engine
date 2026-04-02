from __future__ import annotations

from datetime import date

import pandas as pd

from revops_funnel.analytics_queries import (
    build_query_sql,
    build_template_catalog,
    heuristic_resolution,
    resolve_prompt_to_template,
    validate_columns,
)


def test_build_template_catalog_contains_gold_models() -> None:
    templates = build_template_catalog("analytics_gold")
    assert set(templates) == {
        "Executive Monthly Overview",
        "Public Sector Monthly Overview",
        "Sales Team Performance",
        "Leakage Reason Analysis",
        "Pipeline Velocity",
    }


def test_build_query_sql_adds_filters_and_limit() -> None:
    template = build_template_catalog("analytics_gold")["Executive Monthly Overview"]
    sql = build_query_sql(
        template=template,
        office_filter=["London", "New York"],
        start=date(2026, 1, 1),
        end=date(2026, 3, 31),
        source="DuckDB",
        max_query_rows=250,
    )

    assert "regional_office in ('London', 'New York')" in sql
    assert "metric_month::date between date '2026-01-01' and date '2026-03-31'" in sql
    assert sql.strip().endswith("limit 250")


def test_heuristic_resolution_prefers_leakage_template() -> None:
    resolution = heuristic_resolution(
        "Show leakage for stalled deals in London",
        ["London", "Paris"],
    )
    assert resolution.template_key == "Leakage Reason Analysis"
    assert resolution.offices == ["London"]


def test_resolve_prompt_to_template_falls_back_without_api_key() -> None:
    resolution = resolve_prompt_to_template(
        prompt="Show team performance in London",
        templates=list(build_template_catalog("analytics_gold").keys()),
        offices=["London", "Paris"],
        api_key="",
        model="gpt-4o-mini",
        max_tokens=100,
    )

    assert resolution.mode == "heuristic"
    assert resolution.template_key == "Sales Team Performance"
    assert resolution.offices == ["London"]


def test_validate_columns_reports_missing_fields() -> None:
    frame = pd.DataFrame({"metric_month": ["2026-01-01"], "regional_office": ["London"]})
    missing = validate_columns(frame, {"metric_month", "regional_office", "win_rate"})
    assert missing == ["win_rate"]


def test_heuristic_resolution_prefers_public_sector_template() -> None:
    resolution = heuristic_resolution(
        "Show public sector government funnel performance in Paris",
        ["London", "Paris"],
    )
    assert resolution.template_key == "Public Sector Monthly Overview"
    assert resolution.offices == ["Paris"]
