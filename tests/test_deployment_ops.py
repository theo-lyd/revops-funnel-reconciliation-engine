from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import requests

from revops_funnel.deployment_ops import (
    build_dbt_selector,
    create_deployment_promotion_report,
    create_deployment_rollback_report,
    dispatch_rollback_incident_payload,
    escalate_rollback_dead_letter,
    refresh_runtime_caches,
    resolve_selector_decision,
    validate_release_actor_access,
    write_cache_refresh_report,
    write_selector_decision_report,
)


def test_build_dbt_selector_expands_downstream_layers() -> None:
    selector = build_dbt_selector([Path("dbt/models/staging/crm/example.sql")])
    assert selector == "path:models/staging path:models/intermediate path:models/marts"


def test_build_dbt_selector_defaults_when_no_dbt_changes() -> None:
    selector = build_dbt_selector([Path("README.md")])
    assert selector == "path:models/staging path:models/intermediate path:models/marts"


def test_refresh_runtime_caches_recreates_directories(tmp_path: Path) -> None:
    cache_a = tmp_path / "streamlit-cache"
    cache_b = tmp_path / "artifact-cache"
    cache_a.mkdir()
    cache_b.mkdir()
    (cache_a / "stale.txt").write_text("stale", encoding="utf-8")

    report = refresh_runtime_caches([cache_a, cache_b])

    assert cache_a.exists()
    assert cache_b.exists()
    assert report.refreshed_paths == [str(cache_a), str(cache_b)]


def test_create_deployment_promotion_report_requires_passed_parity(tmp_path: Path) -> None:
    parity_report = tmp_path / "parity.json"
    cache_report = tmp_path / "cache.json"
    output = tmp_path / "promotion.json"
    parity_report.write_text('{"status": "passed"}', encoding="utf-8")
    cache_report.write_text(
        (
            '{"refreshed_at_utc": "2026-04-01T00:00:00+00:00", '
            '"refreshed_paths": [".streamlit/cache"]}'
        ),
        encoding="utf-8",
    )

    report = create_deployment_promotion_report(
        release_id="release-123",
        selector="path:models/marts",
        parity_report_path=parity_report,
        cache_refresh_report_path=cache_report,
        source_base_ref="origin/master",
        git_commit_sha="abc123",
        workflow_run_id="run-99",
        output_path=output,
    )

    assert output.exists()
    assert report.release_id == "release-123"
    assert report.contract_version
    assert report.correlation_id
    assert report.parity_status == "passed"
    assert report.git_commit_sha == "abc123"
    assert report.workflow_run_id == "run-99"
    assert report.release_gate_status == "passed"
    assert report.parity_report_sha256
    assert report.cache_refresh_report_sha256


def test_write_cache_refresh_report_creates_json(tmp_path: Path) -> None:
    cache_a = tmp_path / "cache-a"
    cache_b = tmp_path / "cache-b"
    report = refresh_runtime_caches([cache_a, cache_b])
    output = tmp_path / "cache-refresh.json"

    write_cache_refresh_report(report, output)

    assert output.exists()


def test_resolve_selector_decision_marks_fallback_on_git_error() -> None:
    with patch(
        "revops_funnel.deployment_ops.subprocess.run",
        return_value=SimpleNamespace(returncode=128, stdout=""),
    ):
        report = resolve_selector_decision("origin/master")

    assert report.fallback_used is True
    assert report.fallback_reason == "git-diff-failed"
    assert report.selector == "path:models/staging path:models/intermediate path:models/marts"


def test_resolve_selector_decision_strict_raises_on_git_error() -> None:
    with patch(
        "revops_funnel.deployment_ops.subprocess.run",
        return_value=SimpleNamespace(returncode=128, stdout=""),
    ):
        try:
            resolve_selector_decision("origin/master", strict_mode=True)
        except RuntimeError as error:
            assert "Selector resolution failed" in str(error)
        else:  # pragma: no cover
            raise AssertionError("Expected strict selector mode to raise RuntimeError")


def test_write_selector_decision_report_creates_json(tmp_path: Path) -> None:
    report = resolve_selector_decision(base_ref="", strict_mode=False)
    output = tmp_path / "selector.json"

    write_selector_decision_report(report, output)

    assert output.exists()


