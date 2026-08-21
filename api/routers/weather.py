"""METAR endpoint. Calls get_metar() and decode_metar() from src/."""

from fastapi import APIRouter, HTTPException, Path, Query

from decoder import decode_metar
from weather import get_metar

from ..errors import SOURCE_AWC, error_detail, invalid_language
from ..schemas import LANGUAGES, WeatherResponse

router = APIRouter(tags=["weather"])


@router.get("/weather/{icao}", response_model=WeatherResponse)
def weather(
    icao: str = Path(min_length=4, max_length=4,
                     description="4-letter ICAO code, e.g. SBGR."),
    lang: str = Query("en", description="'en' or 'pt'."),
):
    """Raw METAR plus a plain-language decoding for one airport."""
    if lang not in LANGUAGES:
        raise invalid_language(LANGUAGES)

    code = icao.upper()
    metar = get_metar(code)

    # get_metar() returns None both when the airport has no report and when the
    # service failed -- it cannot distinguish them, so neither can this endpoint.
    if not metar:
        raise HTTPException(
            status_code=404,
            detail=error_detail(
                "no_metar",
                f"No METAR available for {code} right now.",
                icao=code,
            ),
        )

    return {
        "icao": code,
        "language": lang,
        "raw": metar,
        "decoded": decode_metar(metar, language=lang),
        "source": SOURCE_AWC,
    }
