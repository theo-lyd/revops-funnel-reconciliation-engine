"""Email notification helpers for monitoring workflows."""

from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from revops_funnel.analytics_monitoring import (
    MonitoringReport,
    build_alert_message,
    summarize_findings,
)


@dataclass(frozen=True)
class EmailNotificationConfig:
    smtp_host: str
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_sender: str = ""
    use_tls: bool = True

    @classmethod
    def from_env(cls) -> EmailNotificationConfig:
        return cls(
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            smtp_sender=os.getenv("SMTP_SENDER", ""),
            use_tls=os.getenv("SMTP_USE_TLS", "true").strip().lower()
            not in {
                "0",
                "false",
                "no",
                "off",
            },
        )

    def is_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_sender)


def build_monitoring_email(report: MonitoringReport) -> EmailMessage:
    message = EmailMessage()
    subject_prefix = "[RevOps] Monitoring alert"
    if report.severe_count == 0:
        subject_prefix = "[RevOps] Monitoring summary"

    message["Subject"] = f"{subject_prefix}: {report.anomaly_count} findings"
    message["From"] = report.recipients[0] if report.recipients else "noreply@example.com"
    message["To"] = ", ".join(report.recipients)

    lines = [
        f"Generated at: {report.generated_at_utc}",
        f"Source: {report.source}",
        f"Recipients: {', '.join(report.recipients) if report.recipients else 'none'}",
        f"Anomaly count: {report.anomaly_count}",
        f"Severe count: {report.severe_count}",
        "",
        summarize_findings(report.findings),
        "",
        build_alert_message(report.findings),
    ]
    message.set_content("\n".join(lines))
    return message


def send_monitoring_email(
    report: MonitoringReport,
    config: EmailNotificationConfig | None = None,
) -> bool:
    if not report.findings or not report.recipients:
        return False

    email_config = config or EmailNotificationConfig.from_env()
    if not email_config.is_configured():
        return False

    message = build_monitoring_email(report)
    message.replace_header("From", email_config.smtp_sender)

    with smtplib.SMTP(email_config.smtp_host, email_config.smtp_port, timeout=30) as server:
        if email_config.use_tls:
            server.starttls()
        if email_config.smtp_username:
            server.login(email_config.smtp_username, email_config.smtp_password)
        server.send_message(message)

    return True
