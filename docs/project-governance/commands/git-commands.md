# Git Command Log (5Ws and H)

This file records Git commands used in the project with beginner-friendly context.

## Entry format
- What: exact command
- Why: objective of the command
- Who: role executing the command
- When: phase and batch context
- Where: working directory and environment
- How: prerequisites, execution steps, expected output, and rollback guidance

## Entries

### GIT-001
- What: git status --short --branch
- Why: inspect branch divergence and changed files before commits
- Who: project maintainer
- When: all phases, before commit and push
- Where: repository root in local dev container
- How:
  - Preconditions: repository initialized and branch checked out
  - Run: git status --short --branch
  - Expected output: branch line plus changed/untracked files
  - Recovery: if unexpected files appear, update .gitignore or unstage intentional scope

### GIT-002
- What: git add <file list>
- Why: stage only intended files for clean grouped commits
- Who: project maintainer
- When: after successful batch validations
- Where: repository root
- How:
  - Preconditions: ensure quality checks pass
  - Run with explicit file list
  - Expected output: no output on success
  - Recovery: use git restore --staged <file> to remove wrong files from staging

### GIT-003
- What: git commit -m "<message>"
- Why: persist a coherent implementation unit with traceable message
- Who: project maintainer
- When: end of batch or phase
- Where: repository root
- How:
  - Preconditions: staged changes are correct and validated
  - Expected output: commit hash and changed file summary
  - Recovery: if commit fails due to hooks, fix hook issues then recommit

### GIT-004
- What: git push origin master
- Why: publish validated implementation to remote repository
- Who: project maintainer
- When: after successful local commit and stop-gate checks
- Where: repository root with remote configured
- How:
  - Preconditions: authenticated remote access
  - Expected output: branch update confirmation
  - Recovery: if rejected, pull/rebase or resolve branch protection requirements

### GIT-005
- What: git log -1 --date=short --pretty=format:'%h %ad %s'
- Why: capture latest change for reporting
- Who: project maintainer
- When: reporting checkpoints
- Where: repository root
- How:
  - Preconditions: at least one commit exists
  - Expected output: short hash, date, and subject line
  - Recovery: none required

## Phase 4 Batch 4.1 execution entries

### GIT-006
- What: git add dbt/models/marts docs/reports/phase-4 docs/project-governance
- Why: stage Gold marts, phase reports, and governance log updates as one coherent batch
- Who: project maintainer
- When: 2026-04-01, end of Phase 4 Batch 4.1
- Where: repository root
- How:
  - Preconditions: validation commands completed successfully
  - Expected output: files staged with no unintended artifacts
  - Recovery: unstage incorrect files with `git restore --staged <file>`

### GIT-007
- What: git commit -m "feat(phase-4): deliver batch-4.1 gold marts foundation"
- Why: record successful completion of Batch 4.1 with traceable phase context
- Who: project maintainer
- When: 2026-04-01, end of Phase 4 Batch 4.1
- Where: repository root
- How:
  - Preconditions: staged scope reviewed and clean
  - Expected output: new commit hash and file change summary
  - Recovery: if hook fails, remediate hook cause and recommit

### GIT-008
- What: git push origin master
- Why: publish validated Batch 4.1 artifacts and reports
- Who: project maintainer
- When: 2026-04-01, after commit creation
- Where: repository root with remote access
- How:
  - Preconditions: successful commit and authenticated remote
  - Expected output: remote branch updated
  - Recovery: resolve rejected push via pull/rebase and rerun push

## Phase 4 Batch 4.2 execution entries

### GIT-009
- What: git add dbt/models/marts docs/reports/phase-4 docs/project-governance Makefile
- Why: stage semantic contract implementation, phase docs, governance updates, and build-stability tweak
- Who: project maintainer
- When: 2026-04-01, end of Phase 4 Batch 4.2
- Where: repository root
- How:
  - Preconditions: all validation commands passed
  - Expected output: intended files staged and ready for commit
  - Recovery: unstage accidental files before commit

### GIT-010
- What: git commit -m "feat(phase-4): deliver batch-4.2 semantic metric contract"
- Why: capture Batch 4.2 semantic layer/governance completion as traceable unit
- Who: project maintainer
- When: 2026-04-01, after staging review
- Where: repository root
- How:
  - Preconditions: staged scope is correct
  - Expected output: commit hash with file-change summary
  - Recovery: if blocked by hooks, remediate issues and recommit

