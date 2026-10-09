from .tools import get_aircraft_for_region
from .weather import get_metar
from .briefing import generate_briefing
from .decoder import decode_metar
from .agent import run_agent

REGION = "south_america"

AIRPORTS = ["SBGR", "SBGL", "SBPA"]
LANGUAGE = "pt"

aircraft = get_aircraft_for_region(REGION)
print(f"{len(aircraft)} aircraft detected\n")

print("--- DECODED WEATHER ---")
for airport in AIRPORTS:
   metar = get_metar(airport)
   print(f"\n[{airport}] raw: {metar!r}")
   print(decode_metar(metar, language=LANGUAGE))

print(f"\n--- BRIEFING ({LANGUAGE.upper()}) ---")
print(generate_briefing(aircraft, REGION, LANGUAGE))

print("\n--- AGENT ---")
print(run_agent("Como está o tempo para pouso em Porto Alegre?"))
print()
print(run_agent("Quantos aviões existem no total?"))
print(run_agent("Quantos aviões estão sobre o Rio de Janeiro agora?"))
print(run_agent("O tempo está bom para pousar em Guarulhos?"))