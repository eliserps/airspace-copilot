from evals.agent_eval import score


def test_expected_tool_and_arguments_pass_case_insensitively() -> None:
    expected = {"tool": "get_metar", "arguments": {"icao_code": "SBGR"}}
    assert score(expected, [("get_metar", {"icao_code": "sbgr"})])[0]


def test_wrong_tool_or_argument_fails() -> None:
    expected = {"tool": "count_aircraft", "arguments": {"region": "europe"}}
    assert not score(expected, [("get_metar", {"icao_code": "SBGR"})])[0]
    assert not score(expected, [("count_aircraft", {"region": "asia"})])[0]
    assert not score(expected, [])[0]


def test_no_tool_expected() -> None:
    assert score({"tool": None}, [])[0]
    assert not score({"tool": None}, [("count_aircraft", {"region": "world"})])[0]


def test_near_expectation_accepts_nearby_coordinates_only() -> None:
    expected = {
        "tool": "count_aircraft_near",
        "near": {"latitude": -23.55, "longitude": -46.63, "within_km": 40},
    }
    nearby = {"place": "São Paulo", "latitude": -23.5, "longitude": -46.6}
    far = {"place": "Rio", "latitude": -22.9, "longitude": -43.2}
    assert score(expected, [("count_aircraft_near", nearby)])[0]
    assert not score(expected, [("count_aircraft_near", far)])[0]
    assert not score(expected, [("count_aircraft_near", {"place": "São Paulo"})])[0]
