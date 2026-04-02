#!/usr/bin/env python3
"""Escalate rollback dead-letter artifacts to paging or ticketing systems."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict

from revops_funnel.deployment_ops import (
    DEFAULT_ROLLBACK_ESCALATION_OUTPUT,
    DEFAULT_ROLLBACK_INCIDENT_DEAD_LETTER_OUTPUT,
    escalate_rollback_dead_letter,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dead-letter",
        default=str(DEFAULT_ROLLBACK_INCIDENT_DEAD_LETTER_OUTPUT),
        help="Path to rollback dead-letter artifact.",
    )
    parser.add_argument(
        "--webhook-url",
        default=os.getenv("ROLLBACK_ESCALATION_WEBHOOK_URL", ""),
        help="Escalation webhook URL (paging/ticketing endpoint).",
    )
    parser.add_argument(
        "--webhook-token",
        default=os.getenv("ROLLBACK_ESCALATION_WEBHOOK_TOKEN", ""),
        help="Optional escalation webhook bearer token.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=10,
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=int(os.getenv("ROLLBACK_ESCALATION_MAX_ATTEMPTS", "1")),
        help="Maximum escalation delivery attempts.",
    )
    parser.add_argument(
        "--backoff-seconds",
        type=float,
        default=float(os.getenv("ROLLBACK_ESCALATION_BACKOFF_SECONDS", "0")),
        help="Fixed backoff delay between escalation retries.",
    )
    parser.add_argument(
        "--max-backoff-seconds",
        type=float,
        default=float(os.getenv("ROLLBACK_ESCALATION_MAX_BACKOFF_SECONDS", "30")),
        help="Maximum capped backoff delay when retrying escalation attempts.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when dead-letter exists but escalation is not sent.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_ROLLBACK_ESCALATION_OUTPUT),
        help="Output path for escalation report artifact.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = escalate_rollback_dead_letter(
        dead_letter_path=args.dead_letter,
        escalation_webhook_url=args.webhook_url,
        escalation_webhook_token=args.webhook_token,
        timeout_seconds=args.timeout_seconds,
        max_attempts=args.max_attempts,
        backoff_seconds=args.backoff_seconds,
        max_backoff_seconds=args.max_backoff_seconds,
        output_path=args.output,
        strict_validation=args.strict,
    )
    print(json.dumps(asdict(report), indent=2, sort_keys=True))

    if args.strict and report.dead_letter_found and report.escalation_status != "sent":
        raise SystemExit(
            "Rollback dead-letter escalation strict mode failed with status "
            f"'{report.escalation_status}'."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
