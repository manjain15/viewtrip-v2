import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from viewtrip.core.models import Journey, SavedTrip, Stop

SCHEMA = """
CREATE TABLE IF NOT EXISTS saved_trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin_json TEXT NOT NULL,
    destination_json TEXT NOT NULL,
    journey_json TEXT NOT NULL,
    saved_at TEXT NOT NULL,
    last_refreshed_at TEXT
);
"""


class TripsRepository:
    def __init__(self, db_path: Path | str = ":memory:") -> None:
        self._path = str(db_path)
        if self._path != ":memory:":
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def __enter__(self) -> "TripsRepository":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._conn.close()

    def save(self, trip: SavedTrip) -> SavedTrip:
        cursor = self._conn.execute(
            """
            INSERT INTO saved_trips
                (origin_json, destination_json, journey_json, saved_at, last_refreshed_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                trip.origin.model_dump_json(),
                trip.destination.model_dump_json(),
                trip.journey.model_dump_json(),
                trip.saved_at.isoformat(),
                trip.last_refreshed_at.isoformat() if trip.last_refreshed_at else None,
            ),
        )
        self._conn.commit()
        return trip.model_copy(update={"id": cursor.lastrowid})

    def list_all(self) -> list[SavedTrip]:
        rows = self._conn.execute(
            "SELECT * FROM saved_trips ORDER BY saved_at DESC, id DESC"
        ).fetchall()
        return [_row_to_trip(r) for r in rows]

    def get(self, trip_id: int) -> SavedTrip | None:
        row = self._conn.execute(
            "SELECT * FROM saved_trips WHERE id = ?", (trip_id,)
        ).fetchone()
        return _row_to_trip(row) if row else None

    def delete(self, trip_id: int) -> bool:
        cursor = self._conn.execute("DELETE FROM saved_trips WHERE id = ?", (trip_id,))
        self._conn.commit()
        return cursor.rowcount > 0

    def refresh(
        self,
        trip_id: int,
        journey: Journey,
        *,
        at: datetime | None = None,
    ) -> SavedTrip | None:
        moment = at or datetime.now(timezone.utc)
        cursor = self._conn.execute(
            "UPDATE saved_trips SET journey_json = ?, last_refreshed_at = ? WHERE id = ?",
            (journey.model_dump_json(), moment.isoformat(), trip_id),
        )
        self._conn.commit()
        if cursor.rowcount == 0:
            return None
        return self.get(trip_id)


def _row_to_trip(row: sqlite3.Row) -> SavedTrip:
    last_refreshed = row["last_refreshed_at"]
    return SavedTrip(
        id=row["id"],
        origin=Stop.model_validate_json(row["origin_json"]),
        destination=Stop.model_validate_json(row["destination_json"]),
        journey=Journey.model_validate_json(row["journey_json"]),
        saved_at=datetime.fromisoformat(row["saved_at"]),
        last_refreshed_at=datetime.fromisoformat(last_refreshed) if last_refreshed else None,
    )
