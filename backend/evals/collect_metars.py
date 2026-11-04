"""Appends real METARs to the golden dataset as unvalidated cases.

Fill `expected` by hand against the METAR spec, then set validated=true.

Usage (from backend/): python -m evals.collect_metars
"""

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.core.config import configure_tls, get_settings
from app.weather.metar import AviationWeatherClient

DATASET_PATH = Path(__file__).resolve().parent / "golden_dataset.json"

AIRPORTS = [
    "SBGR",
    "SBGL",
    "SBPA",
    "SBBR",
    "SBCF",
    "SBSP",
    "SBCT",
    "SBRF",
    "SBSV",
    "SBFL",
    "SBBE",
    "SBMN",
    "SBKP",
    "SBGO",
    "SBFZ",
]

EMPTY_EXPECTED = {
    "station": None,
    "wind_direction_deg": None,
    "wind_speed_kt": None,
    "wind_gust_kt": None,
    "wind_variable_from_deg": None,
    "wind_variable_to_deg": None,
    "visibility_m": None,
    "cavok": None,
    "weather": None,
    "cloud_layers": None,
    "ceiling_ft": None,
    "temperature_c": None,
    "dewpoint_c": None,
    "qnh_hpa": None,
    "expected_refusal": None,
}


async def collect(
    source: AviationWeatherClient, existing_metars: set[str], collected_at: str
) -> list[dict]:
    new_cases: list[dict] = []
    for icao in AIRPORTS:
        try:
            metar = await source.latest(icao)
        except httpx.HTTPError as error:
            print(f"[skip] {icao}: {error}")
            continue
        if not metar:
            print(f"[skip] {icao}: no report returned")
            continue
        metar = " ".join(metar.split())
        if metar in existing_metars:
            print(f"[skip] {icao}: already in dataset")
            continue

        existing_metars.add(metar)
        new_cases.append(
            {
                "id": f"{icao.lower()}-real-{collected_at[:10]}",
                "metar": metar,
                "synthetic": False,
                "collected_at": collected_at,
                "validated": False,
                "tests": "TODO: state what failure mode this case probes, or drop it.",
                "expected": dict(EMPTY_EXPECTED),
                "notes": "UNVALIDATED. Fill `expected` by hand against the METAR spec, "
                "then set validated=true.",
            }
        )
        print(f"[ok]   {icao}: {metar}")
    return new_cases


async def main() -> int:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    existing_metars = {case["metar"] for case in dataset["cases"]}
    collected_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ")

    configure_tls(get_settings())
    async with httpx.AsyncClient(timeout=10) as http:
        new_cases = await collect(AviationWeatherClient(http), existing_metars, collected_at)

    if not new_cases:
        print("\nNothing new collected.")
        return 0

    dataset["cases"].extend(new_cases)
    DATASET_PATH.write_text(
        json.dumps(dataset, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"\nAdded {len(new_cases)} unvalidated cases to {DATASET_PATH.name}.")
    print("They are EXCLUDED from scoring until you set validated=true on each.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
