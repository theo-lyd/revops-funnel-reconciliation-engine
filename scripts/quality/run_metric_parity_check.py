"""Compare key funnel metrics between local DuckDB and Snowflake targets."""

from __future__ import annotations

import argparse
import importlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from revops_funnel.config import get_settings
from revops_funnel.snowflake_auth import (
    build_snowflake_connector_auth_kwargs,
    missing_required_snowflake_env,
    snowflake_auth_from_env,
)


@dataclass(frozen=True)
class MetricSnapshot:
    win_rate: float | None
    leakage_ratio: float | None
    avg_cycle_days: float | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict-snowflake",
        action="store_true",
        help="Fail when Snowflake credentials/connector are unavailable.",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=float(os.getenv("PARITY_TOLERANCE", "0.02")),
        help="Maximum allowed absolute delta for metric parity.",
    )
    parser.add_argument(
        "--output-json",
        default=os.getenv("PARITY_REPORT_PATH", "artifacts/parity/metric_parity_report.json"),
        help="Path to write machine-readable parity results.",
    )
    return parser.parse_args()


def fetch_duckdb_metrics() -> MetricSnapshot:
    settings = get_settings()
    duckdb = importlib.import_module("duckdb")
    conn = duckdb.connect(settings.duckdb_path, read_only=True)
    row = conn.execute(
        """
        select
            cast(sum(case when deal_stage = 'Won' then 1 else 0 end) as double)
                / nullif(count(*), 0) as win_rate,
            cast(sum(case when is_leakage_point then 1 else 0 end) as double)
                / nullif(count(*), 0) as leakage_ratio,
            avg(total_cycle_days) as avg_cycle_days
        from analytics_gold.fct_revenue_funnel
        """
    ).fetchone()
    conn.close()
    return MetricSnapshot(
        win_rate=None if row[0] is None else float(row[0]),
        leakage_ratio=None if row[1] is None else float(row[1]),
        avg_cycle_days=None if row[2] is None else float(row[2]),
    )


def fetch_snowflake_metrics(strict_snowflake: bool) -> MetricSnapshot | None:
    auth = snowflake_auth_from_env()
    required = ["SNOWFLAKE_ROLE", "SNOWFLAKE_DATABASE", "SNOWFLAKE_WAREHOUSE"]
    missing = missing_required_snowflake_env(auth) + [key for key in required if not os.getenv(key)]
    if missing:
        message = f"Skipping Snowflake parity check; missing env vars: {', '.join(missing)}"
        if strict_snowflake:
            raise SystemExit(message)
        print(message)
        return None

    try:
        connector = importlib.import_module("snowflake.connector")
    except ModuleNotFoundError as err:
        message = "Skipping Snowflake parity check; snowflake connector not installed"
        if strict_snowflake:
            raise SystemExit(message) from err
        print(message)
        return None

    gold_schema = os.getenv("SNOWFLAKE_GOLD_SCHEMA", "analytics_gold")
    query = f"""
        select
            cast(sum(case when deal_stage = 'Won' then 1 else 0 end) as float)
                / nullif(count(*), 0) as win_rate,
            cast(sum(case when is_leakage_point then 1 else 0 end) as float)
                / nullif(count(*), 0) as leakage_ratio,
            avg(total_cycle_days) as avg_cycle_days
        from {gold_schema}.fct_revenue_funnel
    """

    conn = connector.connect(
        account=auth.account,
        user=auth.user,
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "analytics"),
        **build_snowflake_connector_auth_kwargs(auth),
    )

    cursor = conn.cursor()
    try:
        cursor.execute(query)
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    row_values = row if row is not None else (None, None, None)
    return MetricSnapshot(
        win_rate=None if row_values[0] is None else float(row_values[0]),
        leakage_ratio=None if row_values[1] is None else float(row_values[1]),
        avg_cycle_days=None if row_values[2] is None else float(row_values[2]),
    )


def compare_metric(name: str, left: float | None, right: float | None, tolerance: float) -> bool:
    if left is None and right is None:
        print(f"{name}: parity ok (both null)")
        return True
    if left is None or right is None:
        print(f"{name}: parity failed (left={left}, right={right})")
        return False

    delta = abs(left - right)
    status = "ok" if delta <= tolerance else "failed"
    print(f"{name}: {status} (duckdb={left:.6f}, snowflake={right:.6f}, delta={delta:.6f})")
    return delta <= tolerance


def main() -> None:
    args = parse_args()
    effective_tolerance = args.tolerance
    if args.strict_snowflake and "PARITY_TOLERANCE_STRICT" not in os.environ:
        effective_tolerance = 0.0

    duckdb_metrics = fetch_duckdb_metrics()
    snowflake_metrics = fetch_snowflake_metrics(args.strict_snowflake)
    if snowflake_metrics is None:
        print("Metric parity check completed in local-only mode.")
        write_report(
            args.output_json,
            {
                "status": "skipped",
                "reason": "snowflake-unavailable",
                "strict_mode": args.strict_snowflake,
                "tolerance": effective_tolerance,
            },
        )
        return

    deltas = {
        "win_rate": metric_delta(duckdb_metrics.win_rate, snowflake_metrics.win_rate),
        "leakage_ratio": metric_delta(
            duckdb_metrics.leakage_ratio,
            snowflake_metrics.leakage_ratio,
        ),
        "avg_cycle_days": metric_delta(
            duckdb_metrics.avg_cycle_days,
            snowflake_metrics.avg_cycle_days,
        ),
    }

    checks = [
        compare_metric(
            "win_rate",
            duckdb_metrics.win_rate,
            snowflake_metrics.win_rate,
            effective_tolerance,
        ),
        compare_metric(
            "leakage_ratio",
            duckdb_metrics.leakage_ratio,
            snowflake_metrics.leakage_ratio,
            effective_tolerance,
        ),
        compare_metric(
            "avg_cycle_days",
            duckdb_metrics.avg_cycle_days,
            snowflake_metrics.avg_cycle_days,
            effective_tolerance,
        ),
    ]

    write_report(
        args.output_json,
        {
            "status": "passed" if all(checks) else "failed",
            "strict_mode": args.strict_snowflake,
            "tolerance": effective_tolerance,
            "duckdb": {
                "win_rate": duckdb_metrics.win_rate,
                "leakage_ratio": duckdb_metrics.leakage_ratio,
                "avg_cycle_days": duckdb_metrics.avg_cycle_days,
            },
            "snowflake": {
                "win_rate": snowflake_metrics.win_rate,
                "leakage_ratio": snowflake_metrics.leakage_ratio,
                "avg_cycle_days": snowflake_metrics.avg_cycle_days,
            },
            "delta": deltas,
        },
    )

    if not all(checks):
        raise SystemExit(1)

    print("Metric parity check passed.")


def metric_delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return abs(left - right)


def write_report(output_path: str, payload: dict[str, object]) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(payload, indent=2)}\n", encoding="utf-8")
    print(f"Parity report written to {path}")


if __name__ == "__main__":
    main()
