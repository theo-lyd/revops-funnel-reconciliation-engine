"""Helpers for CI/CD selection, cache refreshes, and deployment promotion."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from revops_funnel.artifacts import write_json_artifact

DEFAULT_DBT_SELECTOR = "path:models/staging path:models/intermediate path:models/marts"
DEFAULT_CACHE_PATHS = (
    Path(".streamlit/cache"),
    Path(".streamlit/state"),
    Path("artifacts/cache"),
)
DEFAULT_CACHE_REFRESH_OUTPUT = Path("artifacts/cache/cache_refresh.json")
DEFAULT_PROMOTION_OUTPUT = Path("artifacts/promotions/deployment_promotion.json")


@dataclass(frozen=True)
class CacheRefreshReport:
    refreshed_at_utc: str
    refreshed_paths: list[str]


@dataclass(frozen=True)
class DeploymentPromotionReport:
    release_id: str
    environment: str
    selector: str
    source_base_ref: str
    git_commit_sha: str
    workflow_run_id: str
    parity_status: str
    parity_report_path: str
    parity_report_sha256: str
    cache_refresh_status: str
    cache_refresh_report_path: str
    cache_refresh_report_sha256: str
    release_gate_status: str
    promoted_at_utc: str


def collect_changed_files(base_ref: str, repo_root: Path | None = None) -> list[Path]:
    repo_path = repo_root or Path.cwd()
    if not base_ref:
        return []

    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repo_path),
            "diff",
            "--name-only",
            "--diff-filter=ACMRT",
            f"{base_ref}...HEAD",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return []

    return [Path(line.strip()) for line in completed.stdout.splitlines() if line.strip()]


def build_dbt_selector(changed_files: Sequence[Path]) -> str:
    impacted_layers: set[str] = set()
    for path in changed_files:
        normalized = path.as_posix()
        if normalized.startswith("dbt/models/staging/"):
            impacted_layers.update({"staging", "intermediate", "marts"})
        elif normalized.startswith("dbt/models/intermediate/"):
            impacted_layers.update({"intermediate", "marts"})
        elif normalized.startswith("dbt/models/marts/"):
            impacted_layers.add("marts")
        elif normalized.startswith(("dbt/macros/", "dbt/snapshots/", "dbt/tests/")):
            impacted_layers.update({"staging", "intermediate", "marts"})
        elif normalized in {"dbt/dbt_project.yml", "dbt/packages.yml"}:
            impacted_layers.update({"staging", "intermediate", "marts"})

    if not impacted_layers:
        return DEFAULT_DBT_SELECTOR

    ordered_layers = [
        layer for layer in ("staging", "intermediate", "marts") if layer in impacted_layers
    ]
    return " ".join(f"path:models/{layer}" for layer in ordered_layers)


def refresh_runtime_caches(
    cache_paths: Sequence[Path] = DEFAULT_CACHE_PATHS,
) -> CacheRefreshReport:
    refreshed_paths: list[str] = []
    for cache_path in cache_paths:
        if cache_path.exists():
            if cache_path.is_dir():
                shutil.rmtree(cache_path)
            else:
                cache_path.unlink()
        cache_path.mkdir(parents=True, exist_ok=True)
        refreshed_paths.append(str(cache_path))

    return CacheRefreshReport(
        refreshed_at_utc=datetime.now(timezone.utc).isoformat(),
        refreshed_paths=refreshed_paths,
    )


def write_cache_refresh_report(
    report: CacheRefreshReport,
    output_path: str | Path = DEFAULT_CACHE_REFRESH_OUTPUT,
) -> None:
    write_json_artifact(str(output_path), asdict(report))


def _load_json_payload(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON payload at {path} must be an object.")
    return cast(dict[str, object], payload)


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_deployment_promotion_report(
    release_id: str,
    selector: str,
    parity_report_path: str | Path,
    cache_refresh_report_path: str | Path,
    source_base_ref: str = "origin/master",
    git_commit_sha: str = "unknown",
    workflow_run_id: str = "unknown",
    environment: str = "production",
    output_path: str | Path = DEFAULT_PROMOTION_OUTPUT,
) -> DeploymentPromotionReport:
    parity_path = Path(parity_report_path)
    cache_path = Path(cache_refresh_report_path)
    if not parity_path.exists():
        raise FileNotFoundError(f"Parity report not found: {parity_path}")
    if not cache_path.exists():
        raise FileNotFoundError(f"Cache refresh report not found: {cache_path}")

    parity_payload = _load_json_payload(parity_path)
    if parity_payload.get("status") != "passed":
        raise RuntimeError("Deployment promotion blocked because metric parity did not pass.")

    cache_payload = _load_json_payload(cache_path)
    if cache_payload.get("refreshed_paths") is None:
        raise RuntimeError("Deployment promotion blocked because cache refresh report is invalid.")

    report = DeploymentPromotionReport(
        release_id=release_id,
        environment=environment,
        selector=selector,
        source_base_ref=source_base_ref,
        git_commit_sha=git_commit_sha,
        workflow_run_id=workflow_run_id,
        parity_status=str(parity_payload.get("status", "unknown")),
        parity_report_path=str(parity_path),
        parity_report_sha256=_sha256_file(parity_path),
        cache_refresh_status="refreshed",
        cache_refresh_report_path=str(cache_path),
        cache_refresh_report_sha256=_sha256_file(cache_path),
        release_gate_status="passed",
        promoted_at_utc=datetime.now(timezone.utc).isoformat(),
    )
    write_json_artifact(str(output_path), asdict(report))
    return report


def promotion_enabled() -> bool:
    return os.getenv("DEPLOYMENT_PROMOTION_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
