import httpx
import pytest

from app.traffic.models import StateVector
from app.traffic.regions import REGIONS, UnknownRegionError
from app.traffic.service import AIRCRAFT_TTL_SECONDS, STALE_MAX_SECONDS, TrafficService
from tests.fakes import Clock, FakeAircraft, http_error, plane

pytestmark = pytest.mark.anyio


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def source() -> FakeAircraft:
    return FakeAircraft()


@pytest.fixture
def traffic(source: FakeAircraft, clock: Clock) -> TrafficService:
    return TrafficService(source, clock=clock)


def test_state_vector_parses_opensky_row() -> None:
    row = ["abc", "TAM3456 ", "Brazil", 0, 0, -46.6, -23.5, None, False, 230.0, 90.0, 0, 0, 500.0]
    vector = StateVector.from_opensky(row)
    assert vector.callsign == "TAM3456"
    assert vector.altitude == 500.0
    assert vector.has_position


async def test_unknown_region_raises(traffic: TrafficService) -> None:
    with pytest.raises(UnknownRegionError):
        await traffic.snapshot("mars")


async def test_region_name_is_normalised(traffic: TrafficService, source: FakeAircraft) -> None:
    await traffic.snapshot("  SOUTH_AMERICA ")
    assert source.calls == 1


async def test_fresh_result_is_cached(
    traffic: TrafficService, source: FakeAircraft, clock: Clock
) -> None:
    source.result = [plane()]
    await traffic.snapshot("south_america")
    clock.advance(AIRCRAFT_TTL_SECONDS - 1)
    snapshot = await traffic.snapshot("south_america")
    assert source.calls == 1
    assert snapshot.stale is False


async def test_failure_serves_last_good_result_as_stale(
    traffic: TrafficService, source: FakeAircraft, clock: Clock
) -> None:
    source.result = [plane()]
    await traffic.snapshot("south_america")
    clock.advance(AIRCRAFT_TTL_SECONDS + 1)
    source.result = http_error(503)
    snapshot = await traffic.snapshot("south_america")
    assert snapshot.stale is True
    assert len(snapshot.aircraft) == 1


async def test_failure_without_previous_result_raises(
    traffic: TrafficService, source: FakeAircraft
) -> None:
    source.result = http_error(503)
    with pytest.raises(httpx.HTTPStatusError):
        await traffic.snapshot("south_america")


async def test_rate_limit_backs_off_for_the_advertised_time(
    traffic: TrafficService, source: FakeAircraft, clock: Clock
) -> None:
    source.result = http_error(429, {"X-Rate-Limit-Retry-After-Seconds": "120"})
    with pytest.raises(httpx.HTTPStatusError):
        await traffic.snapshot("south_america")

    clock.advance(119)
    with pytest.raises(httpx.HTTPStatusError):
        await traffic.snapshot("south_america")
    assert source.calls == 1, "must not call OpenSky again during the backoff"

    clock.advance(2)
    source.result = [plane()]
    assert (await traffic.snapshot("south_america")).stale is False
    assert source.calls == 2


async def test_stale_result_expires(
    traffic: TrafficService, source: FakeAircraft, clock: Clock
) -> None:
    source.result = [plane()]
    await traffic.snapshot("south_america")
    clock.advance(STALE_MAX_SECONDS + 1)
    source.result = http_error(503)
    with pytest.raises(httpx.HTTPStatusError):
        await traffic.snapshot("south_america")


async def test_describe_handles_missing_altitude_and_ground(
    traffic: TrafficService, source: FakeAircraft
) -> None:
    source.result = [
        plane(callsign="AAA1", baro=None, geo=None),
        plane(callsign="BBB2", on_ground=True),
        plane(callsign=None, baro=1234.4),
    ]
    text = await traffic.describe("south_america")
    assert "AAA1 altitude unknown" in text
    assert "BBB2 on ground" in text
    assert "unknown at 1234 m" in text
    assert "None" not in text


async def test_describe_mentions_staleness(
    traffic: TrafficService, source: FakeAircraft, clock: Clock
) -> None:
    source.result = [plane()]
    await traffic.snapshot("south_america")
    clock.advance(60)
    source.result = http_error(503)
    assert "temporarily unavailable" in await traffic.describe("south_america")


async def test_one_world_fetch_serves_every_region(
    traffic: TrafficService, source: FakeAircraft
) -> None:
    source.result = [
        plane(icao24="gru", lat=-23.4, lon=-46.5),
        plane(icao24="fra", lat=50.0, lon=8.6),
        plane(icao24="nopos", lat=None, lon=None),
    ]
    south = await traffic.snapshot("south_america")
    europe = await traffic.snapshot("europe")
    world = await traffic.snapshot("world")
    assert [p.icao24 for p in south.aircraft] == ["gru"]
    assert [p.icao24 for p in europe.aircraft] == ["fra"]
    assert len(world.aircraft) == 3
    assert source.calls == 1
    assert source.boxes == [REGIONS["world"]]
