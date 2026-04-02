from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def test_generate_reporting_pack_cli_success(tmp_path: Path) -> None:
    output_path = tmp_path / "reporting_pack.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/analytics/generate_reporting_pack.py",
            "--package-version",
            "1.2.0",
            f"--output={output_path}",
        ],
        cwd="/workspaces/revops-funnel-reconciliation-engine",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["package_version"] == "1.2.0"
    assert payload["asset_count"] >= 2


def test_generate_reporting_pack_cli_strict_missing_file_fails(tmp_path: Path) -> None:
    repo = Path("/workspaces/revops-funnel-reconciliation-engine")
    public_pack = repo / "docs/reports/phase-4/query-packs/metabase-public-sector-funnel-view.sql"
    backup = tmp_path / "metabase-public-sector-funnel-view.sql.bak"

    shutil.copyfile(public_pack, backup)
    public_pack.unlink()
    try:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/analytics/generate_reporting_pack.py",
                "--strict-files",
                f"--output={tmp_path / 'reporting_pack.json'}",
            ],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1
        assert "missing query pack files" in result.stdout.lower()
    finally:
        shutil.copyfile(backup, public_pack)
