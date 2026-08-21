# Evaluation

The decoder is non-deterministic and makes silent factual errors. Real example:
the METAR field `140V200` (wind direction varying 140°–200°) was decoded three
different wrong ways across three runs — "gusts to 200°", "visibility 1400–2000m",
"visibility 140–200m" — each stated confidently.

Inspecting answers by hand does not scale and does not catch this. Hence evaluation.

## The golden dataset

`golden_dataset.json` holds real and synthetic METARs paired with their verified
correct decoding.

**Ground truth comes from the ICAO/FAA METAR specification, never from a language
model.** A model cannot be its own ground truth: an evaluator built from the same
knowledge as the system inherits the system's errors and then certifies them as
correct. Asked to grade `140V200`, the model would likely have written "visibility
1400–2000m" into the answer key — and the eval would have passed the exact bug it
exists to catch.

Hallucinations are systematic, not random. Two model runs agreeing tells you they
share a prior, not that they are right.

### Size, honestly

Hand-built means small: tens of cases, not thousands. The defence is deliberate
coverage over volume — every case names the failure mode it probes in its `tests`
field. A case that cannot say what it tests does not earn its slot.

### `synthetic`

`true` means the METAR was constructed to exercise a specific failure mode (low
ceiling, thunderstorm, undocumented codes) rather than observed live. Synthetic
cases are valid METAR syntax and meteorologically coherent, but they are not real
observations, and the flag says so rather than blurring the claim. Real METARs are
collected via `src/weather.py`.

## Field contract

The eval compares field by field, so the dataset defines the shape the decoder must
emit. Units are baked into the field names deliberately — `visibility_m`,
`height_ft`, `wind_speed_kt` — because unit errors are exactly what the
deterministic pass exists to catch.

| Field | Type | Notes |
|---|---|---|
| `station` | string | ICAO code |
| `wind_direction_deg` | int \| null | `null` when VRB or calm |
| `wind_speed_kt` | int | knots |
| `wind_gust_kt` | int \| null | `null` = no gust reported |
| `wind_variable_from_deg` | int \| null | the `140V200` group |
| `wind_variable_to_deg` | int \| null | |
| `visibility_m` | int \| null | **metres**; `9999` stays `9999` |
| `cavok` | bool | |
| `weather` | string[] | raw codes, e.g. `["-RA", "BR"]` |
| `cloud_layers` | object[] | `{"cover": "BKN", "height_ft": 700}` |
| `ceiling_ft` | int \| null | **derived**, see below |
| `temperature_c` | int | negatives as `-3`, not `"M03"` |
| `dewpoint_c` | int | |
| `qnh_hpa` | int \| null | |
| `expected_refusal` | bool | correct answer is "I cannot decode this" |
| `undecodable_codes` | string[] | present only when `expected_refusal` is true |

### Three decisions worth remembering

**`cloud_layers` stores feet, not the raw code.** `BKN007` means 700 feet. Storing
`"007"` would let "7 feet" or "700 metres" pass. Storing `700` leaves the unit error
nowhere to hide. Choosing the unit is a test decision, not a formatting one.

**`ceiling_ft` is derived, not read.** The ceiling is not written in the METAR — it
is the lowest `BKN` or `OVC` layer (`knowledge/metar_reference.md:31`). In
`FEW015 BKN030` the ceiling is 3000, not 1500, despite FEW being lower. This tests
reasoning rather than lookup.

**`wind_gust_kt` is `null`, never `0`.** `null` means absent; `0` would mean present
and equal to zero. Collapsing them would make "correctly saw no gust" and
"hallucinated a 0 kt gust" indistinguishable — two different claims about the world.

## Running it

```
python evals/collect_metars.py       # append real METARs as unvalidated cases
python evals/evaluate.py             # score validated cases, write results.json
python evals/evaluate.py --repeat 3  # 3 runs per case
python evals/evaluate.py --case ID   # one case
```

Exit code is 0 only when every run is perfect, so this drops into CI unchanged.

**Use `--repeat`.** The decoder is non-deterministic, so a single green run is weak
evidence. The over-refusal bug below was invisible at `--repeat 1` and showed up
2-of-3 at `--repeat 3`.

Unvalidated cases are excluded from scoring and counted separately in the output.
Scoring a case whose `expected` is still a row of nulls would produce a number that
means nothing.

## How the decoder was changed

`decode_metar()` returned free prose, which cannot be compared field by field. Two
options were on the table:

- **A** — extract fields from the prose with regex or a second LLM. Rejected: the
  extractor can fail too, so a bad score would not say whether the decoder or the
  extractor was wrong. That is noise between the system and the ruler.
- **B** — return structured JSON with the prose summary as one field.

**B was implemented**, on the principle that if you want to measure something, make
the system emit it rather than infer it afterwards. Concretely:

- `llm.ask()` gained an optional `json_mode` flag (provider-level JSON constraint).
  Existing callers are unaffected.
- `decoder.decode_metar_structured()` is **new**, alongside the original
  `decode_metar()`, which still returns prose for `main.py`. Nothing that worked
  before was broken.
- Its return value carries `_retrieved_sources`, so a wrong answer can be traced to
  retrieval versus faithfulness — the diagnosis below came straight from that.
- `LLM_MODEL` moved to `config.py` as a single source of truth, and is recorded in
  every eval report. Results are only comparable across runs on the same model.

## Diagnosing `140V200` — solved

`knowledge/metar_reference.md:12` documents variable wind correctly and always did,
so the bug was never a knowledge gap. The two candidates were:

1. **Retrieval failure** — the wind chunk never reached the model.
2. **Faithfulness failure** — it arrived and was overridden.

**It was retrieval.** With `n_results=4`, a query consisting of the whole METAR
returned the document title (17 characters), the structure section, station/time and
pressure. Wind, visibility and cloud never arrived — and the decoder correctly
refused to decode groups its documentation did not cover. The refusal was right; the
input was wrong.

Raising `_retrieve()` to `n_results=8` fixed it: the regression case now passes 3/3.
That is a stopgap, not the fix. The real problem is that one averaged embedding of a
whole METAR matches no section sharply, plus chunking that spends a slot on a
title-only chunk (`rag.py:15` splits on `\n## `). Per-group retrieval belongs in the
tuning step, where the eval can measure whether it actually helps.

## Known failures — first run, 2026-08-21

`openai/gpt-oss-120b`, `--repeat 3`, 5 validated cases: **97.3% fields correct,
66.7% perfect runs.** Both open failures are about calibration, in opposite
directions:

- **Under-refusal** (`sbct-undocumented-codes-refusal`, 3/3 failed) — `VCTS` is not
  in the reference, but the decoder lists it under `weather` as though decoded. One
  run also failed to flag `CB`.
- **Over-refusal** (`sbsp-variable-wind-distinct-bounds`, 2/3 failed) — flags
  documented codes such as `FEW025`, and once the literal `METAR` keyword, as
  undecodable.

The decoder is miscalibrated about what it knows in both directions. Fixes belong in
the tuning step, as measured experiments against these numbers.
