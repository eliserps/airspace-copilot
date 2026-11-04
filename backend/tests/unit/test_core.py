import pytest
from starlette.requests import Request

from app.core.cache import TimedCache
from app.core.config import Settings
from app.core.ratelimit import WINDOW_SECONDS, RateLimiter, RateLimitExceeded
from tests.fakes import Clock


def request_from(host: str) -> Request:
    return Request({"type": "http", "client": (host, 1234), "headers": []})


def test_allows_up_to_limit_then_429() -> None:
    limiter = RateLimiter("t", 2, clock=Clock(1000.0))
    limiter(request_from("1.1.1.1"))
    limiter(request_from("1.1.1.1"))
    with pytest.raises(RateLimitExceeded) as caught:
        limiter(request_from("1.1.1.1"))
    assert caught.value.status_code == 429
    assert caught.value.code == "too_many_requests"
    assert caught.value.headers == {"Retry-After": "61"}


def test_clients_have_separate_buckets() -> None:
    limiter = RateLimiter("t", 1)
    limiter(request_from("1.1.1.1"))
    limiter(request_from("2.2.2.2"))


def test_window_slides() -> None:
    clock = Clock(1000.0)
    limiter = RateLimiter("t", 1, clock=clock)
    limiter(request_from("1.1.1.1"))
    clock.advance(WINDOW_SECONDS)
    limiter(request_from("1.1.1.1"))


def test_zero_disables() -> None:
    limiter = RateLimiter("t", 0)
    for _ in range(100):
        limiter(request_from("1.1.1.1"))


def test_cache_evicts_oldest_when_full() -> None:
    cache: TimedCache[str, int] = TimedCache(max_entries=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    assert cache.get("a") is None
    assert cache.get("c") is not None


def test_cors_origins_accept_a_comma_separated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "https://a.dev/, https://b.dev")
    assert Settings(_env_file=None).cors_origins == ["https://a.dev", "https://b.dev"]
