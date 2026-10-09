from src import briefing
from conftest import state_vector


def test_summarize_counts_bands_ground_and_airlines():
    stats = briefing.summarize_aircraft([
        state_vector(callsign="TAM3456", baro=500.0),
        state_vector(callsign="GLO1234", baro=5000.0),
        state_vector(callsign="GLO9", baro=11000.0),
        state_vector(callsign="PTXYZ", on_ground=True),
        state_vector(callsign="", baro=None, geo=None),
    ])
    assert stats["total"] == 5
    assert stats["on_ground"] == 1
    assert stats["no_altitude"] == 1
    assert stats["bands"] == {"below_fl100": 1, "fl100_300": 1, "above_fl300": 1}
    assert dict(stats["airlines"]) == {"GLO": 2, "TAM": 1}
    assert stats["low_flyers_count"] == 1


def test_bucket_groups_small_changes():
    assert briefing._bucket(842) == briefing._bucket(851)
    assert briefing._bucket(842) != briefing._bucket(1000)
    assert briefing._bucket(0) == 0


def test_reused_briefing_reports_the_count_it_was_written_from(monkeypatch):
    calls = []
    monkeypatch.setattr(briefing, "ask", lambda *a, **k: calls.append(1) or "text")
    now = [1000.0]
    monkeypatch.setattr(briefing.time, "time", lambda: now[0])

    first = briefing.generate_briefing_with_meta([state_vector()] * 100, "europe")
    now[0] += briefing.BRIEFING_TTL_SECONDS + 1
    second = briefing.generate_briefing_with_meta([state_vector()] * 101, "europe")

    assert len(calls) == 1, "a 1% change must reuse the cached text"
    assert second["aircraft_count"] == 100
    assert second["generated_at"] == first["generated_at"] == 1000.0


def test_empty_answer_is_not_cached(monkeypatch):
    answers = iter(["", "text"])
    monkeypatch.setattr(briefing, "ask", lambda *a, **k: next(answers))
    assert briefing.generate_briefing([], "europe") == ""
    assert briefing.generate_briefing([], "europe") == "text"
