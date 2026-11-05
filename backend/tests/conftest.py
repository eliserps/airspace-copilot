from collections.abc import Iterator
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from app.container import Services, wire
from app.core.config import Settings
from app.main import create_app
from tests.fakes import REFERENCE, FakeAircraft, FakeLLM, FakeMetar


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@dataclass
class Fakes:
    llm: FakeLLM
    aircraft: FakeAircraft
    metar: FakeMetar
    services: Services


@pytest.fixture
def fakes() -> Fakes:
    llm, aircraft, metar = FakeLLM(), FakeAircraft(), FakeMetar()
    settings = Settings(_env_file=None, ask_rate_limit_per_minute=100)
    services = wire(settings, llm=llm, aircraft=aircraft, metar=metar, reference=REFERENCE)
    return Fakes(llm, aircraft, metar, services)


@pytest.fixture
def client(fakes: Fakes) -> Iterator[TestClient]:
    app = create_app(Settings(_env_file=None), services=fakes.services)
    with TestClient(app) as test_client:
        yield test_client
