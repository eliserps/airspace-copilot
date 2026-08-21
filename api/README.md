# API

Thin REST wrapper over `src/`. Every endpoint calls an existing function and shapes
the result as JSON — no decoding rules, no agent loop, no bounding boxes, no
guardrail patterns live here.

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

Split by **domain**, not by layer: everything about weather is in one file, so a
change to that endpoint touches one place. `errors.py` and `schemas.py` are the
deliberate exceptions — they hold what all routers must agree on, and duplicating
either would let the shapes drift apart.

`main.py` sets up `sys.path` for `src/` **before** importing routers, since the
routers import from there. That ordering is load-bearing.

## Running

From the project root, with the venv active:

```
uvicorn api.main:app --reload --port 8000
```

- Interactive docs: <http://127.0.0.1:8000/docs>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>

`--reload` restarts on file changes; drop it in production.

## Conventions

**Every error has the same flat shape**, whatever the cause:

```json
{ "error": "unknown_region", "message": "Unknown region 'narnia'.", "allowed": ["brazil", "..."] }
```

`error` is a stable machine-readable slug — branch on it. `message` is
human-readable. Some errors add a context key (`allowed`, `icao`, `field`).
FastAPI's default nests errors under `detail`; that is flattened deliberately so the
frontend needs one error branch, not two.

**Status codes**

| Code | Meaning |
|---|---|
| 200 | OK |
| 404 | Not found — unknown region, or no METAR for that airport |
| 422 | Invalid request — bad `lang`, malformed ICAO, empty question |
| 502 | The agent produced no answer |
| 503 | An upstream data source (OpenSky) is unavailable |

**LLM endpoints are slow.** `/briefing`, `/weather/{icao}` and `/ask` call the model;
`/ask` may run several tool-calling rounds. Budget ~2–10s and show a loading state.
`/health`, `/aircraft` and `/aircraft/map` do not call the model.

**Free text is Markdown.** `briefing`, `decoded` and `answer` come back as Markdown
(tables, bold, bullets) — render it with something like `react-markdown` rather than
dropping it into a `<div>` raw.

---

## GET /health

Liveness check. Touches no upstream service, so it is fast and safe to poll. Use it
to populate region and language pickers instead of hardcoding them.

```json
{
  "status": "ok",
  "regions": ["brasilia", "brazil", "porto_alegre", "rio_de_janeiro", "sao_paulo"],
  "languages": ["en", "pt"]
}
```

---

## GET /briefing

Natural-language briefing of current traffic over a region.

| Param | Type | Default | Notes |
|---|---|---|---|
| `region` | string | `brazil` | One of `/health` → `regions` |
| `lang` | string | `en` | `en` or `pt` |

```json
{
  "region": "rio_de_janeiro",
  "language": "pt",
  "aircraft_count": 10,
  "briefing": "**Resumo do espaço aéreo — Rio de Janeiro**\n\n- Foram detectadas **10 aeronaves**…",
  "source": "OpenSky (partial volunteer coverage)"
}
```

`aircraft_count` is the real count from OpenSky, not parsed out of the text — use it
for a counter widget and let `briefing` be the prose. Errors: 404 unknown region,
422 bad `lang`, 503 OpenSky down.

---

## GET /weather/{icao}

Raw METAR plus a plain-language decoding for one airport.

| Param | Type | Default | Notes |
|---|---|---|---|
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

Show `raw` in monospace next to the decoding — the point of the product is that the
user can see the source text and the explanation side by side.

**404 `no_metar`** covers both "this airport has no report" and "the weather service
failed". `get_metar()` returns `None` for both and cannot distinguish them, so the
API does not pretend to either. Word the UI accordingly: "no report available right
now", not "invalid airport".

---

## GET /aircraft

Aircraft currently detected over a region, as a text summary. Does **not** call the
LLM, so it is the fast one.

| Param | Type | Default | Notes |
|---|---|---|---|
| `region` | string | `brazil` | One of `/health` → `regions` |

```json
{
  "region": "sao_paulo",
  "summary": "60 aircraft detected over sao_paulo.\n- GLO7177 at 4351.02 m\n- GLO1479 at 2804.16 m…",
  "source": "OpenSky (partial volunteer coverage)"
}
```

**`summary` is a newline-joined string, not structured data** — that is what
`count_aircraft()` returns. For per-aircraft rows or map pins use
`/aircraft/map` below; do not parse this string.

---

## GET /aircraft/map

Aircraft over a region as objects with coordinates, for plotting pins. No LLM call.

| Param | Type | Default | Notes |
|---|---|---|---|
| `region` | string | `brazil` | One of `/health` → `regions` |

