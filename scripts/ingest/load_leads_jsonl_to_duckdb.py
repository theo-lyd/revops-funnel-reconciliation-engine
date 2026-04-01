"""Load synthetic lead JSONL events into bronze_raw.marketing_leads."""

from __future__ import annotations

import argparse
import hashlib
import importlib
from datetime import datetime, timezone
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


def derive_company_name(record: dict) -> str | None:
    company_name = record.get("company_name")
    if company_name:
        return str(company_name)

    email = record.get("email")
    if not email:
        return None
    return str(email).split("@", 1)[1].split(".", 1)[0]


def main() -> None:
    args = parse_args()
    settings = get_settings()

    jsonl_path = Path(args.jsonl)
    if not jsonl_path.exists():
        raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")

    duckdb = importlib.import_module("duckdb")
    conn = duckdb.connect(settings.duckdb_path)
    conn.execute("CREATE SCHEMA IF NOT EXISTS bronze_raw")
    conn.execute("CREATE SCHEMA IF NOT EXISTS observability")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS observability.ingestion_audit (
            source_name VARCHAR,
            loaded_at TIMESTAMP,
            row_count BIGINT,
            status VARCHAR,
            details VARCHAR
        )
        """
    )

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
    records = [dict(zip(columns, row, strict=False)) for row in rows]

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
            derive_company_name(rec),
            hash_email(rec.get("email")),
            rec.get("utm_source"),
            rec.get("utm_campaign"),
            rec.get("country"),
            rec.get("created_at"),
            rec.get("ingested_at"),
        )
        for rec in records
        if rec.get("lead_id") and rec.get("created_at")
    ]

    conn.execute("DROP TABLE IF EXISTS bronze_raw._marketing_leads_upsert")
    conn.execute(
        """
        CREATE TABLE bronze_raw._marketing_leads_upsert (
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
    conn.executemany(
        """
        INSERT INTO bronze_raw._marketing_leads_upsert (
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

    insertable_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM bronze_raw._marketing_leads_upsert u
        LEFT JOIN bronze_raw.marketing_leads m
            ON m.lead_id = u.lead_id
            AND m.created_at = u.created_at
            AND COALESCE(m.utm_campaign, '') = COALESCE(u.utm_campaign, '')
        WHERE m.lead_id IS NULL
        """
    ).fetchone()[0]

    conn.execute(
        """
        INSERT INTO bronze_raw.marketing_leads
        SELECT
            u.lead_id,
            u.company_name,
            u.email_hash,
            u.utm_source,
            u.utm_campaign,
            u.country,
            u.created_at,
            u.ingested_at
        FROM bronze_raw._marketing_leads_upsert u
        LEFT JOIN bronze_raw.marketing_leads m
            ON m.lead_id = u.lead_id
            AND m.created_at = u.created_at
            AND COALESCE(m.utm_campaign, '') = COALESCE(u.utm_campaign, '')
        WHERE m.lead_id IS NULL
        """
    )

    conn.execute(
        """
        INSERT INTO observability.ingestion_audit
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            "marketing_leads",
            datetime.now(timezone.utc),
            insertable_count,
            "success",
            f"Loaded from {jsonl_path}",
        ],
    )

    conn.execute("DROP TABLE IF EXISTS bronze_raw._marketing_leads_upsert")
    conn.execute("DROP TABLE IF EXISTS bronze_raw._marketing_leads_stage")
    conn.close()

    print(f"Loaded {insertable_count} new lead records into bronze_raw.marketing_leads")


if __name__ == "__main__":
    main()
