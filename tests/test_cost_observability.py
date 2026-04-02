from __future__ import annotations

from revops_funnel.cost_observability import (
    CostRegressionThresholds,
    QueryCostEntry,
    aggregate_query_cost_attribution,
    detect_query_cost_regressions,
)


def test_aggregate_query_cost_attribution_totals_and_grouping() -> None:
    entries = [
        QueryCostEntry(
            query_id="q1",
            query_tag="dbt-build",
            warehouse_name="WH_XS",
            user_name="svc",
            elapsed_seconds=10.0,
            bytes_scanned=100,
            credits_used=0.4,
            started_at_utc="2026-04-02T00:00:00+00:00",
        ),
        QueryCostEntry(
            query_id="q2",
            query_tag="dbt-build",
            warehouse_name="WH_XS",
            user_name="svc",
            elapsed_seconds=20.0,
            bytes_scanned=200,
            credits_used=0.6,
            started_at_utc="2026-04-02T00:01:00+00:00",
        ),
        QueryCostEntry(
            query_id="q3",
            query_tag="dbt-test",
            warehouse_name="WH_SM",
            user_name="svc",
            elapsed_seconds=15.0,
            bytes_scanned=120,
            credits_used=0.5,
            started_at_utc="2026-04-02T00:02:00+00:00",
        ),
    ]

    payload = aggregate_query_cost_attribution(entries)

    totals = payload["totals"]
    assert totals["query_count"] == 3
    assert totals["elapsed_seconds"] == 45.0
    assert totals["bytes_scanned"] == 420
    assert totals["credits_used"] == 1.5

    by_tag = payload["attribution_by_query_tag"]
    assert by_tag[0]["query_tag"] == "dbt-build"
    assert by_tag[0]["query_count"] == 2
    assert by_tag[0]["credits_used"] == 1.0


def test_aggregate_query_cost_attribution_handles_empty_entries() -> None:
    payload = aggregate_query_cost_attribution([])
    assert payload["totals"]["query_count"] == 0
    assert payload["attribution_by_query_tag"] == []
    assert payload["attribution_by_warehouse"] == []
    assert payload["top_expensive_queries"] == []


def test_detect_query_cost_regressions_flags_threshold_breaches() -> None:
    current = {
        "status": "ok",
        "totals": {
            "credits_used": 12.0,
            "elapsed_seconds": 100.0,
        },
        "attribution_by_query_tag": [
            {"query_tag": "dbt-build", "credits_used": 9.0, "elapsed_seconds": 70.0},
            {"query_tag": "dbt-test", "credits_used": 3.0, "elapsed_seconds": 30.0},
        ],
    }
    baseline = {
        "status": "ok",
        "totals": {
            "credits_used": 9.0,
            "elapsed_seconds": 85.0,
        },
        "attribution_by_query_tag": [
            {"query_tag": "dbt-build", "credits_used": 6.0, "elapsed_seconds": 55.0},
            {"query_tag": "dbt-test", "credits_used": 3.0, "elapsed_seconds": 30.0},
        ],
    }

    result = detect_query_cost_regressions(
        current,
        baseline,
        CostRegressionThresholds(
            max_credits_regression_pct=20.0,
            max_elapsed_regression_pct=20.0,
        ),
    )

    assert result["status"] == "regression-detected"
    assert len(result["overall_regressions"]) == 1
    assert len(result["query_tag_regressions"]) == 2


def test_detect_query_cost_regressions_blocks_new_query_tags_and_tracks_layers() -> None:
    current = {
        "status": "ok",
        "metadata": {"release_id": "current-release"},
        "totals": {"credits_used": 14.0, "elapsed_seconds": 120.0},
        "attribution_by_query_tag": [
            {"query_tag": "dbt-build", "credits_used": 8.0, "elapsed_seconds": 60.0},
            {"query_tag": "dbt-test", "credits_used": 3.0, "elapsed_seconds": 25.0},
            {"query_tag": "dbt-new", "credits_used": 3.0, "elapsed_seconds": 35.0},
        ],
        "attribution_by_transformation_layer": [
            {"layer": "staging", "credits_used": 4.0, "elapsed_seconds": 20.0},
            {"layer": "marts", "credits_used": 10.0, "elapsed_seconds": 100.0},
        ],
        "attribution_by_warehouse": [
            {"warehouse_name": "WH_XS", "credits_used": 14.0, "elapsed_seconds": 120.0},
        ],
    }
    baseline = {
        "status": "ok",
        "metadata": {"release_id": "baseline-release"},
        "totals": {"credits_used": 10.0, "elapsed_seconds": 100.0},
        "attribution_by_query_tag": [
            {"query_tag": "dbt-build", "credits_used": 6.0, "elapsed_seconds": 55.0},
            {"query_tag": "dbt-test", "credits_used": 4.0, "elapsed_seconds": 45.0},
        ],
        "attribution_by_transformation_layer": [
            {"layer": "staging", "credits_used": 3.0, "elapsed_seconds": 20.0},
            {"layer": "marts", "credits_used": 7.0, "elapsed_seconds": 80.0},
        ],
        "attribution_by_warehouse": [
            {"warehouse_name": "WH_XS", "credits_used": 10.0, "elapsed_seconds": 100.0},
        ],
    }

    result = detect_query_cost_regressions(
        current,
        baseline,
        CostRegressionThresholds(
            max_credits_regression_pct=20.0,
            max_elapsed_regression_pct=20.0,
            max_new_query_tags=0,
        ),
    )

    assert result["status"] == "regression-detected"
    assert result["summary"]["blocked"] is True
    assert result["summary"]["new_query_tag_count"] == 1
    assert result["summary"]["new_query_tag_blocked"] is True
    assert result["current_metadata"]["release_id"] == "current-release"
    assert result["baseline_metadata"]["release_id"] == "baseline-release"
    assert result["transformation_layer_regressions"]
    assert result["warehouse_regressions"]
