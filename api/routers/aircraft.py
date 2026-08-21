"""Live traffic endpoints. Call count_aircraft() and list_aircraft() from src/."""

from fastapi import APIRouter, Query

from tools import REGIONS, count_aircraft, list_aircraft

from ..errors import SOURCE_OPENSKY, unknown_region
from ..schemas import AircraftMapResponse, AircraftSummaryResponse

router = APIRouter(tags=["airspace"])


@router.get("/aircraft", response_model=AircraftSummaryResponse)
def aircraft(region: str = Query("brazil", description="One of the regions from /health.")):
    """Aircraft currently detected over a region, as a text summary."""
    if region.lower().strip() not in REGIONS:
        raise unknown_region(region, list(REGIONS))

    return {
        "region": region,
        "summary": count_aircraft(region),
        "source": SOURCE_OPENSKY,
    }


@router.get("/aircraft/map", response_model=AircraftMapResponse)
def aircraft_map(region: str = Query("brazil", description="One of the regions from /health.")):
    """Aircraft over a region as objects with coordinates, for plotting pins."""
    try:
        planes = list_aircraft(region)
    except KeyError:
        raise unknown_region(region, list(REGIONS))

    lamin, lamax, lomin, lomax = REGIONS[region.lower().strip()]

    return {
        "region": region,
        "count": len(planes),
        "bounds": {"lat_min": lamin, "lat_max": lamax,
                   "lon_min": lomin, "lon_max": lomax},
        "aircraft": planes,
        "source": SOURCE_OPENSKY,
    }
