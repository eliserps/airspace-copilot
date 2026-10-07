import threading
import time

import requests
from opensky import get_token, get_aircraft

REGIONS = {
   "south_america": (-56.0, 13.0, -82.0, -34.0),
   "north_america": (24.0, 60.0, -130.0, -60.0),
   "europe": (35.0, 60.0, -10.0, 30.0),
   "africa": (-35.0, 37.0, -18.0, 52.0),
   "asia": (5.0, 55.0, 60.0, 145.0),
   "oceania": (-47.0, -8.0, 110.0, 180.0),
   "world": (-90.0, 90.0, -180.0, 180.0),
}

_token_cache = {"value": None, "expires_at": 0}
_token_lock = threading.Lock()
TOKEN_TTL_SECONDS = 1500

def _cached_token() -> str:
   """Returns a valid token, reusing it until it is close to expiring."""
   with _token_lock:
       now = time.time()
       if _token_cache["value"] is None or now >= _token_cache["expires_at"]:
           _token_cache["value"] = get_token()
           _token_cache["expires_at"] = now + TOKEN_TTL_SECONDS
       return _token_cache["value"]


def _invalidate_token(rejected: str) -> None:
   """Drops the cached token, unless another thread already replaced it."""
   with _token_lock:
       if _token_cache["value"] == rejected:
           _token_cache["value"] = None


def _get_aircraft_authenticated(lamin, lamax, lomin, lomax) -> list:
   """Fetches state vectors, refreshing the token once if OpenSky rejects it.

   The TTL is only an estimate of the token's life; a token revoked or expired
   early would otherwise fail every request until the TTL ran out.
   """
   token = _cached_token()
   try:
       return get_aircraft(token, lamin, lamax, lomin, lomax)
   except requests.HTTPError as error:
       if error.response is None or error.response.status_code != 401:
           raise
       _invalidate_token(token)
       return get_aircraft(_cached_token(), lamin, lamax, lomin, lomax)

AIRCRAFT_TTL_SECONDS = 30
_aircraft_cache: dict[str, tuple[float, list]] = {}
_region_locks = {key: threading.Lock() for key in REGIONS}


def _fetch_region(key: str) -> list:
   """Fetches state vectors for a known region key, reusing a recent result."""
   with _region_locks[key]:
       now = time.time()
       cached = _aircraft_cache.get(key)

       if cached and now - cached[0] < AIRCRAFT_TTL_SECONDS:
           return cached[1]
       lamin, lamax, lomin, lomax = REGIONS[key]
       aircraft = _get_aircraft_authenticated(lamin, lamax, lomin, lomax)
       _aircraft_cache[key] = (time.time(), aircraft)
       return aircraft


def get_aircraft_for_region(region: str) -> list:
   """Fetches raw state vectors for a known region.

   Raises KeyError for an unknown region so callers can tell "no such region"
   apart from "region exists but is empty" — those are different answers.
   """
   key = region.lower().strip()

   if key not in REGIONS:
       raise KeyError(region)
   return _fetch_region(key)

ICAO24 = 0
CALLSIGN = 1
ORIGIN_COUNTRY = 2
LONGITUDE = 5
LATITUDE = 6
BARO_ALTITUDE = 7
ON_GROUND = 8
VELOCITY = 9
TRUE_TRACK = 10
GEO_ALTITUDE = 13


def list_aircraft(region: str) -> list[dict]:
   """Returns aircraft over a region as objects, for plotting on a map.

   Aircraft without a known position are dropped: a pin cannot be placed for
   them, and a null coordinate is more likely to be rendered at (0, 0) off the
   coast of Africa than to be handled.

   Raises KeyError for an unknown region, like get_aircraft_for_region().
   """
   aircraft = get_aircraft_for_region(region)

   plotted = []
   for plane in aircraft:
       latitude = plane[LATITUDE]
       longitude = plane[LONGITUDE]

       if latitude is None or longitude is None:
           continue

       altitude = plane[BARO_ALTITUDE]
       if altitude is None:
           altitude = plane[GEO_ALTITUDE]

       plotted.append({
           "icao24": plane[ICAO24],
           "callsign": (plane[CALLSIGN] or "").strip() or None,
           "country": plane[ORIGIN_COUNTRY],
           "latitude": latitude,
           "longitude": longitude,
           "altitude_m": altitude,
           "on_ground": bool(plane[ON_GROUND]),
           "velocity_ms": plane[VELOCITY],
           "heading_deg": plane[TRUE_TRACK],
       })

   return plotted


def count_aircraft(region: str) -> str:
   """Returns a summary of aircraft currently detected over a known region."""
   try:
       aircraft = get_aircraft_for_region(region)
   except KeyError:
       return f"Unknown region '{region}'. Available: {', '.join(REGIONS)}"

   if not aircraft:
       return f"No aircraft detected over {region} right now."
   lines = [f"{len(aircraft)} aircraft detected over {region}."]

   for plane in aircraft[:5]:
       callsign = (plane[1] or "").strip() or "unknown"
       lines.append(f"- {callsign} at {plane[7]} m")

   return "\n".join(lines)