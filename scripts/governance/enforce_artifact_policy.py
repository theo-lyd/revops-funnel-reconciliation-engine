#!/usr/bin/env python3
"""Enforce repository artifact policy for tracked files.

Policy:
- Runtime-generated artifacts must not be versioned by default.
- Only release evidence artifacts under artifacts/release-evidence/ are allowlisted.
"""

from __future__ import annotations

import subprocess

ALLOWLIST_PREFIXES = ("artifacts/release-evidence/",)


def _tracked_artifacts() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "artifacts"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit("Unable to list tracked artifacts via git ls-files artifacts")

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _is_allowlisted(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in ALLOWLIST_PREFIXES)


def main() -> int:
    tracked = _tracked_artifacts()
    violations = [path for path in tracked if not _is_allowlisted(path)]

    if not violations:
        print("Artifact policy check passed: tracked artifacts are allowlisted.")
        return 0

    print("Artifact policy violation detected.")
    print("The following tracked artifacts are not allowlisted:")
    for path in sorted(violations):
        print(f"- {path}")

    print("Allowlisted prefixes:")
    for prefix in ALLOWLIST_PREFIXES:
        print(f"- {prefix}")

    print("Remediation:")
    print("- Move long-lived release evidence under artifacts/release-evidence/")
    print("- Or untrack runtime artifacts (for example: git rm --cached <path>)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
