"""Artifact writing helpers for reproducible reporting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json_artifact(path_str: str, payload: dict[str, Any]) -> Path:
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_text_artifact(path_str: str, content: str) -> Path:
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
