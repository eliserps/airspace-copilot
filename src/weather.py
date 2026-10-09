import re

import requests

BASE_URL = "https://aviationweather.gov/api/data/metar"
TIMEOUT_SECONDS = 10

ICAO_PATTERN = re.compile(r"^[A-Z0-9]{4}$")


def is_valid_icao(icao_code: str) -> bool:
   return bool(ICAO_PATTERN.fullmatch(icao_code or ""))


def fetch_metar(icao_code: str) -> str | None:
   code = (icao_code or "").strip().upper()
   if not is_valid_icao(code):
       raise ValueError(f"'{icao_code}' is not a 4-character ICAO code.")
   response = requests.get(
       BASE_URL,
       params={"ids": code, "format": "raw"},
       timeout=TIMEOUT_SECONDS,
   )
   response.raise_for_status()
   text = response.text.strip()
   return text or None


def get_metar(icao_code: str) -> str | None:
   """Fetches the latest raw METAR for an airport.
   Returns None if the airport has no report or the service is unavailable.
   External APIs fail — this must never crash the caller.
   """
   try:
       return fetch_metar(icao_code)
   except (ValueError, requests.RequestException) as error:
       print(f"[weather] failed to fetch {icao_code}: {error}")
       return None
