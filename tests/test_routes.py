from datetime import datetime, timezone

from tests.conftest import sample_journey

from viewtrip.core.models import SavedTrip, Stop


def test_start_page(http):
    r = http.get("/")
    assert r.status_code == 200
    assert "ViewTrip" in r.text


def test_new_trip_form(http):
    r = http.get("/trips/new")
    assert r.status_code == 200
    assert 'name="origin"' in r.text
    assert 'name="destination"' in r.text


def test_stops_search_matches(http):
    r = http.get("/stops/search", params={"q": "town"})
    assert r.status_code == 200
    assert "Town Hall Station" in r.text
    assert "Central Station" not in r.text


def test_stops_search_empty_query(http):
    r = http.get("/stops/search", params={"q": ""})
    assert r.status_code == 200
    assert "<option" not in r.text


def test_stops_search_uses_htmx_trigger_name(http):
    r = http.get(
        "/stops/search",
        params={"origin": "town", "destination": "", "date": "", "time": ""},
        headers={"HX-Trigger-Name": "origin"},
    )
    assert r.status_code == 200
    assert "Town Hall Station" in r.text
    assert "Central Station" not in r.text


def test_trip_results_with_unknown_origin(http):
    r = http.get(
        "/trips/results",
        params={
            "origin": "Nonexistent Stop",
            "destination": "Central Station",
            "date": "2026-05-19",
            "time": "09:00",
            "count": 3,
        },
    )
    assert r.status_code == 400
    assert "Origin or destination not found" in r.text


def test_trip_results_renders_journeys(http, fake_client):
    fake_client.trip_response = [sample_journey()]

    r = http.get(
        "/trips/results",
        params={
            "origin": "Town Hall Station",
            "destination": "Central Station",
            "date": "2026-05-19",
            "time": "09:00",
            "count": 3,
        },
    )
    assert r.status_code == 200
    assert "Town Hall Station" in r.text
    assert "Central Station" in r.text
    assert "T1" in r.text
    assert "Save" in r.text


def test_trip_results_no_journeys(http, fake_client):
    fake_client.trip_response = []
    r = http.get(
        "/trips/results",
        params={
            "origin": "Town Hall Station",
            "destination": "Central Station",
            "date": "2026-05-19",
            "time": "09:00",
            "count": 3,
        },
    )
    assert r.status_code == 200
    assert "No journeys returned" in r.text


def test_save_trip_persists_and_redirects(http, repo):
    origin = Stop(id="200060", name="Town Hall Station", lat=-33.873, lon=151.207)
    destination = Stop(id="200070", name="Central Station", lat=-33.883, lon=151.207)
    journey = sample_journey()

    r = http.post(
        "/trips/save",
        data={
            "origin_json": origin.model_dump_json(),
            "destination_json": destination.model_dump_json(),
            "journey_json": journey.model_dump_json(),
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/saved"
    trips = repo.list_all()
    assert len(trips) == 1
    assert trips[0].origin.name == "Town Hall Station"


def test_saved_list_empty(http):
    r = http.get("/saved")
    assert r.status_code == 200
    assert "No saved trips yet" in r.text


def test_saved_list_with_trips(http, repo):
    repo.save(
        SavedTrip(
            origin=Stop(id="200060", name="Town Hall Station"),
            destination=Stop(id="200070", name="Central Station"),
            saved_at=datetime(2026, 5, 19, 12, 0, tzinfo=timezone.utc),
            journey=sample_journey(),
        )
    )
    r = http.get("/saved")
    assert r.status_code == 200
    assert "Town Hall Station" in r.text
    assert "Central Station" in r.text


def test_saved_detail_renders_legs(http, repo):
    trip = repo.save(
        SavedTrip(
            origin=Stop(id="200060", name="Town Hall Station"),
            destination=Stop(id="200070", name="Central Station"),
            saved_at=datetime(2026, 5, 19, 12, 0, tzinfo=timezone.utc),
            journey=sample_journey(),
        )
    )
    r = http.get(f"/saved/{trip.id}")
    assert r.status_code == 200
    assert "T1" in r.text
    assert "iframe" in r.text  # map embedded


def test_saved_detail_missing(http):
    r = http.get("/saved/999")
    assert r.status_code == 404


def test_saved_delete(http, repo):
    trip = repo.save(
        SavedTrip(
            origin=Stop(id="200060", name="Town Hall Station"),
            destination=Stop(id="200070", name="Central Station"),
            saved_at=datetime(2026, 5, 19, 12, 0, tzinfo=timezone.utc),
            journey=sample_journey(),
        )
    )
    r = http.delete(f"/saved/{trip.id}")
    assert r.status_code == 200
    assert repo.get(trip.id) is None


def test_saved_delete_missing(http):
    r = http.delete("/saved/999")
    assert r.status_code == 404


def test_saved_refresh_updates(http, repo, fake_client):
    trip = repo.save(
        SavedTrip(
            origin=Stop(id="200060", name="Town Hall Station"),
            destination=Stop(id="200070", name="Central Station"),
            saved_at=datetime(2026, 5, 19, 12, 0, tzinfo=timezone.utc),
            journey=sample_journey(),
        )
    )
    fake_client.trip_response = [sample_journey()]

    r = http.post(f"/saved/{trip.id}/refresh")
    assert r.status_code == 200
    assert repo.get(trip.id).last_refreshed_at is not None
    assert fake_client.trip_calls[0]["origin"].name == "Town Hall Station"


def test_trips_map_renders_iframe(http):
    journey = sample_journey()
    r = http.post("/trips/map", data={"journey_json": journey.model_dump_json()})
    assert r.status_code == 200
    assert "iframe" in r.text
    assert "srcdoc" in r.text
