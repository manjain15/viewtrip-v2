from datetime import datetime, timezone

from viewtrip.core.models import Journey

SAMPLE_JOURNEY = {
    "legs": [
        {
            "transportation": {"disassembledName": "T1"},
            "origin": {
                "name": "Town Hall Station",
                "departureTimeEstimated": "2025-07-15T08:00:00Z",
            },
            "destination": {
                "name": "Central Station",
                "arrivalTimeEstimated": "2025-07-15T08:05:00Z",
            },
            "stopSequence": [
                {"name": "Town Hall", "coord": [-33.873, 151.207]},
                {"name": "Central", "coord": [-33.883, 151.207]},
            ],
        },
        {
            "transportation": None,
            "origin": {
                "name": "Central Station",
                "departureTimeEstimated": "2025-07-15T08:06:00Z",
            },
            "destination": {
                "name": "Central Bus Stand A",
                "arrivalTimeEstimated": "2025-07-15T08:09:00Z",
            },
        },
    ]
}


def test_journey_from_api_parses_legs():
    journey = Journey.from_api(SAMPLE_JOURNEY)
    assert len(journey.legs) == 2
    assert journey.legs[0].mode == "T1"
    assert journey.legs[0].departure == datetime(2025, 7, 15, 8, 0, tzinfo=timezone.utc)
    assert journey.legs[0].stop_coords == [(-33.873, 151.207), (-33.883, 151.207)]


def test_walk_default_when_transportation_missing():
    journey = Journey.from_api(SAMPLE_JOURNEY)
    assert journey.legs[1].mode == "Walk"
    assert journey.legs[1].stop_coords == []


def test_journey_departure_and_arrival_properties():
    journey = Journey.from_api(SAMPLE_JOURNEY)
    assert journey.departure == datetime(2025, 7, 15, 8, 0, tzinfo=timezone.utc)
    assert journey.arrival == datetime(2025, 7, 15, 8, 9, tzinfo=timezone.utc)
