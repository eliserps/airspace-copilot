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
        log.warning("LLM rate limited: %s", exc)
        return JSONResponse(
            status_code=429,
            content={"error": "llm_rate_limited",
                     "message": "The AI model's usage limit has been reached. "
                                "Try again in a minute."},
        )

    @app.exception_handler(groq.APIError)
    async def llm_error_handler(request, exc: groq.APIError):
        log.error("LLM call failed: %s: %s", type(exc).__name__, exc)
        return JSONResponse(
            status_code=503,
            content={"error": "llm_unavailable",
                     "message": "The AI model is unavailable right now. "
                                "Try again shortly."},
        )
