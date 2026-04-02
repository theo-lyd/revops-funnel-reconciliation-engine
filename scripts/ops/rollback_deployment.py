#!/usr/bin/env python3
"""Create a rollback manifest when a release workflow fails."""

from __future__ import annotations

import argparse
import os

from revops_funnel.deployment_ops import create_deployment_rollback_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release-id",
        default=os.getenv("RELEASE_ID", "unknown-release"),
        help="Release identifier associated with the rollback event.",
    )
    parser.add_argument(
        "--rollback-reason",
        default=os.getenv("ROLLBACK_REASON", "unspecified"),
        help="Human-readable rollback reason.",
    )
    parser.add_argument(
        "--rollback-trigger",
        default=os.getenv("ROLLBACK_TRIGGER", "manual"),
        help="Trigger source (for example: github-actions, manual).",
    )
    parser.add_argument(
        "--promotion-report",
        default=os.getenv(
            "DEPLOYMENT_PROMOTION_REPORT_PATH",
            "artifacts/promotions/deployment_promotion.json",
        ),
        help="Path to the promotion report used as rollback context.",
    )
    parser.add_argument(
        "--output",
        default=os.getenv(
            "DEPLOYMENT_ROLLBACK_REPORT_PATH",
            "artifacts/promotions/deployment_rollback.json",
        ),
        help="Path to write the rollback report.",
    )
    parser.add_argument(
        "--environment",
        default=os.getenv("DEPLOYMENT_ENVIRONMENT", "production"),
        help="Environment name for the rollback report.",
    )
    parser.add_argument(
        "--require-release-access",
        action="store_true",
        help="Require actor to be listed in RELEASE_ALLOWED_ACTORS before writing rollback report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.require_release_access:
        actors = [actor.strip() for actor in os.getenv("RELEASE_ALLOWED_ACTORS", "").split(",")]
        allowed = [actor for actor in actors if actor]
        actor = os.getenv("GITHUB_ACTOR", "")
        if allowed and actor not in allowed:
            allowed_display = ", ".join(allowed)
            raise SystemExit(
                "Rollback report generation blocked for actor "
                f"'{actor}'. Allowed actors: {allowed_display}"
            )

    report = create_deployment_rollback_report(
        release_id=args.release_id,
        rollback_reason=args.rollback_reason,
        rollback_trigger=args.rollback_trigger,
        promotion_report_path=args.promotion_report,
        environment=args.environment,
        output_path=args.output,
    )
    print(
        "Rollback manifest recorded for "
        f"{report.release_id} in {report.environment} ({report.rollback_trigger})"
    )
    print(f"Rollback report written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
