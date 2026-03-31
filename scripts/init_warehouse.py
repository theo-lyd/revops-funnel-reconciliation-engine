"""Initialize local DuckDB schemas used by the RevOps stack."""

from __future__ import annotations

import importlib
from pathlib import Path

from revops_funnel.config import get_settings


def main() -> None:
    settings = get_settings()
    db_path = Path(settings.duckdb_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    duckdb = importlib.import_module("duckdb")
    conn = duckdb.connect(str(db_path))
    sql_path = Path("scripts/sql/bootstrap_duckdb.sql")
    conn.execute(sql_path.read_text(encoding="utf-8"))
    conn.close()

    print(f"DuckDB initialized at {db_path}")


if __name__ == "__main__":
    main()
