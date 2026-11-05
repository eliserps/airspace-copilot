import httpx
import pytest

from app.traffic.opensky import (
    MIN_TOKEN_TTL_SECONDS,
    STATES_URL,
    TOKEN_REFRESH_MARGIN_SECONDS,
    TOKEN_URL,
    OpenSkyClient,
    token_ttl,
)
from app.traffic.regions import REGIONS
from tests.fakes import Clock

pytestmark = pytest.mark.anyio

ROW = ["abc", "GLO1 ", "Brazil", 0, 0, -46.6, -23.5, 9000.0, False, 230.0, 90.0, 0, 0, None]


def opensky(handler: httpx.MockTransport) -> OpenSkyClient:
    return OpenSkyClient(httpx.AsyncClient(transport=handler), "id", "secret")


async def test_token_is_reused_between_calls() -> None:
    tokens = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal tokens
        if str(request.url) == TOKEN_URL:
            tokens += 1
            return httpx.Response(200, json={"access_token": f"t{tokens}"})
        return httpx.Response(200, json={"states": [ROW]})

    client = opensky(httpx.MockTransport(handle))
    await client.states(REGIONS["europe"])
    states = await client.states(REGIONS["europe"])
    assert tokens == 1
    assert states[0].callsign == "GLO1"


async def test_rejected_token_is_refreshed_once() -> None:
    issued: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        if str(request.url) == TOKEN_URL:
            issued.append(f"t{len(issued) + 1}")
            return httpx.Response(200, json={"access_token": issued[-1]})
        assert str(request.url).startswith(STATES_URL)
        if request.headers["Authorization"] == "Bearer t1":
            return httpx.Response(401)
        return httpx.Response(200, json={"states": None})

    states = await opensky(httpx.MockTransport(handle)).states(REGIONS["europe"])
    assert issued == ["t1", "t2"]
    assert states == []


async def test_without_credentials_calls_the_api_anonymously() -> None:
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"states": [ROW]})

    client = OpenSkyClient(httpx.AsyncClient(transport=httpx.MockTransport(handle)), None, "")
    states = await client.states(REGIONS["europe"])
    assert client.authenticated is False
    assert [str(r.url).split("?")[0] for r in requests] == [STATES_URL]
    assert "Authorization" not in requests[0].headers
    assert states[0].callsign == "GLO1"


async def test_token_is_renewed_before_the_advertised_expiry() -> None:
    clock = Clock()
    tokens = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal tokens
        if str(request.url) == TOKEN_URL:
            tokens += 1
            return httpx.Response(200, json={"access_token": f"t{tokens}", "expires_in": 300})
        return httpx.Response(200, json={"states": []})

    client = OpenSkyClient(
        httpx.AsyncClient(transport=httpx.MockTransport(handle)), "id", "secret", clock=clock
    )
    await client.states(REGIONS["europe"])
    clock.advance(300 - TOKEN_REFRESH_MARGIN_SECONDS - 1)
    await client.states(REGIONS["europe"])
    assert tokens == 1
    clock.advance(2)
    await client.states(REGIONS["europe"])
    assert tokens == 2


@pytest.mark.parametrize(
    ("expires_in", "ttl"),
    [(1800, 1740), ("600", 540), (None, 1740), ("soon", 1740), (10, MIN_TOKEN_TTL_SECONDS)],
)
def test_token_ttl(expires_in: object, ttl: float) -> None:
    assert token_ttl(expires_in) == ttl
