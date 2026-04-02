"""Shared Snowflake authentication helpers for password and key-pair modes."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SnowflakeAuthConfig:
    account: str
    user: str
    password: str
    private_key_path: str
    private_key_passphrase: str

    @property
    def uses_key_pair(self) -> bool:
        return bool(self.private_key_path)

    @property
    def has_password(self) -> bool:
        return bool(self.password)

    @property
    def is_auth_configured(self) -> bool:
        return self.has_password or self.uses_key_pair


def snowflake_auth_from_env() -> SnowflakeAuthConfig:
    return SnowflakeAuthConfig(
        account=os.getenv("SNOWFLAKE_ACCOUNT", ""),
        user=os.getenv("SNOWFLAKE_USER", ""),
        password=os.getenv("SNOWFLAKE_PASSWORD", ""),
        private_key_path=os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH", ""),
        private_key_passphrase=os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", ""),
    )


def missing_required_snowflake_env(config: SnowflakeAuthConfig) -> list[str]:
    missing: list[str] = []
    if not config.account:
        missing.append("SNOWFLAKE_ACCOUNT")
    if not config.user:
        missing.append("SNOWFLAKE_USER")
    if not config.is_auth_configured:
        missing.append("SNOWFLAKE_PASSWORD|SNOWFLAKE_PRIVATE_KEY_PATH")
    return missing


def build_snowflake_connector_auth_kwargs(config: SnowflakeAuthConfig) -> dict[str, str]:
    if config.uses_key_pair:
        payload = {"private_key_file": config.private_key_path}
        if config.private_key_passphrase:
            payload["private_key_file_pwd"] = config.private_key_passphrase
        return payload
    return {"password": config.password}
