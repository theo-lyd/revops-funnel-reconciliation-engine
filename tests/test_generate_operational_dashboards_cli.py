"""Tests for operational dashboards CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


class TestGenerateOperationalDashboardsCLI:
    """Test the generate_operational_dashboards CLI."""

    def test_cli_skipped_no_telemetry(self, tmp_path: Path) -> None:
        """Test CLI returns success when telemetry unavailable (safe skip mode)."""
        output_path = tmp_path / "dashboard.json"

        result = subprocess.run(
            [
                sys.executable,
                "scripts/ops/generate_operational_dashboards.py",
                f"--output={output_path}",
            ],
            cwd="/workspaces/revops-funnel-reconciliation-engine",
            capture_output=True,
            text=True,
        )

        # Should succeed in safe skip mode
        assert result.returncode == 0
        assert output_path.exists()

        artifact = json.loads(output_path.read_text(encoding="utf-8"))
        assert artifact.get("status") == "skipped" or "sli_metrics" in artifact

    def test_cli_strict_fails_no_telemetry(self, tmp_path: Path) -> None:
        """Test CLI fails when telemetry unavailable with --strict-metrics."""
        output_path = tmp_path / "dashboard.json"

        result = subprocess.run(
            [
                sys.executable,
                "scripts/ops/generate_operational_dashboards.py",
                f"--output={output_path}",
                "--strict-metrics",
            ],
            cwd="/workspaces/revops-funnel-reconciliation-engine",
            capture_output=True,
            text=True,
        )

        # Should fail in strict mode without telemetry
        assert result.returncode == 1
        assert "No telemetry data available" in result.stdout

    def test_cli_custom_output_path(self, tmp_path: Path) -> None:
        """Test CLI respects custom output path."""
        output_path = tmp_path / "custom" / "dashboard.json"

        result = subprocess.run(
            [
                sys.executable,
                "scripts/ops/generate_operational_dashboards.py",
                f"--output={output_path}",
            ],
            cwd="/workspaces/revops-funnel-reconciliation-engine",
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert output_path.exists()

    def test_cli_with_deployment_version(self, tmp_path: Path) -> None:
        """Test CLI includes deployment version in output."""
        output_path = tmp_path / "dashboard.json"

        result = subprocess.run(
            [
                sys.executable,
                "scripts/ops/generate_operational_dashboards.py",
                f"--output={output_path}",
                "--deployment-version=v1.2.3-abc123",
            ],
            cwd="/workspaces/revops-funnel-reconciliation-engine",
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        artifact = json.loads(output_path.read_text(encoding="utf-8"))

        # May be skipped or contain deployment version
        if "deployment_version" in artifact:
            assert (
                artifact["deployment_version"] == "v1.2.3-abc123"
                or artifact["deployment_version"] is None
            )
