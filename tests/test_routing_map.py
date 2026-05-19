from datetime import datetime, timezone

from viewtrip.core.models import Journey, Leg
from viewtrip.services.routing_map import render_journey_map


def _leg(coords: list[tuple[float, float]]) -> Leg:
    return Leg(
        mode="T1",
        origin_name="A",
        destination_name="B",
        departure=datetime(2026, 5, 19, tzinfo=timezone.utc),
        arrival=datetime(2026, 5, 19, 1, 0, tzinfo=timezone.utc),
        stop_coords=coords,
    )


def test_empty_when_no_coords():
    journey = Journey(legs=[_leg([])])
    assert render_journey_map(journey) == ""


def test_renders_html_with_coords():
    journey = Journey(legs=[_leg([(-33.873, 151.207), (-33.883, 151.207)])])
    html = render_journey_map(journey)
    assert html != ""
    assert "<html" in html.lower()
    assert "antpath" in html.lower()
    assert "-33.873" in html
    assert "-33.883" in html