### GIT-011
- What: git push origin master
- Why: publish Phase 4 Batch 4.2 artifacts and maintain stop-gate discipline
- Who: project maintainer
- When: 2026-04-01, immediately after commit
- Where: repository root
- How:
  - Preconditions: successful commit and remote access
  - Expected output: branch update on origin/master
  - Recovery: resolve remote conflicts and retry push

## Phase 4 Batch 4.3 execution entries

### GIT-012
- What: git add dbt/models/marts dbt/tests docs/reports/phase-4 docs/project-governance
- Why: stage BI readiness implementation artifacts and required governance updates
- Who: project maintainer
- When: 2026-04-01, end of Phase 4 Batch 4.3
- Where: repository root
- How:
  - Preconditions: full validation suite passed
  - Expected output: only intended Batch 4.3 files staged
  - Recovery: unstage unintended files and restage explicitly

### GIT-013
- What: git commit -m "feat(phase-4): deliver batch-4.3 BI readiness layer"
- Why: persist dashboard-readiness models, query packs, and stability tests as a traceable batch
- Who: project maintainer
- When: 2026-04-01, after staging review
- Where: repository root
- How:
  - Preconditions: staged set reviewed and clean
  - Expected output: new commit hash and changed file summary
  - Recovery: resolve hook issues and recommit

### GIT-014
- What: git push origin master
- Why: publish validated Batch 4.3 outputs and keep phase stop-gate discipline
- Who: project maintainer
- When: 2026-04-01, immediately after commit
- Where: repository root
- How:
  - Preconditions: successful commit and remote connectivity
  - Expected output: remote branch updated to include Batch 4.3
  - Recovery: resolve remote rejections and rerun push

## Phase 4 Batch 4.4 execution entries

### GIT-015
- What: git add Makefile README.md .env.example dbt/profiles/profiles.yml.example docs/reports/phase-4 docs/project-governance
- Why: stage Snowflake production alignment changes, phase report artifacts, and governance updates
- Who: project maintainer
- When: 2026-04-01, end of Phase 4 Batch 4.4
- Where: repository root
- How:
  - Preconditions: validation complete and scope reviewed
  - Expected output: intended files staged with no unrelated artifacts
  - Recovery: unstage unintended files and restage explicitly

### GIT-016
- What: git commit -m "feat(phase-4): deliver batch-4.4 snowflake production alignment"
- Why: capture deployment-governance and Snowflake alignment as a traceable completion unit
- Who: project maintainer
- When: 2026-04-01, after staging review
- Where: repository root
- How:
  - Preconditions: staged change set approved
  - Expected output: commit hash with summary
  - Recovery: resolve hook feedback and recommit

### GIT-017
- What: git push origin master
- Why: publish Batch 4.4 outputs and preserve phase stop-gate workflow
- Who: project maintainer
- When: 2026-04-01, immediately after commit
- Where: repository root
- How:
  - Preconditions: successful commit and remote access
  - Expected output: remote updated with Batch 4.4 commit
  - Recovery: resolve branch or authentication issues and retry

## Phase 4 closeout entries

### GIT-018
- What: git add docs/reports/phase-4/phase-4-end-report.md docs/project-governance/phase-completion-checklist.md docs/project-governance/commands
- Why: stage phase closure report and governance status updates
- Who: project maintainer
- When: 2026-04-01, Phase 4 closeout
- Where: repository root
- How:
  - Preconditions: all Phase 4 batches already committed and pushed
  - Expected output: phase-closeout files staged
  - Recovery: unstage unintended files before commit

### GIT-019
- What: git commit -m "docs(phase-4): publish end report and closeout status"
- Why: formally close Phase 4 with auditable summary and stop-gate evidence
- Who: project maintainer
- When: 2026-04-01, after staging closeout files
- Where: repository root
- How:
  - Preconditions: report and governance updates complete
  - Expected output: closeout commit hash and file summary
  - Recovery: resolve hook feedback and recommit

### GIT-020
- What: git push origin master
- Why: publish Phase 4 end report and governance closeout updates
- Who: project maintainer
- When: 2026-04-01, immediately after closeout commit
- Where: repository root
- How:
  - Preconditions: successful closeout commit
  - Expected output: remote branch updated with phase closeout
  - Recovery: resolve remote conflicts and retry push

## Post-Phase 4 hardening entries

### GIT-021
- What: git add Makefile .env.example README.md dbt/models/marts docs/reports/phase-4 scripts/quality docs/project-governance
- Why: stage top-3 hardening changes and required governance updates as one auditable batch
- Who: project maintainer
- When: 2026-04-01, post-Phase 4 hardening
- Where: repository root
- How:
  - Preconditions: lint/test/quality-gate/parity-check pass
  - Expected output: intended hardening files staged cleanly
  - Recovery: unstage non-scope files and restage explicitly

