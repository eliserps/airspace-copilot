# airspace-copilot

An AI copilot for airspace monitoring. It reads live air traffic and aviation weather and explains what's happening in plain language, in English and Brazilian Portuguese.

This is **not** a flight tracker. A map shows *where* planes are; this project uses AI to explain *what is happening and why*. The map is the frame — the AI is the product.

## Why

Air traffic and aviation weather data are public, abundant and unreadable. A report like `SBPA 120300Z 23005KT 4000 BR OVC003 15/15 Q1013` only makes sense to trained pilots. This project turns that raw data into clear, grounded, bilingual explanations.

## What it does today

- **Live traffic** — real aircraft data from the OpenSky Network (OAuth2) for a continent or the whole world, on a 3D globe and as a list
- **Airspace briefing** — a natural-language summary of the current airspace, in EN and PT-BR
- **METAR decoding (RAG)** — raw aviation weather codes translated into plain language, grounded in reference documentation through retrieval, so the model explains from the source instead of guessing
- **Conversational agent (tool calling)** — answers free-form questions such as "how many aircraft are over Europe right now?" or "is the weather good for landing in Guarulhos?" by deciding which tools to call, executing them and composing a grounded answer
- **Automated evaluation** — a golden dataset of METARs with hand-verified decodings, scored field by field

## Repository layout

```
React UI (frontend/)  ──HTTP──▶  FastAPI (api/)  ──calls──▶  core modules (src/)  ──▶  OpenSky · AWC · Groq
  rendering only                  no business logic           all the logic
```

