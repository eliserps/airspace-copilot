# Airspace Copilot — frontend

React + TypeScript + Tailwind UI for **airspace-copilot**: a 3D globe with live
aircraft, an AI copilot chat, regional briefings and decoded METAR weather.

This app is a **thin rendering layer**. It has no database, no auth and no
business logic — all of that lives in the FastAPI backend in [`../api`](../api)
and the Python modules in [`../src`](../src). Every network call goes through one
service file, [`src/lib/api.ts`](src/lib/api.ts), pointed at a single base URL.

## Secrets

The frontend holds **no API keys**. `GROQ_API_KEY`, `OPENSKY_CLIENT_ID` and
`OPENSKY_CLIENT_SECRET` belong to the backend only (repo-root `.env`, read by
`src/config.py`). The browser talks to our API; our API talks to Groq and OpenSky.

The only variable this app needs is the API address:

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Base URL of the FastAPI backend, no trailing slash |

Vite inlines every `VITE_`-prefixed variable into the bundle the browser
downloads, so that prefix is a publication mechanism, not a convention. Only ever
give it to a value you would put on a billboard. Never to a key.

`.env` holds the deployed URL and is committed; `.env.local` holds
`http://localhost:8000` for local work and is gitignored. Vite prefers
`.env.local`.

## Running it locally

Two terminals, from the repo root:

```sh
# 1. backend (needs the root .env and an activated venv)
uvicorn api.main:app --reload --port 8000

# 2. frontend
cd frontend
npm install
npm run dev
```

Vite prints the local URL when it starts. CORS is open in `api/main.py` for local
development — restrict it to the real origin before deploying.

`npm run build` produces a production build; `npm run lint` runs ESLint and
Prettier.

## How it connects to the backend

`src/config.ts` reads `VITE_API_BASE_URL` and exports `API_BASE_URL`.
`src/lib/api.ts` is the only module that calls `fetch`; it owns the request
helper, the typed response shapes and `ApiError`. Components call `api.*` through
TanStack Query and never build a URL themselves.

`GET /health` is the source of truth for valid `region` and `lang` values, and
`/docs` on the running backend serves the full OpenAPI schema.

| Endpoint | Returns |
|---|---|
| `GET /aircraft/map?region=` | `{ region, count, bounds, aircraft[], source }` |
| `GET /aircraft?region=` | `{ region, summary, source }` — text, not structured |
| `GET /briefing?region=&lang=` | `{ region, language, aircraft_count, briefing, source }` |
| `GET /weather/{icao}?lang=` | `{ icao, language, raw, decoded, source }` |
| `POST /ask` `{ question }` | `{ question, answer, flagged }` |

Errors always arrive as `{ error, message }`, where `error` is a stable slug;
`ApiError` surfaces it as `.code` so the UI can branch on the cause rather than
on message text.

### Contract notes that matter

- `altitude_m` and `velocity_ms` are **metric**. `src/lib/units.ts` converts to
  feet and knots and every rendered value carries its unit label.
- `icao24` is the React key — `callsign` is nullable and not unique.
- `heading_deg` drives a CSS `rotate()` so each marker points where it is flying.
- `briefing`, `decoded` and `answer` are markdown — rendered with `<Markdown>`,
  never as raw text.
- `flagged: true` on `/ask` means the input guardrail fired; the chat shows a
  badge rather than hiding it.
- `source` is displayed in the UI. OpenSky's coverage is partial and volunteer-fed,
  and the interface says so instead of presenting the data as complete.

## The four tabs

Each maps to a distinct backend capability, not to a different view of the same
data:

- **Copilot** — free-form questions through the tool-calling agent (`POST /ask`).
- **Traffic** — the live state vectors behind the globe, as a sortable list.
- **Briefing** — a structured regional summary: region, tracked count and update
  time in a stat header, then the generated narrative.
- **Weather** — raw METAR beside its RAG-assisted decoding.

## Internationalisation

`src/lib/i18n-strings.ts` holds the string tables (pure data),
`src/lib/i18n-context.ts` the context and `useI18n` hook, and `src/lib/i18n.tsx`
only the provider component. The split keeps React Fast Refresh working — a file
that exports both a component and a hook breaks hot reload.

The header switch sets the locale, persists it to `localStorage` and passes
`lang` to the API, so briefing and METAR text come back translated too, not just
the chrome.
