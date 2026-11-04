import re
from typing import Protocol

import httpx

from app.core.errors import InvalidInputError, NotFoundError

METAR_URL = "https://aviationweather.gov/api/data/metar"
ICAO_PATTERN = re.compile(r"^[A-Z0-9]{4}$")


class InvalidIcaoError(InvalidInputError):
    code = "invalid_icao"

    def __init__(self, icao: str):
        super().__init__(f"'{icao}' is not a 4-character ICAO code.", icao=icao)


class NoMetarError(NotFoundError):
    code = "no_metar"

    def __init__(self, icao: str):
        super().__init__(f"No METAR available for {icao} right now.", icao=icao)


def normalise_icao(icao: str) -> str:
    code = (icao or "").strip().upper()
    if not ICAO_PATTERN.fullmatch(code):
        raise InvalidIcaoError(icao)
    return code


class MetarSource(Protocol):
    async def latest(self, icao: str) -> str | None: ...


class AviationWeatherClient:
    def __init__(self, http: httpx.AsyncClient):
        self.http = http

    async def latest(self, icao: str) -> str | None:
        code = normalise_icao(icao)
        response = await self.http.get(METAR_URL, params={"ids": code, "format": "raw"})
        response.raise_for_status()
        return response.text.strip() or None
