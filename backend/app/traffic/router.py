from typing import Annotated

from fastapi import APIRouter, Query

from app.dependencies import TrafficDep

from .regions import REGIONS, resolve_region
from .schemas import Aircraft, AircraftMapResponse, AircraftSummaryResponse, Bounds

SOURCE = "OpenSky (partial volunteer coverage)"
RegionQuery = Annotated[str, Query(description="One of the regions from /health.")]

router = APIRouter(tags=["airspace"])


@router.get("/aircraft", response_model=AircraftSummaryResponse)
async def aircraft_summary(
    traffic: TrafficDep, region: RegionQuery = "south_america"
) -> AircraftSummaryResponse:
    """Aircraft currently detected over a region, as a text summary."""
    key = resolve_region(region)
    return AircraftSummaryResponse(region=key, summary=await traffic.describe(key), source=SOURCE)


@router.get("/aircraft/map", response_model=AircraftMapResponse)
async def aircraft_map(
    traffic: TrafficDep, region: RegionQuery = "south_america"
) -> AircraftMapResponse:
    """Aircraft over a region as objects with coordinates, for plotting pins."""
    key = resolve_region(region)
    snapshot = await traffic.snapshot(key)
    planes = [Aircraft.from_state(p) for p in snapshot.aircraft if p.has_position]
    return AircraftMapResponse(
        region=key,
        count=len(planes),
        bounds=Bounds(**REGIONS[key]._asdict()),
        aircraft=planes,
        fetched_at=snapshot.fetched_at,
        stale=snapshot.stale,
        source=SOURCE,
    )
