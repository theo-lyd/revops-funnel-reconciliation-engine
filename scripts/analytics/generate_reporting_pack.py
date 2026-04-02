#!/usr/bin/env python3
"""Generate the Public-Sector and Executive Reporting Pack artifact."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from revops_funnel.reporting_pack import build_reporting_pack, write_reporting_pack

DEFAULT_OUTPUT = os.getenv(
    "REPORTING_PACK_OUTPUT_PATH",
    "artifacts/reports/public_sector_executive_reporting_pack.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package-version",
        default=os.getenv("REPORTING_PACK_VERSION", "1.0.0"),
        help="Reporting pack semantic version.",
    )
    parser.add_argument(
        "--strict-files",
        action="store_true",
        help="Fail if any source query file is missing.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Output artifact path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    query_files = [
        (
            "Executive Funnel View",
            "executive",
            Path("docs/reports/phase-4/query-packs/metabase-executive-funnel-view.sql"),
        ),
        (
            "Public-Sector Funnel View",
            "public-sector",
            Path("docs/reports/phase-4/query-packs/metabase-public-sector-funnel-view.sql"),
        ),
        (
            "Streamlit Safe Templates",
            "analytics-engineering",
            Path("docs/reports/phase-4/query-packs/streamlit-text-to-sql-safe-templates.sql"),
        ),
    ]

    missing = [path for _, _, path in query_files if not path.exists()]
    if missing:
        if args.strict_files:
            missing_text = ", ".join(str(path) for path in missing)
            print(f"Error: missing query pack files: {missing_text}")
            return 1
        query_files = [item for item in query_files if item[2].exists()]

    payload = build_reporting_pack(
        query_files=query_files,
        package_name="public-sector-and-executive-reporting-pack",
        package_version=args.package_version,
    )
    artifact_path = write_reporting_pack(args.output, payload)
    print(f"✓ Reporting pack generated: {artifact_path}")
    print(f"  Assets: {payload['asset_count']}")
    print(f"  Version: {payload['package_version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
