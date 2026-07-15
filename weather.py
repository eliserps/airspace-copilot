import requests

BASE_URL = "https://aviationweather.gov/api/data/metar"

def get_metar(icao_code: str) -> str | None:
   """Fetches the latest raw METAR for an airport. Returns None if unavailable."""
   response = requests.get(
       BASE_URL,
       params={"ids": icao_code, "format": "raw"},
   )
   response.raise_for_status()
   text = response.text.strip()
   return text or None