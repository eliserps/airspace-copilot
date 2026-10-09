import requests

from api.routers import aircraft as aircraft_router
from api.routers import agent as agent_router
from api.routers import briefing as briefing_router
from api.routers import weather as weather_router
from conftest import state_vector


def test_unknown_route_uses_flat_error_shape(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {"error": "not_found", "message": "Not Found"}


def test_wrong_method_uses_flat_error_shape(client):
    response = client.delete("/health")
    assert response.status_code == 405
    assert response.json()["error"] == "method_not_allowed"


def test_validation_error_is_flattened(client):
    response = client.post("/ask", json={"question": ""})
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "invalid_request"
    assert body["field"] == "question"


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert "south_america" in body["regions"]


def test_weather_rejects_malformed_icao(client):
    response = client.get("/weather/SB,G")
    assert response.status_code == 422
    assert response.json()["field"] == "icao"


def test_weather_404_when_station_has_no_report(client, monkeypatch):
    monkeypatch.setattr(weather_router, "fetch_metar", lambda code: None)
    response = client.get("/weather/ZZZZ")
    assert response.status_code == 404
    assert response.json()["error"] == "no_metar"


def test_weather_503_when_source_is_down(client, monkeypatch):
    def down(code):
        raise requests.ConnectionError("unreachable")

    monkeypatch.setattr(weather_router, "fetch_metar", down)
    response = client.get("/weather/SBGR")
    assert response.status_code == 503
    assert response.json()["error"] == "upstream_unavailable"


def test_aircraft_map_reports_staleness(client, monkeypatch):
    snapshot = {"aircraft": [state_vector()], "fetched_at": 1000.0, "stale": True}
    monkeypatch.setattr(aircraft_router, "get_region_snapshot", lambda region: snapshot)
    body = client.get("/aircraft/map?region=EUROPE").json()
    assert body["region"] == "europe"
    assert body["stale"] is True
    assert body["fetched_at"] == 1000.0
    assert body["count"] == 1


def test_briefing_count_comes_from_the_text_snapshot(client, monkeypatch):
    monkeypatch.setattr(briefing_router, "get_aircraft_for_region", lambda region: [])
    monkeypatch.setattr(
        briefing_router,
        "generate_briefing_with_meta",
        lambda aircraft, region, lang: {"text": "x", "aircraft_count": 42, "generated_at": 5.0},
    )
    body = client.get("/briefing?region=europe&lang=pt").json()
    assert body["aircraft_count"] == 42
    assert body["generated_at"] == 5.0


def test_ask_passes_region_to_agent(client, monkeypatch):
    seen = {}

    def fake_agent(question, region=None):
        seen["region"] = region
        return "answer"

    monkeypatch.setattr(agent_router, "run_agent", fake_agent)
    response = client.post("/ask", json={"question": "how many here?", "region": "Europe"})
    assert response.status_code == 200
    assert seen["region"] == "europe"


def test_ask_rejects_unknown_region(client):
    response = client.post("/ask", json={"question": "hi", "region": "mars"})
    assert response.status_code == 422
    assert response.json()["field"] == "region"


def test_llm_not_configured_is_503(client, monkeypatch):
    from src.llm import LLMNotConfigured

    def no_key(question, region=None):
        raise LLMNotConfigured("GROQ_API_KEY is not set.")

    monkeypatch.setattr(agent_router, "run_agent", no_key)
    response = client.post("/ask", json={"question": "hi"})
    assert response.status_code == 503
    assert response.json()["error"] == "llm_unavailable"
