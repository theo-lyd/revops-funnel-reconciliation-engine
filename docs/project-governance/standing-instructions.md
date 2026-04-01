# Standing Instructions For This Repository

These instructions are mandatory for all project execution batches and phases.

## 1) Phase reports are mandatory
At the completion of each phase, create a report document describing:
- Objectives for the phase.
- Batches completed.
- Deliverables created or changed.
- Validation outcomes.
- Risks, assumptions, and unresolved items.
- Readiness for the next phase.

Location convention:
- docs/reports/phase-X/
- Batch report naming: batch-X.Y-<topic>.md
- Phase end report naming: phase-X-end-report.md

## 2) Mandatory project-wide process documentation
The following files must be maintained for the entire project:
1. Issues log: issues, causes, where and when they happened, prevention, resolution, alternatives.
2. All Git commands used.
3. All Bash and shell commands used.
4. All Make commands used.
5. All Python, dbt, and DuckDB commands used.
6. All other commands used.

All command logs must be detailed for complete beginners using 5Ws and H:
- What command was executed.
- Why it was needed.
- Who executed it (role).
- When it was executed (date/time or phase context).
- Where it was executed (working directory, environment).
- How to run it safely, including prerequisites and expected output.

## 3) Commit and push policy
At successful completion of batches in each phase:
- Commit with a clear grouped message.
- Push to origin.
- Ensure only intended files are included.

## 4) End-to-end execution with phase stop-gates
Proceed end-to-end implementation, but stop after successful completion of each phase and request confirmation before continuing to the next phase.

Stop-gate checklist:
- All quality checks pass for the phase.
- Documentation updated.
- Commit and push completed.
- Go/no-go confirmation requested.

## 5) Documentation quality standard
This capstone is intended for technical and non-technical audiences, including industry experts and academic assessors. Documentation must therefore be:
- Precise and auditable.
- Understandable by non-technical stakeholders.
- Sufficient for defense and reproducibility.
