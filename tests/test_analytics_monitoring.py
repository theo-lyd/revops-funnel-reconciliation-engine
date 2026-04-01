from __future__ import annotations

from pathlib import Path

import pandas as pd

from revops_funnel.analytics_monitoring import (
    detect_anomalies,
    summarize_findings,
    write_monitoring_report,
)


def _sample_monitoring_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "metric_month": [
                "2026-01-01",
                "2026-02-01",
                "2026-03-01",
                "2026-04-01",
                "2026-01-01",
                "2026-02-01",
                "2026-03-01",
                "2026-04-01",
            ],
            "regional_office": [
                "London",
                "London",
                "London",
                "London",
                "Paris",
                "Paris",
                "Paris",
                "Paris",
            ],
            "total_opportunities": [10, 12, 11, 13, 8, 9, 9, 10],
            "won_opportunities": [4, 5, 4, 5, 3, 3, 3, 4],
            "lost_opportunities": [1, 1, 2, 1, 1, 1, 1, 1],
            "leakage_points": [0, 1, 0, 1, 0, 0, 0, 0],
            "avg_cycle_days": [20.0, 19.0, 18.0, 35.0, 15.0, 15.0, 14.5, 14.0],
            "avg_stage_age_days": [5.0, 5.5, 5.2, 11.0, 4.0, 4.2, 4.1, 4.0],
            "win_rate": [0.4, 0.42, 0.41, 0.68, 0.35, 0.33, 0.34, 0.36],
            "leakage_ratio": [0.1, 0.12, 0.1, 0.35, 0.05, 0.05, 0.04, 0.05],
        }
    )


def test_detect_anomalies_flags_spike() -> None:
    findings = detect_anomalies(_sample_monitoring_frame(), sensitivity=1.0)
    assert findings
    assert any(finding.regional_office == "London" for finding in findings)


def test_summarize_findings_mentions_anomalies() -> None:
    findings = detect_anomalies(_sample_monitoring_frame(), sensitivity=1.0)
    summary = summarize_findings(findings)
    assert "anomalies" in summary.lower()


def test_write_monitoring_report_creates_json(tmp_path: Path) -> None:
    findings = detect_anomalies(_sample_monitoring_frame(), sensitivity=1.0)
    output_path = tmp_path / "report.json"
    report = write_monitoring_report(
        findings=findings,
        output_path=str(output_path),
        sensitivity=1.0,
        cadence_hours=24,
        source="duckdb",
        recipients=["stakeholder@example.com"],
    )

    assert output_path.exists()
    assert report.anomaly_count == len(findings)
    assert report.source == "duckdb"
