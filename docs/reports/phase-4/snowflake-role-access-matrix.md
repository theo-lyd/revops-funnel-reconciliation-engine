# Snowflake Role-to-Object Access Matrix

## Purpose
Define least-privilege role mapping for Snowflake deployment to support governance, auditability, and operational safety.

## Roles
- `ROLE_INGESTOR`
- `ROLE_TRANSFORMER`
- `ROLE_BI_READER`
- `ROLE_AUDITOR`

## Object domains
- Raw/Bronze: `REVOPS.BRONZE_RAW`
- Silver staging: `REVOPS.ANALYTICS_SILVER_STAGING`
- Silver intermediate: `REVOPS.ANALYTICS_SILVER_INTERMEDIATE`
- Gold marts: `REVOPS.ANALYTICS_GOLD`
- Snapshots/history: `REVOPS.SILVER_HISTORY`
- Observability: `REVOPS.OBSERVABILITY`

## Access matrix

| Role | Bronze Raw | Silver Staging | Silver Intermediate | Gold | Silver History | Observability |
|---|---|---|---|---|---|---|
| ROLE_INGESTOR | SELECT, INSERT, UPDATE | NONE | NONE | NONE | NONE | INSERT, UPDATE, SELECT |
| ROLE_TRANSFORMER | SELECT | CREATE, SELECT, INSERT, UPDATE | CREATE, SELECT, INSERT, UPDATE | CREATE, SELECT, INSERT, UPDATE | CREATE, SELECT, INSERT, UPDATE | SELECT, INSERT |
| ROLE_BI_READER | NONE | NONE | SELECT (optional) | SELECT | SELECT (optional) | SELECT (limited) |
| ROLE_AUDITOR | SELECT | SELECT | SELECT | SELECT | SELECT | SELECT |

## Warehouse mapping
- `WH_INGEST`: ROLE_INGESTOR
- `WH_TRANSFORM`: ROLE_TRANSFORMER
- `WH_BI`: ROLE_BI_READER
- `WH_AUDIT`: ROLE_AUDITOR

## Governance notes
- No role should have ownership of all domains.
- DDL rights limited to transformer role under change control.
- BI role must be read-only on approved semantic and gold assets.
- Audit role must be non-mutating.

## Review cadence
- Quarterly review or after any major architecture change.
- Mandatory review after security incidents.
