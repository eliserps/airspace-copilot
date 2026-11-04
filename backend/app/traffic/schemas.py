from pydantic import BaseModel, Field

from .models import StateVector


class Bounds(BaseModel):
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float


class Aircraft(BaseModel):
    icao24: str = Field(description="ICAO 24-bit transponder address.")
    callsign: str | None = Field(description="Trimmed; null when not broadcast.")
    country: str
    latitude: float = Field(description="Decimal degrees.")
    longitude: float = Field(description="Decimal degrees.")
    altitude_m: float | None = Field(description="Metres; barometric, falling back to geometric.")
    on_ground: bool
    velocity_ms: float | None = Field(description="Metres per second.")
    heading_deg: float | None = Field(description="True track, 0-360.")

    @classmethod
    def from_state(cls, plane: StateVector) -> "Aircraft":
        assert plane.latitude is not None and plane.longitude is not None
        return cls(
            icao24=plane.icao24,
            callsign=plane.callsign,
            country=plane.origin_country,
            latitude=plane.latitude,
            longitude=plane.longitude,
            altitude_m=plane.altitude,
            on_ground=plane.on_ground,
            velocity_ms=plane.velocity,
            heading_deg=plane.true_track,
        )


class AircraftMapResponse(BaseModel):
    region: str
    count: int = Field(description="Aircraft with a known position. Can be lower than /aircraft.")
    bounds: Bounds = Field(description="Region bounding box, for the initial viewport.")
    aircraft: list[Aircraft]
    fetched_at: float = Field(description="Unix time (seconds) of the OpenSky fetch.")
    stale: bool = Field(
        description="True when this is the last good result (at most 10 min old) "
        "because OpenSky is failing."
    )
    source: str


class AircraftSummaryResponse(BaseModel):
    region: str
    summary: str = Field(description="Plain-text summary. For structured data use /aircraft/map.")
    source: str
