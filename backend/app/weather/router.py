from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.core.config import Language
from app.dependencies import DecoderDep, MetarDep, limit_weather

from .metar import NoMetarError
from .schemas import WeatherResponse

SOURCE = "Aviation Weather Center"

router = APIRouter(tags=["weather"])


@router.get(
    "/weather/{icao}", response_model=WeatherResponse, dependencies=[Depends(limit_weather)]
)
async def weather(
    metar_source: MetarDep,
    decoder: DecoderDep,
    icao: Annotated[
        str, Path(pattern=r"^[A-Za-z0-9]{4}$", description="4-character ICAO code, e.g. SBGR.")
    ],
    lang: Annotated[Language, Query(description="'en' or 'pt'.")] = "en",
) -> WeatherResponse:
    """Raw METAR plus a plain-language decoding for one airport."""
    code = icao.upper()
    metar = await metar_source.latest(code)
    if not metar:
        raise NoMetarError(code)
    return WeatherResponse(
        icao=code,
        language=lang,
        raw=metar,
        decoded=await decoder.decode(metar, lang),
        source=SOURCE,
    )
