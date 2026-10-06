# API

Thin REST wrapper over `src/`. Every endpoint calls an existing function and shapes the result as JSON — no decoding rules, no agent loop, no bounding boxes, no guardrail patterns live here. Project overview and setup are in the [root README](../README.md).

## Layout

```
api/
  main.py            app creation, CORS, router registration only
  errors.py          the shared flat error shape + exception handlers
  schemas.py         Pydantic request/response models
  routers/
    briefing.py      GET  /briefing
    weather.py       GET  /weather/{icao}
    aircraft.py      GET  /aircraft, GET /aircraft/map
    agent.py         POST /ask
```

Split by **domain**, not by layer: everything about weather is in one file, so a change to that endpoint touches one place. `errors.py` and `schemas.py` are the deliberate exceptions — they hold what all routers must agree on, and duplicating either would let the shapes drift apart.

`main.py` sets up `sys.path` for `src/` **before** importing routers, since the routers import from there. That ordering is load-bearing.

## Running

From the project root, with the venv active and the root setup done:

    uvicorn api.main:app --reload --port 8000

- Interactive docs: http://127.0.0.1:8000/docs
- OpenAPI schema: http://127.0.0.1:8000/openapi.json

`--reload` restarts on file changes — which also clears the in-memory caches. Drop it in production.

## Conventions

**Every error has the same flat shape**, whatever the cause:

```json
{ "error": "unknown_region", "message": "Unknown region 'narnia'.", "allowed": ["africa", "..."] }
```

`error` is a stable machine-readable slug — branch on it. `message` is human-readable. Some errors add a context key (`allowed`, `icao`, `field`). FastAPI's default nests errors under `detail`; that is flattened deliberately so clients need one error branch, not two.

**Status codes**

| Code | Meaning |
| --- | --- |
| 200 | OK |
| 404 | Not found — unknown region, or no METAR for that airport |
| 422 | Invalid request — bad `lang`, malformed ICAO, empty question |
| 502 | The agent produced no answer |
| 503 | An upstream data source (OpenSky) is unavailable |

