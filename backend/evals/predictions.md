# Predictions

Failure predictions written before running the eval, to compare against the results afterwards.

---

## 2026-08-20: before the deterministic eval

Predicted by: elise
Dataset: 5 synthetic cases, `schema_version` 1
Decoder: `decode_metar()` returning free prose, RAG with `search(metar, n_results=4)`, model `llama-3.3-70b-versatile`

### Most likely to fail: `sbpa-variable-wind-regression`

Reason: it already failed three times in production, and variable wind is the most ambiguous field.

Confirmed if: `wind_variable_from_deg` / `wind_variable_to_deg` are wrong, or `140V200` ends up in `visibility_m` (the failure seen in production: "visibility 1400-2000m").

### Second: `sbct-undocumented-codes-refusal`

Reason: the model may explain `VCTS` and `CB` instead of saying it cannot decode them.

Confirmed if: `expected_refusal` is `true` but the answer explains both codes. A correct explanation still counts as a failure, since the decoder prompt says "never guess".

### Not ranked

`sbsp-variable-wind-distinct-bounds` was added after the prediction. If SBPA fails and SBSP passes, the bug is specific to that input; if both fail, variable wind is broken in general.

---

## 2026-08-21: first deterministic run

The model changed before the run: `llama-3.3-70b-versatile` was removed from Groq (404), so the project moved to `openai/gpt-oss-120b`. The prediction above was left unchanged; some of the differences below may come from the model swap.

Run: `--repeat 3`, 5 validated cases, 97.3% fields correct, 66.7% perfect runs.

| Prediction | Outcome |
|---|---|
| `sbpa-variable-wind-regression` fails | Wrong: 3/3 passed |
| `sbct-undocumented-codes-refusal` fails | Right: 3/3 failed |

**SBPA.** It passed, but the original bug was found. With `n_results=4`, retrieval returned the title, structure, station/time and pressure sections, never wind, visibility or clouds, so the decoder marked almost everything as undecodable. Raising it to 8 fixed it. The production failures were a retrieval problem, not the model ignoring the docs.

**SBCT.** Failed all 3 runs: `VCTS` was listed in `weather` as if decoded (3/3), and one run also missed flagging `CB`.

**Not predicted.** `sbsp-variable-wind-distinct-bounds` failed 2/3 runs by over-refusing: it flagged `FEW025` and even `METAR` as undecodable. The decoder is miscalibrated in both directions. A single run would have shown this case as passing; it only showed up with `--repeat 3`.

## Reading the results

- Both predicted cases fail: the prediction was right.
- A different case fails: add similar cases to the dataset around it.
- Everything passes: check that the eval actually catches a wrong answer before trusting it. Five cases is a small sample.
