# Batch 6.1: Monitoring Email Delivery

## Objective
Add an optional email delivery path for monitoring reports so anomaly detection can notify stakeholders without changing the existing JSON and Markdown artifacts.

## Deliverables
- `src/revops_funnel/notifications.py`
- `scripts/analytics/anomaly_monitor.py`
- `tests/test_notifications.py`

## What Changed
1. Added a shared SMTP helper that composes monitoring emails from the Phase 5 report model.
2. Wired the anomaly monitor CLI to send email alerts only when findings exist and SMTP settings are configured.
3. Preserved local-safe behavior when SMTP credentials or recipients are missing.
4. Added tests for email composition, SMTP delivery, and skip behavior.

## Validation
- Fixture-based tests cover the new email transport path.
- The implementation is designed to be no-op in dev environments without SMTP settings.

## Notes
- This batch extends the Phase 5 monitoring workflow rather than replacing it.
- Existing JSON and Markdown artifacts remain the primary report outputs.
