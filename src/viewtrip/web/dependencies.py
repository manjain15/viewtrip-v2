from fastapi import Request
from fastapi.templating import Jinja2Templates

from viewtrip.core.settings import Settings
from viewtrip.services.gtfs_cache import StopsIndex
from viewtrip.services.tfnsw import TfNSWClient
from viewtrip.services.trips_repo import TripsRepository


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_client(request: Request) -> TfNSWClient:
    return request.app.state.client


def get_stops_index(request: Request) -> StopsIndex:
    return request.app.state.stops_index


def get_repo(request: Request) -> TripsRepository:
    return request.app.state.repo


def get_templates(request: Request) -> Jinja2Templates:
    return request.app.state.templates
