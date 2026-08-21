"""Deterministic field-by-field evaluation of the METAR decoder.

Runs decode_metar_structured() on every VALIDATED case in the golden dataset and
compares each field against the hand-checked expected value. No model grades
anything here -- comparison is exact equality against ground truth taken from the
METAR specification. That is what makes this pass trustworthy: it cannot inherit
the decoder's mistakes.

Usage:
  python evals/evaluate.py            # score all validated cases
  python evals/evaluate.py --case ID  # score one case
  python evals/evaluate.py --repeat 3 # run each case N times (the decoder is
                                      # non-deterministic; a single green run is
                                      # weak evidence)
"""

import truststore
truststore.inject_into_ssl()

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from config import LLM_MODEL  # noqa: E402
from decoder import decode_metar_structured  # noqa: E402

DATASET_PATH = ROOT / "evals" / "golden_dataset.json"
RESULTS_PATH = ROOT / "evals" / "results.json"

# Compared by exact equality. Order matters for lists, which is correct here:
# cloud layers are reported bottom-up and the sequence is part of the meaning.
SCORED_FIELDS = [
    "station",
    "wind_direction_deg",
    "wind_speed_kt",
    "wind_gust_kt",
    "wind_variable_from_deg",
    "wind_variable_to_deg",
    "visibility_m",
    "cavok",
    "weather",
    "cloud_layers",
    "ceiling_ft",
    "temperature_c",
    "dewpoint_c",
    "qnh_hpa",
]


