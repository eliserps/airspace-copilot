# Frontend

React + TypeScript web UI for airspace-copilot: a 3D globe with live aircraft, the copilot chat, regional briefings and decoded METAR weather. Project overview and backend setup are in the [root README](../README.md); the endpoint contract is in [api/README.md](../api/README.md).

This app is a **thin rendering layer** — no database, no auth, no business logic, no credentials. Everything it shows comes from the API.

## Running

With the API already running on port 8000:

    cd frontend
    npm install
    npm run dev

The app opens at http://localhost:8080 (set in `vite.config.ts`).

| Command | What it does |
| --- | --- |
| `npm run dev` | Development server with hot reload |
| `npm run build` | Production build |
| `npm run lint` | ESLint + Prettier check |
| `npm run format` | Prettier, writing fixes |

## Configuration

The only setting is the API address:

| Variable | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Base URL of the FastAPI backend, no trailing slash |

Put `VITE_API_BASE_URL=http://localhost:8000` in `frontend/.env.local` for local work. Both `.env` and `.env.local` are gitignored; with neither, `src/config.ts` falls back to the deployed API on Render.

**Never give a `VITE_` variable a secret.** Vite inlines every `VITE_`-prefixed value into the bundle the browser downloads, so that prefix is a publication mechanism, not a convention.

## Structure

| Path | Responsibility |
| --- | --- |
| `src/config.ts` | API address, region list (centre, zoom, default airport) and display limits |
| `src/lib/api.ts` | The only module that calls `fetch`: request helper, typed responses, `ApiError` |
| `src/lib/units.ts` | Metric → feet and knots, with unit labels |
| `src/lib/markers.ts` | Plane icon, altitude bands and globe sampling |
| `src/lib/sun.ts` | Subsolar point, so the globe's day/night lighting matches the real time |
| `src/lib/i18n*.ts(x)` | Translations — see *Internationalisation* |
| `src/routes/index.tsx` | The single page: header, globe, tabs, traffic polling |
| `src/components/` | One component per panel (`GlobeView`, `ChatPanel`, `TrafficList`, `BriefingPanel`, `WeatherCard`, `AircraftDetail`…) |
| `src/server.ts`, `src/start.ts` | SSR entry and request middleware: a plain error page on failures, CSRF protection for server functions |

Routing is file-based (TanStack Start): each file in `src/routes/` is a route, `__root.tsx` is the app shell, and `routeTree.gen.ts` is generated — never edit it by hand.

**Production build.** `npm run build` targets Cloudflare Workers through Nitro (`defaultPreset` in `vite.config.ts`); change the preset there to deploy elsewhere, e.g. `node-server`.

## Talking to the API

Components call `api.*` from `src/lib/api.ts` through TanStack Query and never build a URL themselves. Errors arrive as `ApiError`, whose `.code` is the API's stable error slug, so the UI branches on the cause rather than on message text.

How the UI honours the contract:

- **Units** — `altitude_m` and `velocity_ms` are converted by `units.ts`; every rendered value carries its unit.
- **Identity** — `icao24` is the React key; `callsign` is nullable and not unique.
- **Heading** — `heading_deg` drives a CSS `rotate()`, so each marker points where it is flying.
- **Markdown** — `briefing`, `decoded` and `answer` go through `<Markdown>`, never raw.
- **Guardrails** — `flagged: true` on `/ask` shows a badge on the answer rather than hiding it.
- **Coverage** — `source` is displayed, so the partial OpenSky coverage is never presented as complete.

## The four tabs

Each maps to a distinct backend capability, not to a different view of the same data:

- **Copilot** — free-form questions to the agent (`/ask`).
- **Traffic** — the live aircraft behind the globe, as a list (first 300 rows when a region has more).
- **Briefing** — region, tracked count and update time in a stat header, then the generated narrative (`/briefing`).
- **Weather** — the raw METAR in a compact strip above its decoding (`/weather/{icao}`); the airport defaults to one per region.

## The globe

Marker colour comes from `altitudeBand()` in `markers.ts`:

| Colour | Meaning |
| --- | --- |
| Yellow | Below FL100, or no altitude reported |
| Orange | FL100–FL300 |
| Violet | Above FL300 |
| Grey | On the ground |
| Gold, enlarged | Selected |

Each marker is a DOM element, so past `MAX_GLOBE_MARKERS` (1,500) the globe draws a sample from `sampleSpread()`: one aircraft per 5°×5° cell per round. Sparse areas — oceans, Africa — keep every aircraft and only dense ones are thinned; a plain every-Nth sample would erase the few oceanic aircraft first. The header counter always shows the real total, and the legend says when the map is sampled.

## Data freshness

The backend caches LLM output (see *Token budget* in the [root README](../README.md#token-budget)); the query settings here are aligned so the UI does not ask for what cannot have changed:

| Data | Refresh |
| --- | --- |
| Live traffic | Every 60 s while **Live** is on; never calls the model |
| Briefing | Fresh for 5 minutes |
| Weather | Fresh for 15 minutes |
| Any query | Never refetched just because the window regained focus |

## Internationalisation

`src/lib/i18n-strings.ts` holds the string tables (pure data), `src/lib/i18n-context.ts` the context and `useI18n` hook, and `src/lib/i18n.tsx` only the provider component. The split keeps React Fast Refresh working — a file that exports both a component and a hook breaks hot reload.

The header switch sets the locale, persists it to `localStorage` and passes `lang` to the API, so briefing and METAR text come back translated too, not just the chrome.
