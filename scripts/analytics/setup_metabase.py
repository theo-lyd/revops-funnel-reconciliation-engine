#!/usr/bin/env python3
"""
Metabase setup and configuration script for Phase 5 dashboard foundation.

This script initializes Metabase with DuckDB and Snowflake data sources
and creates foundational dashboard connections.

Usage:
    python scripts/analytics/setup_metabase.py --host http://localhost --port 3000
"""

import argparse
import os
import sys
import time
from typing import Any

import requests

# Configuration from environment
METABASE_HOST = os.getenv("METABASE_HOST", "http://localhost")
METABASE_PORT = os.getenv("METABASE_PORT", "3000")
METABASE_ADMIN_EMAIL = os.getenv("METABASE_ADMIN_EMAIL", "admin@example.com")
METABASE_ADMIN_PASSWORD = os.getenv("METABASE_ADMIN_PASSWORD", "metabase")

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "./data/warehouse/revops.duckdb")
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT", "")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER", "")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD", "")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "REVOPS")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "TRANSFORMING")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "analytics")


class MetabaseClient:
    """Client for Metabase API interactions."""

    def __init__(self, host: str, port: str, admin_email: str, admin_password: str):
        """Initialize Metabase client."""
        self.base_url = f"{host}:{port}/api"
        self.admin_email = admin_email
        self.admin_password = admin_password
        self.session_token: str | None = None
        self.user_id: int | None = None

    def authenticate(self) -> bool:
        """Authenticate with Metabase admin credentials."""
        try:
            response = requests.post(
                f"{self.base_url}/session",
                json={"username": self.admin_email, "password": self.admin_password},
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                self.session_token = data.get("id")
                self.user_id = data.get("user_id")
                print(f"✓ Authenticated to Metabase as {self.admin_email}")
                return True
            else:
                print(f"✗ Authentication failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Connection error: {e}")
            return False

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication token."""
        headers = {"Content-Type": "application/json"}
        if self.session_token:
            headers["X-Metabase-Session"] = self.session_token
        return headers

    def add_duckdb_database(self, db_name: str, db_path: str) -> int | None:
        """Add DuckDB database as data source."""
        payload = {
            "name": db_name,
            "engine": "duckdb",
            "details": {"db": db_path},
            "is_full_sync": True,
            "auto_run_queries": True,
        }
        try:
            response = requests.post(
                f"{self.base_url}/database",
                json=payload,
                headers=self._get_headers(),
                timeout=30,
            )
            if response.status_code == 200:
                db_id = response.json().get("id")
                print(f"✓ Added DuckDB database: {db_name} (ID: {db_id})")
                return int(db_id) if db_id else None
            else:
                print(f"✗ Failed to add DuckDB database: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"✗ Error adding DuckDB database: {e}")
            return None

    def add_snowflake_database(
        self, db_name: str, account: str, user: str, password: str, warehouse: str, database: str
    ) -> int | None:
        """Add Snowflake database as data source."""
        payload = {
            "name": db_name,
            "engine": "snowflake",
            "details": {
                "account": account,
                "user": user,
                "password": password,
                "warehouse": warehouse,
                "db": database,
            },
            "is_full_sync": False,
            "auto_run_queries": True,
        }
        try:
            response = requests.post(
                f"{self.base_url}/database",
                json=payload,
                headers=self._get_headers(),
                timeout=30,
            )
            if response.status_code == 200:
                db_id = response.json().get("id")
                print(f"✓ Added Snowflake database: {db_name} (ID: {db_id})")
                return int(db_id) if db_id else None
            else:
                print(f"✗ Failed to add Snowflake database: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"✗ Error adding Snowflake database: {e}")
            return None

    def sync_database(self, db_id: int) -> bool:
        """Trigger metadata sync for database."""
        try:
            response = requests.post(
                f"{self.base_url}/database/{db_id}/sync_schema",
                headers=self._get_headers(),
                timeout=60,
            )
            if response.status_code == 200:
                print(f"✓ Synced database schema (ID: {db_id})")
                return True
            else:
                print(f"✗ Failed to sync database: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Error syncing database: {e}")
            return False

    def get_database_tables(self, db_id: int) -> dict[str, Any]:
        """Get tables and metadata for database."""
        try:
            response = requests.get(
                f"{self.base_url}/database/{db_id}/metadata",
                headers=self._get_headers(),
                timeout=30,
            )
            if response.status_code == 200:
                return response.json()  # type: ignore[no-any-return]
            else:
                print(f"✗ Failed to get database metadata: {response.status_code}")
                return {}
        except requests.exceptions.RequestException as e:
            print(f"✗ Error getting database metadata: {e}")
            return {}


def setup_duckdb_source(client: MetabaseClient) -> int | None:
    """Set up DuckDB as data source."""
    print("\n[Step 1/3] Setting up DuckDB data source...")

    # Verify DuckDB file exists
    if not os.path.exists(DUCKDB_PATH):
        print(f"✗ DuckDB file not found at {DUCKDB_PATH}")
        return None

    db_id = client.add_duckdb_database("DuckDB Local", DUCKDB_PATH)
    if db_id is None:
        return None

    # Wait briefly then sync
    print("  Waiting for connection to stabilize...")
    time.sleep(2)
    if client.sync_database(db_id):
        return db_id
    else:
        print("✗ Failed to sync DuckDB schema")
        return None


def setup_snowflake_source(client: MetabaseClient) -> int | None:
    """Set up Snowflake as data source (if credentials present)."""
    print("\n[Step 2/3] Setting up Snowflake data source...")

    if not SNOWFLAKE_ACCOUNT or not SNOWFLAKE_USER or not SNOWFLAKE_PASSWORD:
        print("⊘ Snowflake credentials not configured; skipping Snowflake setup")
        print("  (Set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD to enable)")
        return None

    db_id = client.add_snowflake_database(
        "Snowflake Production",
        SNOWFLAKE_ACCOUNT,
        SNOWFLAKE_USER,
        SNOWFLAKE_PASSWORD,
        SNOWFLAKE_WAREHOUSE,
        SNOWFLAKE_DATABASE,
    )
    if db_id is None:
        return None

    # Wait briefly then sync
    print("  Waiting for connection to stabilize...")
    time.sleep(2)
    if client.sync_database(db_id):
        return db_id
    else:
        print("✗ Failed to sync Snowflake schema")
        return None


def main() -> None:
    """Main setup flow."""
    parser = argparse.ArgumentParser(description="Setup Metabase for Phase 5 dashboards")
    parser.add_argument("--host", default=METABASE_HOST, help="Metabase host")
    parser.add_argument("--port", default=METABASE_PORT, help="Metabase port")
    parser.add_argument("--email", default=METABASE_ADMIN_EMAIL, help="Admin email")
    parser.add_argument("--password", default=METABASE_ADMIN_PASSWORD, help="Admin password")
    args = parser.parse_args()

    print("=" * 70)
    print("Metabase Setup for Phase 5: AI-Driven Analytics and Visualization")
    print("=" * 70)

    # Initialize client
    client = MetabaseClient(args.host, args.port, args.email, args.password)

    # Check connectivity
    try:
        response = requests.get(f"{client.base_url}/health", timeout=5)
        if response.status_code != 200:
            print("✗ Metabase appears to be down (health check failed)")
            print(f"  Ensure Metabase is running at {args.host}:{args.port}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot reach Metabase: {e}")
        print(f"  Ensure Metabase is running at {args.host}:{args.port}")
        sys.exit(1)

    print(f"\n✓ Metabase is reachable at {args.host}:{args.port}")

    # Authenticate
    if not client.authenticate():
        print("✗ Failed to authenticate to Metabase")
        sys.exit(1)

    # Set up data sources
    duckdb_id = setup_duckdb_source(client)
    snowflake_id = setup_snowflake_source(client)

    # Summary
    print("\n" + "=" * 70)
    print("Metabase Setup Complete")
    print("=" * 70)
    print(f"✓ DuckDB Local database: {'Configured' if duckdb_id else 'Skipped'}")
    print(f"✓ Snowflake Production database: {'Configured' if snowflake_id else 'Skipped'}")
    print("\nNext steps:")
    print("1. Open Metabase in browser: http://localhost:3000")
    print("2. Create dashboards from configured data sources")
    print("3. Use Gold layer models (fct_revenue_funnel, bi_executive_funnel_overview)")
    print("4. See docs/reports/phase-5/batch-5.1-dashboard-foundation.md for templates")
    print("=" * 70)


if __name__ == "__main__":
    main()
