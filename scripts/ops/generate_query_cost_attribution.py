#!/usr/bin/env python3
"""Generate query-cost observability and warehouse spend-attribution artifacts."""

from __future__ import annotations

import argparse
import importlib
import json
import os

from revops_funnel.artifacts import write_json_artifact
from revops_funnel.cost_observability import QueryCostEntry, aggregate_query_cost_attribution
from revops_funnel.snowflake_auth import (
    build_snowflake_connector_auth_kwargs,
    missing_required_snowflake_env,
    snowflake_auth_from_env,
)

DEFAULT_OUTPUT = os.getenv(
    "COST_ATTRIBUTION_REPORT_PATH",
    "artifacts/performance/query_cost_attribution_report.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lookback-hours",
        type=int,
        default=int(os.getenv("COST_LOOKBACK_HOURS", "24")),
        help="Snowflake query-history lookback window in hours.",
    )
    parser.add_argument(
        "--max-queries",
        type=int,
        default=int(os.getenv("COST_MAX_QUERIES", "2000")),
        help="Maximum query-history rows to inspect.",
    )
    parser.add_argument(
        "--query-tag-prefix",
        default=os.getenv("COST_QUERY_TAG_PREFIX", ""),
        help="Optional query_tag prefix filter for attribution scope.",
    )
    parser.add_argument(
        "--strict-snowflake",
        action="store_true",
        help="Fail when Snowflake credentials/connector are unavailable.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Output path for cost-attribution artifact.",
    )
    return parser.parse_args()


def _build_query(lookback_hours: int, max_queries: int, query_tag_prefix: str) -> str:
    lookback = max(1, int(lookback_hours))
    limit = max(1, int(max_queries))
    tag_clause = ""
    tag_prefix = query_tag_prefix.strip()
    if tag_prefix:
        escaped = tag_prefix.replace("'", "''")
        tag_clause = f" and coalesce(query_tag, '') like '{escaped}%'"

    return f"""
        select
            query_id,
            coalesce(query_tag, 'un-tagged') as query_tag,
            coalesce(warehouse_name, 'unknown') as warehouse_name,
            coalesce(user_name, 'unknown') as user_name,
            coalesce(total_elapsed_time, 0) / 1000.0 as elapsed_seconds,
            coalesce(bytes_scanned, 0) as bytes_scanned,
            (
                coalesce(credits_used_cloud_services, 0)
                + coalesce(credits_used_compute, 0)
            ) as credits_used,
            to_varchar(start_time, 'YYYY-MM-DD"T"HH24:MI:SS.FF3TZHTZM') as started_at_utc
        from table(information_schema.query_history(
            dateadd('hour', -{lookback}, current_timestamp()),
            current_timestamp()
        ))
        where query_text is not null
        {tag_clause}
        order by start_time desc
        limit {limit}
    """


def fetch_query_cost_entries(args: argparse.Namespace) -> tuple[str, list[QueryCostEntry], str]:
    auth = snowflake_auth_from_env()
    required = ["SNOWFLAKE_ROLE", "SNOWFLAKE_DATABASE", "SNOWFLAKE_WAREHOUSE"]
    missing = missing_required_snowflake_env(auth) + [key for key in required if not os.getenv(key)]
    if missing:
        message = f"missing env vars: {', '.join(missing)}"
        if args.strict_snowflake:
            raise SystemExit(f"Cost attribution failed in strict mode: {message}")
        return "skipped", [], message

    try:
        connector = importlib.import_module("snowflake.connector")
    except ModuleNotFoundError as error:
        if args.strict_snowflake:
            raise SystemExit(
                "Cost attribution failed in strict mode: snowflake connector missing"
            ) from error
        return "skipped", [], "snowflake connector unavailable"

    conn = connector.connect(
        account=auth.account,
        user=auth.user,
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "analytics"),
        **build_snowflake_connector_auth_kwargs(auth),
    )

    query = _build_query(args.lookback_hours, args.max_queries, args.query_tag_prefix)
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    entries = [
        QueryCostEntry(
            query_id=str(row[0] or ""),
            query_tag=str(row[1] or "un-tagged"),
            warehouse_name=str(row[2] or "unknown"),
            user_name=str(row[3] or "unknown"),
            elapsed_seconds=float(row[4] or 0.0),
            bytes_scanned=int(row[5] or 0),
            credits_used=float(row[6] or 0.0),
            started_at_utc=str(row[7] or ""),
        )
        for row in rows
    ]
    if not entries:
        return "no-data", [], "no query history rows returned"
    return "ok", entries, ""


def main() -> int:
    args = parse_args()
    status, entries, detail = fetch_query_cost_entries(args)

    payload: dict[str, object] = {
        "status": status,
        "strict_mode": bool(args.strict_snowflake),
        "lookback_hours": int(max(1, args.lookback_hours)),
        "max_queries": int(max(1, args.max_queries)),
        "query_tag_prefix": args.query_tag_prefix,
        "detail": detail,
    }
    if status == "ok":
        payload.update(aggregate_query_cost_attribution(entries))

    write_json_artifact(args.output, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if status in {"ok", "no-data", "skipped"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
