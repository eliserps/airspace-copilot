from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core import metrics
from app.core.config import LANGUAGE_NAMES
from app.dependencies import ServicesDep
from app.traffic.regions import REGION_IDS

router = APIRouter(tags=["meta"])


class HealthResponse(BaseModel):
    status: str
    regions: list[str] = Field(description="Valid values for the `region` parameter.")
    languages: list[str] = Field(description="Valid values for the `lang` parameter.")


class ReadinessResponse(BaseModel):
    status: str = Field(description="`ready`, or `starting` while a check is still failing.")
    checks: dict[str, bool]


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness check; does not call upstream services."""
    return HealthResponse(status="ok", regions=sorted(REGION_IDS), languages=list(LANGUAGE_NAMES))


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ReadinessResponse}},
    description="Readiness check: the knowledge base is loaded and the AI model is configured.",
)
async def ready(services: ServicesDep) -> JSONResponse:
    checks = {
        "knowledge_base": services.knowledge is None or services.knowledge.ready,
        "llm_configured": services.llm.configured,
    }
    body = ReadinessResponse(status="ready" if all(checks.values()) else "starting", checks=checks)
    return JSONResponse(body.model_dump(), status_code=200 if body.status == "ready" else 503)


@router.get("/metrics", include_in_schema=False)
async def prometheus_metrics() -> Response:
    payload, content_type = metrics.render()
    return Response(payload, media_type=content_type)
