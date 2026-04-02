#!/usr/bin/env python3
"""Execute rollback playbook actions from a rollback report artifact."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict

from revops_funnel.deployment_ops import (
    DEFAULT_ROLLBACK_EXECUTION_OUTPUT,
    execute_deployment_rollback_playbook,
    validate_release_actor_access,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Execute a controlled rollback playbook from an existing deployment rollback report."
        )
    )
    parser.add_argument(
        "--rollback-report",
        required=True,
        help="Path to deployment rollback report JSON artifact.",
    )
    parser.add_argument(
        "--environment",
        default="production",
        choices=("production", "staging", "dev"),
        help="Deployment environment context for generated artifacts.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help=(
            "Enable controlled execution mode. Without this flag, "
            "the command performs a dry-run and writes only an execution report."
        ),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_ROLLBACK_EXECUTION_OUTPUT),
        help="Output path for rollback execution report artifact.",
    )
    parser.add_argument(
        "--require-release-access",
        action="store_true",
        help="Require actor to be listed in ROLLBACK_ALLOWED_ACTORS or RELEASE_ALLOWED_ACTORS.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.require_release_access:
        raw_allowed = os.getenv("ROLLBACK_ALLOWED_ACTORS", "")
        if not raw_allowed.strip():
            raw_allowed = os.getenv("RELEASE_ALLOWED_ACTORS", "")
        actor = os.getenv("GITHUB_ACTOR", "")
        is_allowed, allowed = validate_release_actor_access(raw_allowed, actor)
        if not is_allowed:
            allowed_display = ", ".join(allowed)
            raise SystemExit(
                "Rollback playbook execution blocked for actor "
                f"'{actor}'. Allowed actors: {allowed_display}"
            )

    report = execute_deployment_rollback_playbook(
        rollback_report_path=args.rollback_report,
        execution_enabled=bool(args.execute),
        environment=args.environment,
        output_path=args.output,
        strict_validation=args.require_release_access,
    )
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