**Cost and latency per endpoint.** Three endpoints call the model; the cache rules behind them are explained under *Token budget* in the [root README](../README.md#token-budget).

| Endpoint | Calls the LLM | Typical latency |
| --- | --- | --- |
| `/health` | No | instant |
| `/aircraft`, `/aircraft/map` | No | one OpenSky round-trip, cached 30 s (`world` is the slowest) |
| `/briefing` | Yes — reused while traffic has not changed | instant when cached, ~2–5 s otherwise |
| `/weather/{icao}` | Yes — once per METAR issued | instant when cached, ~2–5 s otherwise |
| `/ask` | Yes — several rounds, never cached | ~2–10 s |

**Free text is Markdown.** `briefing`, `decoded` and `answer` come back as Markdown (tables, bold, bullets) — render it rather than dropping it into a `<div>` raw.

---

## GET /health

Liveness check. Touches no upstream service, so it is fast and safe to poll. Use it to populate region and language pickers instead of hardcoding them.

```json
{
  "status": "ok",
  "regions": ["africa", "asia", "europe", "north_america", "oceania", "south_america", "world"],
  "languages": ["en", "pt"]
}
```

---

## GET /briefing

Natural-language briefing of current traffic over a region.

| Param | Type | Default | Notes |
| --- | --- | --- | --- |
| `region` | string | `south_america` | One of `/health` → `regions` |
| `lang` | string | `en` | `en` or `pt` |

```json
{
  "region": "south_america",
  "language": "pt",
  "aircraft_count": 337,
  "briefing": "**Resumo do espaço aéreo — América do Sul**\n\n- Foram detectadas **337 aeronaves**…",
  "source": "OpenSky (partial volunteer coverage)"
}
```

`aircraft_count` is the live count from OpenSky, not parsed out of the text — use it for a counter widget and let `briefing` be the prose. Because briefings are reused while traffic is stable, the text can lag that count by a few minutes. Errors: 404 unknown region, 422 bad `lang`, 503 OpenSky down.

---

## GET /weather/{icao}

Raw METAR plus a plain-language decoding for one airport.

| Param | Type | Default | Notes |
| --- | --- | --- | --- |
| `icao` | path, 4 chars | — | e.g. `SBGR`; lowercase is accepted and upcased |
| `lang` | query | `en` | `en` or `pt` |

```json
{
  "icao": "SBGR",
  "language": "pt",
  "raw": "METAR SBGR 210000Z 31003KT CAVOK 20/12 Q1017",
  "decoded": "**Decodificação do METAR**\n\n| Elemento | Significado |\n…",
  "source": "Aviation Weather Center"
}
```

Always show `raw` next to the decoding — the point of the product is that the user can see the source text and the explanation together.

**404 `no_metar`** covers both "this airport has no report" and "the weather service failed". `get_metar()` returns `None` for both and cannot distinguish them, so the API does not pretend to either. Word the UI accordingly: "no report available right now", not "invalid airport".

---

## GET /aircraft

Aircraft currently detected over a region, as a text summary.

| Param | Type | Default | Notes |
| --- | --- | --- | --- |
| `region` | string | `south_america` | One of `/health` → `regions` |

```json
{
  "region": "south_america",
  "summary": "337 aircraft detected over south_america.\n- GLO7177 at 4351.02 m\n- GLO1479 at 2804.16 m…",
  "source": "OpenSky (partial volunteer coverage)"
}
```

**`summary` is a newline-joined string, not structured data** — that is what `count_aircraft()` returns, because the agent uses the same function. For per-aircraft rows or map pins use `/aircraft/map`; do not parse this string.

---

## GET /aircraft/map

Aircraft over a region as objects with coordinates, for plotting pins.

| Param | Type | Default | Notes |
| --- | --- | --- | --- |
| `region` | string | `south_america` | One of `/health` → `regions` |

```json
{
  "region": "south_america",
  "count": 331,
  "bounds": { "lat_min": -56.0, "lat_max": 13.0, "lon_min": -82.0, "lon_max": -34.0 },
  "aircraft": [
    {
      "icao24": "e49eec",
      "callsign": "GLO7177",
      "country": "Brazil",
      "latitude": -22.8063,
      "longitude": -46.4351,
      "altitude_m": 3596.64,
      "on_ground": false,
      "velocity_ms": 161.54,
      "heading_deg": 142.77
    }
  ],
  "source": "OpenSky (partial volunteer coverage)"
}
```

| Field | Type | Notes |
| --- | --- | --- |
| `icao24` | string | Unique transponder address — use it as the identity key, not `callsign` |
| `callsign` | string \| null | Trimmed; `null` when the aircraft does not broadcast one |
| `country` | string | Registration country |
| `latitude` / `longitude` | number | Decimal degrees, WGS84 |
| `altitude_m` | number \| null | **Metres**, not feet. Barometric, falling back to geometric |
| `on_ground` | boolean | Always a real boolean |
| `velocity_ms` | number \| null | **Metres per second.** ×1.94384 for knots |
| `heading_deg` | number \| null | True track, 0–360 |

**Aircraft with no known position are dropped**, so `count` here can be lower than the count from `/aircraft`. Every returned aircraft has non-null `latitude` and `longitude`; the other numeric fields *can* be null — an aircraft may report position but not altitude.

**Units are metric**, straight from OpenSky. Convert for display and label the unit either way — silent unit mismatch is the same class of bug the METAR eval exists to catch.

**`bounds` is the region's bounding box** — use it for the initial viewport instead of hardcoding coordinates in the client.

**`world` returns everything OpenSky sees** — typically 10,000–13,000 aircraft and a few MB of JSON. Clients should plan for the size.

---

## POST /ask

Free-form question answered by the tool-calling agent. It picks its own tools (`get_metar`, `count_aircraft`) and answers in the language the question was asked in.

```json
{ "question": "O tempo está bom para pousar em Guarulhos?" }
```

`question` is required, 1–500 characters.

```json
{
  "question": "O tempo está bom para pousar em Guarulhos?",
  "answer": "O METAR de Guarulhos (SBGR) indica:\n\n- **Vento:** 310° a 3 kt…",
  "flagged": false
}
```

`question` echoes what the user typed, before guardrail processing. Errors: 422 invalid input, 502 the agent returned nothing, 503 upstream down.

### Guardrails over HTTP

User text passes through `check_question()` in `src/guardrails.py`; this router only translates the result into HTTP. Why injection attempts are neutralised rather than blocked is explained under *Input guardrails* in the [root README](../README.md#input-guardrails).

**Rejected with 422** — these never reach the model:

| `error` | Cause |
| --- | --- |
| `empty_question` | Empty, whitespace-only, or only invisible characters |
| `question_too_long` | Over 500 characters after normalisation |
| `invalid_request` | Pydantic-level failure (missing field, wrong type) |

**Flagged but answered** — when the text matches a known injection pattern ("ignore previous instructions", "you are now…", "reveal your system prompt", forged `system:` turns), the question is fenced as untrusted data, sent to the agent anyway, and `flagged: true` comes back. Every flagged request also writes a warning to the server log.

---

## CORS

Currently `allow_origins=["*"]` for local development, methods `GET` and `POST`. Before deploying anywhere public, narrow it to the real frontend origin in `main.py`.

## What the API relies on in `src/`

The API holds no business logic, so whatever it needed was added to `src/` instead:

- `tools.get_aircraft_for_region()` — fetches aircraft for a *named* region, reusing the `REGIONS` map rather than copying bounding boxes into the API.
- `tools.list_aircraft()` — state vectors as objects for `/aircraft/map`. OpenSky's positional arrays are mapped by named constants, because index 5 is longitude and index 6 is latitude — reversed from the `(lat, lon)` order most map libraries take, and a silent way to put Brazilian aircraft in the Indian Ocean.
- `guardrails.check_question()` — validates and neutralises user text for `/ask`.

`run_agent()` itself has no guardrails, so the protection applies to the API only; the CLI demo in `main.py` calls the agent directly.
