"""Build distributable executive and public-sector reporting pack artifacts."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from revops_funnel.artifacts import write_json_artifact


@dataclass(frozen=True)
class ReportingQueryAsset:
    name: str
    audience: str
    path: str
    sha256: str
    sql: str


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_reporting_pack(
    query_files: list[tuple[str, str, Path]],
    package_name: str,
    package_version: str,
) -> dict[str, Any]:
    assets: list[ReportingQueryAsset] = []
    for name, audience, query_path in query_files:
        sql = _read_sql(query_path)
        assets.append(
            ReportingQueryAsset(
                name=name,
                audience=audience,
                path=str(query_path),
                sha256=_sha256_text(sql),
                sql=sql,
            )
        )

    return {
        "package_name": package_name,
        "package_version": package_version,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "asset_count": len(assets),
        "assets": [asset.__dict__ for asset in assets],
    }


def write_reporting_pack(path: str, payload: dict[str, Any]) -> Path:
    return write_json_artifact(path, payload)
