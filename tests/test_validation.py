from datetime import datetime, timedelta

from viewtrip.core.times import SYDNEY
from viewtrip.core.validation import MAX_DAYS_AHEAD, validate_departure

NOW = datetime(2026, 5, 19, 14, 0, tzinfo=SYDNEY)


def test_valid_future_time():
    assert validate_departure("2026-05-19", "15:00", now_sydney=NOW) is None


def test_past_date_rejected():
    err = validate_departure("2026-05-18", "12:00", now_sydney=NOW)
    assert err is not None and "past" in err.lower()


def test_past_time_same_day_rejected():
    err = validate_departure("2026-05-19", "09:00", now_sydney=NOW)
    assert err is not None and "past" in err.lower()


def test_within_grace_period_accepted():
    assert validate_departure("2026-05-19", "13:56", now_sydney=NOW) is None


def test_just_outside_grace_rejected():
    err = validate_departure("2026-05-19", "13:54", now_sydney=NOW)
    assert err is not None


def test_far_future_rejected():
    far = NOW.date() + timedelta(days=MAX_DAYS_AHEAD + 1)
    err = validate_departure(far.strftime("%Y-%m-%d"), "12:00", now_sydney=NOW)
    assert err is not None and "400" in err


def test_max_days_boundary_accepted():
    edge = NOW.date() + timedelta(days=MAX_DAYS_AHEAD)
    assert validate_departure(edge.strftime("%Y-%m-%d"), "12:00", now_sydney=NOW) is None


def test_malformed_date():
    err = validate_departure("not-a-date", "12:00", now_sydney=NOW)
    assert err is not None and "format" in err.lower()


def test_malformed_time():
    err = validate_departure("2026-05-19", "25:99", now_sydney=NOW)
    assert err is not None and "format" in err.lower()
