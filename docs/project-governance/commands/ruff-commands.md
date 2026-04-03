# Ruff Command Log (5Ws and H)

This file records Ruff linting and formatting commands.

## Entry format
- What
- Why
- Who
- When
- Where
- How
- Line-numbered example

## Entries

### RF-001
- What: `ruff check .`
- Why: lint the repository for style and correctness rules
- Who: project maintainer
- When: before commit and in CI
- Where: repository root
- How:
  - Preconditions: Ruff installed
  - Alternatives: `ruff check src scripts tests`; `make lint`
  - Expected output: diagnostics list or success
  - Recovery: patch reported issues and rerun
- Line-numbered example:
  1. `ruff check .`

### RF-002
- What: `ruff check . --fix`
- Why: auto-fix eligible lint issues
- Who: project maintainer
- When: after initial lint failures
- Where: repository root
- How:
  - Preconditions: working tree is safe for automated edits
  - Alternatives: manual fix + `ruff check .`
  - Expected output: files updated and reduced diagnostics
  - Recovery: inspect diff, adjust manually, rerun check
- Line-numbered example:
  1. `ruff check . --fix`
  2. `ruff check .`

### RF-003
- What: `ruff format .`
- Why: apply consistent code formatting
- Who: project maintainer
- When: before commit or after major edits
- Where: repository root
- How:
  - Preconditions: Ruff formatter available
  - Alternatives: `ruff format src tests scripts`
  - Expected output: formatted files or no-op
  - Recovery: rerun formatter after resolving syntax issues
- Line-numbered example:
  1. `ruff format .`

### RF-004
- What: `ruff format --check .`
- Why: verify formatting in CI without modifying files
- Who: project maintainer
- When: CI checks and pre-commit verification
- Where: repository root
- How:
  - Preconditions: Ruff installed
  - Alternatives: `ruff format .` for auto-formatting
  - Expected output: pass/fail status
  - Recovery: run format command and rerun check
- Line-numbered example:
  1. `ruff format --check .`

### RF-005
- What: `ruff check <path>`
- Why: lint only changed paths during iterative development
- Who: project maintainer
- When: feature-specific debugging
- Where: repository root
- How:
  - Preconditions: target path exists
  - Alternatives: `ruff check .` for full validation
  - Expected output: scoped diagnostics
  - Recovery: fix scoped issues, then run full repo check
- Line-numbered example:
  1. `ruff check src/revops_funnel/defense_package.py`
