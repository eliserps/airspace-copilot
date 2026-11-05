import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.copilot.agent import Agent
from app.copilot.tools import build_tools
from app.core.config import configure_tls, get_settings
from app.llm.client import GroqClient
from app.traffic.geo import distance_km
from app.traffic.models import StateVector
from app.traffic.regions import BoundingBox
from app.traffic.service import TrafficService

EVALS_DIR = Path(__file__).resolve().parent
CASES_PATH = EVALS_DIR / "agent_cases.json"
RESULTS_PATH = EVALS_DIR / "agent_results.json"


class NoAircraft:
    authenticated = True

    async def states(self, box: BoundingBox) -> list[StateVector]:
        return []


class NoMetar:
    async def latest(self, icao: str) -> str | None:
        return None


def score(expected: dict[str, Any], calls: list[tuple[str, dict[str, Any]]]) -> tuple[bool, str]:
    want = expected.get("tool")
    if want is None:
        return (not calls, "no tool called" if not calls else f"unexpected call {calls[0]}")
    if not calls:
        return False, "no tool called"
    name, arguments = calls[0]
    if name != want:
        return False, f"called {name} instead of {want}"
    for key, value in expected.get("arguments", {}).items():
        got = str(arguments.get(key, "")).strip().lower()
        if got != str(value).lower():
            return False, f"{key}={arguments.get(key)!r}, expected {value!r}"
    near = expected.get("near")
    if near:
        try:
            off = distance_km(
                float(arguments["latitude"]),
                float(arguments["longitude"]),
                near["latitude"],
                near["longitude"],
            )
        except (KeyError, TypeError, ValueError):
            return False, f"no usable coordinates in {arguments}"
        if off > near["within_km"]:
            return False, f"point is {off:.0f} km from the expected place"
    return True, f"{name}({arguments})"


async def first_calls(agent: Agent, question: str, region: str | None) -> list[tuple[str, Any]]:
    completion = await agent.llm.complete(
        agent.initial_messages(question, region), tools=agent.tools.schemas(), label="agent-eval"
    )
    calls = []
    for call in completion.tool_calls:
        try:
            arguments = json.loads(call.arguments or "{}")
        except json.JSONDecodeError:
            arguments = {"_raw": call.arguments}
        calls.append((call.name, arguments))
    return calls


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score the copilot's first tool decision against agent_cases.json."
    )
    parser.add_argument("--repeat", type=int, default=1, help="runs per case (default 1)")
    args = parser.parse_args()

    settings = get_settings()
    configure_tls(settings)
    llm = GroqClient(settings.groq_api_key, settings.llm_model, settings.llm_timeout_seconds)
    agent = Agent(llm, build_tools(TrafficService(NoAircraft()), NoMetar()))
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))["cases"]

    print(f"model:  {settings.llm_model}\ncases:  {len(cases)} x {args.repeat}\n")
    runs = []
    for case in cases:
        for attempt in range(args.repeat):
            calls = await first_calls(agent, case["question"], case.get("region"))
            ok, detail = score(case["expected"], calls)
            runs.append({"id": case["id"], "attempt": attempt + 1, "pass": ok, "detail": detail})
            print(f"  {'ok  ' if ok else 'FAIL'}  {case['id']}: {detail}")

    passed = sum(r["pass"] for r in runs)
    accuracy = round(100 * passed / len(runs), 1)
    print(f"\ntool selection accuracy: {accuracy}% ({passed}/{len(runs)})")
    RESULTS_PATH.write_text(
        json.dumps(
            {
                "run_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ"),
                "model": settings.llm_model,
                "accuracy": accuracy,
                "runs": runs,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0 if passed == len(runs) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
