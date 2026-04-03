# Mypy Command Log (5Ws and H)

This file records Mypy type-check commands used in the project.

## Entry format
- What
- Why
- Who
- When
- Where
- How
- Line-numbered example

## Entries

### MY-001
- What: `mypy src scripts dags`
- Why: run project-wide static type checking
- Who: project maintainer
- When: pre-commit, CI, and release checks
- Where: repository root
- How:
  - Preconditions: dependencies installed and paths importable
  - Alternatives: `make lint`; `python -m mypy src scripts dags`
  - Expected output: success or typed diagnostics by file/line
  - Recovery: resolve type errors and rerun
- Line-numbered example:
  1. `mypy src scripts dags`

### MY-002
- What: `mypy <single module or package>`
- Why: isolate type-checking for focused changes
- Who: project maintainer
- When: iterative debugging of one module
- Where: repository root
- How:
  - Preconditions: target path known
  - Alternatives: full repo command for cross-module verification
  - Expected output: scoped type diagnostics
  - Recovery: patch scoped errors and rerun
- Line-numbered example:
  1. `mypy src/revops_funnel/defense_package.py`

### MY-003
- What: `mypy --strict <path>`
- Why: enforce stricter type checks for critical modules
- Who: project maintainer
- When: hardening/refactor passes
- Where: repository root
- How:
  - Preconditions: path passes baseline mypy checks
  - Alternatives: baseline `mypy <path>` if strict mode is too noisy
  - Expected output: stricter diagnostics
  - Recovery: address strict errors or back down to standard scope
- Line-numbered example:
  1. `mypy --strict src/revops_funnel/defense_package.py`

### MY-004
- What: `python -m mypy <path>`
- Why: ensure mypy runs from the active Python interpreter
- Who: project maintainer
- When: environment/path troubleshooting
- Where: repository root
- How:
  - Preconditions: mypy installed in active interpreter
  - Alternatives: plain `mypy <path>`
  - Expected output: same diagnostics as CLI entrypoint
  - Recovery: install mypy in current environment and rerun
- Line-numbered example:
  1. `python -m mypy scripts/ops/run_defense_package.py`
