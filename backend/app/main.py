from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.briefing.router import router as briefing_router
from app.container import Services, build_services
from app.copilot.router import router as copilot_router
from app.core.config import Settings, configure_tls, get_settings
from app.core.errors import register_error_handlers
from app.core.logging import RequestContextMiddleware, configure_logging
from app.health.router import router as health_router
from app.traffic.router import router as traffic_router
from app.weather.router import router as weather_router


def create_app(settings: Settings | None = None, services: Services | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.log_format)

    configure_tls(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if services is not None:
            app.state.services = services
            yield
            return
        built = build_services(settings)
        app.state.services = built
        try:
            yield
        finally:
            await built.aclose()

    app = FastAPI(
        title="airspace-copilot API",
        description="Live flight data and aviation weather, explained in natural language.",
        version="2.0.0",
        lifespan=lifespan,
    )
    if services is not None:
        app.state.services = services

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(RequestContextMiddleware)
    register_error_handlers(app)

    for router in (health_router, traffic_router, briefing_router, weather_router, copilot_router):
        app.include_router(router)
    return app


app = create_app()