### GIT-022
- What: git commit -m "chore(hardening): implement top-3 safety improvements"
- Why: persist environment-safe optimizations and parity scaffold as a grouped change
- Who: project maintainer
- When: 2026-04-01, after staging review
- Where: repository root
- How:
  - Preconditions: staged files verified and governance docs updated
  - Expected output: commit hash and summary
  - Recovery: resolve hook feedback and recommit

### GIT-023
- What: git push origin master
- Why: publish hardening improvements to remote branch
- Who: project maintainer
- When: 2026-04-01, immediately after hardening commit
- Where: repository root
- How:
  - Preconditions: successful commit and remote access
  - Expected output: remote branch updated with hardening commit
  - Recovery: resolve remote rejection and retry push

## Governance and security hardening block 1 entries

### GIT-024
- What: git add docs/security docs/reports/phase-4 docs/project-governance
- Why: stage Block 1 governance/security deliverables and required ledger updates
- Who: project maintainer
- When: 2026-04-01, Block 1 closeout
- Where: repository root
- How:
  - Preconditions: validation sequence passed
  - Expected output: only intended Block 1 files staged
  - Recovery: unstage unintended files and restage scope

### GIT-025
- What: git commit -m "docs(hardening): implement governance and security block 1"
- Why: capture RBAC, secret rotation runbook, and semantic change-control SOP enhancements
- Who: project maintainer
- When: 2026-04-01, after staging review
- Where: repository root
- How:
  - Preconditions: staged scope and docs reviewed
  - Expected output: commit hash and summary
  - Recovery: resolve hook feedback and recommit

### GIT-026
- What: git push origin master
- Why: publish Block 1 completion artifacts for stop-gate review
- Who: project maintainer
- When: 2026-04-01, immediately after commit
- Where: repository root
- How:
  - Preconditions: successful commit and remote connectivity
  - Expected output: remote branch updated with Block 1 commit
  - Recovery: resolve remote conflicts and retry

## Observability and reliability hardening block 2 entries

### GIT-027
- What: git add dbt/models/staging/crm/_crm__sources.yml Makefile scripts/quality docs/project-governance docs/reports/phase-4
- Why: stage Block 2 observability/reliability artifacts and required governance updates
- Who: project maintainer
- When: 2026-04-01, Block 2 closeout
- Where: repository root
- How:
  - Preconditions: validation sequence passed
  - Expected output: intended Block 2 files staged
  - Recovery: unstage out-of-scope files and restage explicitly

### GIT-028
- What: git commit -m "chore(hardening): implement observability and reliability block 2"
- Why: persist freshness, query-pack validation, and release evidence improvements as a grouped change
- Who: project maintainer
- When: 2026-04-01, after staging review
- Where: repository root
- How:
  - Preconditions: staged file set reviewed and clean
  - Expected output: commit hash and summary
  - Recovery: resolve hook issues and recommit

### GIT-029
- What: git push origin master
- Why: publish Block 2 artifacts and trigger stop-gate decision for next block
- Who: project maintainer
- When: 2026-04-01, immediately after commit
- Where: repository root
- How:
  - Preconditions: successful Block 2 commit
  - Expected output: remote branch updated
  - Recovery: resolve remote conflicts and retry push

## Production readiness and parity enforcement block 3 entries

### GIT-030
- What: git add Makefile .env.example README.md scripts/quality docs/reports/phase-4 docs/project-governance
- Why: stage Block 3 production-readiness and parity-enforcement changes with governance log updates
- Who: project maintainer
- When: 2026-04-01, Block 3 closeout
- Where: repository root
- How:
  - Preconditions: Block 3 validation sequence passed
  - Expected output: intended Block 3 files staged with no unrelated artifacts
  - Recovery: unstage out-of-scope files and restage explicitly

### GIT-031
- What: git commit -m "chore(hardening): implement production readiness block 3"
- Why: persist release-readiness gate and parity evidence enhancements as one auditable change
- Who: project maintainer
- When: 2026-04-01, after staging review
- Where: repository root
- How:
  - Preconditions: staged file set reviewed and clean
  - Expected output: commit hash and file summary
  - Recovery: resolve hook issues and recommit

### GIT-032
- What: git push origin master
- Why: publish Block 3 completion artifacts and stop-gate status
- Who: project maintainer
- When: 2026-04-01, immediately after commit
- Where: repository root
- How:
  - Preconditions: successful Block 3 commit
  - Expected output: remote branch updated to latest commit
  - Recovery: resolve remote conflicts and retry push
