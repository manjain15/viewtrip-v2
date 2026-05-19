from datetime import datetime, timedelta

from viewtrip.core.times import SYDNEY

MAX_DAYS_AHEAD = 400
GRACE = timedelta(minutes=5)


def validate_departure(
    date_str: str,
    time_str: str,
    *,
    now_sydney: datetime | None = None,
) -> str | None:
    try:
        naive = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        return "Invalid date or time format."

    departure = naive.replace(tzinfo=SYDNEY)
    now = now_sydney or datetime.now(SYDNEY)

    if departure < now - GRACE:
        return "Departure time is in the past."

    if departure.date() > now.date() + timedelta(days=MAX_DAYS_AHEAD):
        return (
            f"Departure date is more than {MAX_DAYS_AHEAD} days away — "
            "schedules aren't published that far ahead."
        )

    return None
