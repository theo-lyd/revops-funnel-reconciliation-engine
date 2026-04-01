"""Run Phase 3 Batch 3.1 data quality checks against DuckDB models."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from revops_funnel.config import get_settings


@dataclass(frozen=True)
class QualityCheck:
    name: str
    sql: str


def ensure_audit_table(conn: Any) -> None:
    conn.execute("CREATE SCHEMA IF NOT EXISTS observability")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS observability.quality_audit (
            check_name VARCHAR,
            checked_at TIMESTAMP,
            failed_rows BIGINT,
            status VARCHAR,
            details VARCHAR
        )
        """
    )


def run_checks(conn: Any, checks: list[QualityCheck]) -> int:
    failure_count = 0
    for check in checks:
        failed_rows = conn.execute(check.sql).fetchone()[0]
        status = "failed" if failed_rows > 0 else "passed"
        if failed_rows > 0:
            failure_count += 1

        conn.execute(
            """
            INSERT INTO observability.quality_audit
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                check.name,
                datetime.now(timezone.utc),
                failed_rows,
                status,
                "Phase 3 Batch 3.1 baseline checks",
            ],
        )
        print(f"{check.name}: {status} (failed_rows={failed_rows})")

    return failure_count


def main() -> None:
    settings = get_settings()
    duckdb = importlib.import_module("duckdb")
    conn = duckdb.connect(settings.duckdb_path)

    ensure_audit_table(conn)

    checks = [
        QualityCheck(
            name="int_opportunity_enriched_opportunity_id_not_null",
            sql="""
            SELECT COUNT(*)
                        FROM analytics_silver_intermediate.int_opportunity_enriched
            WHERE opportunity_id IS NULL
            """,
        ),
        QualityCheck(
            name="int_opportunity_enriched_close_value_between_0_and_1m",
            sql="""
            SELECT COUNT(*)
                        FROM analytics_silver_intermediate.int_opportunity_enriched
            WHERE close_value IS NOT NULL
              AND (close_value < 0 OR close_value > 1000000)
            """,
        ),
        QualityCheck(
            name="int_opportunity_enriched_close_after_engage",
            sql="""
            SELECT COUNT(*)
                        FROM analytics_silver_intermediate.int_opportunity_enriched
            WHERE close_date IS NOT NULL
              AND engage_date IS NOT NULL
              AND close_date < engage_date
            """,
        ),
    ]

    failures = run_checks(conn, checks)
    conn.close()

    if failures > 0:
        raise SystemExit(1)

    print("All data quality checks passed.")


if __name__ == "__main__":
    main()
