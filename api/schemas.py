from pydantic import BaseModel, Field, field_validator

from src.config import LANGUAGE_NAMES
from src.tools import REGIONS

LANGUAGES = tuple(LANGUAGE_NAMES)


class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=500,
        description="Natural-language question about traffic or weather.",
        examples=["Is the weather good for landing at Guarulhos?"],
    )
    region: str | None = Field(
        default=None,
        description="Map region the user is viewing, one of the regions from "
                    "/health. Lets \"how many planes here?\" resolve.",
        examples=["south_america"],
    )

    @field_validator("region")
    @classmethod
    def known_region(cls, value: str | None) -> str | None:
        if value is None:
            return None
        key = value.lower().strip()
        if key not in REGIONS:
            raise ValueError(f"region must be one of {sorted(REGIONS)}")
        return key


class HealthResponse(BaseModel):
    status: str
    regions: list[str] = Field(description="Valid values for the `region` parameter.")
    languages: list[str] = Field(description="Valid values for the `lang` parameter.")


class BriefingResponse(BaseModel):
    region: str
    language: str
    aircraft_count: int = Field(
        description="Aircraft in the snapshot the briefing was written from."
    )
    briefing: str = Field(description="Markdown.")
    generated_at: float = Field(
        description="Unix time (seconds) the briefing was generated; may be cached."
    )
    source: str


class WeatherResponse(BaseModel):
    icao: str
    language: str
    raw: str = Field(description="The unmodified METAR string.")
    decoded: str = Field(description="Markdown.")
    source: str


class AircraftSummaryResponse(BaseModel):
    region: str
    summary: str = Field(
        description="Newline-joined text from count_aircraft(). "
                    "For structured data use /aircraft/map."
    )
    source: str


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


class AircraftMapResponse(BaseModel):
    region: str
    count: int = Field(
        description="Aircraft with a known position. Can be lower than /aircraft."
    )
    bounds: Bounds = Field(description="Region bounding box, for the initial viewport.")
    aircraft: list[Aircraft]
    fetched_at: float = Field(description="Unix time (seconds) of the OpenSky fetch.")
    stale: bool = Field(
        description="True when this is the last good result (at most 10 min old) "
                    "because OpenSky is failing."
    )
    source: str


class AskResponse(BaseModel):
    question: str = Field(description="The question as the user typed it.")
    answer: str = Field(description="Markdown.")
    flagged: bool = Field(
        default=False,
        description="True when the input guardrails flagged a possible injection attempt.",
    )

