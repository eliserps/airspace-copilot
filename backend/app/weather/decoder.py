import json
from typing import Any

from app.core.cache import TimedCache
from app.core.config import LANGUAGE_NAMES, Language
from app.core.metrics import CACHE_LOOKUPS
from app.llm.client import LLMClient

from .knowledge import ReferenceDoc, format_reference

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


class MetarDecoder:
    def __init__(self, llm: LLMClient, reference: list[ReferenceDoc], cache_size: int = 256):
        self.llm = llm
        self.reference = format_reference(reference)
        self._cache: TimedCache[tuple[str, Language], str] = TimedCache(max_entries=cache_size)

    async def decode(self, metar: str, language: Language = "en") -> str:
        key = (metar.strip(), language)
        if cached := self._cache.get(key):
            CACHE_LOOKUPS.labels("metar", "hit").inc()
            return cached.value
        CACHE_LOOKUPS.labels("metar", "miss").inc()

        prompt = f"""Reference documentation:

{self.reference}

---

Decode this METAR in {LANGUAGE_NAMES[language]}:

{metar}

Explain each element, then give a one-line operational summary."""

        completion = await self.llm.complete(
            [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            label="metar",
        )
        if completion.content.strip():
            self._cache.set(key, completion.content)
        return completion.content

    async def decode_structured(self, metar: str) -> dict[str, Any]:
        """Decodes a METAR into the fields scored by evals/evaluate.py."""
        if not metar.strip():
            return {"_error": "empty METAR"}

        prompt = f"""Reference documentation:

{self.reference}

---

Decode this METAR:

{metar}

{STRUCTURED_SCHEMA}"""

        completion = await self.llm.complete(
            [
                {"role": "system", "content": STRUCTURED_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            json_mode=True,
            label="metar-structured",
        )
        try:
            decoded: dict[str, Any] = json.loads(completion.content)
        except json.JSONDecodeError as error:
            return {"_error": f"invalid JSON: {error}", "_raw": completion.content}
        return decoded
