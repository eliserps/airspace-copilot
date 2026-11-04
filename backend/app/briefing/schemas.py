from pydantic import BaseModel, Field


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
