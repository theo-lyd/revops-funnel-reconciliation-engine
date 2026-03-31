"""Load synthetic lead JSONL events into bronze_raw.marketing_leads."""

from __future__ import annotations

import argparse
import hashlib
import importlib
from pathlib import Path

from revops_funnel.config import get_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--jsonl",
        default="data/raw/marketing/leads_raw.jsonl",
        help="Path to raw leads JSONL file.",
    )
    return parser.parse_args()


def hash_email(email: str | None) -> str | None:
    if not email:
        return None
    return hashlib.sha256(email.lower().strip().encode("utf-8")).hexdigest()


def main() -> None:
    args = parse_args()
    settings = get_settings()

    jsonl_path = Path(args.jsonl)
    if not jsonl_path.exists():
        raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")

    duckdb = importlib.import_module("duckdb")
    conn = duckdb.connect(settings.duckdb_path)
    conn.execute("CREATE SCHEMA IF NOT EXISTS bronze_raw")

    conn.execute("DROP TABLE IF EXISTS bronze_raw._marketing_leads_stage")
    conn.execute(
        """
        CREATE TABLE bronze_raw._marketing_leads_stage AS
        SELECT *
        FROM read_json_auto(?)
        """,
        [str(jsonl_path)],
    )

    rows = conn.execute("SELECT * FROM bronze_raw._marketing_leads_stage").fetchall()
    columns = [desc[0] for desc in conn.description]
    records = [dict(zip(columns, row)) for row in rows]

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bronze_raw.marketing_leads (
            lead_id VARCHAR,
            company_name VARCHAR,
            email_hash VARCHAR,
            utm_source VARCHAR,
            utm_campaign VARCHAR,
            country VARCHAR,
            created_at TIMESTAMP,
            ingested_at TIMESTAMP
        )
        """
    )

    payload = [
        (
            rec.get("lead_id"),
            rec.get("company_name"),
            hash_email(rec.get("email")),
            rec.get("utm_source"),
            rec.get("utm_campaign"),
            rec.get("country"),
            rec.get("created_at"),
            rec.get("ingested_at"),
        )
        for rec in records
    ]

    conn.executemany(
        """
        INSERT INTO bronze_raw.marketing_leads (
            lead_id,
            company_name,
            email_hash,
            utm_source,
            utm_campaign,
            country,
            created_at,
            ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        payload,
    )
    conn.execute("DROP TABLE IF EXISTS bronze_raw._marketing_leads_stage")
    conn.close()

    print(f"Loaded {len(payload)} lead records into bronze_raw.marketing_leads")


if __name__ == "__main__":
    main()
