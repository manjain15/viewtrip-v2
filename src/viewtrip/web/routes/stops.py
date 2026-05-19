from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from viewtrip.services.gtfs_cache import StopsIndex
from viewtrip.web.dependencies import get_stops_index, get_templates

router = APIRouter()


@router.get("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    q: str = "",
    target: str = "origin",
    stops: StopsIndex = Depends(get_stops_index),
    templates: Jinja2Templates = Depends(get_templates),
):
    return templates.TemplateResponse(
        request,
        "partials/stops_options.html",
        {"stops": stops.search(q, limit=10), "target": target},
    )
