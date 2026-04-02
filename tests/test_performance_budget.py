from revops_funnel.performance import (
    default_selector,
    resolve_effective_threads,
    resolve_timeout_seconds,
)


def test_resolve_effective_threads_caps_local() -> None:
    result = resolve_effective_threads(
        requested_threads=8,
        environment="local",
        max_threads_local=2,
        max_threads_prod=6,
    )
    assert result == 2


def test_resolve_effective_threads_caps_production() -> None:
    result = resolve_effective_threads(
        requested_threads=12,
        environment="production",
        max_threads_local=2,
        max_threads_prod=4,
    )
    assert result == 4


def test_resolve_timeout_seconds_by_environment() -> None:
    local_timeout = resolve_timeout_seconds(
        environment="local",
        timeout_seconds_local=900,
        timeout_seconds_prod=1800,
    )
    prod_timeout = resolve_timeout_seconds(
        environment="production",
        timeout_seconds_local=900,
        timeout_seconds_prod=1800,
    )
    assert local_timeout == 900
    assert prod_timeout == 1800


def test_default_selector_is_stable() -> None:
    assert default_selector() == "path:models/staging path:models/intermediate path:models/marts"
