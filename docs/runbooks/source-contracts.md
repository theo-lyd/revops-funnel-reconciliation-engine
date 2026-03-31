# Source Contracts

## CRM batch files (`data/raw/crm`)
- `accounts.csv`: must include `account` primary business key.
- `products.csv`: must include `product` and `sales_price`.
- `sales_teams.csv`: must include `sales_agent`.
- `sales_pipeline.csv`: must include `opportunity_id`, `deal_stage`, `engage_date`.

## Synthetic leads API
Expected fields per event:
- `lead_id`
- `company_name`
- `email` (anonymized to `email_hash` before landing)
- `utm_source`
- `utm_campaign`
- `country`
- `created_at`

## Contract checks
- Primary/business keys cannot be null.
- Dates must parse to valid ISO date/timestamp values.
- Currency and numeric values must cast without overflow.
- Pipeline stage values must be in controlled enumeration.
