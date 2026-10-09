"""The shared flat error shape, and the exception handlers that enforce it.

Every failure the API returns looks the same:

    {"error": "<stable_slug>", "message": "<human readable>", ...context}

`error` is a machine-readable slug the frontend branches on; `message` is for
humans. FastAPI nests errors under `detail` by default, which would give clients
two different shapes depending on whether the error came from us or from
validation. These handlers flatten that to one.
"""

import logging

import groq
import requests
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.llm import LLMNotConfigured

SOURCE_OPENSKY = "OpenSky (partial volunteer coverage)"
SOURCE_AWC = "Aviation Weather Center"

log = logging.getLogger("airspace.errors")


def error_detail(error: str, message: str, **context) -> dict:
    """Builds the body for an HTTPException detail.

    Keeping the shape in one function means a new endpoint cannot accidentally
    invent a different error format.
    """
    return {"error": error, "message": message, **context}


def unknown_region(region: str, allowed: list[str]) -> HTTPException:
    """404 for a region with no bounding box defined."""
    return HTTPException(
        status_code=404,
        detail=error_detail(
            "unknown_region", f"Unknown region '{region}'.", allowed=sorted(allowed)
        ),
    )


def invalid_language(allowed: tuple[str, ...]) -> HTTPException:
    """422 for an unsupported language code."""
    return HTTPException(
        status_code=422,
        detail=error_detail(
            "invalid_language",
            f"lang must be one of {list(allowed)}.",
            allowed=list(allowed),
        ),
    )


def register_error_handlers(app: FastAPI) -> None:
    """Attaches the handlers that flatten every error to the shared shape."""

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request, exc: StarletteHTTPException):
        if isinstance(exc.detail, dict):
            return JSONResponse(status_code=exc.status_code, content=exc.detail,
                                headers=exc.headers)
        slugs = {404: "not_found", 405: "method_not_allowed"}
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": slugs.get(exc.status_code, "http_error"),
                     "message": str(exc.detail)},
            headers=exc.headers,
        )

    @app.exception_handler(LLMNotConfigured)
    async def llm_not_configured_handler(request, exc: LLMNotConfigured):
        log.error("LLM call skipped: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"error": "llm_unavailable",
                     "message": "The AI model is not configured on this server."},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        loc = list(first.get("loc", []))
        if loc and loc[0] in ("body", "query", "path", "header", "cookie"):
            loc = loc[1:]
        field = ".".join(str(p) for p in loc)
        return JSONResponse(
            status_code=422,
            content={"error": "invalid_request",
                     "message": first.get("msg", "Invalid request."),
                     "field": field or None},
        )

    @app.exception_handler(requests.RequestException)
    async def upstream_error_handler(request, exc: requests.RequestException):
        """Upstream network failure becomes 503, never a 500 stack trace.

        OpenSky auth and state fetches call raise_for_status(), so they raise
        rather than returning None. Without this the client gets an opaque 500.
        """
        return JSONResponse(
            status_code=503,
            content={"error": "upstream_unavailable",
                     "message": "A data source is unavailable right now. "
                                "Try again shortly."},
        )

    @app.exception_handler(requests.HTTPError)
    async def upstream_http_error_handler(request, exc: requests.HTTPError):
        """Maps a 429 from OpenSky to its own slug, everything else to 503."""
        status = exc.response.status_code if exc.response is not None else None
        if status == 429:
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limited",
                         "message": "OpenSky's request limit for this account "
                                    "has been reached. Live positions resume "
                                    "once the quota resets."},
            )
        return JSONResponse(
            status_code=503,
            content={"error": "upstream_unavailable",
                     "message": "A data source is unavailable right now. "
                                "Try again shortly."},
        )

    @app.exception_handler(groq.RateLimitError)
    async def llm_rate_limited_handler(request, exc: groq.RateLimitError):
        """The language model's token/request quota ran out -- 429, not 500.

        The Groq SDK uses httpx, so these never reach the requests handlers
        above; without their own handlers they surface as opaque 500s.
        """
        log.warning("LLM rate limited: %s", exc)
        return JSONResponse(
            status_code=429,
            content={"error": "llm_rate_limited",
                     "message": "The AI model's usage limit has been reached. "
                                "Try again in a minute."},
        )

    @app.exception_handler(groq.APIError)
    async def llm_error_handler(request, exc: groq.APIError):
        """Any other model failure (timeout, outage, bad key) becomes 503.

        Logged at error level: an AuthenticationError here means GROQ_API_KEY
        is wrong, which only the operator can fix.
        """
        log.error("LLM call failed: %s: %s", type(exc).__name__, exc)
        return JSONResponse(
            status_code=503,
            content={"error": "llm_unavailable",
                     "message": "The AI model is unavailable right now. "
                                "Try again shortly."},
        )
