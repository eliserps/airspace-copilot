import math
import threading
import time
from collections import Counter

from config import LANGUAGE_NAMES
from llm import ask

SYSTEM_PROMPT = """You are an airspace analyst assistant.

STRICT RULES:
- Use ONLY the aircraft data provided. Never invent flights, airlines or numbers.
- The data comes from OpenSky, a volunteer-powered ADS-B network with partial
 coverage. It shows DETECTED aircraft, not all aircraft flying. Always make
 this limitation clear.
- If the data is empty, say so plainly. Do not speculate.
- Be concise and factual. No filler.
"""

FL100_M = 3048
FL300_M = 9144
LOW_ALTITUDE_M = 1000

TOP_COUNTRIES = 8
TOP_AIRLINES = 8
NOTABLE_LIMIT = 5


def summarize_aircraft(aircraft: list) -> dict:
   """Aggregates raw OpenSky state vectors into the numbers a briefing needs.

   The model used to receive one line per aircraft, which for a busy region is
   thousands of tokens of data it only ever counted. Counting here costs nothing
   and keeps the prompt the same size whether there are 50 aircraft or 10,000.
   """
   countries = Counter()
   airlines = Counter()
   bands = {"below_fl100": 0, "fl100_300": 0, "above_fl300": 0}
   on_ground = 0
   no_altitude = 0
   low_flyers = []

   for plane in aircraft:
       callsign = (plane[1] or "").strip()
       countries[plane[2] or "unknown"] += 1

       prefix = callsign[:3]
       if len(callsign) > 3 and prefix.isalpha() and callsign[3].isdigit():
           airlines[prefix.upper()] += 1

       if plane[8]:
           on_ground += 1
           continue

       altitude = plane[7] if plane[7] is not None else plane[13]
       if altitude is None:
           no_altitude += 1
       elif altitude < FL100_M:
           bands["below_fl100"] += 1
           if 0 <= altitude < LOW_ALTITUDE_M:
               low_flyers.append((altitude, callsign or "unknown", plane[2], plane[9]))
       elif altitude < FL300_M:
           bands["fl100_300"] += 1
       else:
           bands["above_fl300"] += 1

   low_flyers.sort()
   return {
       "total": len(aircraft),
       "on_ground": on_ground,
       "airborne": len(aircraft) - on_ground,
       "no_altitude": no_altitude,
       "bands": bands,
       "countries": countries.most_common(TOP_COUNTRIES),
       "airlines": airlines.most_common(TOP_AIRLINES),
       "low_flyers_count": len(low_flyers),
       "lowest": low_flyers[:NOTABLE_LIMIT],
   }


def format_summary(stats: dict) -> str:
   """Turns the aggregated stats into compact text for the model."""
   if stats["total"] == 0:
       return "No aircraft detected in this area."

   bands = stats["bands"]
   countries = ", ".join(f"{name} {n}" for name, n in stats["countries"]) or "none"
   airlines = ", ".join(f"{code} {n}" for code, n in stats["airlines"]) or "none"
   lines = [
       f"Total detected: {stats['total']} "
       f"(airborne {stats['airborne']}, on ground {stats['on_ground']}, "
       f"no altitude reported {stats['no_altitude']})",
       f"Airborne by altitude: below FL100 {bands['below_fl100']}, "
       f"FL100-FL300 {bands['fl100_300']}, above FL300 {bands['above_fl300']}",
       f"Top countries of registration: {countries}",
       f"Top airline callsign prefixes (ICAO codes): {airlines}",
       f"Airborne below {LOW_ALTITUDE_M} m: {stats['low_flyers_count']}",
   ]
   for altitude, callsign, country, velocity in stats["lowest"]:
       lines.append(f"- {callsign} | {country} | altitude {altitude:.0f} m | speed {velocity} m/s")
   return "\n".join(lines)


BRIEFING_TTL_SECONDS = 180
_briefings: dict[tuple[str, str], dict] = {}
_briefing_locks: dict[tuple[str, str], threading.Lock] = {}


def _bucket(n: int) -> int:
   """Groups a count into ~10% steps, so 842 -> 851 is 'unchanged'."""
   return 0 if n <= 0 else round(math.log(n) / math.log(1.1))


def _fingerprint(stats: dict) -> tuple:
   """What has to change for a new briefing to say something different."""
   return (
       _bucket(stats["total"]),
       _bucket(stats["on_ground"]),
       _bucket(stats["low_flyers_count"]),
       tuple(name for name, _ in stats["countries"][:3]),
       tuple(code for code, _ in stats["airlines"][:3]),
   )


def generate_briefing(aircraft: list, region: str, language: str = "en") -> str:
   """Generates a natural-language briefing of the current airspace."""
   stats = summarize_aircraft(aircraft)
   key = (region.lower().strip(), language)
   with _briefing_locks.setdefault(key, threading.Lock()):
       return _generate_briefing_locked(stats, key, region, language)


def _generate_briefing_locked(stats: dict, key: tuple[str, str], region: str, language: str) -> str:
   """Body of generate_briefing(); must run while holding the lock for `key`."""
   now = time.time()
   cached = _briefings.get(key)

   if cached and now - cached["at"] < BRIEFING_TTL_SECONDS:
       return cached["text"]

   fingerprint = _fingerprint(stats)
   if cached and cached["fingerprint"] == fingerprint:
       print(f"[briefing] {key} unchanged, reusing")
       return cached["text"]

   language_name = LANGUAGE_NAMES[language]
   prompt = f"""Write a short airspace briefing for: {region}
Aggregated data for the aircraft currently detected:
{format_summary(stats)}
Write the briefing in {language_name}. Cover:
1. How many aircraft were detected
2. Which countries/airlines appear most
3. Anything notable (unusually low altitude, aircraft on ground, etc.)
4. A one-line reminder that coverage is partial
Keep it under 150 words."""
   text = ask(prompt, system_prompt=SYSTEM_PROMPT, label="briefing")
   if text and text.strip():
       _briefings[key] = {"text": text, "fingerprint": fingerprint, "at": now}
   return text
