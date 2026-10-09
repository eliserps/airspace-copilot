"""Per-client rate limiting for endpoints that spend LLM tokens.

A sliding window held in memory: like the other caches it resets on restart and
is not shared between processes, which is acceptable for a single instance. It
bounds what one client can spend; it is not a defence against a distributed
attack -- the provider-side quota is the backstop for that.

Behind a reverse proxy (Render, Fly, nginx) every request arrives from the
proxy's address, so WITHOUT --proxy-headers all users share one bucket. Run
uvicorn with --proxy-headers and set --forwarded-allow-ips to the proxy's
address. "*" is only safe when the app port is reachable solely through the
proxy: otherwise any client can send its own X-Forwarded-For and pick a fresh
bucket on every request.
"""

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from src.config import ASK_RATE_LIMIT_PER_MINUTE, WEATHER_RATE_LIMIT_PER_MINUTE

from .errors import error_detail

WINDOW_SECONDS = 60


class RateLimiter:
    """Allows at most `limit` requests per client within a rolling minute."""

    def __init__(self, name: str, limit: int):
        self.name = name
        self.limit = limit
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def __call__(self, request: Request) -> None:
        """FastAPI dependency: raises 429 when the client is over its limit."""
        if self.limit <= 0:
            return
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()

        with self._lock:
            hits = self._hits[client]
            while hits and now - hits[0] >= WINDOW_SECONDS:
                hits.popleft()
            if len(hits) >= self.limit:
                retry_after = int(WINDOW_SECONDS - (now - hits[0])) + 1
                raise HTTPException(
                    status_code=429,
                    detail=error_detail(
                        "too_many_requests",
                        f"Too many requests. Try again in {retry_after} s.",
                        retry_after=retry_after,
                    ),
                    headers={"Retry-After": str(retry_after)},
                )
            hits.append(now)
            self._prune(now)

    def _prune(self, now: float) -> None:
        """Forgets idle clients so the table does not grow without bound."""
        if len(self._hits) < 1024:
            return
        for client in [c for c, h in self._hits.items()
                       if not h or now - h[-1] >= WINDOW_SECONDS]:
            del self._hits[client]


ask_limiter = RateLimiter("ask", ASK_RATE_LIMIT_PER_MINUTE)
weather_limiter = RateLimiter("weather", WEATHER_RATE_LIMIT_PER_MINUTE)
