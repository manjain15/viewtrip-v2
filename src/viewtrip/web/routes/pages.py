from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from viewtrip.web.dependencies import get_templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def start(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
):
    return templates.TemplateResponse(request, "pages/start.html")
