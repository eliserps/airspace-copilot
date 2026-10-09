# 🔌 API

FastAPI layer over `src/`. It only receives requests and returns JSON; all the logic lives in `src/`.

▶️ **Run** (from the project root): `uvicorn api.main:app --reload --port 8000`

📖 **Interactive docs**: http://localhost:8000/docs

## Endpoints

❤️ **`GET /health`**: status, valid regions and languages

🗺️ **`GET /aircraft/map?region=`**: aircraft with coordinates for the map, cached 30 s

✈️ **`GET /aircraft?region=`**: short text summary of traffic, cached 30 s

📝 **`GET /briefing?region=&lang=`**: AI summary of the airspace 🤖, reused until traffic changes

🌦️ **`GET /weather/{icao}?lang=`**: raw METAR plus an AI explanation 🤖, once per report

💬 **`POST /ask`**: copilot answer 🤖, never cached. Body: `{"question": "...", "region": "europe"}` (`region` is optional)

🤖 = calls the AI and spends tokens

**Accepted values**

🌍 `region`: `south_america` · `north_america` · `europe` · `africa` · `asia` · `oceania` · `world`

🗣️ `lang`: `en` · `pt`

## Errors

Every error looks like `{"error": "slug", "message": "text"}`. Branch on `error`.

🔍 **404**: region, METAR or route doesn't exist (`unknown_region`, `no_metar`, `not_found`)

✋ **422**: bad input (`invalid_request`, `invalid_language`, `empty_question`)

⏳ **429**: too many requests from you (`too_many_requests`), or the OpenSky/Groq quota ran out (`rate_limited`, `llm_rate_limited`)

🤷 **502**: the copilot produced no answer (`no_answer`)

🔥 **503**: OpenSky, AWC or Groq is down (`upstream_unavailable`, `llm_unavailable`)

## Good to know

📏 **`altitude_m`, `velocity_ms`**: metric units, metres and metres per second

🆔 **`icao24`**: the unique aircraft ID. `callsign` can be `null`

✍️ **`briefing`, `decoded`, `answer`**: Markdown, so render it

🕰️ **`stale`** on `/aircraft/map`: `true` means OpenSky is down and the data is up to 10 min old

📊 **`aircraft_count`, `generated_at`** on `/briefing`: describe the data the text was written from

🛡️ **`flagged`** on `/ask`: `true` means the question looked like manipulation; it was answered safely

📦 **`world` region**: 10,000+ aircraft, a few MB of JSON

🚀 **Deploying**: add the frontend's URL to `CORS_ORIGINS`, otherwise the browser blocks the calls

## Files

🚀 **`main.py`**: app setup, CORS, routers

❗ **`errors.py`**: shared error format

📋 **`schemas.py`**: request and response models

⏱️ **`ratelimit.py`**: per-user limits

📂 **`routers/`**: one file per area: aircraft, briefing, weather, agent
