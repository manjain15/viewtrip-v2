from datetime import datetime
from pydantic import BaseModel, Field


class Stop(BaseModel):
    id: str
    name: str
    lat: float | None = None
    lon: float | None = None


class Leg(BaseModel):
    mode: str
    origin_name: str
    destination_name: str
    departure: datetime
    arrival: datetime
    stop_coords: list[tuple[float, float]] = Field(default_factory=list)


class Journey(BaseModel):
    legs: list[Leg]

    @property
    def departure(self) -> datetime:
        return self.legs[0].departure

    @property
    def arrival(self) -> datetime:
        return self.legs[-1].arrival

    @classmethod
    def from_api(cls, payload: dict) -> "Journey":
        legs: list[Leg] = []
        for leg in payload["legs"]:
            transportation = leg.get("transportation") or {}
            mode = transportation.get("disassembledName") or "Walk"
            stop_seq = leg.get("stopSequence") or []
            coords = [tuple(s["coord"]) for s in stop_seq if "coord" in s]
            legs.append(
                Leg(
                    mode=mode,
                    origin_name=leg["origin"]["name"],
                    destination_name=leg["destination"]["name"],
                    departure=_parse_ts(leg["origin"]["departureTimeEstimated"]),
                    arrival=_parse_ts(leg["destination"]["arrivalTimeEstimated"]),
                    stop_coords=coords,
                )
            )
        return cls(legs=legs)


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
