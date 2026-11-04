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
