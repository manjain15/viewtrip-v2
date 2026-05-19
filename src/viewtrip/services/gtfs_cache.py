import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Iterable

from viewtrip.core.models import Stop
from viewtrip.services.tfnsw import GTFSMode, TfNSWClient

CACHE_TTL_SECONDS = 24 * 60 * 60

logger = logging.getLogger(__name__)


class StopsIndex:
    def __init__(self, stops: Iterable[Stop]) -> None:
        by_id: dict[str, Stop] = {}
        for s in stops:
            by_id.setdefault(s.id, s)
        self._stops: list[Stop] = sorted(by_id.values(), key=lambda s: s.name.lower())

    def __len__(self) -> int:
        return len(self._stops)

    def search(self, query: str, *, limit: int = 20) -> list[Stop]:
        q = query.strip().lower()
        if not q:
            return []
        hits: list[Stop] = []
        for stop in self._stops:
            if stop.name.lower().startswith(q):
                hits.append(stop)
                if len(hits) >= limit:
                    break
        return hits

    def get(self, stop_id: str) -> Stop | None:
        for s in self._stops:
            if s.id == stop_id:
                return s
        return None

    def find_by_name(self, name: str) -> Stop | None:
        target = name.strip().lower()
        if not target:
            return None
        for s in self._stops:
            if s.name.lower() == target:
                return s
        return None


class StopsCache:
    def __init__(self, cache_dir: Path, *, ttl_seconds: int = CACHE_TTL_SECONDS) -> None:
        self._cache_dir = cache_dir
        self._ttl = ttl_seconds

    @property
    def _file(self) -> Path:
        return self._cache_dir / "stops.json"

    def _is_fresh(self) -> bool:
        f = self._file
        if not f.exists():
            return False
        return (time.time() - f.stat().st_mtime) < self._ttl

    def _load_from_disk(self) -> list[Stop]:
        data = json.loads(self._file.read_text())
        return [Stop.model_validate(item) for item in data]

    def _save_to_disk(self, stops: list[Stop]) -> None:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        payload = [s.model_dump() for s in stops]
        self._file.write_text(json.dumps(payload))

    async def load(
        self,
        client: TfNSWClient,
        *,
        modes: tuple[GTFSMode, ...] = ("buses", "sydneytrains"),
        force_refresh: bool = False,
    ) -> StopsIndex:
        if not force_refresh and self._is_fresh():
            return StopsIndex(self._load_from_disk())
        try:
            batches = await asyncio.gather(*(client.gtfs_stops(m) for m in modes))
        except Exception as exc:
            if self._file.exists():
                logger.warning(
                    "GTFS fetch failed (%s); serving stale cache from %s",
                    exc,
                    self._file,
                )
                return StopsIndex(self._load_from_disk())
            raise
        merged: list[Stop] = [s for batch in batches for s in batch]
        self._save_to_disk(merged)
        return StopsIndex(merged)
