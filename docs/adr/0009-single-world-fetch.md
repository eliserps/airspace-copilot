# 0009. Fetch the whole world once and filter regions locally

**Status:** Accepted. Amends the caching rule in [0006](0006-stale-traffic.md).

## Context

Traffic was cached per region, so each of the seven regions made its own OpenSky call. Every region is large enough to be billed at OpenSky's highest credit cost per request, the same as the whole world. With users spread across regions, the daily credit quota went up to seven times faster than necessary.

## Decision

- `TrafficService` makes one `states/all` call for the whole world, cached for 30 s.
- Each region is served by filtering that snapshot with the region's bounding box.
- Backoff and stale data apply to the single world snapshot, as described in 0006.

## Consequences

- At most one OpenSky call every 30 s, whatever region users are looking at.
- All regions share the same `fetched_at` and `stale` state.
- Aircraft without a position are only counted in `world`, where OpenSky's own bounding-box filter used to drop them from regional queries anyway.
