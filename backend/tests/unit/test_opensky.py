import httpx
import pytest

from app.traffic.opensky import STATES_URL, TOKEN_URL, OpenSkyClient
from app.traffic.regions import REGIONS

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
