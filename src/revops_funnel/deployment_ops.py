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
DEFAULT_ROLLBACK_OUTPUT = Path("artifacts/promotions/deployment_rollback.json")
DEFAULT_ROLLBACK_EXECUTION_OUTPUT = Path("artifacts/promotions/deployment_rollback_execution.json")


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


@dataclass(frozen=True)
class DeploymentRollbackReport:
    release_id: str
    environment: str
    rollback_trigger: str
    rollback_reason: str
    promotion_report_path: str
    promotion_report_sha256: str
    source_base_ref: str
    git_commit_sha: str
    workflow_run_id: str
    rollback_actions: list[str]
    rolled_back_at_utc: str


@dataclass(frozen=True)
class DeploymentRollbackExecutionReport:
    release_id: str
    environment: str
    execution_mode: str
    execution_enabled: bool
    source_rollback_report_path: str
    source_rollback_report_sha256: str
    applied_actions: list[str]
    deferred_actions: list[str]
    generated_artifacts: list[str]
    executed_at_utc: str


@dataclass(frozen=True)
class SelectorDecisionReport:
    base_ref: str
    selector: str
    changed_file_count: int
    changed_files: list[str]
    git_diff_exit_code: int
    fallback_used: bool
    fallback_reason: str
    strict_mode: bool
    generated_at_utc: str


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


def resolve_selector_decision(
    base_ref: str,
    repo_root: Path | None = None,
    strict_mode: bool = False,
) -> SelectorDecisionReport:
    repo_path = repo_root or Path.cwd()
    if not base_ref:
        if strict_mode:
            raise RuntimeError("Selector resolution failed: base ref is required in strict mode.")
        selector = DEFAULT_DBT_SELECTOR
        return SelectorDecisionReport(
            base_ref="",
            selector=selector,
            changed_file_count=0,
            changed_files=[],
            git_diff_exit_code=2,
            fallback_used=True,
            fallback_reason="missing-base-ref",
            strict_mode=False,
            generated_at_utc=datetime.now(timezone.utc).isoformat(),
        )

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
        if strict_mode:
            raise RuntimeError(
                "Selector resolution failed: git diff returned "
                f"exit code {completed.returncode} for base ref {base_ref}."
            )
        selector = DEFAULT_DBT_SELECTOR
        return SelectorDecisionReport(
            base_ref=base_ref,
            selector=selector,
            changed_file_count=0,
            changed_files=[],
            git_diff_exit_code=completed.returncode,
            fallback_used=True,
            fallback_reason="git-diff-failed",
            strict_mode=False,
            generated_at_utc=datetime.now(timezone.utc).isoformat(),
        )

    changed_files = [Path(line.strip()) for line in completed.stdout.splitlines() if line.strip()]
    selector = build_dbt_selector(changed_files)
    return SelectorDecisionReport(
        base_ref=base_ref,
        selector=selector,
        changed_file_count=len(changed_files),
        changed_files=[path.as_posix() for path in changed_files],
        git_diff_exit_code=0,
        fallback_used=False,
        fallback_reason="none",
        strict_mode=strict_mode,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
    )


def write_selector_decision_report(
    report: SelectorDecisionReport,
    output_path: str | Path,
) -> None:
    write_json_artifact(str(output_path), asdict(report))


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


def create_deployment_rollback_report(
    release_id: str,
    rollback_reason: str,
    rollback_trigger: str,
    promotion_report_path: str | Path,
    environment: str = "production",
    output_path: str | Path = DEFAULT_ROLLBACK_OUTPUT,
) -> DeploymentRollbackReport:
    promotion_path = Path(promotion_report_path)
    if not promotion_path.exists():
        raise FileNotFoundError(f"Promotion report not found: {promotion_path}")

    promotion_payload = _load_json_payload(promotion_path)
    report = DeploymentRollbackReport(
        release_id=release_id,
        environment=environment,
        rollback_trigger=rollback_trigger,
        rollback_reason=rollback_reason,
        promotion_report_path=str(promotion_path),
        promotion_report_sha256=_sha256_file(promotion_path),
        source_base_ref=str(promotion_payload.get("source_base_ref", "unknown")),
        git_commit_sha=str(promotion_payload.get("git_commit_sha", "unknown")),
        workflow_run_id=str(promotion_payload.get("workflow_run_id", "unknown")),
        rollback_actions=[
            "Disable promotion flag for subsequent runs",
            "Re-run release-readiness and strict parity checks",
            "Redeploy last known good release artifact",
            "Attach rollback report to incident ticket and notify stakeholders",
        ],
        rolled_back_at_utc=datetime.now(timezone.utc).isoformat(),
    )
    write_json_artifact(str(output_path), asdict(report))
    return report


def execute_deployment_rollback_playbook(
    rollback_report_path: str | Path,
    execution_enabled: bool,
    environment: str = "production",
    output_path: str | Path = DEFAULT_ROLLBACK_EXECUTION_OUTPUT,
) -> DeploymentRollbackExecutionReport:
    rollback_path = Path(rollback_report_path)
    if not rollback_path.exists():
        raise FileNotFoundError(f"Rollback report not found: {rollback_path}")

    payload = _load_json_payload(rollback_path)
    release_id = str(payload.get("release_id", "unknown-release"))
    actions_raw = payload.get("rollback_actions", [])
    actions = [str(item) for item in actions_raw] if isinstance(actions_raw, list) else []

    mode = "controlled" if execution_enabled else "dry-run"
    applied_actions: list[str] = []
    deferred_actions: list[str] = []
    generated_artifacts: list[str] = []

    base_dir = Path("artifacts/promotions")
    base_dir.mkdir(parents=True, exist_ok=True)

    for action in actions:
        if not execution_enabled:
            deferred_actions.append(action)
            continue

        if action.startswith("Disable promotion flag"):
            lock_path = base_dir / "release_lock.json"
            write_json_artifact(
                str(lock_path),
                {
                    "release_id": release_id,
                    "locked": True,
                    "reason": "rollback-execution",
                    "created_at_utc": datetime.now(timezone.utc).isoformat(),
                },
            )
            generated_artifacts.append(str(lock_path))
            applied_actions.append(action)
        elif action.startswith("Attach rollback report"):
            incident_path = base_dir / "rollback_incident_payload.json"
            write_json_artifact(
                str(incident_path),
                {
                    "release_id": release_id,
                    "environment": environment,
                    "rollback_report_path": str(rollback_path),
                    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                },
            )
            generated_artifacts.append(str(incident_path))
            applied_actions.append(action)
        else:
            deferred_actions.append(action)

    report = DeploymentRollbackExecutionReport(
        release_id=release_id,
        environment=environment,
        execution_mode=mode,
        execution_enabled=execution_enabled,
        source_rollback_report_path=str(rollback_path),
        source_rollback_report_sha256=_sha256_file(rollback_path),
        applied_actions=applied_actions,
        deferred_actions=deferred_actions,
        generated_artifacts=generated_artifacts,
        executed_at_utc=datetime.now(timezone.utc).isoformat(),
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
