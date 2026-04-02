from __future__ import annotations

import json
from pathlib import Path

from revops_funnel.reporting_pack import build_reporting_pack, write_reporting_pack


def test_build_reporting_pack_collects_assets(tmp_path: Path) -> None:
    executive_sql = tmp_path / "executive.sql"
    public_sql = tmp_path / "public.sql"
    executive_sql.write_text("select 1", encoding="utf-8")
    public_sql.write_text("select 2", encoding="utf-8")

    payload = build_reporting_pack(
        query_files=[
            ("Executive", "executive", executive_sql),
            ("Public Sector", "public-sector", public_sql),
        ],
        package_name="public-sector-and-executive-reporting-pack",
        package_version="1.0.0",
    )

    assert payload["asset_count"] == 2
    assert payload["package_name"] == "public-sector-and-executive-reporting-pack"
    assert payload["assets"][0]["name"] == "Executive"
    assert payload["assets"][1]["audience"] == "public-sector"


def test_write_reporting_pack_creates_json_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / "pack.json"
    payload = {
        "package_name": "public-sector-and-executive-reporting-pack",
        "package_version": "1.0.0",
        "asset_count": 0,
        "assets": [],
    }

    artifact = write_reporting_pack(str(output_path), payload)
    loaded = json.loads(artifact.read_text(encoding="utf-8"))
    assert loaded["package_name"] == "public-sector-and-executive-reporting-pack"
