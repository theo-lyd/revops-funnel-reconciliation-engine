# Project Governance Documentation Index

This directory contains mandatory project-process documents for this capstone.

## Standing rules
- Standing instructions: see [standing-instructions.md](standing-instructions.md).
- Phase completion checklist and stop-gate workflow: see [phase-completion-checklist.md](phase-completion-checklist.md).
- CI/CD pipeline and deployment workflow: see [ci-cd-runbook.md](ci-cd-runbook.md).
- Artifact versioning policy and allowlist guard: see [artifact-policy.md](artifact-policy.md).

## Phase 4 post-completion hardening blocks
After Phase 4 batches 4.1-4.4 are complete, the following optional hardening blocks strengthen production safety and governance:
- **Block 1**: Governance and security hardening - RBAC, secret rotation, change-control SOP.
- **Block 2**: Observability and reliability hardening - source freshness, query-pack validation, release evidence.
- **Block 3**: Production readiness and parity enforcement - release gate, parity artifact, local-safe workflow.
- **Block 4**: Governance automation and stop-gate orchestration - evidence bundle generation, orchestrated gates.

See [../reports/phase-4/](../reports/phase-4/) for post-phase-4-block-X-*.md documents detailing each block.

## Required project-wide logs
- Issue and resolution register: see [issues-log.md](issues-log.md).
- Git command log: see [commands/git-commands.md](commands/git-commands.md).
- Bash and shell command log: see [commands/bash-shell-commands.md](commands/bash-shell-commands.md).
- Make command log: see [commands/make-commands.md](commands/make-commands.md).
- Python, dbt, and DuckDB command log: see [commands/python-dbt-duckdb-commands.md](commands/python-dbt-duckdb-commands.md).
- Other command log: see [commands/other-commands.md](commands/other-commands.md).

## Usage notes
- Update these logs during implementation, not after-the-fact.
- Every command entry must include the 5Ws and H: What, Why, Who, When, Where, and How.
- At phase completion, create the phase report in docs/reports and then pause for go/no-go confirmation before starting the next phase.
