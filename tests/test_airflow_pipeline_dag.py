from __future__ import annotations

import pytest


def test_revops_pipeline_uses_deterministic_full_dbt_path() -> None:
    pytest.importorskip("airflow")

    from dags.revops_end_to_end_pipeline import dag

    assert "dbt_build_full" in dag.task_ids
    assert "dbt_test_full" in dag.task_ids
    assert "parity_report" in dag.task_ids

    build_task = dag.get_task("dbt_build_full")
    test_task = dag.get_task("dbt_test_full")

    assert "make dbt-build" in build_task.bash_command
    assert "make dbt-test" in test_task.bash_command
