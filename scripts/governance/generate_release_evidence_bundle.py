"""Generate a release evidence bundle from the governance template."""

from __future__ import annotations

import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release-id",
        required=True,
        help="Identifier for this release evidence bundle.",
    )
    parser.add_argument(
        "--scope",
        default="post-phase-4-hardening-block-4",
        help="Scope label (batch/phase/block) for the evidence bundle.",
    )
    parser.add_argument(
        "--owner",
        default="project maintainer",
        help="Release owner name or role.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/release-evidence/release-evidence-bundle.md",
        help="Output markdown file path.",
    )
    return parser.parse_args()


def git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return "unavailable"
    return completed.stdout.strip() or "unavailable"


def render_bundle(release_id: str, scope: str, owner: str) -> str:
    commit_hash = git_output("rev-parse", "--short", "HEAD")
    branch_name = git_output("rev-parse", "--abbrev-ref", "HEAD")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")

    lines = [
        "# Release Evidence Bundle",
        "",
        "## 1) Release identity",
        f"- Release ID: {release_id}",
        f"- Scope (batch/phase): {scope}",
        f"- Commit hash(es): {commit_hash}",
        f"- Date/time: {timestamp}",
        f"- Release owner: {owner}",
        "- Approvers: pending",
        "",
        "## 2) Change summary",
        "- What changed: Block 4 governance automation and stop-gate enforcement updates.",
        "- Why it changed: strengthen release auditability and reduce manual governance overhead.",
        "- Stakeholders impacted: data engineering, analytics governance, "
        "production release owners.",
        "- Rollback impact: rollback to prior commit restores pre-automation workflow.",
        "",
        "## 3) Validation evidence",
        "- Lint result: see latest `make lint` run.",
        "- Test result: see latest `make test` run.",
        "- dbt build result: see latest `make quality-gate` run.",
        "- dbt test result: see latest `make quality-gate` run.",
        "- Source freshness result (if applicable): see latest `make dbt-source-freshness` run.",
        "- Query-pack validation result: see latest `make quality-gate` run.",
        "- Quality checks result: see latest `make quality-gate` run.",
        "- Great Expectations result: see latest `make quality-gate` run.",
        "- Metric parity result (local or strict): see latest parity report artifact.",
        "",
        "## 4) Governance evidence",
        "- Semantic contract version changes: none in this release unless separately documented.",
        "- Security and access checks: governed by Snowflake deployment checklist.",
        "- Role matrix confirmation: refer to phase 4 role-access matrix document.",
        "- Secrets rotation/emergency path status: refer to security runbook.",
        "",
        "## 5) Deployment evidence",
        f"- Target environment: {branch_name}",
        "- Deployment commands executed: `make production-stop-gate` "
        "or `make production-stop-gate-strict`",
        "- Runtime observations: capture from command logs for this release window.",
        "- Post-deploy checks: parity and dashboard checks per deployment checklist.",
        "",
        "## 6) Risk and exception register",
        "- Open risks: none newly identified during generation.",
        "- Temporary exceptions: local-safe mode may skip Snowflake checks in non-prod envs.",
        "- Mitigation owners: release owner and governance approver.",
        "- Review date: next scheduled release gate review.",
        "",
        "## 7) Sign-off",
        "- Engineering sign-off: pending",
        "- Governance sign-off: pending",
        "- Business sign-off: pending",
        "- Final status: GO / NO-GO",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_bundle(args.release_id, args.scope, args.owner),
        encoding="utf-8",
    )
    print(f"Release evidence bundle written to {output_path}")


if __name__ == "__main__":
    main()
