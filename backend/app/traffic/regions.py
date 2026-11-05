from typing import Literal, NamedTuple, get_args

from app.core.errors import NotFoundError

RegionId = Literal["south_america", "north_america", "europe", "africa", "asia", "oceania", "world"]


class BoundingBox(NamedTuple):
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float

    def contains(self, latitude: float | None, longitude: float | None) -> bool:
        if latitude is None or longitude is None:
            return False
        return (
            self.lat_min <= latitude <= self.lat_max and self.lon_min <= longitude <= self.lon_max
        )


REGIONS: dict[RegionId, BoundingBox] = {
    "south_america": BoundingBox(-56.0, 13.0, -82.0, -34.0),
    "north_america": BoundingBox(24.0, 60.0, -130.0, -60.0),
    "europe": BoundingBox(35.0, 60.0, -10.0, 30.0),
    "africa": BoundingBox(-35.0, 37.0, -18.0, 52.0),
    "asia": BoundingBox(5.0, 55.0, 60.0, 145.0),
    "oceania": BoundingBox(-47.0, -8.0, 110.0, 180.0),
    "world": BoundingBox(-90.0, 90.0, -180.0, 180.0),
}

REGION_IDS: tuple[RegionId, ...] = get_args(RegionId)


class UnknownRegionError(NotFoundError):
    code = "unknown_region"

    def __init__(self, region: str):
        super().__init__(f"Unknown region '{region}'.", allowed=sorted(REGIONS))


def normalise_region(region: str) -> str:
    return region.lower().strip()


def resolve_region(region: str) -> RegionId:
    key = normalise_region(region)
    if key not in REGIONS:
        raise UnknownRegionError(region)
    return key
