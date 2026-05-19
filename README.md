# ViewTrip v2

A Sydney public transport trip planner. This is a rewrite of [my Y12 SDD major project](https://github.com/manjain15/Manav-Jain-Major-Project) (2024), targeting a cleaner architecture and a web UI.

The original is preserved as-is.

## What's in this repo

Phase 1 of the rewrite — the API layer and core domain. No UI yet.

```
src/viewtrip/
  core/
    times.py     # Sydney <-> UTC (fixes a TZ bug in v1)
    models.py    # Stop, Leg, Journey domain types
  services/
    tfnsw.py     # async httpx client for Transport for NSW APIs
tests/           # pytest, mocked with pytest-httpx
```

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync
cp .env.example .env  # then add your TfNSW API key
uv run pytest
```

## API key

Get one from https://opendata.transport.nsw.gov.au — you need access to:

- *Trip Planner APIs* (for trip queries)
- *Public Transport - Timetables - For Realtime* (for GTFS stop data)

Put the key in `.env` as `TFNSW_API_KEY=...`. It is loaded via `pydantic-settings` and never committed.

## Roadmap

- [x] Phase 1: services + core, fully tested with mocked API
- [ ] Phase 2: SQLite-backed saved trips (real itinerary snapshots)
- [ ] Phase 3: FastAPI + HTMX UI
- [ ] Phase 4: deploy
