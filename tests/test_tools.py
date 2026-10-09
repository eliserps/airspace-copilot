import pytest
import requests

from src import tools
from conftest import state_vector


def http_error(status, headers=None):
    response = requests.Response()
    response.status_code = status
    response.headers.update(headers or {})
    return requests.HTTPError(response=response)


@pytest.fixture
def clock(monkeypatch):
    now = [10_000.0]
    monkeypatch.setattr(tools.time, "time", lambda: now[0])
    return now


@pytest.fixture
def upstream(monkeypatch):
    class Upstream:
        calls = 0
        result: object = []

    def fetch(*bbox):
        Upstream.calls += 1
        if isinstance(Upstream.result, Exception):
            raise Upstream.result
        return Upstream.result

    monkeypatch.setattr(tools, "_get_aircraft_authenticated", fetch)
    return Upstream


def test_plot_drops_positionless_and_falls_back_to_geo_altitude():
    planes = tools.plot_aircraft([
        state_vector(icao24="a", baro=None, geo=500.0),
        state_vector(icao24="b", lat=None),
    ])
    assert [p["icao24"] for p in planes] == ["a"]
    assert planes[0]["altitude_m"] == 500.0
    assert planes[0]["callsign"] == "TAM3456"


def test_unknown_region_raises_keyerror():
    with pytest.raises(KeyError):
        tools.get_region_snapshot("mars")


def test_fresh_result_is_cached(clock, upstream):
    upstream.result = [state_vector()]
    tools.get_region_snapshot("europe")
    clock[0] += tools.AIRCRAFT_TTL_SECONDS - 1
    snapshot = tools.get_region_snapshot("europe")
    assert upstream.calls == 1
    assert snapshot["stale"] is False


def test_failure_serves_last_good_result_as_stale(clock, upstream):
    upstream.result = [state_vector()]
    tools.get_region_snapshot("europe")

    clock[0] += tools.AIRCRAFT_TTL_SECONDS + 1
    upstream.result = http_error(503)
    snapshot = tools.get_region_snapshot("europe")

    assert snapshot["stale"] is True
    assert len(snapshot["aircraft"]) == 1


def test_failure_without_previous_result_raises(upstream):
    upstream.result = http_error(503)
    with pytest.raises(requests.HTTPError):
        tools.get_region_snapshot("europe")


def test_rate_limit_backs_off_for_the_advertised_time(clock, upstream):
    upstream.result = http_error(429, {"X-Rate-Limit-Retry-After-Seconds": "120"})
    with pytest.raises(requests.HTTPError):
        tools.get_region_snapshot("europe")

    clock[0] += 119
    with pytest.raises(requests.HTTPError):
        tools.get_region_snapshot("europe")
    assert upstream.calls == 1, "must not call OpenSky again during the backoff"

    clock[0] += 2
    upstream.result = [state_vector()]
    assert tools.get_region_snapshot("europe")["stale"] is False
    assert upstream.calls == 2


def test_stale_result_expires(clock, upstream):
    upstream.result = [state_vector()]
    tools.get_region_snapshot("europe")
    clock[0] += tools.STALE_MAX_SECONDS + 1
    upstream.result = http_error(503)
    with pytest.raises(requests.HTTPError):
        tools.get_region_snapshot("europe")


def test_count_aircraft_handles_missing_altitude_and_ground(upstream):
    upstream.result = [
        state_vector(callsign="AAA1", baro=None, geo=None),
        state_vector(callsign="BBB2", on_ground=True),
        state_vector(callsign=None, baro=1234.4),
    ]
    text = tools.count_aircraft("europe")
    assert "AAA1 altitude unknown" in text
    assert "BBB2 on ground" in text
    assert "unknown at 1234 m" in text
    assert "None" not in text


def test_count_aircraft_mentions_staleness(clock, upstream):
    upstream.result = [state_vector()]
    tools.get_region_snapshot("europe")
    clock[0] += 60
    upstream.result = http_error(503)
    assert "temporarily unavailable" in tools.count_aircraft("europe")
