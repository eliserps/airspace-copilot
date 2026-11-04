import logging
from typing import Any

import groq
import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str, *, code: str | None = None, **context: Any):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.context = context

    def body(self) -> dict[str, Any]:
        return {"error": self.code, "message": self.message, **self.context}


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class InvalidInputError(AppError):
    status_code = 422
    code = "invalid_request"


class TooManyRequestsError(AppError):
    status_code = 429
    code = "too_many_requests"


class UpstreamUnavailableError(AppError):
    status_code = 503
    code = "upstream_unavailable"


class LLMNotConfiguredError(AppError):
    status_code = 503
    code = "llm_unavailable"


UPSTREAM_DOWN = "A data source is unavailable right now. Try again shortly."


def error_response(exc: Exception) -> tuple[int, dict[str, Any]]:
    if isinstance(exc, AppError):
        if exc.status_code >= 500:
            log.error("%s: %s", exc.code, exc.message)
        return exc.status_code, exc.body()
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
        return 429, {
            "error": "rate_limited",
            "message": "OpenSky's request limit for this account has been reached. "
            "Live positions resume once the quota resets.",
        }
    if isinstance(exc, httpx.HTTPError):
        log.warning("upstream failure: %s", exc)
        return 503, {"error": "upstream_unavailable", "message": UPSTREAM_DOWN}
    if isinstance(exc, groq.RateLimitError):
        log.warning("LLM rate limited: %s", exc)
        return 429, {
            "error": "llm_rate_limited",
            "message": "The AI model's usage limit has been reached. Try again in a minute.",
        }
    if isinstance(exc, groq.APIError):
        log.error("LLM call failed: %s: %s", type(exc).__name__, exc)
        return 503, {
            "error": "llm_unavailable",
            "message": "The AI model is unavailable right now. Try again shortly.",
        }
    log.exception("unhandled error", exc_info=exc)
    return 500, {"error": "internal_error", "message": "Something went wrong."}


def register_error_handlers(app: FastAPI) -> None:
    async def handle(request: Request, exc: Exception) -> JSONResponse:
        status, body = error_response(exc)
        headers = getattr(exc, "headers", None)
        return JSONResponse(status_code=status, content=body, headers=headers)

    async def handle_http(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, StarletteHTTPException)
        slugs = {404: "not_found", 405: "method_not_allowed"}
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": slugs.get(exc.status_code, "http_error"), "message": str(exc.detail)},
            headers=exc.headers,
        )

    async def handle_validation(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, RequestValidationError)
        first = exc.errors()[0] if exc.errors() else {}
        loc = list(first.get("loc", []))
        if loc and loc[0] in ("body", "query", "path", "header", "cookie"):
            loc = loc[1:]
        field = ".".join(str(p) for p in loc)
        return JSONResponse(
            status_code=422,
            content={
                "error": "invalid_request",
                "message": first.get("msg", "Invalid request."),
                "field": field or None,
            },
        )

    app.add_exception_handler(StarletteHTTPException, handle_http)
    app.add_exception_handler(RequestValidationError, handle_validation)
    for exc_type in (AppError, httpx.HTTPError, groq.APIError):
        app.add_exception_handler(exc_type, handle)
