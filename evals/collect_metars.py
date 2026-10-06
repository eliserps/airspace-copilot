"""Collects real METARs and appends them to the golden dataset as UNVALIDATED cases.

The `expected` fields are left null on purpose. They must be filled in by hand
against the METAR specification -- never by a model. A dataset validated by the
system it grades inherits that system's errors and then certifies them as correct.

Usage:  python evals/collect_metars.py
"""

import truststore
truststore.inject_into_ssl()

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from weather import get_metar  # noqa: E402

DATASET_PATH = ROOT / "evals" / "golden_dataset.json"

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


def main() -> int:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    existing_metars = {case["metar"] for case in dataset["cases"]}
    collected_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")

    new_cases = []
    for icao in AIRPORTS:
        metar = get_metar(icao)
        if not metar:
            print(f"[skip] {icao}: no report returned")
            continue
        metar = " ".join(metar.split())
        if metar in existing_metars:
            print(f"[skip] {icao}: already in dataset")
            continue

        existing_metars.add(metar)
        new_cases.append({
            "id": f"{icao.lower()}-real-{collected_at[:10]}",
            "metar": metar,
            "synthetic": False,
            "collected_at": collected_at,
            "validated": False,
            "tests": "TODO: state what failure mode this case probes, or drop it.",
            "expected": dict(EMPTY_EXPECTED),
            "notes": "UNVALIDATED. Fill `expected` by hand against the METAR spec, then set validated=true.",
        })
        print(f"[ok]   {icao}: {metar}")

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
    raise SystemExit(main())
