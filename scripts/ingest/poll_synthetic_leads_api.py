"""Poll synthetic leads API and append raw events to local JSONL landing zone."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


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


def build_session() -> requests.Session:
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session = requests.Session()
    session.mount("http://", HTTPAdapter(max_retries=retry))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def fetch_lead(session: requests.Session, url: str, timeout: float) -> dict[str, object]:
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Expected JSON object payload from leads API")
    payload["ingested_at"] = datetime.now(timezone.utc).isoformat()
    return payload


def main() -> None:
    args = parse_args()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    session = build_session()

    with out_path.open("a", encoding="utf-8") as handle:
        for _ in range(args.count):
            record = fetch_lead(session, args.url, args.timeout)
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    print(f"Fetched {args.count} lead events into {out_path}")


if __name__ == "__main__":
    main()
