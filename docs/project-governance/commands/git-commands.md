# Git Command Log (5Ws and H)

This file documents commonly used Git commands for this project and includes
numbered examples for each entry.

## Entry format
- What: command or command family
- Why: the operational reason to use it
- Who: the role expected to run it
- When: the typical lifecycle point
- Where: the working directory or environment
- How: prerequisites, alternatives, expected output, and recovery path
- Line-numbered example: concrete numbered command sequence

## Entries

### GIT-001
- What: `git status --short --branch`
- Why: inspect branch and file-change scope before staging or pushing
- Who: project maintainer
- When: before every commit and push
- Where: repository root
- How:
  - Preconditions: repository initialized and branch checked out
  - Alternatives: `git status`; `git status -sb`
  - Expected output: branch summary plus changed/untracked files
  - Recovery: investigate unexpected files before staging
- Line-numbered example:
  1. `git status --short --branch`

### GIT-002
- What: `git add <file list>`
- Why: stage only intended files for a coherent commit
- Who: project maintainer
- When: after local validations pass
- Where: repository root
- How:
  - Preconditions: exact files to include are known
  - Alternatives: `git add -p`; `git add .` (only if scope is fully safe)
  - Expected output: no terminal output on success
  - Recovery: unstage accidental files with `git restore --staged <file>`
- Line-numbered example:
  1. `git add docs/project-governance/README.md`
  2. `git add docs/project-governance/commands/git-commands.md`

### GIT-003
- What: `git restore --staged <file>`
- Why: remove files from staging without deleting local edits
- Who: project maintainer
- When: after a staging mistake
- Where: repository root
- How:
  - Preconditions: file is currently staged
  - Alternatives: `git reset HEAD <file>`
  - Expected output: file removed from index and remains modified in workspace
  - Recovery: restage the correct files
- Line-numbered example:
  1. `git restore --staged docs/project-governance/commands/git-commands.md`

### GIT-004
- What: `git commit -m "<message>"`
- Why: persist a validated implementation unit
- Who: project maintainer
- When: end of a batch or task
- Where: repository root
- How:
  - Preconditions: staged scope is correct and hooks pass
  - Alternatives: `git commit --amend` (only for unpublished local corrections)
  - Expected output: commit hash and changed-file summary
  - Recovery: fix hook failures and recommit
- Line-numbered example:
  1. `git commit -m "docs: add command reference examples"`

### GIT-005
- What: `git push origin master`
- Why: publish validated commits to the remote default branch
- Who: project maintainer
- When: after commit creation and final checks
- Where: repository root
- How:
  - Preconditions: remote access and branch permission available
  - Alternatives: `git push origin HEAD`
  - Expected output: remote update confirmation
  - Recovery: resolve rejection via sync/rebase and retry
- Line-numbered example:
  1. `git push origin master`

### GIT-006
- What: `git log -1 --date=short --pretty=format:'%h %ad %s'`
- Why: capture latest commit metadata for reporting
- Who: project maintainer
- When: release notes and handover checkpoints
- Where: repository root
- How:
  - Preconditions: at least one commit exists
  - Alternatives: `git log -1 --oneline`; `git show --stat --oneline -1`
  - Expected output: short hash, date, and subject
  - Recovery: none typically required
- Line-numbered example:
  1. `git log -1 --date=short --pretty=format:'%h %ad %s'`

### GIT-007
- What: `git diff --staged`
- Why: verify exactly what will be committed
- Who: project maintainer
- When: immediately before commit
- Where: repository root
- How:
  - Preconditions: at least one staged change
  - Alternatives: `git diff`; `git diff --name-only --staged`
  - Expected output: patch view of staged files
  - Recovery: unstage or adjust files before commit
- Line-numbered example:
  1. `git diff --staged`

### GIT-008
- What: `git rev-parse --short HEAD`
- Why: quickly retrieve current commit id
- Who: project maintainer
- When: traceability and status reporting
- Where: repository root
- How:
  - Preconditions: repository has commits
  - Alternatives: `git log -1 --oneline`
  - Expected output: short commit hash
  - Recovery: none typically required
- Line-numbered example:
  1. `git rev-parse --short HEAD`

### GIT-009
- What: `git branch --show-current`
- Why: confirm active branch before commit/push
- Who: project maintainer
- When: pre-commit and pre-push checks
- Where: repository root
- How:
  - Preconditions: in a git repository
  - Alternatives: `git status --short --branch`
  - Expected output: current branch name
  - Recovery: checkout intended branch and revalidate scope
- Line-numbered example:
  1. `git branch --show-current`

### GIT-010
- What: `git pull --rebase origin master`
- Why: synchronize local branch before pushing
- Who: project maintainer
- When: push rejected due to remote updates
- Where: repository root
- How:
  - Preconditions: clean or safely stashed working tree
  - Alternatives: `git pull origin master`; fetch + manual rebase
  - Expected output: local branch rebased on latest remote
  - Recovery: resolve conflicts, continue rebase, rerun tests
- Line-numbered example:
  1. `git pull --rebase origin master`
  2. `git push origin master`
