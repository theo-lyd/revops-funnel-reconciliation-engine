"""Performance and cost guardrails for dbt execution paths."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DbtBudgetConfig:
    max_threads_local: int
    max_threads_prod: int
    timeout_seconds_local: int
    timeout_seconds_prod: int


def resolve_effective_threads(
    requested_threads: int,
    environment: str,
    max_threads_local: int,
    max_threads_prod: int,
) -> int:
    requested = max(1, int(requested_threads))
    if environment == "production":
        return min(requested, max(1, int(max_threads_prod)))
    return min(requested, max(1, int(max_threads_local)))


def resolve_timeout_seconds(
    environment: str,
    timeout_seconds_local: int,
    timeout_seconds_prod: int,
) -> int:
    if environment == "production":
        return max(1, int(timeout_seconds_prod))
    return max(1, int(timeout_seconds_local))


def default_selector() -> str:
    return "path:models/staging path:models/intermediate path:models/marts"
