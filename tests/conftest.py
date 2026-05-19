from datetime import datetime, timezone
from typing import Iterable

import pytest
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

from viewtrip.core.models import Journey, Leg, Stop
from viewtrip.services.gtfs_cache import StopsIndex
from viewtrip.services.trips_repo import TripsRepository
from viewtrip.web.app import STATIC_DIR, TEMPLATES_DIR
from viewtrip.web.routes import pages, saved, stops as stops_routes, trips


class FakeTfNSW:
    def __init__(self) -> None:
        self.trip_calls: list[dict] = []
        self.trip_response: list[Journey] = []

    async def trip(
        self,
        origin: Stop,
        destination: Stop,
        departure_sydney: datetime,
        *,
        count: int = 5,
    ) -> list[Journey]:
        self.trip_calls.append(
            {
                "origin": origin,
                "destination": destination,
                "departure": departure_sydney,
                "count": count,
            }
        )
        return list(self.trip_response)

    async def aclose(self) -> None:
        pass


def make_test_app(
    *,
    stops_index: StopsIndex,
    client: FakeTfNSW,
    repo: TripsRepository,
) -> FastAPI:
    app = FastAPI()
    app.state.stops_index = stops_index
    app.state.client = client
    app.state.repo = repo
    app.state.templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.include_router(pages.router)
    app.include_router(stops_routes.router, prefix="/stops")
    app.include_router(trips.router, prefix="/trips")
    app.include_router(saved.router, prefix="/saved")
    return app


def sample_stops() -> Iterable[Stop]:
    return [
        Stop(id="200060", name="Town Hall Station", lat=-33.873, lon=151.207),
        Stop(id="200070", name="Central Station", lat=-33.883, lon=151.207),
        Stop(id="200080", name="Wynyard Station", lat=-33.865, lon=151.206),
    ]


def sample_journey() -> Journey:
    return Journey(
        legs=[
            Leg(
                mode="T1",
                origin_name="Town Hall Station",
                destination_name="Central Station",
                departure=datetime(2026, 5, 19, 13, 0, tzinfo=timezone.utc),
                arrival=datetime(2026, 5, 19, 13, 5, tzinfo=timezone.utc),
                stop_coords=[(-33.873, 151.207), (-33.883, 151.207)],
            )
        ]
    )


@pytest.fixture
def stops_index() -> StopsIndex:
    return StopsIndex(sample_stops())


@pytest.fixture
def fake_client() -> FakeTfNSW:
    return FakeTfNSW()


@pytest.fixture
def repo() -> TripsRepository:
    with TripsRepository(":memory:") as r:
        yield r


@pytest.fixture
def app(stops_index, fake_client, repo):
    return make_test_app(stops_index=stops_index, client=fake_client, repo=repo)


@pytest.fixture
def http(app):
    return TestClient(app)
