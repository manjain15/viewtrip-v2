import io
import re
import zipfile
from datetime import datetime

import pytest

from viewtrip.core.models import Stop
from viewtrip.services.tfnsw import GTFS_URL_TEMPLATE, TRIP_URL, TfNSWClient

TRIP_URL_RE = re.compile(re.escape(TRIP_URL) + r".*")

API_KEY = "test-key"


@pytest.fixture
def trip_response() -> dict:
    return {
        "journeys": [
            {
                "legs": [
                    {
                        "transportation": {"disassembledName": "T1"},
                        "origin": {
                            "name": "Town Hall Station",
                            "departureTimeEstimated": "2025-07-14T23:00:00Z",
                        },
                        "destination": {
                            "name": "Central Station",
                            "arrivalTimeEstimated": "2025-07-14T23:05:00Z",
                        },
                        "stopSequence": [],
                    }
                ]
            }
        ]
    }


def _make_stops_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "stops.txt",
            "stop_id,stop_name,stop_lat,stop_lon\n"
            "200060,Town Hall Station,-33.873,151.207\n"
            "200070,Central Station,-33.883,151.207\n",
        )
    return buf.getvalue()


async def test_trip_passes_utc_converted_time(httpx_mock, trip_response):
    httpx_mock.add_response(url=TRIP_URL_RE, json=trip_response)

    origin = Stop(id="200060", name="Town Hall Station", lat=-33.873, lon=151.207)
    destination = Stop(id="200070", name="Central Station", lat=-33.883, lon=151.207)
    async with TfNSWClient(API_KEY) as client:
        sydney_dt = datetime(2025, 7, 15, 9, 0)  # AEST, +10
        journeys = await client.trip(origin, destination, sydney_dt, count=3)

    assert len(journeys) == 1
    assert journeys[0].legs[0].mode == "T1"

    request = httpx_mock.get_requests()[0]
    assert request.url.params["itdDate"] == "20250714"
    assert request.url.params["itdTime"] == "2300"
    assert request.url.params["type_origin"] == "coord"
    assert request.url.params["name_origin"] == "151.207:-33.873:EPSG:4326"
    assert request.url.params["type_destination"] == "coord"
    assert request.url.params["name_destination"] == "151.207:-33.883:EPSG:4326"
    assert request.url.params["calcNumberOfTrips"] == "3"
    assert request.headers["Authorization"] == f"apikey {API_KEY}"


async def test_gtfs_stops_parses_zip(httpx_mock):
    httpx_mock.add_response(
        url=GTFS_URL_TEMPLATE.format(mode="sydneytrains"),
        content=_make_stops_zip(),
    )

    async with TfNSWClient(API_KEY) as client:
        stops = await client.gtfs_stops("sydneytrains")

    assert len(stops) == 2
    assert stops[0].id == "200060"
    assert stops[0].name == "Town Hall Station"
    assert stops[0].lat == -33.873
    assert stops[1].name == "Central Station"


async def test_trip_falls_back_to_stop_id_without_coords(httpx_mock):
    httpx_mock.add_response(url=TRIP_URL_RE, json={"journeys": []})
    async with TfNSWClient(API_KEY) as client:
        await client.trip(
            Stop(id="200060", name="X"),
            Stop(id="200070", name="Y"),
            datetime(2025, 7, 15, 9, 0),
        )
    req = httpx_mock.get_requests()[0]
    assert req.url.params["type_origin"] == "stop"
    assert req.url.params["name_origin"] == "200060"


async def test_trip_handles_empty_journeys(httpx_mock):
    httpx_mock.add_response(url=TRIP_URL_RE, json={"journeys": []})
    async with TfNSWClient(API_KEY) as client:
        result = await client.trip(
            Stop(id="a", name="A"),
            Stop(id="b", name="B"),
            datetime(2025, 7, 15, 9, 0),
        )
    assert result == []