def test_create_deployment_rollback_report_uses_promotion_context(tmp_path: Path) -> None:
    promotion_report = tmp_path / "promotion.json"
    rollback_report = tmp_path / "rollback.json"
    promotion_report.write_text(
        (
            '{"source_base_ref": "origin/master", '
            '"git_commit_sha": "deadbeef", '
            '"workflow_run_id": "12345"}'
        ),
        encoding="utf-8",
    )

    report = create_deployment_rollback_report(
        release_id="release-007",
        rollback_reason="parity-failed",
        rollback_trigger="github-actions",
        promotion_report_path=promotion_report,
        output_path=rollback_report,
    )

    assert rollback_report.exists()
    assert report.release_id == "release-007"
    assert report.git_commit_sha == "deadbeef"
    assert report.workflow_run_id == "12345"
    assert report.rollback_actions


def test_validate_release_actor_access() -> None:
    allowed, allowlist = validate_release_actor_access("alice,bob", "alice")
    assert allowed is True
    assert allowlist == ["alice", "bob"]

    blocked, allowlist_blocked = validate_release_actor_access("alice,bob", "charlie")
    assert blocked is False
    assert allowlist_blocked == ["alice", "bob"]

    allowed_ci, allowlist_ci = validate_release_actor_access(" Alice,BOB ", "alice")
    assert allowed_ci is True
    assert allowlist_ci == ["alice", "bob"]


def test_dispatch_rollback_incident_payload_skips_without_webhook(tmp_path: Path) -> None:
    payload = tmp_path / "rollback_incident_payload.json"
    output = tmp_path / "rollback_incident_dispatch.json"
    payload.write_text(
        json.dumps({"release_id": "release-123", "environment": "production"}),
        encoding="utf-8",
    )

    report = dispatch_rollback_incident_payload(
        incident_payload_path=payload,
        incident_webhook_url="",
        output_path=output,
    )

    assert report.dispatch_status == "skipped"
    assert report.contract_version
    assert report.correlation_id
    assert report.incident_webhook_configured is False
    assert report.attempt_count == 0
    assert report.dead_letter_created is False
    assert output.exists()


def test_dispatch_rollback_incident_payload_sends_webhook(tmp_path: Path) -> None:
    payload = tmp_path / "rollback_incident_payload.json"
    output = tmp_path / "rollback_incident_dispatch.json"
    payload.write_text(
        json.dumps({"release_id": "release-123", "environment": "production"}),
        encoding="utf-8",
    )

    class _Response:
        status_code = 202
        text = "accepted"

    with patch("revops_funnel.deployment_ops.requests.post", return_value=_Response()):
        report = dispatch_rollback_incident_payload(
            incident_payload_path=payload,
            incident_webhook_url="https://example.com/webhook",
            output_path=output,
        )

    assert report.dispatch_status == "sent"
    assert report.http_status_code == 202
    assert report.attempt_count == 1
    assert report.dead_letter_created is False
    assert output.exists()


def test_dispatch_rollback_incident_payload_handles_request_error(tmp_path: Path) -> None:
    payload = tmp_path / "rollback_incident_payload.json"
    output = tmp_path / "rollback_incident_dispatch.json"
    dead_letter = tmp_path / "rollback_incident_dead_letter.json"
    payload.write_text(
        json.dumps({"release_id": "release-123", "environment": "production"}),
        encoding="utf-8",
    )

    with patch(
        "revops_funnel.deployment_ops.requests.post",
        side_effect=requests.RequestException("network down"),
    ):
        report = dispatch_rollback_incident_payload(
            incident_payload_path=payload,
            incident_webhook_url="https://example.com/webhook",
            dead_letter_output_path=dead_letter,
            output_path=output,
        )

    assert report.dispatch_status == "failed"
    assert "network down" in report.error_message
    assert report.dead_letter_created is True
    assert report.dead_letter_path == str(dead_letter)
    dead_letter_payload = json.loads(dead_letter.read_text(encoding="utf-8"))
    assert dead_letter_payload["incident_webhook_url"] == "redacted"
    assert dead_letter_payload["incident_webhook_endpoint_fingerprint"]
    assert output.exists()
    assert dead_letter.exists()


def test_dispatch_rollback_incident_payload_retries_then_succeeds(tmp_path: Path) -> None:
    payload = tmp_path / "rollback_incident_payload.json"
    output = tmp_path / "rollback_incident_dispatch.json"
    payload.write_text(
        json.dumps({"release_id": "release-123", "environment": "production"}),
        encoding="utf-8",
    )

    class _SuccessResponse:
        status_code = 200
        text = "ok"

    with patch(
        "revops_funnel.deployment_ops.requests.post",
        side_effect=[requests.RequestException("transient"), _SuccessResponse()],
    ):
        report = dispatch_rollback_incident_payload(
            incident_payload_path=payload,
            incident_webhook_url="https://example.com/webhook",
            max_attempts=2,
            backoff_seconds=0,
            output_path=output,
        )

    assert report.dispatch_status == "sent"
    assert report.attempt_count == 2
    assert report.max_attempts == 2
    assert report.dead_letter_created is False


