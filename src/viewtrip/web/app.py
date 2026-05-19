from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from viewtrip.core.settings import Settings
from viewtrip.services.gtfs_cache import StopsCache
from viewtrip.services.tfnsw import TfNSWClient
from viewtrip.services.trips_repo import TripsRepository

PACKAGE_DIR = Path(__file__).parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    client = TfNSWClient(settings.tfnsw_api_key)
    cache = StopsCache(settings.cache_dir)

    app.state.client = client
    app.state.repo = TripsRepository(settings.db_path)
    app.state.stops_index = await cache.load(client)

    try:
        yield
    finally:
        await client.aclose()
        app.state.repo.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(lifespan=lifespan, title="ViewTrip")
    app.state.settings = settings or Settings()
    app.state.templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    from viewtrip.web.routes import pages, saved, stops, trips

    app.include_router(pages.router)
    app.include_router(stops.router, prefix="/stops")
    app.include_router(trips.router, prefix="/trips")
    app.include_router(saved.router, prefix="/saved")
    return app
