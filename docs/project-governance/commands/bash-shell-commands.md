# Bash and Shell Command Log (5Ws and H)

This file records shell commands used directly in the terminal.

## Entry format
- What
- Why
- Who
- When
- Where
- How
- Line-numbered example

## Entries

### SH-001
- What: `find docs -maxdepth 4 -type f | sort`
- Why: inventory documentation files quickly
- Who: project maintainer
- When: documentation audits and discovery
- Where: repository root
- How:
  - Preconditions: `find` is available
  - Alternatives: `ls -R docs`; `tree docs`
  - Expected output: sorted file-path listing
  - Recovery: narrow the path if output is too large
- Line-numbered example:
  1. `find docs -maxdepth 4 -type f | sort`

### SH-002
- What: `sed -n '1,220p' README.md`
- Why: preview a section of a file without editing
- Who: project maintainer
- When: quick document inspection
- Where: repository root
- How:
  - Preconditions: target file exists
  - Alternatives: `head -n 220 README.md`
  - Expected output: selected line range in terminal
  - Recovery: adjust the line range and rerun
- Line-numbered example:
  1. `sed -n '1,220p' README.md`

### SH-003
- What: `grep -RIn "<pattern>" <path>`
- Why: locate references in the workspace when needed
- Who: project maintainer
- When: refactoring and debugging
- Where: repository root or scoped folder
- How:
  - Preconditions: the path exists
  - Alternatives: `rg` (if installed); `grep -RIn --include='*.py'`
  - Expected output: file, line number, and matching text
  - Recovery: refine the pattern to reduce noise
- Line-numbered example:
  1. `grep -RIn "phase12" docs`

### SH-004
- What: `python -m pip install -r requirements/dev.txt`
- Why: install development dependencies
- Who: project maintainer
- When: setup or environment refresh
- Where: repository root
- How:
  - Preconditions: active Python environment and network access
  - Alternatives: `pip install -r requirements/dev.txt`
  - Expected output: installed or already satisfied packages
  - Recovery: use a virtual environment if permissions fail
- Line-numbered example:
  1. `python -m pip install -r requirements/dev.txt`

### SH-005
- What: `python -m pip install -e .`
- Why: install project package in editable mode
- Who: project maintainer
- When: after import issues or package updates
- Where: repository root
- How:
  - Preconditions: project metadata is valid
  - Alternatives: `pip install -e .`
  - Expected output: editable install confirmation
  - Recovery: rerun after fixing packaging metadata
- Line-numbered example:
  1. `python -m pip install -e .`

### SH-006
- What: `pre-commit run --all-files`
- Why: run repository guardrails before commit
- Who: project maintainer
- When: pre-commit validation
- Where: repository root
- How:
  - Preconditions: pre-commit installed
  - Alternatives: `pre-commit run <hook-id> --all-files`
  - Expected output: pass/fail per hook
  - Recovery: apply fixes and rerun hooks
- Line-numbered example:
  1. `pre-commit run --all-files`

### SH-007
- What: `pytest -q <test paths>`
- Why: execute focused tests during development
- Who: project maintainer
- When: iterative debugging
- Where: repository root
- How:
  - Preconditions: dependencies installed
  - Alternatives: `pytest -q`; `pytest -q -k <expr>`
  - Expected output: concise test result summary
  - Recovery: inspect failing assertions and rerun
- Line-numbered example:
  1. `pytest -q tests/test_defense_package.py`

### SH-008
- What: `python scripts/<task>.py`
- Why: run a project script directly
- Who: project maintainer
- When: ad hoc checks and artifact generation
- Where: repository root
- How:
  - Preconditions: required input files/env vars exist
  - Alternatives: `python3 scripts/<task>.py`; `make <target>`
  - Expected output: script-specific status and output artifact
  - Recovery: fix path/env issues and rerun
- Line-numbered example:
  1. `python scripts/ops/run_defense_package.py --help`
