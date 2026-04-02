#!/usr/bin/env python3
"""Create a deployment promotion report when release gates have passed."""

from __future__ import annotations

import argparse
import os

from revops_funnel.deployment_ops import (
    build_dbt_selector,
    collect_changed_files,
    create_deployment_promotion_report,
    promotion_enabled,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release-id",
        default=os.getenv("RELEASE_ID", "local"),
        help="Release identifier used in the promotion report.",
    )
    parser.add_argument(
        "--base-ref",
        default=os.getenv("DBT_BASE_REF", "origin/master"),
        help="Git ref used to determine the selector recorded in the report.",
    )
    parser.add_argument(
        "--parity-report",
        default=os.getenv("PARITY_REPORT_PATH", "artifacts/parity/metric_parity_report.json"),
        help="Path to the metric parity report.",
    )
    parser.add_argument(
        "--cache-refresh-report",
        default=os.getenv("CACHE_REFRESH_REPORT_PATH", "artifacts/cache/cache_refresh.json"),
        help="Path to the cache refresh report.",
    )
    parser.add_argument(
        "--output",
        default=os.getenv(
            "DEPLOYMENT_PROMOTION_REPORT_PATH",
            "artifacts/promotions/deployment_promotion.json",
        ),
        help="Path to write the deployment promotion report.",
    )
    parser.add_argument(
        "--environment",
        default=os.getenv("DEPLOYMENT_ENVIRONMENT", "production"),
        help="Environment name recorded in the promotion report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not promotion_enabled():
        print("Deployment promotion skipped; set DEPLOYMENT_PROMOTION_ENABLED=true to enable.")
        return 0

    selector = build_dbt_selector(collect_changed_files(args.base_ref))
    report = create_deployment_promotion_report(
        release_id=args.release_id,
        selector=selector,
        parity_report_path=args.parity_report,
        cache_refresh_report_path=args.cache_refresh_report,
        environment=args.environment,
        output_path=args.output,
    )
    print(
        "Deployment promotion recorded for "
        f"{report.release_id} in {report.environment} with selector {report.selector}"
    )
    print(f"Promotion report written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
