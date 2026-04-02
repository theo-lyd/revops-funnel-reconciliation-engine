#!/usr/bin/env python3
"""Dispatch rollback incident payload to an external incident webhook."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict

from revops_funnel.deployment_ops import (
    DEFAULT_ROLLBACK_INCIDENT_DEAD_LETTER_OUTPUT,
    DEFAULT_ROLLBACK_INCIDENT_DISPATCH_OUTPUT,
    DEFAULT_ROLLBACK_INCIDENT_PAYLOAD,
    dispatch_rollback_incident_payload,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--incident-payload",
        default=str(DEFAULT_ROLLBACK_INCIDENT_PAYLOAD),
        help="Path to rollback incident payload artifact.",
    )
    parser.add_argument(
        "--webhook-url",
        default=os.getenv("ROLLBACK_INCIDENT_WEBHOOK_URL", ""),
        help="Incident webhook URL (or use ROLLBACK_INCIDENT_WEBHOOK_URL).",
    )
    parser.add_argument(
        "--webhook-token",
        default=os.getenv("ROLLBACK_INCIDENT_WEBHOOK_TOKEN", ""),
        help="Optional bearer token (or use ROLLBACK_INCIDENT_WEBHOOK_TOKEN).",
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
        default=int(os.getenv("ROLLBACK_INCIDENT_MAX_ATTEMPTS", "1")),
        help="Maximum webhook delivery attempts before declaring failure.",
    )
    parser.add_argument(
        "--backoff-seconds",
        type=float,
        default=float(os.getenv("ROLLBACK_INCIDENT_BACKOFF_SECONDS", "0")),
        help="Fixed backoff delay between retry attempts.",
    )
    parser.add_argument(
        "--max-backoff-seconds",
        type=float,
        default=float(os.getenv("ROLLBACK_INCIDENT_MAX_BACKOFF_SECONDS", "30")),
        help="Maximum capped backoff delay when retrying dispatch attempts.",
    )
    parser.add_argument(
        "--dead-letter-output",
        default=str(DEFAULT_ROLLBACK_INCIDENT_DEAD_LETTER_OUTPUT),
        help="Path for dead-letter artifact when dispatch fails after retries.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when incident dispatch is skipped or fails.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_ROLLBACK_INCIDENT_DISPATCH_OUTPUT),
        help="Output path for incident dispatch report artifact.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = dispatch_rollback_incident_payload(
        incident_payload_path=args.incident_payload,
        incident_webhook_url=args.webhook_url,
        incident_webhook_token=args.webhook_token,
        timeout_seconds=args.timeout_seconds,
        max_attempts=args.max_attempts,
        backoff_seconds=args.backoff_seconds,
        max_backoff_seconds=args.max_backoff_seconds,
        dead_letter_output_path=args.dead_letter_output,
        output_path=args.output,
        strict_validation=args.strict,
    )
    print(json.dumps(asdict(report), indent=2, sort_keys=True))

    if args.strict and report.dispatch_status != "sent":
        raise SystemExit(
            f"Incident dispatch strict mode failed with status '{report.dispatch_status}'."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
