"""Load CRM CSV files from data/raw/crm into bronze_raw DuckDB tables."""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path

from revops_funnel.config import get_settings

CRM_TABLES = ["accounts", "products", "sales_teams", "sales_pipeline"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-dir",
        default="data/raw/crm",
        help="Directory containing raw CRM CSV files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()

    raw_dir = Path(args.raw_dir)
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

    duckdb = importlib.import_module("duckdb")
    conn = duckdb.connect(settings.duckdb_path)
    conn.execute("CREATE SCHEMA IF NOT EXISTS bronze_raw")

    for table_name in CRM_TABLES:
        csv_path = raw_dir / f"{table_name}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing source file: {csv_path}")

        conn.execute(f"DROP TABLE IF EXISTS bronze_raw.{table_name}")
        conn.execute(
            f"""
            CREATE TABLE bronze_raw.{table_name} AS
            SELECT *
            FROM read_csv_auto(?, header = true)
            """,
            [str(csv_path)],
        )
        print(f"Loaded bronze_raw.{table_name} from {csv_path}")

    conn.close()


if __name__ == "__main__":
    main()
