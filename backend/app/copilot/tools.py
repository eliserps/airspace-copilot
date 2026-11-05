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


DEFAULT_RADIUS_KM = 50
MAX_RADIUS_KM = 500


class CountAircraftNearArgs(BaseModel):
    place: str = Field(max_length=100, description="Name of the city, airport or place.")
    latitude: float = Field(ge=-90, le=90, description="Latitude of the place, decimal degrees.")
    longitude: float = Field(
        ge=-180, le=180, description="Longitude of the place, decimal degrees."
    )
    radius_km: float = Field(
        default=DEFAULT_RADIUS_KM,
        ge=5,
        le=MAX_RADIUS_KM,
        description=f"Search radius in kilometres. Default {DEFAULT_RADIUS_KM}; use more "
        "for a state or a large metropolitan area.",
    )


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

    async def count_aircraft_near(args: CountAircraftNearArgs) -> str:
        return await traffic.describe_near(
            args.place, args.latitude, args.longitude, args.radius_km
        )

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
                "Use this for a continent, the whole world, or the region on the map.",
                args=CountAircraftArgs,
                handler=count_aircraft,
            ),
            Tool(
                name="count_aircraft_near",
                description="Get live aircraft within a radius of a point, closest first. "
                "Use this when the user names a city, airport, state or any place smaller "
                "than a continent. Pass the place's coordinates.",
                args=CountAircraftNearArgs,
                handler=count_aircraft_near,
            ),
        ]
    )
