from typing import Annotated, cast

from fastapi import Depends, Request

from app.briefing.service import BriefingService
from app.container import Services
from app.copilot.agent import Agent
from app.traffic.service import TrafficService
from app.weather.decoder import MetarDecoder
from app.weather.metar import MetarSource


def get_services(request: Request) -> Services:
    return cast(Services, request.app.state.services)


ServicesDep = Annotated[Services, Depends(get_services)]


def get_traffic(services: ServicesDep) -> TrafficService:
    return services.traffic


def get_briefing(services: ServicesDep) -> BriefingService:
    return services.briefing


def get_metar(services: ServicesDep) -> MetarSource:
    return services.metar


def get_decoder(services: ServicesDep) -> MetarDecoder:
    return services.decoder


def get_agent(services: ServicesDep) -> Agent:
    return services.agent


def limit_ask(request: Request, services: ServicesDep) -> None:
    services.ask_limiter(request)


def limit_weather(request: Request, services: ServicesDep) -> None:
    services.weather_limiter(request)


TrafficDep = Annotated[TrafficService, Depends(get_traffic)]
BriefingDep = Annotated[BriefingService, Depends(get_briefing)]
MetarDep = Annotated[MetarSource, Depends(get_metar)]
DecoderDep = Annotated[MetarDecoder, Depends(get_decoder)]
AgentDep = Annotated[Agent, Depends(get_agent)]
