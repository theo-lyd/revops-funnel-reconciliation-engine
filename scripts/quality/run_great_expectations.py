"""Run Great Expectations-style validations against curated funnel tables."""

from __future__ import annotations

import importlib

import pandas as pd
from great_expectations.dataset import PandasDataset

from revops_funnel.config import get_settings


def load_dataframe(query: str) -> pd.DataFrame:
    settings = get_settings()
    duckdb = importlib.import_module("duckdb")
    conn = duckdb.connect(settings.duckdb_path, read_only=True)
    df = conn.execute(query).df()
    conn.close()
    return df


def validate_sales_pipeline() -> list[str]:
    errors: list[str] = []
    df = load_dataframe(
        """
        select opportunity_id, engage_date, close_date, close_value
        from analytics_silver_intermediate.int_opportunity_enriched
        """
    )
    validator = PandasDataset(df)

    if not validator.expect_column_values_to_not_be_null("opportunity_id")["success"]:
        errors.append("opportunity_id contains null values")

    if not validator.expect_column_values_to_be_between(
        "close_value", min_value=0, max_value=1000000, mostly=1.0
    )["success"]:
        errors.append("close_value is outside expected range [0, 1,000,000]")

    closed_df = df[df["close_date"].notna() & df["engage_date"].notna()]
    closed_validator = PandasDataset(closed_df)
    if not closed_validator.expect_column_pair_values_A_to_be_greater_than_B(
        "close_date", "engage_date", or_equal=True
    )["success"]:
        errors.append("close_date is earlier than engage_date for one or more rows")

    return errors


def main() -> None:
    failures = validate_sales_pipeline()
    if failures:
        print("Great Expectations validation failed:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("Great Expectations validation passed.")


if __name__ == "__main__":
    main()