def test_dispatch_rollback_incident_payload_writes_dead_letter_on_non_2xx(tmp_path: Path) -> None:
    payload = tmp_path / "rollback_incident_payload.json"
    output = tmp_path / "rollback_incident_dispatch.json"
    dead_letter = tmp_path / "rollback_incident_dead_letter.json"
    payload.write_text(
        json.dumps({"release_id": "release-123", "environment": "production"}),
        encoding="utf-8",
    )

    class _FailureResponse:
        status_code = 503
        text = "unavailable"

    with patch(
        "revops_funnel.deployment_ops.requests.post",
        return_value=_FailureResponse(),
    ):
        report = dispatch_rollback_incident_payload(
            incident_payload_path=payload,
            incident_webhook_url="https://example.com/webhook",
            max_attempts=2,
            backoff_seconds=0,
            dead_letter_output_path=dead_letter,
            output_path=output,
        )

    assert report.dispatch_status == "failed"
    assert report.http_status_code == 503
    assert report.attempt_count == 2
    assert report.dead_letter_created is True
    assert dead_letter.exists()


def test_escalate_rollback_dead_letter_skips_when_missing(tmp_path: Path) -> None:
    missing_dead_letter = tmp_path / "missing_dead_letter.json"
    output = tmp_path / "rollback_dead_letter_escalation.json"

    report = escalate_rollback_dead_letter(
        dead_letter_path=missing_dead_letter,
        escalation_webhook_url="https://example.com/escalation",
        output_path=output,
    )

    assert report.dead_letter_found is False
    assert report.escalation_status == "skipped-no-dead-letter"
    assert output.exists()


def test_escalate_rollback_dead_letter_skips_without_webhook(tmp_path: Path) -> None:
    dead_letter = tmp_path / "rollback_incident_dead_letter.json"
    output = tmp_path / "rollback_dead_letter_escalation.json"
    dead_letter.write_text(
        json.dumps({"release_id": "release-123", "environment": "production"}),
        encoding="utf-8",
    )

    report = escalate_rollback_dead_letter(
        dead_letter_path=dead_letter,
        escalation_webhook_url="",
        output_path=output,
    )

    assert report.dead_letter_found is True
    assert report.escalation_status == "skipped-no-webhook"
    assert report.contract_version
    assert report.correlation_id
    assert output.exists()


def test_escalate_rollback_dead_letter_sends_webhook(tmp_path: Path) -> None:
    dead_letter = tmp_path / "rollback_incident_dead_letter.json"
    output = tmp_path / "rollback_dead_letter_escalation.json"
    dead_letter.write_text(
        json.dumps({"release_id": "release-123", "environment": "production"}),
        encoding="utf-8",
    )

    class _Response:
        status_code = 202
        text = "accepted"

    with patch("revops_funnel.deployment_ops.requests.post", return_value=_Response()):
        report = escalate_rollback_dead_letter(
            dead_letter_path=dead_letter,
            escalation_webhook_url="https://example.com/escalation",
            output_path=output,
        )

    assert report.escalation_status == "sent"
    assert report.http_status_code == 202
    assert report.escalation_endpoint_fingerprint
    assert output.exists()


def test_escalate_rollback_dead_letter_retries_and_fails(tmp_path: Path) -> None:
    dead_letter = tmp_path / "rollback_incident_dead_letter.json"
    output = tmp_path / "rollback_dead_letter_escalation.json"
    dead_letter.write_text(
        json.dumps({"release_id": "release-123", "environment": "production"}),
        encoding="utf-8",
    )

    with patch(
        "revops_funnel.deployment_ops.requests.post",
        side_effect=requests.RequestException("endpoint down"),
    ):
        report = escalate_rollback_dead_letter(
            dead_letter_path=dead_letter,
            escalation_webhook_url="https://example.com/escalation",
            max_attempts=2,
            backoff_seconds=0,
            output_path=output,
        )

    assert report.escalation_status == "failed"
    assert report.attempt_count == 2
    assert "endpoint down" in report.error_message
    assert output.exists()
