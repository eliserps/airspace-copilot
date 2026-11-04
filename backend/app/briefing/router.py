from typing import Annotated

from fastapi import APIRouter, Query

from app.core.config import Language
from app.dependencies import BriefingDep, TrafficDep
from app.traffic.regions import resolve_region
from app.traffic.router import SOURCE, RegionQuery

from .schemas import BriefingResponse

router = APIRouter(tags=["airspace"])


@router.get("/briefing", response_model=BriefingResponse)
async def briefing(
    traffic: TrafficDep,
    briefings: BriefingDep,
    region: RegionQuery = "south_america",
    lang: Annotated[Language, Query(description="'en' or 'pt'.")] = "en",
) -> BriefingResponse:
    """Natural-language briefing of current traffic over a region."""
    key = resolve_region(region)
    snapshot = await traffic.snapshot(key)
    result = await briefings.generate(snapshot.aircraft, key, lang)
    return BriefingResponse(
        region=key,
        language=lang,
        aircraft_count=result.aircraft_count,
        briefing=result.text,
        generated_at=result.generated_at,
        source=SOURCE,
    )
