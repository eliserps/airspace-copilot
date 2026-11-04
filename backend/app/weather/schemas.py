from pydantic import BaseModel, Field


class WeatherResponse(BaseModel):
    icao: str
    language: str
    raw: str = Field(description="The unmodified METAR string.")
    decoded: str = Field(description="Markdown.")
    source: str
