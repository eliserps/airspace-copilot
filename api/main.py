"""REST API for airspace-copilot.

A THIN wrapper over src/. Every endpoint calls an existing function and shapes the
result as JSON. No decoding, no agent logic, no bounding boxes, no guardrail rules
live here -- if a rule about aviation or the LLM is needed, it belongs in src/.

This file does app creation, CORS and router registration ONLY. Allowed origins
come from CORS_ORIGINS in .env (see src/config.py). Endpoints live in
api/routers/, grouped by domain.

Run:  uvicorn api.main:app --reload --port 8000
"""

import logging
import threading
from contextlib import asynccontextmanager

import anyio.to_thread
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import CORS_ORIGINS, WORKER_THREADS
from src.rag import warm_up
from src.tools import REGIONS

from .errors import register_error_handlers
from .routers import aircraft, agent, briefing, weather
from .schemas import LANGUAGES, HealthResponse

log = logging.getLogger("airspace.startup")


def _warm_up_rag() -> None:
    try:
        warm_up()
    except Exception:  # noqa: BLE001
        log.exception("RAG warm-up failed; it will be retried on the first METAR request")


@asynccontextmanager
async def lifespan(app: FastAPI):
    anyio.to_thread.current_default_thread_limiter().total_tokens = WORKER_THREADS
    threading.Thread(target=_warm_up_rag, name="rag-warm-up", daemon=True).start()
    yield


app = FastAPI(
    title="airspace-copilot API",
    description="Live flight data and aviation weather, explained in natural language.",
    version="1.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

register_error_handlers(app)

app.include_router(briefing.router)
app.include_router(weather.router)
app.include_router(aircraft.router)
app.include_router(agent.router)


@app.get("/health", tags=["meta"], response_model=HealthResponse)
async def health():
    """Liveness check. Does not touch upstream services, so it stays fast."""
    return {"status": "ok", "regions": sorted(REGIONS), "languages": list(LANGUAGES)}
