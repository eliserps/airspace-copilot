"""Shared Pydantic models for request and response bodies.

These document the contract in one place and make the shapes visible in /docs and
openapi.json, which is what the frontend integrates against. They describe what the
existing src/ functions already return -- they do not reshape anything.
"""

from pydantic import BaseModel, Field

from config import LANGUAGE_NAMES

LANGUAGES = tuple(LANGUAGE_NAMES)


class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=500,
        description="Natural-language question about traffic or weather.",
        examples=["Is the weather good for landing at Guarulhos?"],
    )


class HealthResponse(BaseModel):
    status: str
    regions: list[str] = Field(description="Valid values for the `region` parameter.")
    languages: list[str] = Field(description="Valid values for the `lang` parameter.")


class BriefingResponse(BaseModel):
    region: str
    language: str
    aircraft_count: int = Field(
        description="Real count from OpenSky, not parsed from the text."
    )
    briefing: str = Field(description="Markdown.")
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
    icao24: str = Field(description="Unique transponder address. Use as list key.")
    callsign: str | None = Field(description="Trimmed; null when not broadcast.")
    country: str
    latitude: float = Field(description="Decimal degrees. Never null.")
    longitude: float = Field(description="Decimal degrees. Never null.")
    altitude_m: float | None = Field(description="METRES. Barometric, geometric fallback.")
    on_ground: bool
    velocity_ms: float | None = Field(description="METRES PER SECOND.")
    heading_deg: float | None = Field(description="True track, 0-360.")


class AircraftMapResponse(BaseModel):
    region: str
    count: int = Field(
        description="Aircraft with a known position. Can be lower than /aircraft."
    )
    bounds: Bounds = Field(description="Region bounding box, for the initial viewport.")
    aircraft: list[Aircraft]
    source: str


class AskResponse(BaseModel):
    question: str = Field(description="Echoes what the user typed, before guardrails.")
    answer: str = Field(description="Markdown.")
    flagged: bool = Field(
        default=False,
        description="True when input guardrails detected a possible injection "
                    "attempt. The question was still answered, with the text "
                    "fenced as untrusted data.",
    )

