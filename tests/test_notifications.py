from __future__ import annotations

from unittest.mock import patch

from revops_funnel.analytics_monitoring import AnomalyFinding, MonitoringReport
from revops_funnel.notifications import (
    EmailNotificationConfig,
    build_monitoring_email,
    send_monitoring_email,
)


def _sample_report() -> MonitoringReport:
    finding = AnomalyFinding(
        regional_office="London",
        metric_name="win_rate",
        latest_month="2026-04-01",
        latest_value=0.68,
        baseline_mean=0.40,
        baseline_std=0.05,
        z_score=5.6,
        change_pct=0.70,
        severity="critical",
        direction="increase",
    )
    return MonitoringReport(
        generated_at_utc="2026-04-01T00:00:00+00:00",
        sensitivity=2.0,
        cadence_hours=24,
        source="duckdb",
        recipients=["alerts@example.com"],
        findings=[finding],
    )


def test_build_monitoring_email_includes_summary() -> None:
    message = build_monitoring_email(_sample_report())

    assert message["Subject"].startswith("[RevOps] Monitoring alert")
    assert "London" in message.get_content()
    assert "critical" in message.get_content()


def test_send_monitoring_email_uses_smtp() -> None:
    report = _sample_report()
    config = EmailNotificationConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="user",
        smtp_password="smtp-pass",  # pragma: allowlist secret
        smtp_sender="alerts@example.com",
    )

    with patch("revops_funnel.notifications.smtplib.SMTP") as mock_smtp:
        server = mock_smtp.return_value.__enter__.return_value
        assert send_monitoring_email(report, config) is True

    mock_smtp.assert_called_once_with("smtp.example.com", 587, timeout=30)
    server.starttls.assert_called_once()
    server.login.assert_called_once_with("user", "smtp-pass")
    server.send_message.assert_called_once()


def test_send_monitoring_email_skips_without_configuration() -> None:
    report = _sample_report()
    config = EmailNotificationConfig(
        smtp_host="",
        smtp_sender="",
    )

    assert send_monitoring_email(report, config) is False
