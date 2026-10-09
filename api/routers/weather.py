"""METAR endpoint. Calls fetch_metar() and decode_metar() from src/."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from src.decoder import decode_metar
from src.weather import fetch_metar

from ..errors import SOURCE_AWC, error_detail, invalid_language
from ..ratelimit import weather_limiter
from ..schemas import LANGUAGES, WeatherResponse

router = APIRouter(tags=["weather"])


@router.get(
    "/weather/{icao}",
    response_model=WeatherResponse,
    dependencies=[Depends(weather_limiter)],
)
def weather(
    icao: str = Path(pattern=r"^[A-Za-z0-9]{4}$",
                     description="4-character ICAO code, e.g. SBGR."),
    lang: str = Query("en", description="'en' or 'pt'."),
):
    """Raw METAR plus a plain-language decoding for one airport."""
    if lang not in LANGUAGES:
        raise invalid_language(LANGUAGES)

    code = icao.upper()
    metar = fetch_metar(code)

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
