from dataclasses import dataclass

import httpx

from app.briefing.service import BriefingService
from app.copilot.agent import Agent
from app.copilot.tools import build_tools
from app.core.config import Settings
from app.core.ratelimit import RateLimiter
from app.llm.client import GroqClient, LLMClient
from app.traffic.opensky import AircraftSource, OpenSkyClient
from app.traffic.service import TrafficService
from app.weather.decoder import MetarDecoder
from app.weather.knowledge import ReferenceDoc, load_reference
from app.weather.metar import AviationWeatherClient, MetarSource

HTTP_TIMEOUT = httpx.Timeout(30, connect=5)


@dataclass
class Services:
    llm: LLMClient
    traffic: TrafficService
    briefing: BriefingService
    metar: MetarSource
    decoder: MetarDecoder
    agent: Agent
    ask_limiter: RateLimiter
    weather_limiter: RateLimiter
    http: httpx.AsyncClient | None = None

    async def aclose(self) -> None:
        if self.http is not None:
            await self.http.aclose()


def wire(
    settings: Settings,
    *,
    llm: LLMClient,
    aircraft: AircraftSource,
    metar: MetarSource,
    reference: list[ReferenceDoc],
) -> Services:
    traffic = TrafficService(aircraft)
    return Services(
        llm=llm,
        traffic=traffic,
        briefing=BriefingService(llm),
        metar=metar,
        decoder=MetarDecoder(llm, reference),
        agent=Agent(llm, build_tools(traffic, metar)),
        ask_limiter=RateLimiter("ask", settings.ask_rate_limit_per_minute),
        weather_limiter=RateLimiter("weather", settings.weather_rate_limit_per_minute),
    )


def build_services(settings: Settings) -> Services:
    http = httpx.AsyncClient(timeout=HTTP_TIMEOUT)
    services = wire(
        settings,
        llm=GroqClient(settings.groq_api_key, settings.llm_model, settings.llm_timeout_seconds),
        aircraft=OpenSkyClient(http, settings.opensky_client_id, settings.opensky_client_secret),
        metar=AviationWeatherClient(http),
        reference=load_reference(settings.knowledge_dir),
    )
    services.http = http
    return services
