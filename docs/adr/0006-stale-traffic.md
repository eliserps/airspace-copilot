# 0006. Serve stale traffic while OpenSky is failing

**Status:** Accepted. Per-region caching is amended by [0009](0009-single-world-fetch.md).

## Context

OpenSky is a free, volunteer network with strict rate limits. It returns 429 with a retry-after header, and sometimes simply times out. An empty map is the worst possible answer during an outage.

## Decision

- Positions are cached per region for 30 s, shared by all users.
- On failure, the last good result is returned with `stale: true` if it is under 10 minutes old; older than that, the error goes to the client.
- After a failure, OpenSky is not called again for 15 s, or for the advertised retry-after time on a 429 (capped at one hour).

## Consequences

- Users see recent positions plus a "Stale" badge instead of an error.
- A 429 never turns into a retry storm against OpenSky.
- The copilot's `count_aircraft` tool states the data age when it answers from stale data.
