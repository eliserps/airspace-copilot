import time

import httpx

from app.core.cache import Clock, KeyedLocks, TimedCache
from app.core.metrics import CACHE_LOOKUPS, UPSTREAM_ERRORS

from .models import Snapshot, StateVector
from .opensky import AircraftSource
from .regions import REGIONS, RegionId, resolve_region

AIRCRAFT_TTL_SECONDS = 30
STALE_MAX_SECONDS = 600
FAILURE_BACKOFF_SECONDS = 15
RATE_LIMIT_BACKOFF_SECONDS = 60
RATE_LIMIT_BACKOFF_MAX_SECONDS = 3600


def backoff_seconds(error: Exception) -> float:
    if not isinstance(error, httpx.HTTPStatusError) or error.response.status_code != 429:
        return FAILURE_BACKOFF_SECONDS
    try:
        retry_after = float(error.response.headers.get("X-Rate-Limit-Retry-After-Seconds", ""))
    except ValueError:
        return RATE_LIMIT_BACKOFF_SECONDS
    return min(max(retry_after, FAILURE_BACKOFF_SECONDS), RATE_LIMIT_BACKOFF_MAX_SECONDS)


class TrafficService:
    def __init__(self, source: AircraftSource, clock: Clock = time.time):
        self.source = source
        self.clock = clock
        self._cache: TimedCache[RegionId, list[StateVector]] = TimedCache(clock=clock)
        self._failures: dict[RegionId, tuple[float, Exception]] = {}
        self._locks: KeyedLocks[RegionId] = KeyedLocks()

    async def snapshot(self, region: str) -> Snapshot:
        key = resolve_region(region)
        async with self._locks(key):
            now = self.clock()
            cached = self._cache.get(key)

            if cached and now - cached.stored_at < AIRCRAFT_TTL_SECONDS:
                CACHE_LOOKUPS.labels("traffic", "hit").inc()
                return Snapshot(cached.value, cached.stored_at, stale=False)
            CACHE_LOOKUPS.labels("traffic", "miss").inc()

            failure = self._failures.get(key)
            if failure and now < failure[0]:
                return self._stale_or_raise(key, failure[1], now)

            try:
                aircraft = await self.source.states(REGIONS[key])
            except httpx.HTTPError as error:
                UPSTREAM_ERRORS.labels("opensky").inc()
                self._failures[key] = (now + backoff_seconds(error), error)
                return self._stale_or_raise(key, error, now)

            self._failures.pop(key, None)
            entry = self._cache.set(key, aircraft)
            return Snapshot(aircraft, entry.stored_at, stale=False)

    def _stale_or_raise(self, key: RegionId, error: Exception, now: float) -> Snapshot:
        cached = self._cache.get(key)
        if cached and now - cached.stored_at < STALE_MAX_SECONDS:
            CACHE_LOOKUPS.labels("traffic", "stale").inc()
            return Snapshot(cached.value, cached.stored_at, stale=True)
        raise error

    async def describe(self, region: str) -> str:
        key = resolve_region(region)
        snapshot = await self.snapshot(key)
        note = ""
        if snapshot.stale:
            age = round(self.clock() - snapshot.fetched_at)
            note = f" (data from {age} s ago; the live feed is temporarily unavailable)"

        if not snapshot.aircraft:
            return f"No aircraft detected over {key} right now{note}."
        lines = [f"{len(snapshot.aircraft)} aircraft detected over {key}{note}."]
        for plane in snapshot.aircraft[:5]:
            altitude = plane.altitude
            if plane.on_ground:
                where = "on ground"
            elif altitude is None:
                where = "altitude unknown"
            else:
                where = f"at {altitude:.0f} m"
            lines.append(f"- {plane.callsign or 'unknown'} {where}")
        return "\n".join(lines)
