import pytest
from fastapi import HTTPException

from api import ratelimit
from api.ratelimit import RateLimiter


class FakeRequest:
    def __init__(self, host):
        self.client = type("Client", (), {"host": host})()


def test_allows_up_to_limit_then_429(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(ratelimit.time, "monotonic", lambda: now[0])
    limiter = RateLimiter("t", 2)

    limiter(FakeRequest("1.1.1.1"))
    limiter(FakeRequest("1.1.1.1"))
    with pytest.raises(HTTPException) as caught:
        limiter(FakeRequest("1.1.1.1"))

    assert caught.value.status_code == 429
    assert caught.value.detail["error"] == "too_many_requests"
    assert caught.value.headers["Retry-After"] == "61"


def test_clients_have_separate_buckets():
    limiter = RateLimiter("t", 1)
    limiter(FakeRequest("1.1.1.1"))
    limiter(FakeRequest("2.2.2.2"))


def test_window_slides(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(ratelimit.time, "monotonic", lambda: now[0])
    limiter = RateLimiter("t", 1)

    limiter(FakeRequest("1.1.1.1"))
    now[0] += ratelimit.WINDOW_SECONDS
    limiter(FakeRequest("1.1.1.1"))


def test_zero_disables():
    limiter = RateLimiter("t", 0)
    for _ in range(100):
        limiter(FakeRequest("1.1.1.1"))
