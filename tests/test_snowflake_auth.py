from __future__ import annotations

from revops_funnel.snowflake_auth import (
    SnowflakeAuthConfig,
    build_snowflake_connector_auth_kwargs,
    missing_required_snowflake_env,
)


def test_missing_required_snowflake_env_accepts_password_auth() -> None:
    config = SnowflakeAuthConfig(
        account="acct",
        user="svc_user",
        password="pwd-value",  # pragma: allowlist secret
        private_key_path="",
        private_key_passphrase="",
    )

    assert missing_required_snowflake_env(config) == []


def test_missing_required_snowflake_env_accepts_key_pair_auth() -> None:
    config = SnowflakeAuthConfig(
        account="acct",
        user="svc_user",
        password="",
        private_key_path="/tmp/key.p8",
        private_key_passphrase="passphrase",  # pragma: allowlist secret
    )

    assert missing_required_snowflake_env(config) == []


def test_missing_required_snowflake_env_requires_auth_mode() -> None:
    config = SnowflakeAuthConfig(
        account="acct",
        user="svc_user",
        password="",
        private_key_path="",
        private_key_passphrase="",
    )

    assert "SNOWFLAKE_PASSWORD|SNOWFLAKE_PRIVATE_KEY_PATH" in missing_required_snowflake_env(config)


def test_build_snowflake_connector_auth_kwargs_key_pair() -> None:
    config = SnowflakeAuthConfig(
        account="acct",
        user="svc_user",
        password="",
        private_key_path="/tmp/key.p8",
        private_key_passphrase="passphrase",  # pragma: allowlist secret
    )

    payload = build_snowflake_connector_auth_kwargs(config)
    assert payload["private_key_file"] == "/tmp/key.p8"
    assert payload["private_key_file_pwd"] == "passphrase"  # pragma: allowlist secret


def test_build_snowflake_connector_auth_kwargs_password() -> None:
    config = SnowflakeAuthConfig(
        account="acct",
        user="svc_user",
        password="pwd-value",  # pragma: allowlist secret
        private_key_path="",
        private_key_passphrase="",
    )

    payload = build_snowflake_connector_auth_kwargs(config)
    assert payload == {"password": "pwd-value"}  # pragma: allowlist secret
