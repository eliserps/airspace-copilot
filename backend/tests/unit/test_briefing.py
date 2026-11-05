import pytest

from app.briefing.service import (
    BRIEFING_MAX_REUSE_SECONDS,
    BRIEFING_TTL_SECONDS,
    BriefingService,
)
from app.briefing.summary import bucket, format_stats, summarize
from tests.fakes import Clock, FakeLLM, plane, reply

pytestmark = pytest.mark.anyio


def test_summarize_counts_bands_ground_and_airlines() -> None:
    stats = summarize(
        [
            plane(callsign="TAM3456", baro=500.0),
            plane(callsign="GLO1234", baro=5000.0),
            plane(callsign="GLO9", baro=11000.0),
            plane(callsign="PTXYZ", on_ground=True),
            plane(callsign=None, baro=None, geo=None),
        ]
    )
    assert stats.total == 5
    assert stats.on_ground == 1
    assert stats.no_altitude == 1
    assert (stats.below_fl100, stats.fl100_300, stats.above_fl300) == (1, 1, 1)
    assert dict(stats.airlines) == {"GLO": 2, "TAM": 1}
    assert stats.low_flyers_count == 1


def test_empty_traffic_is_stated_plainly() -> None:
    assert format_stats(summarize([])) == "No aircraft detected in this area."


def test_bucket_groups_small_changes() -> None:
    assert bucket(842) == bucket(851)
    assert bucket(842) != bucket(1000)
    assert bucket(0) == 0


async def test_reused_briefing_reports_the_count_it_was_written_from() -> None:
    llm, clock = FakeLLM([reply("text")]), Clock(1000.0)
    service = BriefingService(llm, clock=clock)

    first = await service.generate([plane()] * 100, "europe")
    clock.advance(BRIEFING_TTL_SECONDS + 1)
    second = await service.generate([plane()] * 101, "europe")

    assert len(llm.calls) == 1, "a 1% change must reuse the cached text"
    assert second.aircraft_count == 100
    assert second.generated_at == first.generated_at == 1000.0


async def test_language_is_part_of_the_cache_key() -> None:
    llm = FakeLLM([reply("en"), reply("pt")])
    service = BriefingService(llm)
    assert (await service.generate([], "europe", "en")).text == "en"
    assert (await service.generate([], "europe", "pt")).text == "pt"
    assert "Brazilian Portuguese" in llm.calls[1][0][1]["content"]


async def test_empty_answer_is_not_cached() -> None:
    service = BriefingService(FakeLLM([reply(""), reply("text")]))
    assert (await service.generate([], "europe")).text == ""
    assert (await service.generate([], "europe")).text == "text"


async def test_unchanged_traffic_is_rewritten_after_the_maximum_reuse_age() -> None:
    llm, clock = FakeLLM([reply("old"), reply("new")]), Clock(1000.0)
    service = BriefingService(llm, clock=clock)
    await service.generate([plane()] * 100, "europe")
    clock.advance(BRIEFING_MAX_REUSE_SECONDS + 1)
    assert (await service.generate([plane()] * 100, "europe")).text == "new"


async def test_stale_data_is_flagged_to_the_model_and_not_reused_once_fresh() -> None:
    llm, clock = FakeLLM([reply("stale"), reply("fresh")]), Clock(1000.0)
    service = BriefingService(llm, clock=clock)
    await service.generate([plane()] * 100, "europe", stale=True)
    assert "temporarily unavailable" in llm.calls[0][0][1]["content"]
    clock.advance(BRIEFING_TTL_SECONDS + 1)
    assert (await service.generate([plane()] * 100, "europe")).text == "fresh"
    assert "temporarily unavailable" not in llm.calls[1][0][1]["content"]
