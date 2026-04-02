#!/usr/bin/env python3
"""Run dbt build/test with performance and cost budget controls."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from revops_funnel.artifacts import write_json_artifact
from revops_funnel.performance import (
    default_selector,
    resolve_effective_threads,
    resolve_timeout_seconds,
)

DEFAULT_OUTPUT = "artifacts/performance/dbt_budget_execution_report.json"


@dataclass(frozen=True)
class DbtBudgetExecutionReport:
    command: str
    environment: str
    selector: str
    project_dir: str
    profiles_dir: str
    target: str
    requested_threads: int
    effective_threads: int
    timeout_seconds: int
    timed_out: bool
    exit_code: int
    duration_seconds: float
    started_at_utc: str
    finished_at_utc: str
    stdout_excerpt: str
    stderr_excerpt: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", choices=("build", "test"), required=True)
    parser.add_argument(
        "--environment",
        choices=("local", "production"),
        default="local",
        help="Execution environment used for budget resolution.",
    )
    parser.add_argument("--project-dir", default="dbt", help="Path to dbt project directory.")
    parser.add_argument("--profiles-dir", default="profiles", help="dbt profiles dir path.")
    parser.add_argument("--target", default="", help="Optional dbt target name.")
    parser.add_argument(
        "--select",
        default=default_selector(),
        help="dbt selector expression.",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=int(os.getenv("DBT_THREADS_LOCAL", "1")),
        help="Requested dbt threads before budget capping.",
    )
    parser.add_argument(
        "--max-threads-local",
        type=int,
        default=int(os.getenv("DBT_MAX_THREADS_LOCAL", "2")),
        help="Max allowed dbt threads for local environment.",
    )
    parser.add_argument(
        "--max-threads-prod",
        type=int,
        default=int(os.getenv("DBT_MAX_THREADS_PROD", "4")),
        help="Max allowed dbt threads for production environment.",
    )
    parser.add_argument(
        "--timeout-seconds-local",
        type=int,
        default=int(os.getenv("DBT_TIMEOUT_SECONDS_LOCAL", "900")),
        help="Timeout for local budgeted dbt command.",
    )
    parser.add_argument(
        "--timeout-seconds-prod",
        type=int,
        default=int(os.getenv("DBT_TIMEOUT_SECONDS_PROD", "1800")),
        help="Timeout for production budgeted dbt command.",
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Execution report artifact path.")
    return parser.parse_args()


def _build_dbt_command(args: argparse.Namespace, effective_threads: int) -> list[str]:
    command = [
        "dbt",
        args.command,
        "--profiles-dir",
        args.profiles_dir,
        "--threads",
        str(effective_threads),
        "--select",
        args.select,
    ]
    target = args.target.strip()
    if target:
        command.extend(["--target", target])
    return command


def main() -> int:
    args = parse_args()
    effective_threads = resolve_effective_threads(
        requested_threads=args.threads,
        environment=args.environment,
        max_threads_local=args.max_threads_local,
        max_threads_prod=args.max_threads_prod,
    )
    timeout_seconds = resolve_timeout_seconds(
        environment=args.environment,
        timeout_seconds_local=args.timeout_seconds_local,
        timeout_seconds_prod=args.timeout_seconds_prod,
    )

    dbt_command = _build_dbt_command(args, effective_threads)
    started = datetime.now(timezone.utc)
    timed_out = False
    exit_code = 1
    stdout_excerpt = ""
    stderr_excerpt = ""

    try:
        completed = subprocess.run(
            dbt_command,
            cwd=args.project_dir,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        exit_code = int(completed.returncode)
        stdout_excerpt = completed.stdout[-2000:]
        stderr_excerpt = completed.stderr[-2000:]
    except subprocess.TimeoutExpired as error:
        timed_out = True
        exit_code = 124
        stdout_excerpt = str(error.stdout or "")[-2000:]
        stderr_excerpt = str(error.stderr or "")[-2000:]

    finished = datetime.now(timezone.utc)
    report = DbtBudgetExecutionReport(
        command=args.command,
        environment=args.environment,
        selector=args.select,
        project_dir=args.project_dir,
        profiles_dir=args.profiles_dir,
        target=args.target or "",
        requested_threads=max(1, int(args.threads)),
        effective_threads=effective_threads,
        timeout_seconds=timeout_seconds,
        timed_out=timed_out,
        exit_code=exit_code,
        duration_seconds=(finished - started).total_seconds(),
        started_at_utc=started.isoformat(),
        finished_at_utc=finished.isoformat(),
        stdout_excerpt=stdout_excerpt,
        stderr_excerpt=stderr_excerpt,
    )
    write_json_artifact(args.output, asdict(report))
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
