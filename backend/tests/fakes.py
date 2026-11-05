from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field

import httpx

from app.llm.client import Completion, Message, StreamEvent, TextDelta, ToolCall, ToolSchema
from app.traffic.models import StateVector
from app.traffic.regions import BoundingBox
from app.weather.knowledge import ReferenceDoc


def plane(
    icao24: str = "abc123",
    callsign: str | None = "TAM3456",
    country: str = "Brazil",
    lon: float | None = -46.6,
    lat: float | None = -23.5,
    baro: float | None = 10000.0,
    on_ground: bool = False,
    velocity: float | None = 230.0,
    track: float | None = 90.0,
    geo: float | None = None,
) -> StateVector:
    return StateVector(icao24, callsign, country, lon, lat, baro, on_ground, velocity, track, geo)


def http_error(status: int, headers: dict[str, str] | None = None) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://example.test")
    response = httpx.Response(status, headers=headers, request=request)
    return httpx.HTTPStatusError(f"{status}", request=request, response=response)


class Clock:
    def __init__(self, now: float = 10_000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def reply(text: str) -> Completion:
    return Completion(text)


def call(name: str, arguments: str, call_id: str = "c1") -> Completion:
    return Completion("", [ToolCall(call_id, name, arguments)])


@dataclass
class FakeLLM:
    script: list[Completion | Exception] = field(default_factory=list)
    calls: list[tuple[list[Message], list[ToolSchema] | None]] = field(default_factory=list)
    configured: bool = True

    def _next(self, messages: Sequence[Message], tools: Sequence[ToolSchema] | None) -> Completion:
        self.calls.append(([dict(m) for m in messages], list(tools) if tools else None))
        item = self.script.pop(0) if self.script else Completion("")
        if isinstance(item, Exception):
            raise item
        return item

    async def complete(
        self,
        messages: Sequence[Message],
        *,
        tools: Sequence[ToolSchema] | None = None,
        json_mode: bool = False,
        label: str = "llm",
    ) -> Completion:
        return self._next(messages, tools)

    async def stream(
        self,
        messages: Sequence[Message],
        *,
        tools: Sequence[ToolSchema] | None = None,
        label: str = "llm",
    ) -> AsyncIterator[StreamEvent]:
        completion = self._next(messages, tools)
        for word in completion.content.split(" "):
            if word:
                yield TextDelta(word + " ")
        yield completion


@dataclass
class FakeAircraft:
    result: list[StateVector] | Exception = field(default_factory=list)
    calls: int = 0

    async def states(self, box: BoundingBox) -> list[StateVector]:
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


@dataclass
class FakeMetar:
    reports: dict[str, str | Exception | None] = field(default_factory=dict)

    async def latest(self, icao: str) -> str | None:
        report = self.reports.get(icao.upper())
        if isinstance(report, Exception):
            raise report
        return report


REFERENCE = [ReferenceDoc("metar.md", "## Wind\n...")]
