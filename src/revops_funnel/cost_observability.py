"""Query-cost observability and warehouse spend-attribution helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class QueryCostEntry:
    query_id: str
    query_tag: str
    warehouse_name: str
    user_name: str
    elapsed_seconds: float
    bytes_scanned: int
    credits_used: float
    started_at_utc: str


def normalize_query_tag(raw_tag: str) -> str:
    normalized = raw_tag.strip()
    return normalized if normalized else "un-tagged"


def aggregate_query_cost_attribution(entries: list[QueryCostEntry]) -> dict[str, object]:
    total_queries = len(entries)
    total_elapsed_seconds = sum(max(0.0, entry.elapsed_seconds) for entry in entries)
    total_bytes_scanned = sum(max(0, int(entry.bytes_scanned)) for entry in entries)
    total_credits_used = sum(max(0.0, float(entry.credits_used)) for entry in entries)

    by_tag: dict[str, dict[str, float | int | str]] = {}
    by_warehouse: dict[str, dict[str, float | int | str]] = {}

    for entry in entries:
        tag_key = normalize_query_tag(entry.query_tag)
        warehouse_key = entry.warehouse_name.strip() or "unknown"

        tag_record = by_tag.setdefault(
            tag_key,
            {
                "query_tag": tag_key,
                "query_count": 0,
                "elapsed_seconds": 0.0,
                "bytes_scanned": 0,
                "credits_used": 0.0,
            },
        )
        tag_record["query_count"] = int(tag_record["query_count"]) + 1
        tag_record["elapsed_seconds"] = float(tag_record["elapsed_seconds"]) + max(
            0.0, entry.elapsed_seconds
        )
        tag_record["bytes_scanned"] = int(tag_record["bytes_scanned"]) + max(
            0, int(entry.bytes_scanned)
        )
        tag_record["credits_used"] = float(tag_record["credits_used"]) + max(
            0.0, float(entry.credits_used)
        )

        warehouse_record = by_warehouse.setdefault(
            warehouse_key,
            {
                "warehouse_name": warehouse_key,
                "query_count": 0,
                "elapsed_seconds": 0.0,
                "bytes_scanned": 0,
                "credits_used": 0.0,
            },
        )
        warehouse_record["query_count"] = int(warehouse_record["query_count"]) + 1
        warehouse_record["elapsed_seconds"] = float(warehouse_record["elapsed_seconds"]) + max(
            0.0, entry.elapsed_seconds
        )
        warehouse_record["bytes_scanned"] = int(warehouse_record["bytes_scanned"]) + max(
            0, int(entry.bytes_scanned)
        )
        warehouse_record["credits_used"] = float(warehouse_record["credits_used"]) + max(
            0.0, float(entry.credits_used)
        )

    tag_rows = sorted(
        by_tag.values(),
        key=lambda row: float(row["credits_used"]),
        reverse=True,
    )
    warehouse_rows = sorted(
        by_warehouse.values(),
        key=lambda row: float(row["credits_used"]),
        reverse=True,
    )

    for row in tag_rows:
        credits = float(row["credits_used"])
        row["credits_share"] = (credits / total_credits_used) if total_credits_used > 0 else 0.0

    for row in warehouse_rows:
        credits = float(row["credits_used"])
        row["credits_share"] = (credits / total_credits_used) if total_credits_used > 0 else 0.0

    top_queries = sorted(
        entries,
        key=lambda entry: (float(entry.credits_used), float(entry.elapsed_seconds)),
        reverse=True,
    )[:20]

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "totals": {
            "query_count": total_queries,
            "elapsed_seconds": total_elapsed_seconds,
            "bytes_scanned": total_bytes_scanned,
            "credits_used": total_credits_used,
        },
        "attribution_by_query_tag": tag_rows,
        "attribution_by_warehouse": warehouse_rows,
        "top_expensive_queries": [asdict(item) for item in top_queries],
    }


@dataclass(frozen=True)
class CostRegressionThresholds:
    max_credits_regression_pct: float
    max_elapsed_regression_pct: float


def _safe_float(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


def _percent_change(current: float, baseline: float) -> float | None:
    if baseline <= 0:
        return None
    return ((current - baseline) / baseline) * 100.0


def _query_tag_totals(report: dict[str, object]) -> dict[str, dict[str, float]]:
    rows = report.get("attribution_by_query_tag")
    if not isinstance(rows, list):
        return {}

    totals: dict[str, dict[str, float]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw_tag = str(row.get("query_tag", ""))
        tag = normalize_query_tag(raw_tag)
        totals[tag] = {
            "credits_used": _safe_float(row.get("credits_used")),
            "elapsed_seconds": _safe_float(row.get("elapsed_seconds")),
            "query_count": _safe_float(row.get("query_count")),
        }
    return totals


def detect_query_cost_regressions(
    current_report: dict[str, object],
    baseline_report: dict[str, object],
    thresholds: CostRegressionThresholds,
) -> dict[str, object]:
    current_totals = current_report.get("totals")
    baseline_totals = baseline_report.get("totals")

    if not isinstance(current_totals, dict) or not isinstance(baseline_totals, dict):
        return {
            "status": "error",
            "detail": "current and baseline reports must include totals",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "thresholds": asdict(thresholds),
            "overall_regressions": [],
            "query_tag_regressions": [],
            "new_query_tags": [],
        }

    metrics = [
        ("credits_used", thresholds.max_credits_regression_pct),
        ("elapsed_seconds", thresholds.max_elapsed_regression_pct),
    ]

    overall_regressions: list[dict[str, object]] = []
    for metric, threshold_pct in metrics:
        current_value = _safe_float(current_totals.get(metric))
        baseline_value = _safe_float(baseline_totals.get(metric))
        change_pct = _percent_change(current_value, baseline_value)
        if change_pct is None:
            continue
        if change_pct > threshold_pct:
            overall_regressions.append(
                {
                    "scope": "totals",
                    "metric": metric,
                    "baseline_value": baseline_value,
                    "current_value": current_value,
                    "change_pct": change_pct,
                    "threshold_pct": threshold_pct,
                }
            )

    current_tags = _query_tag_totals(current_report)
    baseline_tags = _query_tag_totals(baseline_report)

    query_tag_regressions: list[dict[str, object]] = []
    new_query_tags: list[str] = []

    for tag, current_values in current_tags.items():
        baseline_values = baseline_tags.get(tag)
        if baseline_values is None:
            new_query_tags.append(tag)
            continue

        for metric, threshold_pct in metrics:
            current_value = _safe_float(current_values.get(metric))
            baseline_value = _safe_float(baseline_values.get(metric))
            change_pct = _percent_change(current_value, baseline_value)
            if change_pct is None:
                continue
            if change_pct > threshold_pct:
                query_tag_regressions.append(
                    {
                        "scope": "query_tag",
                        "query_tag": tag,
                        "metric": metric,
                        "baseline_value": baseline_value,
                        "current_value": current_value,
                        "change_pct": change_pct,
                        "threshold_pct": threshold_pct,
                    }
                )

    status = "ok"
    if overall_regressions or query_tag_regressions:
        status = "regression-detected"

    return {
        "status": status,
        "detail": "",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "thresholds": asdict(thresholds),
        "overall_regressions": overall_regressions,
        "query_tag_regressions": query_tag_regressions,
        "new_query_tags": sorted(new_query_tags),
    }
