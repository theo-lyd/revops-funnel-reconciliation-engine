# Semantic Metric Change Control SOP

## Purpose
Prevent KPI drift by enforcing controlled change management for semantic metrics used by dashboards, reports, and AI-assisted analytics.

## Scope
Applies to:
- `dim_metric_contract`
- semantic metric glossary
- BI query packs and dashboard definitions

## Change categories
- Minor: wording clarification without formula impact.
- Moderate: formula or filter adjustment that preserves business intent.
- Major: grain/denominator/ownership changes or KPI deprecation.

## Approval matrix
- Minor: RevOps Analytics Owner + Reviewer.
- Moderate: RevOps Analytics Owner + Data Engineering Owner + BI Owner.
- Major: Governance Board + Security Owner + Executive Sponsor.

## Required artifacts per change
1. Proposed change record with rationale.
2. Before/after SQL expression.
3. Affected models and dashboards.
4. Expected impact analysis.
5. Validation evidence:
   - `make quality-gate`
   - parity checks where applicable.
6. Effective date and rollback plan.

## Execution workflow
1. Open change request document and classify change level.
2. Update `dim_metric_contract` metadata (`contract_version`, `effective_from`, approvals).
3. Update semantic glossary and query packs.
4. Run full validation and capture results.
5. Obtain approvals per matrix.
6. Merge, deploy, and publish release note.

## Rollback policy
- Every moderate/major change must define rollback SQL and prior version reference.
- If post-deploy anomaly is detected, revert to prior contract version and notify stakeholders.

## Audit requirements
- Keep a complete log of approvals and validation outputs.
- Link change request ID in commit message and report artifacts.
