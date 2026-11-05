import asyncio

import pytest

from app.weather.decoder import MetarDecoder
from tests.fakes import REFERENCE, FakeLLM, reply

pytestmark = pytest.mark.anyio

METAR = "SBGR 091800Z 19011G21KT 6000 BKN007 22/19 Q1015"


async def test_decoded_report_is_cached_per_language() -> None:
    llm = FakeLLM([reply("decoded en"), reply("decoded pt")])
    decoder = MetarDecoder(llm, REFERENCE)
    assert await decoder.decode(METAR, "en") == "decoded en"
    assert await decoder.decode(METAR, "en") == "decoded en"
    assert await decoder.decode(METAR, "pt") == "decoded pt"
    assert len(llm.calls) == 2


async def test_prompt_includes_the_reference_documentation() -> None:
    llm = FakeLLM([reply("x")])
    await MetarDecoder(llm, REFERENCE).decode(METAR)
    assert "[source: metar.md]" in llm.calls[0][0][1]["content"]


async def test_structured_decode_reports_invalid_json() -> None:
    decoder = MetarDecoder(FakeLLM([reply("not json")]), REFERENCE)
    result = await decoder.decode_structured(METAR)
    assert result["_error"].startswith("invalid JSON")


async def test_structured_decode_returns_fields() -> None:
    decoder = MetarDecoder(FakeLLM([reply('{"station": "SBGR"}')]), REFERENCE)
    assert (await decoder.decode_structured(METAR))["station"] == "SBGR"


async def test_concurrent_requests_for_the_same_report_share_one_llm_call() -> None:
    llm = FakeLLM([reply("decoded")])
    decoder = MetarDecoder(llm, REFERENCE)
    results = await asyncio.gather(*(decoder.decode(METAR) for _ in range(3)))
    assert results == ["decoded"] * 3
    assert len(llm.calls) == 1


async def test_a_failed_decode_is_shared_then_retried() -> None:
    llm = FakeLLM([RuntimeError("model down"), reply("decoded")])
    decoder = MetarDecoder(llm, REFERENCE)
    results = await asyncio.gather(
        decoder.decode(METAR), decoder.decode(METAR), return_exceptions=True
    )
    assert all(isinstance(r, RuntimeError) for r in results)
    assert await decoder.decode(METAR) == "decoded"
    assert len(llm.calls) == 2
