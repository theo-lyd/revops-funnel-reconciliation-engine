"""Central configuration helpers for local and CI execution."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    environment: str = os.getenv("ENVIRONMENT", "dev")
    duckdb_path: str = os.getenv("DUCKDB_PATH", "./data/warehouse/revops.duckdb")
    snowflake_account: str = os.getenv("SNOWFLAKE_ACCOUNT", "")
    snowflake_user: str = os.getenv("SNOWFLAKE_USER", "")
    snowflake_database: str = os.getenv("SNOWFLAKE_DATABASE", "REVOPS")


def get_settings() -> Settings:
    """Return immutable runtime settings."""

    return Settings()
