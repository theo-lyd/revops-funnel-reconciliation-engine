#!/usr/bin/env python3
"""Run dbt build/test against a selector inferred from changed model files."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from revops_funnel.deployment_ops import resolve_selector_decision, write_selector_decision_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=("build", "test"),
        help="dbt command to run against the inferred selector.",
    )
    parser.add_argument(
        "--base-ref",
        default="origin/master",
        help="Git ref used to determine changed files.",
    )
    parser.add_argument(
        "--dbt-dir",
        default="dbt",
        help="Path to the dbt project directory.",
    )
    parser.add_argument(
        "--profiles-dir",
        default="profiles",
        help="dbt profiles directory relative to the dbt project.",
    )
    parser.add_argument(
        "--strict-selector",
        action="store_true",
        help="Fail when changed-file selector resolution cannot be determined.",
    )
    parser.add_argument(
        "--selector-report",
        default=os.getenv("SELECTOR_REPORT_PATH", "artifacts/ci/selector_decision.json"),
        help="Path to write selector decision metadata.",
    )
    return parser.parse_args()


def run_command(command: list[str], cwd: Path) -> None:
    print(f"Running: {' '.join(command)}")
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    args = parse_args()
    dbt_root = Path(args.dbt_dir)
    decision = resolve_selector_decision(
        base_ref=args.base_ref,
        strict_mode=args.strict_selector,
    )
    write_selector_decision_report(decision, args.selector_report)

    print(f"Changed-model selector: {decision.selector}")
    print(f"Selector report written to {args.selector_report}")
    run_command(["dbt", "deps"], dbt_root)
    run_command(
        ["dbt", args.action, "--profiles-dir", args.profiles_dir, "--select", decision.selector],
        dbt_root,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
