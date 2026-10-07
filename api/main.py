"""REST API for airspace-copilot.

A THIN wrapper over src/. Every endpoint calls an existing function and shapes the
result as JSON. No decoding, no agent logic, no bounding boxes, no guardrail rules
live here -- if a rule about aviation or the LLM is needed, it belongs in src/.

This file does app creation, CORS and router registration ONLY. Allowed origins
come from CORS_ORIGINS in .env (see src/config.py). Endpoints live in
api/routers/, grouped by domain.

Run:  uvicorn api.main:app --reload --port 8000
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from config import CORS_ORIGINS  # noqa: E402
from tools import REGIONS  # noqa: E402

from .errors import register_error_handlers  # noqa: E402
from .routers import aircraft, agent, briefing, weather  # noqa: E402
from .schemas import LANGUAGES, HealthResponse  # noqa: E402

app = FastAPI(
    title="airspace-copilot API",
    description="Live flight data and aviation weather, explained in natural language.",
    version="1.1.0",
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
def health():
    """Liveness check. Does not touch upstream services, so it stays fast."""
    return {"status": "ok", "regions": sorted(REGIONS), "languages": list(LANGUAGES)}
