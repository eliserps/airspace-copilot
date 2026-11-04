from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class StateVector:
    icao24: str
    callsign: str | None
    origin_country: str
    longitude: float | None
    latitude: float | None
    baro_altitude: float | None
    on_ground: bool
    velocity: float | None
    true_track: float | None
    geo_altitude: float | None

    @classmethod
    def from_opensky(cls, row: Sequence[Any]) -> "StateVector":
        return cls(
            icao24=row[0],
            callsign=(row[1] or "").strip() or None,
            origin_country=row[2] or "",
            longitude=row[5],
            latitude=row[6],
            baro_altitude=row[7],
            on_ground=bool(row[8]),
            velocity=row[9],
            true_track=row[10],
            geo_altitude=row[13],
        )

    @property
    def altitude(self) -> float | None:
        return self.geo_altitude if self.baro_altitude is None else self.baro_altitude

    @property
    def has_position(self) -> bool:
        return self.latitude is not None and self.longitude is not None


@dataclass(frozen=True, slots=True)
class Snapshot:
    aircraft: list[StateVector]
    fetched_at: float
    stale: bool
