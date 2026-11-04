from pydantic import BaseModel, Field, field_validator

from app.llm.tools import Tool, ToolRegistry
from app.traffic.regions import RegionId, normalise_region
from app.traffic.service import TrafficService
from app.weather.metar import InvalidIcaoError, MetarSource


class GetMetarArgs(BaseModel):
    icao_code: str = Field(
        description="The 4-letter ICAO airport code, e.g. SBGR for Guarulhos, "
        "SBGL for Galeao, SBPA for Porto Alegre."
    )


class CountAircraftArgs(BaseModel):
    region: RegionId = Field(description="The region to check.")

    @field_validator("region", mode="before")
    @classmethod
    def lower(cls, value: object) -> object:
        return normalise_region(value) if isinstance(value, str) else value


def build_tools(traffic: TrafficService, metar: MetarSource) -> ToolRegistry:
    async def get_metar(args: GetMetarArgs) -> str:
        try:
            report = await metar.latest(args.icao_code)
        except InvalidIcaoError as error:
            return f"Error: {error.message}"
        if not report:
            return f"No current METAR is published for {args.icao_code.strip().upper()}."
        return report

    async def count_aircraft(args: CountAircraftArgs) -> str:
        return await traffic.describe(args.region)

    return ToolRegistry(
        [
            Tool(
                name="get_metar",
                description="Get the current aviation weather (METAR) for an airport. "
                "Use this when the user asks about weather, visibility, wind or landing "
                "conditions at a specific airport.",
                args=GetMetarArgs,
                handler=get_metar,
            ),
            Tool(
                name="count_aircraft",
                description="Get live aircraft currently detected over a region. "
                "Use this when the user asks how many planes are flying somewhere, "
                "or what traffic looks like in an area.",
                args=CountAircraftArgs,
                handler=count_aircraft,
            ),
        ]
    )
