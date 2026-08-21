# airspace-copilot

An AI copilot for airspace monitoring. It reads live air traffic and aviation weather and explains what’s happening in plain language, in English and Brazilian Portuguese.

This is **not** a flight tracker. A map shows *where* planes are; this project uses AI to explain *what is happening and why*. The map is the frame — the AI is the product.

## Why

Air traffic and aviation weather data are public, abundant and unreadable. A report like `SBPA 120300Z 23005KT 4000 BR OVC003 15/15 Q1013` only makes sense to trained pilots. This project turns that raw data into clear, grounded, bilingual explanations.

## What it does today

- **Live traffic** — fetches real aircraft data from the OpenSky Network (OAuth2), filtered to a geographic region
- **Airspace briefing** — generates a natural-language summary of the current airspace, in EN and PT-BR
- **METAR decoding (RAG)** — translates raw aviation weather codes into plain language, grounded in official reference documentation using retrieval, so the model explains from the source instead of guessing
- **Conversational agent (tool calling)** — answers free-form questions such as "how many aircraft are over Rio right now?" or "is the weather good for landing in Guarulhos?" by deciding which tools to call, executing them and composing a grounded answer

## Architecture

The project is built as independent modules, each with a single responsibility:

| Module | Responsibility |
| --- | --- |
| config.py | Loads secrets and configuration |
| opensky.py | Client for the live air traffic API (OAuth2) |
| weather.py | Client for the aviation weather API (METAR) |
| llm.py | LLM provider adapter — swappable in one file |
| llm_tools.py | LLM adapter for tool calling |
| rag.py | Knowledge ingestion + semantic search (Chroma) |
| briefing.py | Airspace briefing logic |
| decoder.py | RAG-grounded METAR decoding |
| tools.py | Tools exposed to the agent (region map, live traffic) |
| agent.py | Agent loop: decide, execute, respond |
| guardrails.py | Input validation and prompt-injection defense |
| main.py | Entry point |

The LLM layer is deliberately isolated: the project was validated by switching providers without touching the rest of the code.

### API layer

`api/` is a thin HTTP wrapper containing **no business logic** — every endpoint calls a function in `src/`. It is split by domain so no single file holds everything:

| File | Responsibility |
| --- | --- |
| api/main.py | App creation, CORS, router registration |
| api/errors.py | Shared flat error shape + exception handlers |
| api/schemas.py | Pydantic request/response models |
| api/routers/briefing.py | `/briefing` |
| api/routers/weather.py | `/weather/{icao}` |
| api/routers/aircraft.py | `/aircraft`, `/aircraft/map` |
| api/routers/agent.py | `/ask` |

The rule that keeps it thin: if a router needs a rule about aviation or the LLM, that rule goes in `src/` and the router calls it. Guardrails followed exactly this path.

### Agent design

The agent runs a bounded loop — the model decides which tool to call, this code executes it, and the result is fed back until the model produces a final answer. The model never executes anything itself; it only requests.

Three safeguards are built into the loop:
- **Iteration limit** — the loop can never run indefinitely
- **Call cache** — an identical tool call is never executed twice; the cached result is reused
- **Loop breaker** — if the model requests data it already has, the final call is made with no tools available, forcing it to answer instead of looping

Region lookups are deterministic: the model chooses a region *name* from a fixed list, and this code maps it to coordinates. Anything that can be deterministic is kept out of the model's hands.

### Input guardrails

Free-form questions sent to the API pass through `guardrails.py` first: structurally invalid input (empty, oversized, invisible-character-only) is rejected before a model call is spent on it, and known prompt-injection phrasings are detected, logged and fenced as untrusted data rather than blocked outright — blocking would break legitimate questions like *"ignore the previous METAR, what's the current one?"*.

Pattern matching is deliberately treated as the weaker layer. The real containment is architectural: the agent has two read-only tools with enum-constrained arguments, no shell, no database and no secrets in context. A successful injection can make the model say something wrong; it cannot make it *do* anything outside those two calls.

## Known limitations
- **Partial coverage.** OpenSky relies on volunteer-operated receivers. Coverage is strong over Europe and North America and sparser elsewhere, so the data shows *detected* aircraft, not all traffic. The system always states this.
- **RAG reduces hallucination, it doesn’t eliminate it.** Grounding the model in documentation improves accuracy, but factual errors still occur. Because the model is non-deterministic, the same input can even produce a different error on each run. Automated evaluation is on the roadmap to measure and control this.
## Tech stack
Python · Chroma (vector database) · OpenSky Network API · Aviation Weather Center API · LLM via provider API

## Roadmap
- ✅ Live traffic + bilingual briefing
- ✅ RAG-based METAR decoding
- ✅ Agent with tool calling (natural-language questions about the airspace)
- 🚧 Automated evaluation (golden dataset) — deterministic eval running; ✅ input guardrails done
- 🚧 REST API (FastAPI) — ✅ done; React frontend + deployment pending

## Running locally

**Prerequisites:** Python 3.11 or newer, plus API credentials.

**1. Clone and enter the project**

   git clone https://github.com/eliserps/airspace-copilot.git
   
**2. cd airspace-copilot**

**3. Create and activate a virtual environment**

   python -m venv .venv
   - Windows (PowerShell): .venv\Scripts\Activate.ps1
   - macOS / Linux: source .venv/bin/activate
   
 **4. Install dependencies**
   pip install -r requirements.txt
   
 **5. Set up your credentials.** Create a file named `.env` in the project root with:
 
   GROQ_API_KEY=your_groq_key
   OPENSKY_CLIENT_ID=your_opensky_client_id
   OPENSKY_CLIENT_SECRET=your_opensky_client_secret
   
Get a Groq key at https://console.groq.com and OpenSky credentials at https://opensky-network.org (Account → API Client).

**6. Build the knowledge base (one time).** This reads the reference docs, creates embeddings and stores them in Chroma:

   python src/rag.py
   
**7. Run the project**

   python src/main.py
   
You should see live aircraft counts, decoded weather, a bilingual airspace briefing and the agent answering natural-language questions in your terminal.

## Running the API

The same logic is exposed over HTTP by a thin FastAPI wrapper in `api/`. From the project root, with the venv active and steps 1–6 above already done:

   uvicorn api.main:app --reload --port 8000

Then open:
- **Interactive docs:** http://127.0.0.1:8000/docs
- **Health check:** http://127.0.0.1:8000/health

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Status, plus the valid regions and languages |
| GET | `/briefing?region=&lang=` | Natural-language briefing of current traffic |
| GET | `/weather/{icao}?lang=` | Raw METAR + plain-language decoding |
| GET | `/aircraft?region=` | Aircraft detected over a region (text summary) |
| GET | `/aircraft/map?region=` | Aircraft as objects with coordinates, for map pins |
| POST | `/ask` | Free-form question answered by the agent |

The API contains **no business logic** — each endpoint calls an existing function in `src/`. Full request/response shapes, error contracts and status codes are documented in [api/README.md](api/README.md).

CORS is currently open (`*`) for local frontend development; narrow it to the real origin before deploying.