def normalise(field: str, value):
    """Makes trivially-equivalent representations compare equal.

    Deliberately narrow. It fixes formatting noise (a float 700.0 vs int 700),
    never semantics: null stays distinct from 0, and "700 feet" is not coerced
    into 700 because a decoder emitting that is failing the contract.
    """
    if value is None:
        return None
    if field == "station" and isinstance(value, str):
        return value.strip().upper()
    if field == "cavok":
        return bool(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if field == "weather" and isinstance(value, list):
        return [str(w).strip().upper() for w in value]
    if field == "cloud_layers" and isinstance(value, list):
        layers = []
        for layer in value:
            if not isinstance(layer, dict):
                return value  # malformed: let it fail loudly
            height = layer.get("height_ft")
            if isinstance(height, float) and height.is_integer():
                height = int(height)
            layers.append({
                "cover": str(layer.get("cover", "")).strip().upper(),
                "height_ft": height,
            })
        return layers
    return value


def check_refusal(expected: dict, actual: dict) -> tuple[bool, str]:
    """Scores whether the decoder refused undocumented codes when it should.

    A refusal case passes only if every code the gold answer marks undecodable is
    actually listed. Explaining an undocumented code is a failure EVEN IF the
    explanation is meteorologically correct -- the system prompt says "never
    guess", so an accurate guess still breaks the rule.
    """
    should_refuse = bool(expected.get("expected_refusal"))
    listed = {str(c).strip().upper() for c in (actual.get("undecodable_codes") or [])}

    if not should_refuse:
        # Over-refusal is also a failure: refusing documented codes makes the
        # decoder useless, which is how the n_results=4 retrieval bug showed up.
        if listed:
            return False, f"refused codes that are documented: {sorted(listed)}"
        return True, "no refusal expected, none given"

    required = {str(c).strip().upper() for c in expected.get("undecodable_codes", [])}
    missing = required - listed
    if missing:
        return False, f"failed to flag undocumented codes: {sorted(missing)}"
    return True, f"correctly flagged {sorted(required)}"


def evaluate_case(case: dict) -> dict:
    """Runs the decoder once on a case and scores every field."""
    expected = case["expected"]
    actual = decode_metar_structured(case["metar"])

    result = {
        "id": case["id"],
        "metar": case["metar"],
        "fields": {},
        "error": actual.get("_error"),
        "retrieved_sources": actual.get("_retrieved_sources", []),
    }

    if result["error"]:
        # The decoder produced nothing comparable. Every field fails; that is the
        # honest score, not a crash and not a skip.
        for field in SCORED_FIELDS:
            result["fields"][field] = {
                "pass": False, "expected": expected.get(field), "actual": None,
            }
        result["refusal"] = {"pass": False, "detail": "decoder error"}
        return result

    for field in SCORED_FIELDS:
        want = normalise(field, expected.get(field))
        got = normalise(field, actual.get(field))
        result["fields"][field] = {"pass": want == got, "expected": want, "actual": got}

    ok, detail = check_refusal(expected, actual)
    result["refusal"] = {"pass": ok, "detail": detail}
    return result


def load_validated_cases(dataset: dict, case_id: str | None) -> list[dict]:
    """Returns cases eligible for scoring.

    A case counts only when its expected values were checked by hand. Synthetic
    cases were validated when written; collected ones carry validated=false until
    a human fills them in. Scoring an unvalidated case would compare the decoder
    against a row of nulls and report a meaningless number.
    """
    cases = []
    for case in dataset["cases"]:
        if case_id and case["id"] != case_id:
            continue
        if case.get("validated") is False:
            continue
        if not any(case["expected"].get(f) is not None for f in SCORED_FIELDS):
            continue
        cases.append(case)
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", help="run a single case by id")
    parser.add_argument("--repeat", type=int, default=1,
                        help="runs per case (default 1)")
    parser.add_argument("--dataset", default=str(DATASET_PATH),
                        help="dataset path (used by the self-test)")
    parser.add_argument("--quiet", action="store_true",
                        help="summary only, no per-field detail")
    args = parser.parse_args()

    dataset = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    cases = load_validated_cases(dataset, args.case)

    total_cases = len(dataset["cases"])
    skipped = total_cases - len([c for c in dataset["cases"]
                                 if c.get("validated") is not False])

    if not cases:
        print("No validated cases to score.")
        return 1

    print(f"model:   {LLM_MODEL}")
    print(f"dataset: {Path(args.dataset).name} "
          f"({len(cases)} validated, {total_cases - len(cases)} awaiting validation)")
    print(f"repeat:  {args.repeat}\n")

    runs = []
    field_tally = defaultdict(lambda: {"pass": 0, "total": 0})
    case_tally = defaultdict(lambda: {"pass": 0, "total": 0})

    for case in cases:
        for attempt in range(args.repeat):
            result = evaluate_case(case)
            runs.append(result)

            failures = [f for f, r in result["fields"].items() if not r["pass"]]
            if not result["refusal"]["pass"]:
                failures.append("refusal")

            for field, r in result["fields"].items():
                field_tally[field]["total"] += 1
                field_tally[field]["pass"] += bool(r["pass"])
            field_tally["refusal"]["total"] += 1
            field_tally["refusal"]["pass"] += bool(result["refusal"]["pass"])

            case_tally[case["id"]]["total"] += 1
            case_tally[case["id"]]["pass"] += not failures

            label = f"{case['id']}" + (f" #{attempt + 1}" if args.repeat > 1 else "")
            if failures:
                print(f"  FAIL  {label}")
                if not args.quiet:
                    if result["error"]:
                        print(f"          decoder error: {result['error']}")
                    for field in failures:
                        if field == "refusal":
                            print(f"          refusal: {result['refusal']['detail']}")
                        else:
                            r = result["fields"][field]
                            print(f"          {field}: "
                                  f"expected {r['expected']!r}, got {r['actual']!r}")
            else:
                print(f"  ok    {label}")

    field_checks = sum(t["total"] for t in field_tally.values())
    field_passes = sum(t["pass"] for t in field_tally.values())
    perfect = sum(t["pass"] for t in case_tally.values())
    attempts = sum(t["total"] for t in case_tally.values())

    print("\n--- per field ---")
    for field in SCORED_FIELDS + ["refusal"]:
        t = field_tally[field]
        if not t["total"]:
            continue
        pct = 100 * t["pass"] / t["total"]
        bar = "#" * round(pct / 5)
        print(f"  {field:26} {pct:5.1f}%  {t['pass']}/{t['total']}  {bar}")

    print("\n--- score ---")
    print(f"  fields correct:  {100 * field_passes / field_checks:.1f}% "
          f"({field_passes}/{field_checks})")
    print(f"  perfect runs:    {100 * perfect / attempts:.1f}% ({perfect}/{attempts})")
    if skipped:
        print(f"  NOT SCORED:      {skipped} cases awaiting hand validation")

    report = {
        "run_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "model": LLM_MODEL,
        "repeat": args.repeat,
        "cases_scored": len(cases),
        "cases_awaiting_validation": skipped,
        "field_score": round(100 * field_passes / field_checks, 1),
        "perfect_run_score": round(100 * perfect / attempts, 1),
        "per_field": {f: dict(t) for f, t in field_tally.items()},
        "runs": runs,
    }
    if args.dataset == str(DATASET_PATH):
        RESULTS_PATH.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"\nWrote {RESULTS_PATH.name}")

    return 0 if perfect == attempts else 1


if __name__ == "__main__":
    raise SystemExit(main())
