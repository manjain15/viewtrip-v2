from datetime import datetime

from viewtrip.core.times import SYDNEY, UTC, format_for_tfnsw, sydney_to_utc


def test_aest_winter_subtracts_ten_hours():
    sydney_dt = datetime(2025, 7, 15, 9, 0)
    utc_dt = sydney_to_utc(sydney_dt)
    assert utc_dt == datetime(2025, 7, 14, 23, 0, tzinfo=UTC)


def test_aedt_summer_subtracts_eleven_hours():
    sydney_dt = datetime(2026, 1, 15, 9, 0)
    utc_dt = sydney_to_utc(sydney_dt)
    assert utc_dt == datetime(2026, 1, 14, 22, 0, tzinfo=UTC)


def test_dst_end_boundary():
    # April 2026: DST ends 04:00 AEDT on the first Sunday (5th)
    before = datetime(2026, 4, 5, 1, 30)
    after = datetime(2026, 4, 5, 4, 0)
    assert sydney_to_utc(before).utcoffset().total_seconds() == 0
    assert sydney_to_utc(before).hour == 14  # 01:30 AEDT (+11) -> 14:30 UTC prev day
    assert sydney_to_utc(after).hour == 18   # 04:00 AEST (+10) -> 18:00 UTC prev day


def test_preserves_tz_aware_input():
    aware = datetime(2025, 7, 15, 9, 0, tzinfo=SYDNEY)
    assert sydney_to_utc(aware) == datetime(2025, 7, 14, 23, 0, tzinfo=UTC)


def test_format_for_tfnsw():
    utc_dt = datetime(2025, 7, 14, 23, 5, tzinfo=UTC)
    assert format_for_tfnsw(utc_dt) == ("20250714", "2305")


def test_original_v1_bug_demonstrated():
    """The v1 code added 10 hours instead of subtracting. Document the fix.

    v1: sydney 09:00 -> '+= 10 hours' -> 19:00 (treated as UTC). Wrong.
    v2: sydney 09:00 AEST -> 23:00 UTC previous day. Correct.
    """
    sydney_dt = datetime(2025, 7, 15, 9, 0)
    v1_wrong = sydney_dt.hour + 10  # 19
    v2_right = sydney_to_utc(sydney_dt)
    assert v1_wrong == 19
    assert v2_right.hour == 23
    assert v2_right.day == 14
