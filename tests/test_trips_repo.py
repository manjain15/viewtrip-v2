from datetime import datetime, timedelta, timezone

import pytest

from viewtrip.core.models import Journey, Leg, SavedTrip, Stop
from viewtrip.services.trips_repo import TripsRepository


def _make_trip(*, suffix: str = "", saved_at: datetime | None = None) -> SavedTrip:
    return SavedTrip(
        origin=Stop(id="200060", name=f"Town Hall{suffix}", lat=-33.873, lon=151.207),
        destination=Stop(id="200070", name=f"Central{suffix}", lat=-33.883, lon=151.207),
        saved_at=saved_at or datetime(2026, 5, 19, 12, 0, tzinfo=timezone.utc),
        journey=Journey(
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
        ),
    )


@pytest.fixture
def repo():
    with TripsRepository(":memory:") as r:
        yield r


def test_save_populates_id(repo):
    saved = repo.save(_make_trip())
    assert saved.id is not None and saved.id > 0


def test_list_returns_newest_first(repo):
    earlier = _make_trip(suffix=" earlier")
    later = _make_trip(
        suffix=" later",
        saved_at=earlier.saved_at + timedelta(hours=1),
    )
    repo.save(earlier)
    repo.save(later)

    trips = repo.list_all()
    assert [t.origin.name for t in trips] == ["Town Hall later", "Town Hall earlier"]


def test_get_returns_full_snapshot(repo):
    saved = repo.save(_make_trip())
    fetched = repo.get(saved.id)
    assert fetched == saved
    assert fetched.journey.legs[0].stop_coords == [(-33.873, 151.207), (-33.883, 151.207)]


def test_get_missing_returns_none(repo):
    assert repo.get(999) is None


def test_delete_existing(repo):
    saved = repo.save(_make_trip())
    assert repo.delete(saved.id) is True
    assert repo.get(saved.id) is None


def test_delete_missing_returns_false(repo):
    assert repo.delete(999) is False


def test_refresh_updates_journey_and_timestamp(repo):
    saved = repo.save(_make_trip())
    new_journey = Journey(
        legs=[
            Leg(
                mode="T8",
                origin_name="Town Hall Station",
                destination_name="Central Station",
                departure=datetime(2026, 5, 19, 13, 30, tzinfo=timezone.utc),
                arrival=datetime(2026, 5, 19, 13, 35, tzinfo=timezone.utc),
            )
        ]
    )
    refreshed_at = datetime(2026, 5, 19, 14, 0, tzinfo=timezone.utc)

    refreshed = repo.refresh(saved.id, new_journey, at=refreshed_at)

    assert refreshed is not None
    assert refreshed.journey.legs[0].mode == "T8"
    assert refreshed.last_refreshed_at == refreshed_at
    assert refreshed.origin == saved.origin


def test_refresh_missing_returns_none(repo):
    assert repo.refresh(999, _make_trip().journey) is None


def test_persists_across_connections(tmp_path):
    db_path = tmp_path / "trips.db"
    with TripsRepository(db_path) as repo:
        saved = repo.save(_make_trip())
        trip_id = saved.id

    with TripsRepository(db_path) as repo:
        loaded = repo.get(trip_id)
        assert loaded is not None
        assert loaded.origin.name == "Town Hall"
        assert loaded.journey.legs[0].mode == "T1"


def test_creates_parent_directory(tmp_path):
    db_path = tmp_path / "nested" / "dir" / "trips.db"
    with TripsRepository(db_path) as repo:
        repo.save(_make_trip())
    assert db_path.exists()
