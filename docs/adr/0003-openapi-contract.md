# 0003. OpenAPI is the contract between backend and frontend

**Status:** Accepted

## Context

The frontend declared its own TypeScript copies of the API types. Renaming a field in a Pydantic model compiled fine on both sides and broke at runtime.

## Decision

- Pydantic response models are the single source of truth.
- `scripts/export_openapi.py` writes `frontend/openapi.json`; `openapi-typescript` turns it into `src/api/schema.gen.ts`; `openapi-fetch` gives a client typed by path, method and parameters.
- Both files are committed, so a pull request shows exactly how the contract changed.

## Consequences

- A breaking backend change becomes a TypeScript error in the frontend PR, not a production bug.
- Enums such as regions and languages flow to the UI from the backend definitions.
- The streaming endpoint is outside what OpenAPI describes well; its event types are documented in the router and parsed by hand in `src/api/copilot.ts`.
