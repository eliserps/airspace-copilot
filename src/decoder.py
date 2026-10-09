import json

from .config import LANGUAGE_NAMES
from .llm import ask
from .rag import search

SYSTEM_PROMPT = """You are an aviation weather decoder.

STRICT RULES:
- Decode METAR reports using ONLY the reference documentation provided.
- If a code is not covered by the documentation, say you cannot decode it.
 Never guess.
- Always state the operational meaning: are conditions good or poor for landing?
- Be concise and factual.
"""

STRUCTURED_SYSTEM_PROMPT = """You are an aviation weather decoder.

STRICT RULES:
- Decode METAR reports using ONLY the reference documentation provided.
- If a code is not covered by the documentation, list it in undecodable_codes
 and do NOT invent a meaning for it. Never guess.
- Answer with a single JSON object and nothing else.
"""

STRUCTURED_SCHEMA = """Answer with a JSON object with EXACTLY these keys:

{
 "station": string,                      // ICAO code
 "wind_direction_deg": int or null,      // null if VRB or calm
 "wind_speed_kt": int,                   // knots
 "wind_gust_kt": int or null,            // null if no gust reported, never 0
 "wind_variable_from_deg": int or null,  // the "140V200" group, lower bound
 "wind_variable_to_deg": int or null,    // the "140V200" group, upper bound
 "visibility_m": int or null,            // METRES; 9999 stays 9999
 "cavok": boolean,
 "weather": [string],                    // raw codes, e.g. ["-RA","BR"], [] if none
 "cloud_layers": [{"cover": string, "height_ft": int}],  // height in FEET
 "ceiling_ft": int or null,              // lowest BKN/OVC layer; null if none
 "temperature_c": int,
 "dewpoint_c": int,
 "qnh_hpa": int or null,
 "undecodable_codes": [string],          // codes absent from the documentation
 "summary": string                       // one-line operational reading
}

Rules for the values:
- Cloud height is in HUNDREDS of feet: BKN007 is 700, not 7 and not 700 metres.
- The ceiling is the height of the LOWEST BKN or OVC layer. FEW and SCT are
 never a ceiling. If there is no BKN or OVC layer, ceiling_ft is null.
- "140V200" is a wind DIRECTION range in degrees. It is never visibility and
 never a gust.
- Use null for absent values, not 0 and not "unknown"."""


def _retrieve(metar: str, n_results: int = 8) -> tuple[str, list[dict]]:
   """Fetches reference chunks for a METAR and formats them as prompt context."""
   chunks = search(metar, n_results=n_results)
   context = "\n\n---\n\n".join(
       f"[source: {c['source']}]\n{c['text']}" for c in chunks
   )
   return context, chunks


_DECODED_CACHE_MAX = 256
_decoded_cache: dict[tuple[str, str], str] = {}


def decode_metar(metar: str | None, language: str = "en") -> str:
   """Decodes a raw METAR into plain language, grounded in the reference docs."""
   if not metar or not metar.strip():
       return "No METAR available for this airport right now."

   key = (metar.strip(), language)
   if key in _decoded_cache:
       return _decoded_cache[key]

   context, _ = _retrieve(metar)

   language_name = LANGUAGE_NAMES[language]

   prompt = f"""Reference documentation:

{context}

---

Decode this METAR in {language_name}:

{metar}

Explain each element, then give a one-line operational summary."""

   decoded = ask(prompt, system_prompt=SYSTEM_PROMPT, label="metar")

   if decoded and decoded.strip():
       if len(_decoded_cache) >= _DECODED_CACHE_MAX:
           _decoded_cache.clear()
       _decoded_cache[key] = decoded
   return decoded


def decode_metar_structured(metar: str | None) -> dict:
   """Decodes a METAR into structured fields for field-by-field evaluation.

   Returns a dict with the contract keys plus:
     "_retrieved_sources": which chunks RAG returned, so a wrong answer can be
       traced to retrieval (the chunk never arrived) or faithfulness (it arrived
       and was ignored) -- different bugs with different fixes.
     "_error": set when the model returned something that is not valid JSON.
   """
   if not metar or not metar.strip():
       return {"_error": "empty METAR", "_retrieved_sources": []}

   context, chunks = _retrieve(metar)
   sources = [c["source"] for c in chunks]

   prompt = f"""Reference documentation:

{context}

---

Decode this METAR:

{metar}

{STRUCTURED_SCHEMA}"""

   raw = ask(prompt, system_prompt=STRUCTURED_SYSTEM_PROMPT, json_mode=True)

   try:
       decoded = json.loads(raw)
   except json.JSONDecodeError as error:
       return {"_error": f"invalid JSON: {error}", "_raw": raw,
               "_retrieved_sources": sources}

   decoded["_retrieved_sources"] = sources
   return decoded
