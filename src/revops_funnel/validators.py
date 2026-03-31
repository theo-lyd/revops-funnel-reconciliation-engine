"""Validation helpers for environment and runtime preflight checks."""

from __future__ import annotations

import os
from typing import Iterable


def validate_required_env(required_keys: Iterable[str]) -> list[str]:
    """Return missing environment variable names from required_keys."""

    return [key for key in required_keys if not os.getenv(key)]
