"""Preflight checks for local and CI runtime environments."""

from __future__ import annotations

import os
import sys

from revops_funnel.validators import validate_required_env


def main() -> None:
    env = os.getenv("ENVIRONMENT", "dev")
    required = ["DUCKDB_PATH"]

    if env == "prod":
        required.extend(["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"])

    missing = validate_required_env(required)
    if missing:
        print("Missing required environment variables:")
        for key in missing:
            print(f"- {key}")
        sys.exit(1)

    print("Preflight checks passed.")


if __name__ == "__main__":
    main()
