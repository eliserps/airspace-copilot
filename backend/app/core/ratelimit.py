"""In-memory per-client rate limiting for endpoints that spend LLM tokens.

Behind a reverse proxy, run uvicorn with --proxy-headers and --forwarded-allow-ips
set to the proxy address, otherwise every client shares one bucket.
"""

import time
from collections import defaultdict, deque

from fastapi import Request

from .cache import Clock
from .errors import TooManyRequestsError

WINDOW_SECONDS = 60
PRUNE_THRESHOLD = 1024


class RateLimitExceeded(TooManyRequestsError):
    def __init__(self, retry_after: int):
        super().__init__(
            f"Too many requests. Try again in {retry_after} s.", retry_after=retry_after
        )
        self.headers = {"Retry-After": str(retry_after)}


class RateLimiter:
    def __init__(self, name: str, limit: int, clock: Clock = time.monotonic):
        self.name = name
        self.limit = limit
        self.clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def __call__(self, request: Request) -> None:
        if self.limit <= 0:
            return
        client = request.client.host if request.client else "unknown"
        now = self.clock()

        hits = self._hits[client]
        while hits and now - hits[0] >= WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= self.limit:
            raise RateLimitExceeded(int(WINDOW_SECONDS - (now - hits[0])) + 1)
        hits.append(now)
        self._prune(now)

    def reset(self) -> None:
        self._hits.clear()

    def _prune(self, now: float) -> None:
        if len(self._hits) < PRUNE_THRESHOLD:
            return
        for client in [c for c, h in self._hits.items() if not h or now - h[-1] >= WINDOW_SECONDS]:
            del self._hits[client]
