# Secrets and Access Policy

## Secret management
- Never commit credentials to the repository.
- Store runtime secrets in Codespaces Secrets (dev) and GitHub Actions Encrypted Secrets (CI).
- Use `.env.example` only for non-sensitive templates.
- Run `pre-commit` before each push to detect accidental secret leakage.

## Access model
- Principle of least privilege applies to all warehouse roles.
- Separate roles for ingestion, transformation, and read-only analytics.
- Rotate credentials on a fixed schedule (recommended: every 90 days).

## Environments
- Development: DuckDB local file + optional Snowflake dev role.
- Production: Snowflake role-based auth only.

## Required production environment variables
- SNOWFLAKE_ACCOUNT
- SNOWFLAKE_USER
- SNOWFLAKE_PASSWORD
- SNOWFLAKE_ROLE
- SNOWFLAKE_DATABASE
- SNOWFLAKE_WAREHOUSE
