"""Validate SQL query-pack templates against local DuckDB gold models."""

from __future__ import annotations

import importlib
from pathlib import Path

from revops_funnel.config import get_settings

QUERY_PACK_PATHS = [
    Path("docs/reports/phase-4/query-packs/metabase-executive-funnel-view.sql"),
    Path("docs/reports/phase-4/query-packs/streamlit-text-to-sql-safe-templates.sql"),
]


def split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []

    for raw_line in sql.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("--"):
            continue
        current.append(raw_line)
        if line.endswith(";"):
            statement = "\n".join(current).strip().rstrip(";")
            if statement:
                statements.append(statement)
            current = []

    if current:
        statement = "\n".join(current).strip().rstrip(";")
        if statement:
            statements.append(statement)

    return statements


def main() -> None:
    settings = get_settings()
    duckdb = importlib.import_module("duckdb")
    conn = duckdb.connect(settings.duckdb_path, read_only=True)

    try:
        for query_pack in QUERY_PACK_PATHS:
            if not query_pack.exists():
                raise FileNotFoundError(f"Query pack not found: {query_pack}")

            content = query_pack.read_text(encoding="utf-8")
            statements = split_sql_statements(content)
            if not statements:
                raise ValueError(f"No executable SQL statements found in {query_pack}")

            for index, statement in enumerate(statements, start=1):
                wrapped = f"select * from ({statement}) as q limit 1"
                conn.execute(wrapped).fetchall()
                print(f"Validated {query_pack} statement #{index}")
    finally:
        conn.close()

    print("All query packs validated successfully.")


if __name__ == "__main__":
    main()
