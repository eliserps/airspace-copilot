import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass

from app.core.cache import Clock, KeyedLocks, TimedCache
from app.core.config import LANGUAGE_NAMES, Language
from app.core.metrics import CACHE_LOOKUPS
from app.llm.client import LLMClient
from app.traffic.models import StateVector

from .summary import fingerprint, format_stats, summarize

log = logging.getLogger(__name__)

BRIEFING_TTL_SECONDS = 180

SYSTEM_PROMPT = """You are an airspace analyst assistant.

STRICT RULES:
- Use ONLY the aircraft data provided. Never invent flights, airlines or numbers.
- The data comes from OpenSky, a volunteer-powered ADS-B network with partial
 coverage. It shows DETECTED aircraft, not all aircraft flying. Always make
 this limitation clear.
- If the data is empty, say so plainly. Do not speculate.
- Be concise and factual. No filler.
"""


@dataclass(frozen=True)
class Briefing:
    text: str
    aircraft_count: int
    generated_at: float
    fingerprint: tuple[object, ...]


class BriefingService:
    def __init__(self, llm: LLMClient, clock: Clock = time.time):
        self.llm = llm
        self.clock = clock
        self._cache: TimedCache[tuple[str, Language], Briefing] = TimedCache(clock=clock)
        self._locks: KeyedLocks[tuple[str, Language]] = KeyedLocks()

    async def generate(
        self, aircraft: Sequence[StateVector], region: str, language: Language = "en"
    ) -> Briefing:
        stats = summarize(aircraft)
        key = (region.lower().strip(), language)
        async with self._locks(key):
            now = self.clock()
            cached = self._cache.get(key)
            if cached and now - cached.value.generated_at < BRIEFING_TTL_SECONDS:
                CACHE_LOOKUPS.labels("briefing", "hit").inc()
                return cached.value

            current = fingerprint(stats)
            if cached and cached.value.fingerprint == current:
                log.info("briefing %s unchanged, reusing", key)
                CACHE_LOOKUPS.labels("briefing", "unchanged").inc()
                return cached.value
            CACHE_LOOKUPS.labels("briefing", "miss").inc()

            prompt = f"""Write a short airspace briefing for: {region}
Aggregated data for the aircraft currently detected:
{format_stats(stats)}
Write the briefing in {LANGUAGE_NAMES[language]}. Cover:
1. How many aircraft were detected
2. Which countries/airlines appear most
3. Anything notable (unusually low altitude, aircraft on ground, etc.)
4. A one-line reminder that coverage is partial
Keep it under 150 words."""
            completion = await self.llm.complete(
                [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
                label="briefing",
            )
            briefing = Briefing(completion.content, stats.total, now, current)
            if briefing.text.strip():
                self._cache.set(key, briefing)
            return briefing
