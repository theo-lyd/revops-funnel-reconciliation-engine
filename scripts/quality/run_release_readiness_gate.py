"""Run production readiness checks for Snowflake deployment."""

from __future__ import annotations

import argparse
import os
import subprocess
from collections.abc import Sequence

REQUIRED_SNOWFLAKE_ENV = (
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_USER",
    "SNOWFLAKE_PASSWORD",
    "SNOWFLAKE_ROLE",
    "SNOWFLAKE_DATABASE",
    "SNOWFLAKE_WAREHOUSE",
    "SNOWFLAKE_SCHEMA",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when Snowflake environment variables are missing.",
    )
    return parser.parse_args()


def run_command(command: Sequence[str]) -> None:
    print(f"Running: {' '.join(command)}")
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> None:
    args = parse_args()

    missing = [key for key in REQUIRED_SNOWFLAKE_ENV if not os.getenv(key)]
    if missing:
        message = "Skipping release readiness gate; missing Snowflake env vars: " + ", ".join(
            missing
        )
        if args.strict:
            raise SystemExit(message)
        print(message)
        print("Release readiness gate completed in local-safe mode.")
        return

    run_command(("make", "dbt-build-prod"))
    run_command(("make", "dbt-test-prod"))
    run_command(("make", "metric-parity-check-strict"))
    print("Release readiness gate passed.")


if __name__ == "__main__":
    main()
