import time
from opensky import get_token, get_aircraft

REGIONS = {
   "brazil": (-34.0, 6.0, -74.0, -34.0),
   "sao_paulo": (-24.5, -22.5, -48.0, -45.5),
   "rio_de_janeiro": (-23.5, -21.5, -44.5, -42.0),
   "porto_alegre": (-31.0, -29.5, -51.5, -50.0),
   "brasilia": (-16.5, -15.0, -48.5, -47.0),
}

_token_cache = {"value": None, "expires_at": 0}
TOKEN_TTL_SECONDS = 1500

def _cached_token() -> str:
   """Returns a valid token, reusing it until it is close to expiring."""
   now = time.time()

   if _token_cache["value"] is None or now >= _token_cache["expires_at"]:
       _token_cache["value"] = get_token()
       _token_cache["expires_at"] = now + TOKEN_TTL_SECONDS
   return _token_cache["value"]

def is_known_region(region: str) -> bool:
   """True when the region has a bounding box defined."""
   return region.lower().strip() in REGIONS


def get_aircraft_for_region(region: str) -> list:
   """Fetches raw state vectors for a known region.

   Raises KeyError for an unknown region so callers can tell "no such region"
   apart from "region exists but is empty" — those are different answers.
   """
   key = region.lower().strip()

   if key not in REGIONS:
       raise KeyError(region)
   lamin, lamax, lomin, lomax = REGIONS[key]
   return get_aircraft(_cached_token(), lamin, lamax, lomin, lomax)


# OpenSky state vectors are positional arrays, not objects. Naming the indices
# here keeps that knowledge in one place -- and index 5 is LONGITUDE while index 6
# is LATITUDE, the reverse of the (lat, lon) order most map libraries expect.
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

       # Barometric altitude is the usual reading; geometric is the fallback when
       # the transponder does not report it. Both are metres.
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
   key = region.lower().strip()

   if key not in REGIONS:
       return f"Unknown region '{region}'. Available: {', '.join(REGIONS)}"
   lamin, lamax, lomin, lomax = REGIONS[key]
   aircraft = get_aircraft(_cached_token(), lamin, lamax, lomin, lomax)

   if not aircraft:
       return f"No aircraft detected over {region} right now."
   lines = [f"{len(aircraft)} aircraft detected over {region}."]

   for plane in aircraft[:5]:
       callsign = (plane[1] or "").strip() or "unknown"
       lines.append(f"- {callsign} at {plane[7]} m")

   return "\n".join(lines)