from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from viewtrip.core.models import Journey, SavedTrip, Stop
from viewtrip.services.gtfs_cache import StopsIndex
from viewtrip.services.routing_map import render_journey_map
from viewtrip.services.tfnsw import TfNSWClient
from viewtrip.services.trips_repo import TripsRepository
from viewtrip.web.dependencies import (
    get_client,
    get_repo,
    get_stops_index,
    get_templates,
)

router = APIRouter()


@router.get("/new", response_class=HTMLResponse)
async def new_trip_form(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
):
    now = datetime.now()
    return templates.TemplateResponse(
        request,
        "pages/selection.html",
        {
            "default_date": now.strftime("%Y-%m-%d"),
            "default_time": now.strftime("%H:%M"),
            "count": 3,
        },
    )


@router.get("/results", response_class=HTMLResponse)
async def trip_results(
    request: Request,
    origin: str,
    destination: str,
    date: str,
    time: str,
    count: int = 3,
    client: TfNSWClient = Depends(get_client),
    stops: StopsIndex = Depends(get_stops_index),
    templates: Jinja2Templates = Depends(get_templates),
):
    origin_stop = stops.find_by_name(origin)
    destination_stop = stops.find_by_name(destination)

    if not origin_stop or not destination_stop:
        return templates.TemplateResponse(
            request,
            "pages/selection.html",
            {
                "error": "Origin or destination not found — pick from the suggestions.",
                "origin": origin,
                "destination": destination,
                "default_date": date,
                "default_time": time,
                "count": count,
            },
            status_code=400,
        )

    departure = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    journeys = await client.trip(
        origin_stop,
        destination_stop,
        departure,
        count=count,
    )

    return templates.TemplateResponse(
        request,
        "pages/trip_results.html",
        {
            "origin": origin_stop,
            "destination": destination_stop,
            "journeys": journeys,
            "departure": departure,
        },
    )


@router.post("/map", response_class=HTMLResponse)
async def render_map(
    request: Request,
    journey_json: str = Form(...),
    templates: Jinja2Templates = Depends(get_templates),
):
    journey = Journey.model_validate_json(journey_json)
    html = render_journey_map(journey)
    return templates.TemplateResponse(
        request, "partials/map.html", {"map_html": html}
    )


@router.post("/save")
async def save_trip(
    origin_json: str = Form(...),
    destination_json: str = Form(...),
    journey_json: str = Form(...),
    repo: TripsRepository = Depends(get_repo),
):
    trip = SavedTrip(
        origin=Stop.model_validate_json(origin_json),
        destination=Stop.model_validate_json(destination_json),
        saved_at=datetime.now(timezone.utc),
        journey=Journey.model_validate_json(journey_json),
    )
    repo.save(trip)
    return RedirectResponse("/saved", status_code=303)
