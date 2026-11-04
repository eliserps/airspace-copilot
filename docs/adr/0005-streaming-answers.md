# 0005. Copilot answers stream over Server-Sent Events

**Status:** Accepted

## Context

A copilot answer can take several seconds: one or more tool rounds, then the final text. With a single JSON response the user stares at a spinner for the whole time.

## Decision

- `POST /ask/stream` returns `text/event-stream` with `meta` (guardrail flag), `delta` (text chunks), then `done` or `error`.
- The agent loop streams every model call. Text deltas go straight to the client; tool calls are accumulated from deltas and executed between rounds.
- `POST /ask` keeps the non-streaming JSON answer for scripts and simple clients.
- The browser uses `fetch` plus a small SSE parser, because `EventSource` cannot send a POST body.

## Consequences

- First text appears as soon as the model starts writing.
- Errors after the stream starts cannot change the HTTP status, so they arrive as an `error` event with the same `{error, message}` body as normal errors.
- Proxies must not buffer the response; the endpoint sends `X-Accel-Buffering: no`.
