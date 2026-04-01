"""Shared anomaly detection helpers for Phase 5 monitoring."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

MONITORED_METRICS = {
    "win_rate": "win_rate",
    "leakage_ratio": "leakage_ratio",
    "avg_cycle_days": "avg_cycle_days",
}


@dataclass(frozen=True)
class AnomalyFinding:
    regional_office: str
    metric_name: str
    latest_month: str
    latest_value: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    change_pct: float
    severity: str
    direction: str


@dataclass(frozen=True)
class MonitoringReport:
    generated_at_utc: str
    sensitivity: float
    cadence_hours: int
    source: str
    recipients: list[str]
    findings: list[AnomalyFinding]

    @property
    def anomaly_count(self) -> int:
        return len(self.findings)

    @property
    def severe_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity in {"high", "critical"})

    def to_dict(self) -> dict[str, object]:
        return {
            "generated_at_utc": self.generated_at_utc,
            "sensitivity": self.sensitivity,
            "cadence_hours": self.cadence_hours,
            "source": self.source,
            "recipients": self.recipients,
            "anomaly_count": self.anomaly_count,
            "severe_count": self.severe_count,
            "findings": [asdict(finding) for finding in self.findings],
        }


def detect_anomalies(frame: pd.DataFrame, sensitivity: float) -> list[AnomalyFinding]:
    required_columns = {"metric_month", "regional_office", *MONITORED_METRICS.values()}
    if frame.empty or not required_columns.issubset(frame.columns):
        return []

    normalized = frame.copy()
    normalized["metric_month"] = pd.to_datetime(normalized["metric_month"], errors="coerce")
    normalized = normalized.dropna(subset=["metric_month", "regional_office"])
    normalized = normalized.sort_values(["regional_office", "metric_month"])

    findings: list[AnomalyFinding] = []
    for office, office_frame in normalized.groupby("regional_office"):
        for metric_name in MONITORED_METRICS.values():
            metric_frame = office_frame[["metric_month", metric_name]].dropna()
            if len(metric_frame) < 4:
                continue

            history = metric_frame.iloc[:-1]
            latest_row = metric_frame.iloc[-1]
            baseline_mean = float(history[metric_name].mean())
            baseline_std = float(history[metric_name].std(ddof=0))
            latest_value = float(latest_row[metric_name])
            delta = latest_value - baseline_mean
            if baseline_mean == 0:
                change_pct = 0.0 if latest_value == 0 else 1.0
            else:
                change_pct = delta / abs(baseline_mean)

            if baseline_std == 0:
                z_score = float("inf") if delta != 0 else 0.0
            else:
                z_score = abs(delta) / baseline_std

            if z_score < sensitivity and abs(change_pct) < 0.2:
                continue

            severity = _severity_from_signal(z_score, change_pct, sensitivity)
            direction = "increase" if delta >= 0 else "decrease"
            findings.append(
                AnomalyFinding(
                    regional_office=str(office),
                    metric_name=metric_name,
                    latest_month=latest_row["metric_month"].date().isoformat(),
                    latest_value=latest_value,
                    baseline_mean=baseline_mean,
                    baseline_std=baseline_std,
                    z_score=z_score,
                    change_pct=change_pct,
                    severity=severity,
                    direction=direction,
                )
            )

    return sorted(
        findings,
        key=lambda finding: (
            finding.severity,
            finding.regional_office,
            finding.metric_name,
        ),
        reverse=True,
    )


def _severity_from_signal(z_score: float, change_pct: float, sensitivity: float) -> str:
    if z_score == float("inf") or abs(change_pct) >= 0.5:
        return "critical"
    if z_score >= sensitivity * 1.5 or abs(change_pct) >= 0.3:
        return "high"
    if z_score >= sensitivity or abs(change_pct) >= 0.2:
        return "medium"
    return "low"


def summarize_findings(findings: list[AnomalyFinding]) -> str:
    if not findings:
        return "No anomalies detected in the latest monitoring window."

    severe_findings = [finding for finding in findings if finding.severity in {"high", "critical"}]
    metric_names = ", ".join(sorted({finding.metric_name for finding in findings}))
    office_names = ", ".join(sorted({finding.regional_office for finding in findings}))
    return (
        f"Detected {len(findings)} anomalies across offices [{office_names}] for "
        f"metrics [{metric_names}]. High-priority items: {len(severe_findings)}."
    )


def build_alert_message(findings: list[AnomalyFinding]) -> str:
    if not findings:
        return "Monitoring check completed with no anomalies detected."

    lines = ["Monitoring alert summary:"]
    for finding in findings[:5]:
        lines.append(
            "- "
            f"{finding.regional_office} / {finding.metric_name}: "
            f"{finding.direction} to {finding.latest_value:.4f} "
            f"(baseline {finding.baseline_mean:.4f}, z={finding.z_score:.2f}, "
            f"severity={finding.severity})"
        )
    return "\n".join(lines)


def write_monitoring_report(
    findings: list[AnomalyFinding],
    output_path: str,
    sensitivity: float,
    cadence_hours: int,
    source: str,
    recipients: list[str],
) -> MonitoringReport:
    report = MonitoringReport(
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        sensitivity=sensitivity,
        cadence_hours=cadence_hours,
        source=source,
        recipients=recipients,
        findings=findings,
    )
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return report
