import csv
import io
import zipfile
from datetime import datetime
from typing import Literal

import httpx

from viewtrip.core.models import Journey, Stop
from viewtrip.core.times import format_for_tfnsw, sydney_to_utc

TRIP_URL = "https://api.transport.nsw.gov.au/v1/tp/trip"
GTFS_URL_TEMPLATE = "https://api.transport.nsw.gov.au/v1/gtfs/schedule/{mode}"

GTFSMode = Literal["buses", "sydneytrains"]


class TfNSWClient:
    def __init__(self, api_key: str, *, client: httpx.AsyncClient | None = None) -> None:
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            headers={"Authorization": f"apikey {api_key}"},
            timeout=httpx.Timeout(30.0),
        )

    async def __aenter__(self) -> "TfNSWClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def trip(
        self,
        origin: Stop,
        destination: Stop,
        departure_sydney: datetime,
        *,
        count: int = 5,
    ) -> list[Journey]:
        utc_date, utc_time = format_for_tfnsw(sydney_to_utc(departure_sydney))
        params = {
            "outputFormat": "rapidJSON",
            "coordOutputFormat": "EPSG:4326",
            "depArrMacro": "dep",
            "itdDate": utc_date,
            "itdTime": utc_time,
            **_locate(origin, "origin"),
            **_locate(destination, "destination"),
            "calcNumberOfTrips": count,
            "TfNSWTR": "true",
            "version": "10.2.1.42",
        }
        resp = await self._client.get(TRIP_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        return [Journey.from_api(j) for j in data.get("journeys", [])]

    async def gtfs_stops(self, mode: GTFSMode) -> list[Stop]:
        resp = await self._client.get(GTFS_URL_TEMPLATE.format(mode=mode))
        resp.raise_for_status()
        return _parse_stops_zip(resp.content)


def _locate(stop: Stop, role: str) -> dict[str, str]:
    if stop.lat is not None and stop.lon is not None:
        return {
            f"type_{role}": "coord",
            f"name_{role}": f"{stop.lon}:{stop.lat}:EPSG:4326",
        }
    return {f"type_{role}": "stop", f"name_{role}": stop.id}


def _parse_stops_zip(content: bytes) -> list[Stop]:
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        with zf.open("stops.txt") as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader = csv.DictReader(text)
            return [
                Stop(
                    id=row["stop_id"],
                    name=row["stop_name"],
                    lat=float(row["stop_lat"]) if row.get("stop_lat") else None,
                    lon=float(row["stop_lon"]) if row.get("stop_lon") else None,
                )
                for row in reader
            ]