```json
{
  "region": "sao_paulo",
  "count": 55,
  "bounds": { "lat_min": -24.5, "lat_max": -22.5, "lon_min": -48.0, "lon_max": -45.5 },
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
|---|---|---|
| `icao24` | string | Unique transponder address — **use this as the React `key`**, not `callsign` |
| `callsign` | string \| null | Trimmed; `null` when the aircraft does not broadcast one |
| `country` | string | Registration country |
| `latitude` / `longitude` | number | Decimal degrees, WGS84 |
| `altitude_m` | number \| null | **Metres**, not feet. Barometric, falling back to geometric |
| `on_ground` | boolean | Always a real boolean |
| `velocity_ms` | number \| null | **Metres per second.** ×1.94384 for knots |
| `heading_deg` | number \| null | True track, 0–360. Feed straight into a CSS `rotate()` for the pin |

**`bounds` is the region's bounding box** — use it to set the initial map viewport
instead of hardcoding coordinates in React.

**Aircraft with no known position are dropped**, so `count` here can be lower than
the count from `/aircraft`. Every returned aircraft is guaranteed to have non-null
`latitude` and `longitude`, so pins never need a null check. The other numeric
fields *can* be null — an aircraft may report position but not altitude.

**`altitude_m` and `velocity_ms` are metric**, straight from OpenSky. Aviation UIs
normally display feet and knots; convert in the frontend, and label the unit either
way. Silent unit mismatch is the same class of bug the METAR eval exists to catch.

---

## POST /ask

Free-form question answered by the tool-calling agent. It picks its own tools
(`get_metar`, `count_aircraft`) and answers in the language the question was asked
in.

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

`question` echoes what the user typed, before guardrail processing. The slowest
endpoint — several model round-trips. Errors: 422 invalid input, 502 the agent
returned nothing, 503 upstream down.

### Input guardrails

User text passes through `check_question()` in `src/guardrails.py` before reaching
the agent. The API only translates the result into HTTP; the rules live in `src/`.

**Rejected with 422** — these never reach the model:

| `error` | Cause |
|---|---|
| `empty_question` | Empty, whitespace-only, or only invisible characters |
| `question_too_long` | Over 500 characters after normalisation |
| `invalid_request` | Pydantic-level failure (missing field, wrong type) |

**Flagged but answered** — when the text matches a known injection pattern
("ignore previous instructions", "you are now…", "reveal your system prompt", forged
`system:` turns), the question is **not** rejected. It is fenced in an explicit
untrusted-data marker, sent to the agent anyway, and `flagged: true` comes back.

Neutralising rather than blocking is deliberate: the patterns have false positives,
and a pilot asking *"ignore the previous METAR, what's the current one?"* is not
attacking anything. Rejecting outright would break real questions to stop attacks
the architecture already contains.

`flagged` is there if you want to surface it in the UI, but it is mostly for
logging — every flagged request writes a warning to the server log.

**Honest limits.** Pattern matching is weak defense: any blocklist can be rephrased
around. The real containment is architectural — the agent has two read-only tools
with enum-constrained arguments, no shell, no database, no secrets in context. A
successful injection can make the model say something silly; it cannot make it *do*
anything outside those two calls. The rationale is written out at the top of
`src/guardrails.py`.

---

## CORS

Currently `allow_origins=["*"]` for local development, methods `GET` and `POST`.
Verified against a Vite origin (`http://localhost:5173`). Before deploying anywhere
public, narrow it to the real frontend origin in `api/main.py`.

## Changes in `src/`

The API holds no business logic, so anything it needed was added to `src/tools.py`:

- `get_aircraft_for_region()` and `is_known_region()` — `/briefing` needed aircraft
  for a *named* region, but `generate_briefing()` takes an already-fetched list and
  `main.py` did that fetching inline with hardcoded coordinates. These reuse the
  existing `REGIONS` map rather than copying bounding boxes into the API.
- `list_aircraft()` — returns state vectors as objects for `/aircraft/map`. The
  index-to-name mapping for OpenSky's positional arrays lives here as named
  constants, because index 5 is longitude and index 6 is latitude — reversed from
  the `(lat, lon)` order most map libraries take, and a silent way to put Brazilian
  aircraft in the Indian Ocean.
- `src/guardrails.py` (new module) — `check_question()` validates and neutralises
  user text for `/ask`. Patterns, normalisation and the untrusted-data fence all
  live there.

`count_aircraft()` is unchanged and still returns its string. `run_agent()` is
unchanged too — the CLI path in `main.py` calls it directly, without guardrails,
which is fine for a local terminal but means the protection is API-only.
