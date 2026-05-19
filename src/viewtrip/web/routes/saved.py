from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from viewtrip.services.routing_map import render_journey_map
from viewtrip.services.tfnsw import TfNSWClient
from viewtrip.services.trips_repo import TripsRepository
from viewtrip.web.dependencies import get_client, get_repo, get_templates

router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def saved_list(
    request: Request,
    repo: TripsRepository = Depends(get_repo),
    templates: Jinja2Templates = Depends(get_templates),
):
    return templates.TemplateResponse(
        request,
        "pages/saved_list.html",
        {"trips": repo.list_all()},
    )


@router.get("/{trip_id}", response_class=HTMLResponse)
async def saved_detail(
    request: Request,
    trip_id: int,
    repo: TripsRepository = Depends(get_repo),
    templates: Jinja2Templates = Depends(get_templates),
):
    trip = repo.get(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Saved trip not found")

    map_html = render_journey_map(trip.journey)
    return templates.TemplateResponse(
        request,
        "pages/saved_detail.html",
        {"trip": trip, "map_html": map_html},
    )


@router.delete("/{trip_id}")
async def saved_delete(
    trip_id: int,
    repo: TripsRepository = Depends(get_repo),
):
    if not repo.delete(trip_id):
        raise HTTPException(status_code=404, detail="Saved trip not found")
    return Response(status_code=200)


@router.post("/{trip_id}/refresh", response_class=HTMLResponse)
async def saved_refresh(
    request: Request,
    trip_id: int,
    repo: TripsRepository = Depends(get_repo),
    client: TfNSWClient = Depends(get_client),
    templates: Jinja2Templates = Depends(get_templates),
):
    trip = repo.get(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Saved trip not found")

    journeys = await client.trip(
        trip.origin,
        trip.destination,
        datetime.now(),
        count=1,
    )
    if not journeys:
        return templates.TemplateResponse(
            request,
            "partials/saved_row.html",
            {"trip": trip, "error": "No journeys returned"},
        )

    refreshed = repo.refresh(trip_id, journeys[0])
    return templates.TemplateResponse(
        request,
        "partials/saved_row.html",
        {"trip": refreshed},
    )
