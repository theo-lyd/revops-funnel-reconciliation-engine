# Bash and Shell Command Log (5Ws and H)

This file records shell commands used outside of Make shortcuts.

## Entry format
- What
- Why
- Who
- When
- Where
- How

## Entries

### SH-001
- What: find docs -maxdepth 4 -type f | sort
- Why: inventory documentation artifacts by path
- Who: project maintainer
- When: phase discovery and reporting
- Where: repository root in dev container
- How:
  - Preconditions: GNU find available
  - Expected output: sorted list of documentation files
  - Safety: read-only command

### SH-002
- What: sed -n '1,220p' README.md
- Why: inspect project quick-start and repository contract
- Who: project maintainer
- When: project-state reviews
- Where: repository root
- How:
  - Preconditions: file exists
  - Expected output: selected line range printed to terminal
  - Safety: read-only command

### SH-003
- What: pip install -r requirements/dev.txt
- Why: install developer dependencies required for linting and typing
- Who: project maintainer
- When: setup and dependency updates
- Where: repository root, Python environment active
- How:
  - Preconditions: network access and pip availability
  - Expected output: installed or already satisfied packages
  - Recovery: if permission errors occur, use virtual environment or user install

### SH-004
- What: pip install -e .
- Why: install local package in editable mode so scripts can import project module
- Who: project maintainer
- When: after module import failures during script execution
- Where: repository root
- How:
  - Preconditions: pyproject metadata is valid
  - Expected output: editable wheel installed
  - Recovery: reinstall after dependency or metadata changes

### SH-005
- What: pre-commit run --all-files
- Why: run repository guardrails and auto-fix trivial formatting issues
- Who: project maintainer
- When: before commits and after pre-commit config changes
- Where: repository root
- How:
  - Preconditions: pre-commit installed, config file valid
  - Expected output: pass/fail per hook with possible auto-fix output
  - Recovery: rerun after applying suggested fixes

### SH-006
- What: pytest -q tests/test_notifications.py tests/test_analytics_monitoring.py
- Why: run focused validation for the new monitoring email path before full repo checks
- Who: project maintainer
- When: 2026-04-02, Phase 6 Batch 6.1 validation
- Where: repository root
- How:
  - Preconditions: project package importable and test dependencies available
  - Expected output: focused pytest summary for notification and monitoring helpers
  - Recovery: inspect failing assertions, fix code, and rerun the targeted tests
