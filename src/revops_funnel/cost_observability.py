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
