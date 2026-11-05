import asyncio
import logging
import time
from typing import Protocol

import httpx

from app.core.cache import Clock

from .models import StateVector
from .regions import BoundingBox

TOKEN_URL = (
    "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
)
STATES_URL = "https://opensky-network.org/api/states/all"
DEFAULT_TOKEN_TTL_SECONDS = 1800
TOKEN_REFRESH_MARGIN_SECONDS = 60
MIN_TOKEN_TTL_SECONDS = 30

log = logging.getLogger(__name__)


class AircraftSource(Protocol):
    @property
    def authenticated(self) -> bool: ...

    async def states(self, box: BoundingBox) -> list[StateVector]: ...


def token_ttl(expires_in: object) -> float:
    try:
        seconds = float(str(expires_in))
    except ValueError:
        seconds = DEFAULT_TOKEN_TTL_SECONDS
    return max(seconds - TOKEN_REFRESH_MARGIN_SECONDS, MIN_TOKEN_TTL_SECONDS)


class OpenSkyClient:
    def __init__(
        self,
        http: httpx.AsyncClient,
        client_id: str | None,
        client_secret: str | None,
        clock: Clock = time.time,
    ):
        self.http = http
        self.client_id = client_id
        self.client_secret = client_secret
        self.clock = clock
        self._token: str | None = None
        self._expires_at = 0.0
        self._lock = asyncio.Lock()
        if not self.authenticated:
            log.warning("OpenSky credentials not set; using anonymous access (lower daily quota)")

    @property
    def authenticated(self) -> bool:
        return bool(self.client_id and self.client_secret)

    async def states(self, box: BoundingBox) -> list[StateVector]:
        if not self.authenticated:
            return await self._fetch(None, box)
        token = await self._valid_token()
        try:
            return await self._fetch(token, box)
        except httpx.HTTPStatusError as error:
            if error.response.status_code != 401:
                raise
            await self._invalidate(token)
            return await self._fetch(await self._valid_token(), box)

    async def _fetch(self, token: str | None, box: BoundingBox) -> list[StateVector]:
        response = await self.http.get(
            STATES_URL,
            headers={"Authorization": f"Bearer {token}"} if token else {},
            params={
                "lamin": box.lat_min,
                "lamax": box.lat_max,
                "lomin": box.lon_min,
                "lomax": box.lon_max,
            },
        )
        response.raise_for_status()
        return [StateVector.from_opensky(row) for row in response.json()["states"] or []]

    async def _valid_token(self) -> str:
        async with self._lock:
            now = self.clock()
            if self._token is None or now >= self._expires_at:
                self._token, ttl = await self._request_token()
                self._expires_at = now + ttl
            return self._token

    async def _invalidate(self, rejected: str) -> None:
        async with self._lock:
            if self._token == rejected:
                self._token = None

    async def _request_token(self) -> tuple[str, float]:
        response = await self.http.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id or "",
                "client_secret": self.client_secret or "",
            },
        )
        response.raise_for_status()
        body = response.json()
        token: str = body["access_token"]
        return token, token_ttl(body.get("expires_in"))
