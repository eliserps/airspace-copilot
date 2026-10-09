import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.ratelimit import ask_limiter, weather_limiter
from src import briefing, decoder, tools


def state_vector(
    icao24="abc123",
    callsign="TAM3456 ",
    country="Brazil",
    lon=-46.6,
    lat=-23.5,
    baro=10000.0,
    on_ground=False,
    velocity=230.0,
    track=90.0,
    geo=None,
):
    vector = [None] * 17
    vector[0], vector[1], vector[2] = icao24, callsign, country
    vector[5], vector[6], vector[7] = lon, lat, baro
    vector[8], vector[9], vector[10] = on_ground, velocity, track
    vector[13] = geo
    return vector


@pytest.fixture(autouse=True)
def clean_state():
    tools._aircraft_cache.clear()
    tools._failures.clear()
    briefing._briefings.clear()
    decoder._decoded_cache.clear()
    ask_limiter._hits.clear()
    weather_limiter._hits.clear()
    yield


@pytest.fixture
def client():
    return TestClient(app)
