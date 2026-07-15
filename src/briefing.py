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

def format_aircraft(aircraft: list) -> str:
   """Turns raw OpenSky state vectors into readable text for the model."""
   if not aircraft:
       return "No aircraft detected in this area."
   lines = []
   for plane in aircraft:
       callsign = (plane[1] or "").strip() or "unknown"
       country = plane[2]
       altitude = plane[7]
       velocity = plane[9]
       on_ground = plane[8]
       status = "on ground" if on_ground else f"altitude {altitude} m"
       lines.append(f"- {callsign} | {country} | {status} | speed {velocity} m/s")
   return "\n".join(lines)

def generate_briefing(aircraft: list, region: str, language: str = "en") -> str:
   """Generates a natural-language briefing of the current airspace."""
   language_name = "English" if language == "en" else "Brazilian Portuguese"
   prompt = f"""Write a short airspace briefing for: {region}
Aircraft currently detected ({len(aircraft)} total):
{format_aircraft(aircraft)}
Write the briefing in {language_name}. Cover:
1. How many aircraft were detected
2. Which countries/airlines appear most
3. Anything notable (unusually low altitude, aircraft on ground, etc.)
4. A one-line reminder that coverage is partial
Keep it under 150 words."""
   return ask(prompt, system_prompt=SYSTEM_PROMPT)