# Python and Pytest Command Log (5Ws and H)

This file records direct Python and pytest command usage.

## Entry format
- What
- Why
- Who
- When
- Where
- How
- Line-numbered example

## Python commands

### PY-001
- What: `python scripts/<name>.py`
- Why: execute project scripts directly
- Who: project maintainer
- When: feature work and troubleshooting
- Where: repository root
- How:
  - Preconditions: dependencies installed and script exists
  - Alternatives: `python3 scripts/<name>.py`; `make <target>`
  - Expected output: script logs and output artifact
  - Recovery: fix import/env/path issues and rerun
- Line-numbered example:
  1. `python scripts/ops/run_defense_package.py --help`

### PY-002
- What: `python -m pip install -r requirements/dev.txt`
- Why: install developer toolchain
- Who: project maintainer
- When: setup and environment reset
- Where: repository root
- How:
  - Preconditions: active Python environment
  - Alternatives: `pip install -r requirements/dev.txt`
  - Expected output: dependency installation summary
  - Recovery: use virtualenv or user install for permission issues
- Line-numbered example:
  1. `python -m pip install -r requirements/dev.txt`

### PY-003
- What: `python -m pip install -e .`
- Why: install package in editable mode
- Who: project maintainer
- When: local module changes
- Where: repository root
- How:
  - Preconditions: packaging metadata valid
  - Alternatives: `pip install -e .`
  - Expected output: editable install success
  - Recovery: correct pyproject metadata and rerun
- Line-numbered example:
  1. `python -m pip install -e .`

### PY-004
- What: `python -m compileall src scripts`
- Why: quick syntax validation sweep
- Who: project maintainer
- When: troubleshooting or sanity checks
- Where: repository root
- How:
  - Preconditions: Python interpreter available
  - Alternatives: `python -m py_compile <file>`
  - Expected output: compile pass/fail summary
  - Recovery: fix syntax errors and rerun
- Line-numbered example:
  1. `python -m compileall src scripts`

## Pytest commands

### PYT-001
- What: `pytest -q`
- Why: run full test suite
- Who: project maintainer
- When: before commit/push and at phase closeout
- Where: repository root
- How:
  - Preconditions: test dependencies installed
  - Alternatives: `python -m pytest -q`
  - Expected output: full suite pass/fail summary
  - Recovery: fix failing tests and rerun
- Line-numbered example:
  1. `pytest -q`

### PYT-002
- What: `pytest -q tests/test_<name>.py`
- Why: run focused test module
- Who: project maintainer
- When: feature iteration
- Where: repository root
- How:
  - Preconditions: test file exists
  - Alternatives: `pytest -q -k <expression>`
  - Expected output: module-level test summary
  - Recovery: narrow failing case, patch, and rerun
- Line-numbered example:
  1. `pytest -q tests/test_defense_package.py`

### PYT-003
- What: `pytest -q -k <expression>`
- Why: run a subset by keyword
- Who: project maintainer
- When: quick targeted validation
- Where: repository root
- How:
  - Preconditions: expression matches intended tests
  - Alternatives: direct file paths
  - Expected output: filtered test execution summary
  - Recovery: refine keyword if scope is too broad/narrow
- Line-numbered example:
  1. `pytest -q -k "defense_package and not cli"`

### PYT-004
- What: `pytest -q --maxfail=1`
- Why: fail fast during triage
- Who: project maintainer
- When: first-pass debugging of broken suite
- Where: repository root
- How:
  - Preconditions: tests are runnable
  - Alternatives: plain `pytest -q` for full failure list
  - Expected output: stops at first failure
  - Recovery: fix first failure and rerun
- Line-numbered example:
  1. `pytest -q --maxfail=1`
