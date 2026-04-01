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
