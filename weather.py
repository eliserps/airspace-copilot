import requests

BASE_URL = "https://aviationweather.gov/api/data/metar"
TIMEOUT_SECONDS = 10

def get_metar(icao_code: str) -> str | None:
   """Fetches the latest raw METAR for an airport.
   Returns None if the airport has no report or the service is unavailable.
   External APIs fail — this must never crash the caller.
   """
   try:
       response = requests.get(
           BASE_URL,
           params={"ids": icao_code, "format": "raw"},
           timeout=TIMEOUT_SECONDS,
       )
       response.raise_for_status()
   except requests.RequestException as error:
       print(f"[weather] failed to fetch {icao_code}: {error}")
       return None
   text = response.text.strip()
   return text or None
