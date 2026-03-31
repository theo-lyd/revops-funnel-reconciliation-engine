from datetime import datetime, timedelta, timezone

from monitor.check_freshness import age_hours


def test_age_hours_is_non_negative() -> None:
    loaded_at = datetime.now(timezone.utc) - timedelta(minutes=30)
    assert age_hours(loaded_at) >= 0


def test_age_hours_approximately_one_hour() -> None:
    loaded_at = datetime.now(timezone.utc) - timedelta(hours=1)
    value = age_hours(loaded_at)
    assert 0.95 <= value <= 1.05
