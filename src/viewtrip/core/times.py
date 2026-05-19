from datetime import datetime
from zoneinfo import ZoneInfo

SYDNEY = ZoneInfo("Australia/Sydney")
UTC = ZoneInfo("UTC")


def sydney_to_utc(sydney_dt: datetime) -> datetime:
    if sydney_dt.tzinfo is None:
        sydney_dt = sydney_dt.replace(tzinfo=SYDNEY)
    return sydney_dt.astimezone(UTC)


def format_for_tfnsw(utc_dt: datetime) -> tuple[str, str]:
    return utc_dt.strftime("%Y%m%d"), utc_dt.strftime("%H%M")
