from pydantic import BaseModel, Field


class BriefingResponse(BaseModel):
    region: str
    language: str
    aircraft_count: int = Field(
        description="Aircraft in the current snapshot. A reused briefing may have been "
        "written from a count up to about 10% different."
    )
    briefing: str = Field(description="Markdown.")
    generated_at: float = Field(
        description="Unix time (seconds) the briefing was generated; may be cached."
    )
    stale: bool = Field(
        description="True when the traffic data is the last good snapshot because OpenSky "
        "is failing."
    )
    source: str
