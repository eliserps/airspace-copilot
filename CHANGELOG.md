# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/). Versions follow the API version in `backend/pyproject.toml`.

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
