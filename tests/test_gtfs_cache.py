import time

from viewtrip.core.models import Stop
from viewtrip.services.gtfs_cache import StopsCache, StopsIndex


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def gtfs_stops(self, mode: str) -> list[Stop]:
        self.calls.append(mode)
        if mode == "buses":
            return [
                Stop(id="bus1", name="Central Bus Stand A"),
                Stop(id="bus2", name="Town Hall Stand"),
            ]
        return [
            Stop(id="train1", name="Central Station"),
            Stop(id="train2", name="Town Hall Station"),
        ]


def test_stops_index_startswith_is_case_insensitive():
    idx = StopsIndex(
        [Stop(id="a", name="Town Hall Station"), Stop(id="b", name="Central Station")]
    )
    assert [s.id for s in idx.search("town")] == ["a"]
    assert [s.id for s in idx.search("CENT")] == ["b"]


def test_stops_index_limits_results():
    idx = StopsIndex([Stop(id=str(i), name=f"Stop {i:02d}") for i in range(30)])
    assert len(idx.search("stop", limit=5)) == 5


def test_stops_index_deduplicates_by_id():
    idx = StopsIndex(
        [Stop(id="a", name="A"), Stop(id="a", name="A duplicate")]
    )
    assert len(idx) == 1


def test_stops_index_empty_query_returns_empty():
    idx = StopsIndex([Stop(id="a", name="Anything")])
    assert idx.search("") == []
    assert idx.search("   ") == []


def test_stops_index_get_by_id():
    idx = StopsIndex([Stop(id="a", name="A"), Stop(id="b", name="B")])
    assert idx.get("b").name == "B"
    assert idx.get("missing") is None


async def test_cache_fetches_when_cold(tmp_path):
    cache = StopsCache(tmp_path / "cache")
    client = FakeClient()
    idx = await cache.load(client)
    assert len(idx) == 4
    assert client.calls == ["buses", "sydneytrains"]


async def test_cache_uses_disk_when_fresh(tmp_path):
    cache = StopsCache(tmp_path / "cache")
    await cache.load(FakeClient())

    client2 = FakeClient()
    idx = await cache.load(client2)
    assert len(idx) == 4
    assert client2.calls == []


async def test_cache_refreshes_when_stale(tmp_path):
    cache = StopsCache(tmp_path / "cache", ttl_seconds=0)
    await cache.load(FakeClient())
    time.sleep(0.01)

    client2 = FakeClient()
    await cache.load(client2)
    assert client2.calls == ["buses", "sydneytrains"]


async def test_force_refresh_bypasses_cache(tmp_path):
    cache = StopsCache(tmp_path / "cache")
    await cache.load(FakeClient())

    client2 = FakeClient()
    await cache.load(client2, force_refresh=True)
    assert client2.calls == ["buses", "sydneytrains"]


class FailingClient:
    async def gtfs_stops(self, mode):
        raise RuntimeError("TfNSW unreachable")


async def test_falls_back_to_stale_cache_on_fetch_failure(tmp_path):
    cache = StopsCache(tmp_path / "cache", ttl_seconds=0)
    await cache.load(FakeClient())
    time.sleep(0.01)

    idx = await cache.load(FailingClient())
    assert len(idx) == 4


async def test_fetch_failure_with_no_cache_raises(tmp_path):
    cache = StopsCache(tmp_path / "cache")
    import pytest

    with pytest.raises(RuntimeError):
        await cache.load(FailingClient())
