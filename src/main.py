from opensky import get_token, get_aircraft
from weather import get_metar
from briefing import generate_briefing
from decoder import decode_metar

# Brazil (full country)
LAT_MIN, LAT_MAX = -34.0, 6.0
LON_MIN, LON_MAX = -74.0, -34.0
REGION = "Brazilian airspace"

AIRPORTS = ["SBGR", "SBGL", "SBPA"]
LANGUAGE = "pt"

# --- Live traffic ---
token = get_token()
aircraft = get_aircraft(token, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX)
print(f"{len(aircraft)} aircraft detected\n")

# --- Weather ---
print("--- DECODED WEATHER ---")
for airport in AIRPORTS:
   metar = get_metar(airport)
   print(f"\n[{airport}] raw: {metar!r}")
   print(decode_metar(metar, language=LANGUAGE))

# --- Briefing ---
print(f"\n--- BRIEFING ({LANGUAGE.upper()}) ---")
print(generate_briefing(aircraft, REGION, LANGUAGE))