| Folder | What it is | Details |
| --- | --- | --- |
| `src/` | Core Python modules — every rule about aviation and the LLM | this file |
| `api/` | Thin FastAPI wrapper: endpoints, error contract, status codes | [api/README.md](api/README.md) |
| `frontend/` | React web UI: globe, copilot chat, briefing, weather | [frontend/README.md](frontend/README.md) |
| `evals/` | Golden dataset and deterministic evaluation of the decoder | [Evaluation](#evaluation) |
| `knowledge/` | METAR reference documentation ingested by the RAG | — |

## Core modules (`src/`)

Each module has a single responsibility:

| Module | Responsibility |
| --- | --- |
| config.py | Loads secrets and configuration, including `LLM_MODEL` |
| opensky.py | Client for the live air traffic API (OAuth2) |
| weather.py | Client for the aviation weather API (METAR) |
| llm.py | LLM provider adapter — swappable in one file; logs token usage per call |
| llm_tools.py | LLM adapter for tool calling |
| rag.py | Knowledge ingestion + semantic search (Chroma) |
| briefing.py | Airspace briefing: aggregates traffic, then asks the model to narrate it |
| decoder.py | RAG-grounded METAR decoding — prose for users, structured JSON for the eval |
| tools.py | Region map, live traffic lookups and the tools exposed to the agent |
| agent.py | Agent loop: decide, execute, respond |
| guardrails.py | Input validation and prompt-injection defense |
| main.py | Command-line demo of every feature |

The LLM layer is deliberately isolated: the project was validated by switching providers without touching the rest of the code.

### Regions

Traffic is queried by region *name*; `REGIONS` in `tools.py` maps each name to a bounding box.

| Region | Notes |
| --- | --- |
| `south_america`, `north_america`, `europe`, `africa`, `asia`, `oceania` | Continental bounding boxes |
| `world` | The whole globe — typically 10,000–13,000 detected aircraft, for the same OpenSky credits as a large continent |

### Agent design

The agent runs a bounded loop — the model decides which tool to call, this code executes it, and the result is fed back until the model produces a final answer. The model never executes anything itself; it only requests.

Three safeguards are built into the loop:
- **Iteration limit** — the loop can never run indefinitely
- **Call cache** — an identical tool call is never executed twice; the cached result is reused
- **Loop breaker** — if the model requests data it already has, the final call is made with no tools available, forcing it to answer instead of looping

Region lookups are deterministic: the model chooses a region name from the fixed list above, and this code maps it to coordinates. Anything that can be deterministic is kept out of the model's hands.

### Input guardrails

Free-form questions pass through `guardrails.py` before reaching the agent: structurally invalid input (empty, oversized, invisible-character-only) is rejected before a model call is spent on it, and known prompt-injection phrasings are detected, logged and fenced as untrusted data rather than blocked outright — blocking would break legitimate questions like *"ignore the previous METAR, what's the current one?"*.

Pattern matching is deliberately treated as the weaker layer. The real containment is architectural: the agent has two read-only tools with enum-constrained arguments, no shell, no database and no secrets in context. A successful injection can make the model say something wrong; it cannot make it *do* anything outside those two calls.

### Token budget

LLM tokens are the scarce resource, so the model is only called when there is something new to say:

- **Briefings get aggregates, not raw data.** `briefing.py` counts aircraft by altitude band, country and airline prefix in Python and sends the model a fixed-size summary. The prompt is the same size for 50 aircraft or 12,000 (~200 tokens for the whole world; one line per aircraft would exceed the model's context).
- **Briefings regenerate only when the picture changes.** A briefing is reused for 3 minutes; after that it is regenerated only if the totals or the top countries/airlines moved by roughly 10%. Positions change on every poll, so they are deliberately left out of the comparison.
- **METARs are decoded once per report.** Decodings are cached by raw METAR text and language, so a new model call happens exactly when a new report is issued.
- **OpenSky results are cached for 30 seconds**, so every consumer of a region shares one fetch.

Every model call prints its usage to the backend log, e.g. `[llm] briefing: prompt=412 completion=180 total=592` (labels: `briefing`, `metar`, `agent`, `ask`). All caches live in memory: they reset on restart and are not shared between processes. The UI adds its own limits on top — see [frontend/README.md](frontend/README.md).

## Evaluation

The decoder is non-deterministic and makes silent factual errors. Real example: `140V200` (wind direction varying 140°–200°) was decoded three different wrong ways across three runs — "gusts to 200°", "visibility 1400–2000m", "visibility 140–200m" — each stated confidently. Inspecting answers by hand does not catch this, so `evals/` measures it.

**Ground truth comes from the ICAO/FAA METAR specification, never from a language model.** An evaluator built from the same knowledge as the system inherits its errors and then certifies them as correct — asked to grade `140V200`, a model would likely have written "visibility 1400–2000m" into the answer key.

| File | Role |
| --- | --- |
| `evals/golden_dataset.json` | METARs paired with hand-verified decodings. Small by design: every case names the failure mode it probes in `tests`, and `synthetic: true` marks METARs built to exercise one rather than observed live |
| `evals/evaluate.py` | Runs `decode_metar_structured()` on every validated case and compares field by field, by exact equality — no model grades anything |
| `evals/collect_metars.py` | Appends real METARs as unvalidated cases, excluded from scoring until checked |
| `evals/predictions.md` | Failure predictions written *before* each run, so intuition is scored against measurement |
| `evals/results.json` | Latest report, including the model it ran on |

**The field contract** is `STRUCTURED_SCHEMA` in `src/decoder.py`. Units are in the field names (`visibility_m`, `height_ft`, `wind_speed_kt`) because unit errors are exactly what the eval must catch. Three decisions worth remembering:
- **Cloud layers store feet, not the raw code** — `BKN007` is `700`, so "7 feet" or "700 metres" cannot pass.
- **`ceiling_ft` is derived, not read** — it is the lowest BKN or OVC layer, so `FEW015 BKN030` has a ceiling of 3000. This tests reasoning, not lookup.
- **`wind_gust_kt` is `null`, never `0`** — `0` would claim a gust exists; collapsing the two would hide a hallucinated gust.

**Running it** (venv active, knowledge base built):

    python evals/evaluate.py             # score validated cases, write results.json
    python evals/evaluate.py --repeat 3  # 3 runs per case — use this
    python evals/evaluate.py --case ID   # one case

The exit code is 0 only when every run is perfect, so it drops into CI unchanged. A single green run is weak evidence for a non-deterministic system: one bug below was invisible at `--repeat 1` and failed 2 of 3 at `--repeat 3`. **It spends real tokens** — one model call per case per run, on the same Groq key as the app, and the METAR cache deliberately does not apply.

**Latest results** (2026-08-21, `openai/gpt-oss-120b`, `--repeat 3`, 5 validated cases): **97.3% of fields correct, 66.7% perfect runs.**
- **Solved — `140V200` was a retrieval failure.** With 4 retrieved chunks, the wind, visibility and cloud sections never reached the model, and it correctly refused to decode them. Retrieving 8 fixed it (3/3). That is a stopgap: one embedding of a whole METAR matches no section sharply, and per-group retrieval is the real fix.
- **Open — under-refusal.** `VCTS` is not in the reference, yet the decoder lists it as decoded (3/3 failed).
- **Open — over-refusal.** Documented codes such as `FEW025` are flagged as undecodable (2/3 failed).

The decoder is miscalibrated about what it knows in both directions; fixes belong in a tuning step, measured against these numbers.

## Known limitations

- **Partial coverage.** OpenSky relies on volunteer-operated ground receivers with a range of a few hundred kilometres. Coverage is strong over Europe and North America, sparser elsewhere, and **almost absent over oceans** — one world snapshot showed 25 aircraft over the mid-North Atlantic, where hundreds are typically flying. Oceanic tracking needs satellite ADS-B, which only paid providers offer. The data shows *detected* aircraft, not all traffic, and the system always says so.
- **RAG reduces hallucination, it doesn't eliminate it.** Grounding the model in documentation improves accuracy, but factual errors still occur, and the same input can produce a different error on each run. The evaluation suite measures this; current results and open failures are under [Evaluation](#evaluation).
- **Guardrails are API-only.** `main.py` calls the agent directly, which is fine for a local terminal.
- **Briefings can lag slightly.** Because of the cache, a briefing may describe traffic a few minutes old; live counts are always current.

## Tech stack

Python · FastAPI · Chroma (vector database) · Groq (default model `openai/gpt-oss-120b`) · OpenSky Network API · Aviation Weather Center API · React · TypeScript · TanStack Start/Query · Tailwind · react-globe.gl

## Roadmap

- ✅ Live traffic + bilingual briefing
- ✅ RAG-based METAR decoding
- ✅ Agent with tool calling
- ✅ Input guardrails
- ✅ REST API (FastAPI)
- ✅ React frontend with 3D globe and world view
- ✅ Token budget: aggregated briefings, change-based caching, usage logging
- 🚧 Automated evaluation — deterministic eval running; decoder calibration fixes pending
- 🚧 Deployment

## Running locally

**Prerequisites:** Python 3.11 or newer, Node.js 20 or newer, plus API credentials.

**1. Clone and enter the project**

    git clone https://github.com/eliserps/airspace-copilot.git
    cd airspace-copilot

**2. Create and activate a virtual environment**

    python -m venv .venv

- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- macOS / Linux: `source .venv/bin/activate`

**3. Install dependencies**

    pip install -r requirements.txt

**4. Set up your credentials.** Create a file named `.env` in the project root with:

    GROQ_API_KEY=your_groq_key
    OPENSKY_CLIENT_ID=your_opensky_client_id
    OPENSKY_CLIENT_SECRET=your_opensky_client_secret
    # optional — defaults to openai/gpt-oss-120b
    LLM_MODEL=openai/gpt-oss-120b

Get a Groq key at https://console.groq.com and OpenSky credentials at https://opensky-network.org (Account → API Client). The file is read once at startup, so restart the backend after changing a key.

**5. Build the knowledge base (one time).** This reads the reference docs, creates embeddings and stores them in Chroma:

    python src/rag.py

**6. Run it** — pick what you need:

| Goal | Command | More |
| --- | --- | --- |
| Web app | API: `uvicorn api.main:app --reload --port 8000` · UI: `cd frontend && npm install && npm run dev` (two terminals) | [api/](api/README.md), [frontend/](frontend/README.md) |
| Terminal demo | `python src/main.py` — traffic over South America, three decoded METARs, a briefing and a few agent answers | — |
| Evaluation | `python evals/evaluate.py --repeat 3` | [Evaluation](#evaluation) |

### Credentials stay in the backend

`GROQ_API_KEY`, `OPENSKY_CLIENT_ID` and `OPENSKY_CLIENT_SECRET` are read only by `src/config.py` from the root `.env`. The browser talks to the API; the API talks to Groq and OpenSky. The frontend's only setting is the public API address.
