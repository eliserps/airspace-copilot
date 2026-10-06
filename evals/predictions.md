# Predictions

Failure predictions recorded **before** the eval is run, so intuition about the
system can be scored against measurement instead of rationalised after the fact.

A prediction written after seeing results is worthless — hindsight always finds a
reason. Recorded up front, a wrong prediction is the useful kind of wrong: it says
the mental model of the system needs updating, and points at which part.

---

## 2026-08-20 — before the deterministic eval exists

Predicted by: elise
Dataset at time of prediction: 5 synthetic cases, `schema_version` 1
Decoder at time of prediction: `decode_metar()` returns free prose, RAG with
`search(metar, n_results=4)`, model `llama-3.3-70b-versatile`

### Most likely to fail: `sbpa-variable-wind-regression`

**Reasoning given:** it is the one already observed failing three times in
production, and it is the most ambiguous field.

**What would confirm it:** `wind_variable_from_deg` / `wind_variable_to_deg` wrong,
or the `140V200` group leaking into `visibility_m` (the observed failure mode:
"visibility 1400–2000m").

### Second most likely: `sbct-undocumented-codes-refusal`

**Reasoning given:** the model may invent meaning for `VCTS` and `CB` instead of
saying it cannot decode them.

**What would confirm it:** `expected_refusal` is `true` but the answer explains both
codes confidently. Note this counts as a failure **even if the explanation is
meteorologically correct** — the rule in `decoder.py:8` is "never guess", so an
accurate guess is still a rule violation. That distinction is the whole point of the
case.

### Unscored at prediction time

`sbsp-variable-wind-distinct-bounds` was added after this prediction was framed, so
no ranking was given for it. Worth watching anyway: if SBPA fails and SBSP passes,
the bug is specific to that input; if both fail, the variable-wind group is broken
generally.

---

### Outcome — 2026-08-21, first deterministic run

**Model changed between prediction and measurement.** `llama-3.3-70b-versatile` was
withdrawn from Groq (404) before the eval could run; the project moved to
`openai/gpt-oss-120b`. The prediction was kept as written rather than rewritten
after the fact. Part of any miss below may be the model swap, and that is exactly
why the swap is recorded here instead of quietly absorbed.

Run: `--repeat 3`, 5 validated cases, 97.3% fields correct, 66.7% perfect runs.

| Prediction | Outcome |
|---|---|
| `sbpa-variable-wind-regression` fails | **Wrong — 3/3 passed**, `140V200` correct every time |
| `sbct-undocumented-codes-refusal` fails | **Right — 3/3 failed** |

**On the miss.** The variable-wind bug did not reproduce, but the cause was found
anyway and it was not what either hypothesis in the evaluation notes framed as most likely.
Retrieval was returning the document title, the structure section, station/time and
pressure — the wind, visibility and cloud sections never arrived. With `n_results=4`
the decoder marked nearly every group undecodable, which was correct behaviour on
bad input. Raising it to 8 fixed the input and the field came out right. So the
original three wrong decodings were **retrieval failure** (hypothesis 1), not the
model overriding documentation it had been given.

The intuition was still pointing at a real defect — just one layer lower than
expected. "The wind field is fragile" was right; "the model ignores the docs" was
not.

**On the hit.** The refusal case failed all three runs, and it failed in two
different ways: `VCTS` was listed in `weather` as though decoded (all 3 runs), and
one run additionally missed flagging `CB`. Predicted correctly.

**Unpredicted finding.** `sbsp-variable-wind-distinct-bounds` failed 2 of 3 runs on
over-refusal — flagging `FEW025` and even the literal `METAR` keyword as
undecodable. This is the mirror image of the refusal bug: the decoder is not
calibrated about what it knows in *either* direction. Nobody predicted it, and it
only surfaced because `--repeat 3` ran the same input more than once. A single run
would have shown this case green.

## How to score this

When the deterministic eval runs, compare per-case results against the ranking above
and record the outcome here. Three things to look for:

- **Both predicted cases fail** — intuition calibrated; the known bug and the
  refusal weakness are the real failure modes.
- **A different case fails harder** — more informative than being right. A surprise
  failure means the mental model of the system is wrong somewhere specific, and that
  case deserves siblings in the dataset.
- **Everything passes** — do not celebrate yet. First check the eval is actually
  discriminating: a comparison that passes a deliberately wrong answer is measuring
  nothing. Five cases is a small enough set that a green board is weak evidence.
