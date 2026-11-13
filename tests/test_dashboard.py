from datetime import date, datetime, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from backend.services.dashboard import _streak_metrics


def _session(day: date, status: str):
    return SimpleNamespace(
        start_time=datetime.combine(day, datetime.min.time()),
        status=status,
    )


def test_streak_counts_scheduled_days_and_ignores_unscheduled_days():
    berlin = ZoneInfo("Europe/Berlin")
    sessions = [
        _session(date(2026, 1, 5), "completed"),
        _session(date(2026, 1, 7), "completed"),
    ]

    assert _streak_metrics(sessions, date(2026, 1, 9), berlin) == (2, 2)


def test_missed_scheduled_day_breaks_streak_without_erasing_history():
    berlin = ZoneInfo("Europe/Berlin")
    sessions = [
        _session(date(2026, 1, 5), "completed"),
        _session(date(2026, 1, 7), "missed"),
        _session(date(2026, 1, 9), "completed"),
    ]

    assert _streak_metrics(sessions, date(2026, 1, 9), berlin) == (1, 1)


def test_future_completion_does_not_count_toward_streak():
    berlin = ZoneInfo("Europe/Berlin")
    sessions = [_session(date(2026, 1, 10), "completed")]

    assert _streak_metrics(sessions, date(2026, 1, 9), berlin) == (0, 0)


def test_streak_uses_local_day_for_utc_sessions():
    berlin = ZoneInfo("Europe/Berlin")
    session = SimpleNamespace(
        start_time=datetime(2026, 1, 1, 23, 30, tzinfo=timezone.utc),
        status="completed",
    )

    assert _streak_metrics([session], date(2026, 1, 2), berlin) == (1, 1)
