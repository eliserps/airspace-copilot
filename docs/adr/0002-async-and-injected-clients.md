# 0002. Async I/O with injected clients

**Status:** Accepted. The ChromaDB part is superseded by [0008](0008-reference-in-prompt.md).

## Context

Every endpoint waits on the network: OpenSky, aviationweather.gov and Groq. The sync version ran handlers in Starlette's thread pool and needed `WORKER_THREADS=100` so slow LLM calls would not starve the others.

## Decision

- Handlers and services are `async`. HTTP goes through one shared `httpx.AsyncClient` (connection pooling, timeouts in one place); the LLM goes through `AsyncGroq`.
- Per-key `asyncio.Lock`s replace thread locks, so concurrent requests for the same region still result in a single OpenSky call.
- ChromaDB has no async API, so knowledge-base queries run in a worker thread via `anyio.to_thread`.

## Consequences

- No thread-count tuning; concurrency is bounded by upstream latency, not by threads.
- Code that blocks the event loop is a bug. Ruff's `ASYNC` rules catch the common cases.
- The in-memory caches and rate limiter assume a single process. Scaling out would need a shared store (e.g. Redis).
