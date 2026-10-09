"""Airspace briefing endpoint. Calls generate_briefing_with_meta() from src/."""

from fastapi import APIRouter, Query

from src.briefing import generate_briefing_with_meta
from src.tools import REGIONS, get_aircraft_for_region, normalise_region

from ..errors import SOURCE_OPENSKY, invalid_language, unknown_region
from ..schemas import LANGUAGES, BriefingResponse

router = APIRouter(tags=["airspace"])


@router.get("/briefing", response_model=BriefingResponse)
def briefing(
    region: str = Query("south_america", description="One of the regions from /health."),
    lang: str = Query("en", description="'en' or 'pt'."),
):
    """Natural-language briefing of current traffic over a region."""
    if lang not in LANGUAGES:
        raise invalid_language(LANGUAGES)
    try:
        aircraft = get_aircraft_for_region(region)
    except KeyError:
        raise unknown_region(region, list(REGIONS))

    key = normalise_region(region)
    result = generate_briefing_with_meta(aircraft, key, lang)

    return {
        "region": key,
        "language": lang,
        "aircraft_count": result["aircraft_count"],
        "briefing": result["text"],
        "generated_at": result["generated_at"],
        "source": SOURCE_OPENSKY,
    }
