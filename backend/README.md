# 🔌 Backend

FastAPI app organised by domain. Routers only translate HTTP; services hold the logic and receive their clients by injection.

▶️ **Run** (from `backend/`): `uv run uvicorn app.main:app --reload --port 8000`, or just `uvicorn app.main:app --reload --port 8000` inside an activated `.venv`

📖 **Interactive docs**: http://localhost:8000/docs

## Endpoints

❤️ **`GET /health`**: liveness, valid regions and languages

🚦 **`GET /health/ready`**: readiness; `503` until the knowledge base is loaded and the AI key is set

📈 **`GET /metrics`**: Prometheus metrics (requests by route, LLM tokens and latency, cache hits, upstream errors)

🗺️ **`GET /aircraft/map?region=`**: aircraft with coordinates for the map, cached 30 s

✈️ **`GET /aircraft?region=`**: short text summary of traffic, cached 30 s

📝 **`GET /briefing?region=&lang=`**: AI summary of the airspace 🤖, reused until traffic changes

🌦️ **`GET /weather/{icao}?lang=`**: raw METAR plus an AI explanation 🤖, once per report

💬 **`POST /ask`**: copilot answer 🤖, never cached. Body: `{"question": "...", "region": "europe"}` (`region` is optional)

⚡ **`POST /ask/stream`**: same as `/ask`, as Server-Sent Events: `meta` → `delta`… → `done` or `error`

🤖 = calls the AI and spends tokens

**Accepted values**

🌍 `region`: `south_america` · `north_america` · `europe` · `africa` · `asia` · `oceania` · `world`

🗣️ `lang`: `en` · `pt`

## Errors

Every error looks like `{"error": "slug", "message": "text"}`. Branch on `error`.

🔍 **404**: region, METAR or route doesn't exist (`unknown_region`, `no_metar`, `not_found`)

✋ **422**: bad input (`invalid_request` with the offending `field`, `empty_question`, `question_too_long`)

⏳ **429**: too many requests from you (`too_many_requests`), or the OpenSky/Groq quota ran out (`rate_limited`, `llm_rate_limited`)

🤷 **502**: the copilot produced no answer (`no_answer`)

🔥 **503**: OpenSky, AWC or Groq is down (`upstream_unavailable`, `llm_unavailable`)

On `/ask/stream`, errors after the stream starts arrive as an `error` event with the same body.

## Good to know

📏 **`altitude_m`, `velocity_ms`**: metric units, metres and metres per second

🆔 **`icao24`**: the unique aircraft ID. `callsign` can be `null`

✍️ **`briefing`, `decoded`, `answer`**: Markdown, so render it

🕰️ **`stale`** on `/aircraft/map`: `true` means OpenSky is down and the data is up to 10 min old

🛡️ **`flagged`** on `/ask`: `true` means the question looked like manipulation; it was answered safely

🔎 **`X-Request-ID`**: sent back on every response and attached to every log line

🌐 **Another frontend URL**: add it to `CORS_ORIGINS`, otherwise the browser blocks the calls

## Layout

🧱 **`app/core/`**: settings, error contract, logging, cache, rate limiting

🧠 **`app/llm/`**: `LLMClient` protocol, Groq client (with streaming), tool registry

✈️ **`app/traffic/`**: regions, OpenSky client, `TrafficService` (cache, backoff, stale data)

📝 **`app/briefing/`**: traffic summary and `BriefingService`

🌦️ **`app/weather/`**: AWC client, knowledge base (RAG), `MetarDecoder`

💬 **`app/copilot/`**: guardrails, tools, agent loop, `/ask` endpoints

🔌 **`app/container.py`**: builds every service once; tests build the same graph with fakes

📊 **`evals/`**: decoder evaluation · 📚 **`knowledge/`**: docs the AI reads · 🛠️ **`scripts/`**: demo and OpenAPI export

## Commands

Run from `backend/`. With an activated `.venv` instead of uv, drop the `uv run` prefix.

🧪 `uv run pytest --cov`: tests (no network, no tokens)

🔍 `uv run ruff check . && uv run mypy app tests scripts`: lint and strict types

🖥️ `uv run python -m scripts.demo`: terminal demo of every feature (spends tokens)

📜 `uv run python -m scripts.export_openapi ../frontend/openapi.json`: refresh the API contract

📊 `uv run python -m evals.evaluate --repeat 3`: decoder evaluation (spends tokens)

🧭 `uv run python -m evals.agent_eval --repeat 3`: agent tool-selection evaluation (spends tokens)

📚 Edit `knowledge/` and delete `chroma_db/` to rebuild the index on the next start
