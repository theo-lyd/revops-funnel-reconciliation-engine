"""Export sanitized Bronze datasets from DuckDB to Parquet files."""

from __future__ import annotations

import argparse
import hashlib
import importlib
from pathlib import Path

from revops_funnel.config import get_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        default="data/processed/bronze",
        help="Output directory for parquet exports.",
    )
    return parser.parse_args()


def hash_text(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()


def main() -> None:
    args = parse_args()
    settings = get_settings()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    duckdb = importlib.import_module("duckdb")
    conn = duckdb.connect(settings.duckdb_path)

    sales_teams = conn.execute("SELECT * FROM bronze_raw.sales_teams").fetchall()
    sales_team_cols = [desc[0] for desc in conn.description]
    sales_team_records = [dict(zip(sales_team_cols, row)) for row in sales_teams]

    conn.execute("DROP TABLE IF EXISTS bronze_raw._sales_teams_sanitized")
    conn.execute(
        """
        CREATE TABLE bronze_raw._sales_teams_sanitized (
            sales_agent_hash VARCHAR,
            manager_hash VARCHAR,
            regional_office VARCHAR
        )
        """
    )
    conn.executemany(
        """
        INSERT INTO bronze_raw._sales_teams_sanitized VALUES (?, ?, ?)
        """,
        [
            (
                hash_text(rec.get("sales_agent")),
                hash_text(rec.get("manager")),
                rec.get("regional_office"),
            )
            for rec in sales_team_records
        ],
    )

    conn.execute(
        """
        COPY (
            SELECT
                opportunity_id,
                sales_agent,
                product,
                account,
                deal_stage,
                engage_date,
                close_date,
                close_value,
                'USD' AS currency_iso
            FROM bronze_raw.sales_pipeline
        ) TO ? (FORMAT PARQUET)
        """,
        [str(out_dir / "sales_pipeline.parquet")],
    )

    for table_name in ["accounts", "products", "marketing_leads"]:
        conn.execute(
            f"""
            COPY bronze_raw.{table_name}
            TO ? (FORMAT PARQUET)
            """,
            [str(out_dir / f"{table_name}.parquet")],
        )

    conn.execute(
        """
        COPY bronze_raw._sales_teams_sanitized
        TO ? (FORMAT PARQUET)
        """,
        [str(out_dir / "sales_teams_sanitized.parquet")],
    )

    conn.execute("DROP TABLE IF EXISTS bronze_raw._sales_teams_sanitized")
    conn.close()

    print(f"Sanitized bronze parquet exports written to {out_dir}")


if __name__ == "__main__":
    main()
