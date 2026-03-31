"""Poll synthetic leads API and append raw events to local JSONL landing zone."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8000/leads", help="Leads API endpoint.")
    parser.add_argument(
        "--out",
        default="data/raw/marketing/leads_raw.jsonl",
        help="Output JSONL file path.",
    )
    parser.add_argument("--count", type=int, default=100, help="Number of leads to fetch.")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout in seconds.")
    return parser.parse_args()


def fetch_lead(url: str, timeout: float) -> dict:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    payload["ingested_at"] = datetime.now(timezone.utc).isoformat()
    return payload


def main() -> None:
    args = parse_args()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("a", encoding="utf-8") as handle:
        for _ in range(args.count):
            record = fetch_lead(args.url, args.timeout)
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    print(f"Fetched {args.count} lead events into {out_path}")


if __name__ == "__main__":
    main()
