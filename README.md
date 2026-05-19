# ViewTrip v2

A Sydney public transport trip planner. This is a rewrite of [my Y12 SDD major project](https://github.com/manjain15/Manav-Jain-Major-Project) (2024), targeting a cleaner architecture and a web UI.

The original is preserved as-is.

## What's in this repo

Phases 1-3 of the rewrite — core domain, async TfNSW client, SQLite-backed saved trips, and a FastAPI + HTMX web UI.

```
src/viewtrip/
  core/
    times.py        # Sydney <-> UTC (fixes a TZ bug in v1)
    models.py       # Stop, Leg, Journey, SavedTrip domain types
    settings.py     # pydantic-settings: API key, data dir
  services/
    tfnsw.py        # async httpx client for Transport for NSW APIs
    trips_repo.py   # SQLite repo for SavedTrip CRUD + refresh
    gtfs_cache.py   # 24h-cached stops index with search()
    routing_map.py  # folium map HTML generation
  web/
    app.py          # FastAPI factory + lifespan
    dependencies.py # Depends() providers
    routes/         # pages, stops, trips, saved
    templates/      # Jinja2 + HTMX
    static/style.css
tests/              # pytest, mocked TfNSW client + in-memory SQLite
```

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync
cp .env.example .env  # then add your TfNSW API key
uv run pytest         # 49 tests
```

## Run

```sh
uv run uvicorn viewtrip.web:create_app --factory --reload --port 8000
```

Then open http://localhost:8000. First boot fetches the GTFS stops feed (~10s); subsequent boots use the cached copy in `~/.viewtrip/cache/` for 24 hours.

## API key

Get one from https://opendata.transport.nsw.gov.au — you need access to:

- *Trip Planner APIs* (for trip queries)
- *Public Transport - Timetables - For Realtime* (for GTFS stop data)

Put the key in `.env` as `TFNSW_API_KEY=...`. It is loaded via `pydantic-settings` and never committed.

## Roadmap

- [x] Phase 1: services + core, fully tested with mocked API
- [x] Phase 2: SQLite-backed saved trips (real itinerary snapshots)
- [x] Phase 3: FastAPI + HTMX UI
- [ ] Phase 4: deploy
