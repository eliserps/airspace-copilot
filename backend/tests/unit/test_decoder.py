import pytest

from app.weather.decoder import MetarDecoder
from app.weather.knowledge import chunk_markdown
from tests.fakes import FakeKnowledge, FakeLLM, reply

pytestmark = pytest.mark.anyio

METAR = "SBGR 091800Z 19011G21KT 6000 BKN007 22/19 Q1015"


async def test_decoded_report_is_cached_per_language() -> None:
    llm = FakeLLM([reply("decoded en"), reply("decoded pt")])
    decoder = MetarDecoder(llm, FakeKnowledge())
    assert await decoder.decode(METAR, "en") == "decoded en"
    assert await decoder.decode(METAR, "en") == "decoded en"
    assert await decoder.decode(METAR, "pt") == "decoded pt"
    assert len(llm.calls) == 2


async def test_prompt_includes_retrieved_documentation() -> None:
    llm = FakeLLM([reply("x")])
    await MetarDecoder(llm, FakeKnowledge()).decode(METAR)
    assert "[source: metar.md]" in llm.calls[0][0][1]["content"]


async def test_structured_decode_reports_invalid_json() -> None:
    decoder = MetarDecoder(FakeLLM([reply("not json")]), FakeKnowledge())
    result = await decoder.decode_structured(METAR)
    assert result["_error"].startswith("invalid JSON")
    assert result["_retrieved_sources"] == ["metar.md"]


async def test_structured_decode_returns_fields() -> None:
    decoder = MetarDecoder(FakeLLM([reply('{"station": "SBGR"}')]), FakeKnowledge())
    assert (await decoder.decode_structured(METAR))["station"] == "SBGR"


def test_markdown_is_chunked_by_section() -> None:
    assert chunk_markdown("# Title\n## Wind\nA\n## Clouds\nB") == [
        "# Title",
        "Wind\nA",
        "Clouds\nB",
    ]
