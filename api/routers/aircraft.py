"""Live traffic endpoints. Call count_aircraft() and get_region_snapshot() from src/."""

from fastapi import APIRouter, Query

from src.tools import (
    REGIONS,
    count_aircraft,
    get_region_snapshot,
    normalise_region,
    plot_aircraft,
)

from ..errors import SOURCE_OPENSKY, unknown_region
from ..schemas import AircraftMapResponse, AircraftSummaryResponse

router = APIRouter(tags=["airspace"])


@router.get("/aircraft", response_model=AircraftSummaryResponse)
def aircraft(region: str = Query("south_america", description="One of the regions from /health.")):
    """Aircraft currently detected over a region, as a text summary."""
    key = normalise_region(region)
    if key not in REGIONS:
        raise unknown_region(region, list(REGIONS))

    return {
        "region": key,
        "summary": count_aircraft(key),
        "source": SOURCE_OPENSKY,
    }


@router.get("/aircraft/map", response_model=AircraftMapResponse)
def aircraft_map(region: str = Query("south_america", description="One of the regions from /health.")):
    """Aircraft over a region as objects with coordinates, for plotting pins."""
    try:
        snapshot = get_region_snapshot(region)
    except KeyError:
        raise unknown_region(region, list(REGIONS))

    key = normalise_region(region)
    planes = plot_aircraft(snapshot["aircraft"])
    lamin, lamax, lomin, lomax = REGIONS[key]

    return {
        "region": key,
        "count": len(planes),
        "bounds": {"lat_min": lamin, "lat_max": lamax,
                   "lon_min": lomin, "lon_max": lomax},
        "aircraft": planes,
        "fetched_at": snapshot["fetched_at"],
        "stale": snapshot["stale"],
        "source": SOURCE_OPENSKY,
    }
