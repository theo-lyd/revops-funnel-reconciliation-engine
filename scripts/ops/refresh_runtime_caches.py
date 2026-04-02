#!/usr/bin/env python3
"""Refresh local runtime caches used by analytics and deployment workflows."""

from __future__ import annotations

import argparse

from revops_funnel.deployment_ops import refresh_runtime_caches, write_cache_refresh_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="artifacts/cache/cache_refresh.json",
        help="Path to write the cache refresh report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = refresh_runtime_caches()
    write_cache_refresh_report(report, args.output)
    print(f"Refreshed caches: {', '.join(report.refreshed_paths)}")
    print(f"Cache refresh report written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
