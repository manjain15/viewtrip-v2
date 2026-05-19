from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from viewtrip.services.gtfs_cache import StopsIndex
from viewtrip.web.dependencies import get_stops_index, get_templates

router = APIRouter()


@router.get("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    stops: StopsIndex = Depends(get_stops_index),
    templates: Jinja2Templates = Depends(get_templates),
):
    trigger_name = request.headers.get("HX-Trigger-Name", "")
    if trigger_name and trigger_name in request.query_params:
        query = request.query_params[trigger_name]
    else:
        query = request.query_params.get("q", "")
    return templates.TemplateResponse(
        request,
        "partials/stops_options.html",
        {"stops": stops.search(query, limit=10)},
    )
