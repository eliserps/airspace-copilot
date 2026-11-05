import asyncio
import time

import httpx

from app.core.cache import Clock, TimedCache
from app.core.metrics import CACHE_LOOKUPS, UPSTREAM_ERRORS

from .geo import distance_km
from .models import Snapshot, StateVector
from .opensky import AircraftSource
from .regions import REGIONS, RegionId, resolve_region

AIRCRAFT_TTL_SECONDS = 30
STALE_MAX_SECONDS = 600
FAILURE_BACKOFF_SECONDS = 15
RATE_LIMIT_BACKOFF_SECONDS = 60
RATE_LIMIT_BACKOFF_MAX_SECONDS = 3600
WORLD: RegionId = "world"
LISTED_AIRCRAFT = 5


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
        self._failure: tuple[float, Exception] | None = None
        self._lock = asyncio.Lock()

    async def snapshot(self, region: str) -> Snapshot:
        key = resolve_region(region)
        world = await self._world()
        if key == WORLD:
            return world
        box = REGIONS[key]
        aircraft = [p for p in world.aircraft if box.contains(p.latitude, p.longitude)]
        return Snapshot(aircraft, world.fetched_at, world.stale)

    async def _world(self) -> Snapshot:
        async with self._lock:
            now = self.clock()
            cached = self._cache.get(WORLD)

            if cached and now - cached.stored_at < AIRCRAFT_TTL_SECONDS:
                CACHE_LOOKUPS.labels("traffic", "hit").inc()
                return Snapshot(cached.value, cached.stored_at, stale=False)
            CACHE_LOOKUPS.labels("traffic", "miss").inc()

            if self._failure and now < self._failure[0]:
                return self._stale_or_raise(self._failure[1], now)

            try:
                aircraft = await self.source.states(REGIONS[WORLD])
            except httpx.HTTPError as error:
                UPSTREAM_ERRORS.labels("opensky").inc()
                self._failure = (now + backoff_seconds(error), error)
                return self._stale_or_raise(error, now)

            self._failure = None
            entry = self._cache.set(WORLD, aircraft)
            return Snapshot(aircraft, entry.stored_at, stale=False)

    def _stale_or_raise(self, error: Exception, now: float) -> Snapshot:
        cached = self._cache.get(WORLD)
        if cached and now - cached.stored_at < STALE_MAX_SECONDS:
            CACHE_LOOKUPS.labels("traffic", "stale").inc()
            return Snapshot(cached.value, cached.stored_at, stale=True)
        raise error

    async def describe(self, region: str) -> str:
        key = resolve_region(region)
        snapshot = await self.snapshot(key)
        note = self._stale_note(snapshot)

        if not snapshot.aircraft:
            return f"No aircraft detected over {key} right now{note}."
        lines = [f"{len(snapshot.aircraft)} aircraft detected over {key}{note}."]
        for plane in snapshot.aircraft[:LISTED_AIRCRAFT]:
            lines.append(f"- {plane.callsign or 'unknown'} {_where(plane)}")
        return "\n".join(lines)

    async def describe_near(
        self, place: str, latitude: float, longitude: float, radius_km: float
    ) -> str:
        world = await self._world()
        note = self._stale_note(world)
        distances = [
            (distance_km(latitude, longitude, p.latitude, p.longitude), p)
            for p in world.aircraft
            if p.latitude is not None and p.longitude is not None
        ]
        nearby = sorted(((d, p) for d, p in distances if d <= radius_km), key=lambda i: i[0])
        within = f"within {radius_km:.0f} km of {place} ({latitude:.2f}, {longitude:.2f})"

        if not nearby:
            return f"No aircraft detected {within} right now{note}."
        on_ground = sum(1 for _, p in nearby if p.on_ground)
        lines = [
            f"{len(nearby)} aircraft detected {within}{note}: "
            f"{len(nearby) - on_ground} airborne, {on_ground} on ground. Closest:"
        ]
        for distance, plane in nearby[:LISTED_AIRCRAFT]:
            lines.append(f"- {plane.callsign or 'unknown'} {distance:.0f} km away, {_where(plane)}")
        return "\n".join(lines)

    def _stale_note(self, snapshot: Snapshot) -> str:
        if not snapshot.stale:
            return ""
        age = round(self.clock() - snapshot.fetched_at)
        return f" (data from {age} s ago; the live feed is temporarily unavailable)"


def _where(plane: StateVector) -> str:
    if plane.on_ground:
        return "on ground"
    if plane.altitude is None:
        return "altitude unknown"
    return f"at {plane.altitude:.0f} m"
