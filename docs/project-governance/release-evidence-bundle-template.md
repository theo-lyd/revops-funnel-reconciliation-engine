# Release Evidence Bundle Template

Use this template for batch or phase releases to keep an auditable, presentation-ready evidence package.

## 1) Release identity
- Release ID:
- Scope (batch/phase):
- Commit hash(es):
- Date/time:
- Release owner:
- Approvers:

## 2) Change summary
- What changed:
- Why it changed:
- Stakeholders impacted:
- Rollback impact:

## 3) Validation evidence
- Lint result:
- Test result:
- dbt build result:
- dbt test result:
- Source freshness result (if applicable):
- Query-pack validation result:
- Quality checks result:
- Great Expectations result:
- Metric parity result (local or strict):

## 4) Governance evidence
- Semantic contract version changes:
- Security and access checks:
- Role matrix confirmation:
- Secrets rotation/emergency path status:

## 5) Deployment evidence
- Target environment:
- Deployment commands executed:
- Runtime observations:
- Post-deploy checks:

## 6) Risk and exception register
- Open risks:
- Temporary exceptions:
- Mitigation owners:
- Review date:

## 7) Sign-off
- Engineering sign-off:
- Governance sign-off:
- Business sign-off:
- Final status: GO / NO-GO
