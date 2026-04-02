#!/usr/bin/env python3
"""Analyze query patterns and emit optimization hints based on cost metrics."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from revops_funnel.artifacts import write_json_artifact
from revops_funnel.cost_observability import _bytes_per_result_row

DEFAULT_ATTRIBUTION = os.getenv(
    "COST_ATTRIBUTION_REPORT_PATH",
    "artifacts/performance/query_cost_attribution_report.json",
)
DEFAULT_OUTPUT = os.getenv(
    "COST_PATTERN_ANALYSIS_PATH",
    "artifacts/performance/query_pattern_analysis.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--attribution-report",
        default=DEFAULT_ATTRIBUTION,
        help="Query-cost attribution report path.",
    )
    parser.add_argument(
        "--peer-deviation-threshold-sigma",
        type=float,
        default=3.0,
        help="Z-score threshold for high-confidence optimization hints.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Output path for pattern analysis.",
    )
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def main() -> int:
    args = parse_args()

    report_path = Path(args.attribution_report)
    if not report_path.exists():
        analysis = {
            "status": "skipped",
            "reason": f"Attribution report not found: {report_path}",
            "query_patterns": [],
            "optimization_opportunities_by_roi": [],
        }
        write_json_artifact(args.output, analysis)
        print(json.dumps(analysis, indent=2, sort_keys=True))
        return 0

    attribution = _read_json(report_path)
    top_queries = attribution.get("top_expensive_queries", [])

    query_patterns: list[dict[str, object]] = []
    opportunities: list[dict[str, object]] = []

    for query in top_queries:
        if not isinstance(query, dict):
            continue

        query_id = str(query.get("query_id", ""))
        query_tag = str(query.get("query_tag", ""))
        bytes_scanned = int(query.get("bytes_scanned", 0))
        elapsed_seconds = float(query.get("elapsed_seconds", 0.0))
        credits_used = float(query.get("credits_used", 0.0))

        # Estimate result rows (simple heuristic: assume 100 bytes per result row on average)
        estimated_result_rows = max(1, bytes_scanned // 100)
        bytes_per_row = _bytes_per_result_row(bytes_scanned, estimated_result_rows)

        pattern: dict[str, object] = {
            "query_id": query_id,
            "query_tag": query_tag,
            "bytes_scanned": bytes_scanned,
            "result_rows": estimated_result_rows,
            "bytes_per_row": round(bytes_per_row, 2),
            "elapsed_seconds": round(elapsed_seconds, 2),
            "credits_used": round(credits_used, 2),
            "optimization_hints": [],
        }

        # High bytes per row suggests data explosion (potential full scan)
        if bytes_per_row > 1_000_000:
            hint_msg = (
                "Extremely high bytes-per-row ratio; likely full table scan or data explosion"
            )
            pattern["optimization_hints"].append(
                {
                    "hint": hint_msg,
                    "confidence": "high",
                    "estimated_credits_saved_monthly": round(credits_used * 0.5, 2),
                    "effort_hours": 2,
                }
            )
            opportunities.append(
                {
                    "query_id": query_id,
                    "hint": "Eliminate full table scan",
                    "roi_credits_per_effort_hour": round((credits_used * 0.5) / 2, 2),
                    "rank": len(opportunities) + 1,
                }
            )

        query_patterns.append(pattern)

    analysis = {
        "status": "ok",
        "threshold_sigma": args.peer_deviation_threshold_sigma,
        "query_patterns": query_patterns,
        "optimization_opportunities_by_roi": sorted(
            opportunities,
            key=lambda x: float(x.get("roi_credits_per_effort_hour", 0)),
            reverse=True,
        ),
    }

    write_json_artifact(args.output, analysis)
    print(json.dumps(analysis, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    exit(main())
