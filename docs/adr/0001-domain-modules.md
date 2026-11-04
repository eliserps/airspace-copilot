# 0001. Backend organised by domain, wired through a container

**Status:** Accepted

## Context

The first version split the backend into `api/` (FastAPI) and `src/` (logic). The split was right, but `src/` grew into modules that each did several jobs: `tools.py` held the OpenSky client, token cache, region boxes, snapshot cache and the LLM-facing text. State lived in module-level dicts, so tests had to clear private globals and monkeypatch functions by name.

## Decision

- One package per domain under `app/`: `traffic`, `briefing`, `weather`, `copilot`, plus `core` (config, errors, logging, cache, rate limiting) and `llm` (client protocol, tool registry).
- Each domain owns its `router.py`, `schemas.py` and service classes. Routers stay thin: validate, call a service, shape the response.
- Services are plain classes that receive their collaborators in the constructor. `app/container.py` builds the object graph once in the FastAPI lifespan; routers get services through `Depends`.
- External systems sit behind small `Protocol`s (`AircraftSource`, `MetarSource`, `KnowledgeSearch`, `LLMClient`).

## Consequences

- Tests build the same graph with fakes (`tests/fakes.py`) through `container.wire()`, without monkeypatching.
- Adding a domain means adding a folder and one line in the container.
- Full hexagonal architecture (ports/adapters for everything, separate domain entities) was considered and rejected as too heavy for a codebase of this size.
