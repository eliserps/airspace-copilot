# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/). Versions follow the API version in `backend/pyproject.toml`.

## [Unreleased]

### Added
- Copilot follow-ups keep context: `POST /ask` and `/ask/stream` accept an optional `history` of earlier turns.
- GitHub Actions CI: lint, types, tests and build for both sides, plus an OpenAPI drift check.
- `count_aircraft_near` copilot tool: traffic within a radius of a city, airport or any place, closest aircraft first.
- `tool` event on `/ask/stream`; the chat shows which live data the copilot is checking.
- `stale` on `/briefing`, shown as a badge in the Briefing tab.
- `opensky_access` on `/health/ready`.

### Changed
- One OpenSky call for the whole world every 30 s, filtered per region, instead of one call per region.
- The METAR decoder sends the whole reference in the prompt instead of retrieving chunks.
- `/health/ready` only checks that the AI model is configured.
- OpenSky credentials are optional; without them the API is called anonymously.
- OpenSky tokens are renewed from the `expires_in` the server returns instead of a fixed 25 minutes.
- Briefings are reused for at most 15 minutes, and `aircraft_count` is always the current count.

### Removed
- ChromaDB and the knowledge-base warm-up.

### Fixed
- Flaky frontend test that read the page before the lazily loaded route had rendered.
- Aircraft markers drawn above the aircraft detail card and other globe overlays.
- Text the model wrote before a tool call ran straight into the final answer; steps are now separated.
- Concurrent requests for the same METAR each called the model; they now share one call.
- Briefings written from stale traffic did not say so.

## [2.0.0] - 2026-11-04

### Added
- Copilot answers stream token by token (`POST /ask/stream`, Server-Sent Events).
- Region, tab and selected aircraft are kept in the URL, so links can be shared.
- `/health/ready` readiness check and Prometheus metrics at `/metrics` (requests, LLM tokens and latency, cache hits, upstream errors).
- `X-Request-ID` on every response and log line; JSON logs with `LOG_FORMAT=json`.
- Agent tool-selection eval.
- Error messages translated in the UI by error code.
- Frontend tests (Vitest, Testing Library, MSW), Playwright end-to-end tests and an axe accessibility audit.

### Changed
- Backend reorganised by domain (`app/traffic`, `briefing`, `weather`, `copilot`) with injected services; fully async.
- Frontend is a static SPA organised by screen area, with API types generated from the backend's OpenAPI.
- Dependencies managed with uv (`pyproject.toml` + `uv.lock`).

### Removed
- `WORKER_THREADS` setting, no longer needed with async I/O.
- Server-side rendering and the Cloudflare Worker build.
- `requirements.txt`, replaced by `pyproject.toml` + `uv.lock`.

## [1.2.0]

- Per-client rate limiting for endpoints that spend LLM tokens.
- Flat error contract and upstream error mapping.
