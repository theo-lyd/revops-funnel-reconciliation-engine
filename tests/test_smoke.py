from revops_funnel.config import get_settings


def test_settings_load() -> None:
    settings = get_settings()
    assert settings.environment in {"dev", "test", "prod"}
