import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field

from app.traffic.models import StateVector

FL100_M = 3048
FL300_M = 9144
LOW_ALTITUDE_M = 1000

TOP_COUNTRIES = 8
TOP_AIRLINES = 8
NOTABLE_LIMIT = 5


@dataclass(frozen=True)
class LowFlyer:
    altitude: float
    callsign: str
    country: str
    velocity: float | None


@dataclass(frozen=True)
class TrafficStats:
    total: int = 0
    on_ground: int = 0
    no_altitude: int = 0
    below_fl100: int = 0
    fl100_300: int = 0
    above_fl300: int = 0
    countries: list[tuple[str, int]] = field(default_factory=list)
    airlines: list[tuple[str, int]] = field(default_factory=list)
    low_flyers_count: int = 0
    lowest: list[LowFlyer] = field(default_factory=list)

    @property
    def airborne(self) -> int:
        return self.total - self.on_ground


def airline_prefix(callsign: str | None) -> str | None:
    if not callsign or len(callsign) <= 3:
        return None
    prefix = callsign[:3]
    return prefix.upper() if prefix.isalpha() and callsign[3].isdigit() else None


def summarize(aircraft: Sequence[StateVector]) -> TrafficStats:
    countries: Counter[str] = Counter()
    airlines: Counter[str] = Counter()
    bands = {"below_fl100": 0, "fl100_300": 0, "above_fl300": 0}
    on_ground = no_altitude = 0
    low_flyers: list[LowFlyer] = []

    for plane in aircraft:
        countries[plane.origin_country or "unknown"] += 1
        if prefix := airline_prefix(plane.callsign):
            airlines[prefix] += 1

        if plane.on_ground:
            on_ground += 1
            continue

        altitude = plane.altitude
        if altitude is None:
            no_altitude += 1
        elif altitude < FL100_M:
            bands["below_fl100"] += 1
            if 0 <= altitude < LOW_ALTITUDE_M:
                low_flyers.append(
                    LowFlyer(
                        altitude, plane.callsign or "unknown", plane.origin_country, plane.velocity
                    )
                )
        elif altitude < FL300_M:
            bands["fl100_300"] += 1
        else:
            bands["above_fl300"] += 1

    low_flyers.sort(key=lambda f: (f.altitude, f.callsign))
    return TrafficStats(
        total=len(aircraft),
        on_ground=on_ground,
        no_altitude=no_altitude,
        countries=countries.most_common(TOP_COUNTRIES),
        airlines=airlines.most_common(TOP_AIRLINES),
        low_flyers_count=len(low_flyers),
        lowest=low_flyers[:NOTABLE_LIMIT],
        **bands,
    )


def format_stats(stats: TrafficStats) -> str:
    if stats.total == 0:
        return "No aircraft detected in this area."

    countries = ", ".join(f"{name} {n}" for name, n in stats.countries) or "none"
    airlines = ", ".join(f"{code} {n}" for code, n in stats.airlines) or "none"
    lines = [
        f"Total detected: {stats.total} "
        f"(airborne {stats.airborne}, on ground {stats.on_ground}, "
        f"no altitude reported {stats.no_altitude})",
        f"Airborne by altitude: below FL100 {stats.below_fl100}, "
        f"FL100-FL300 {stats.fl100_300}, above FL300 {stats.above_fl300}",
        f"Top countries of registration: {countries}",
        f"Top airline callsign prefixes (ICAO codes): {airlines}",
        f"Airborne below {LOW_ALTITUDE_M} m: {stats.low_flyers_count}",
    ]
    for f in stats.lowest:
        lines.append(
            f"- {f.callsign} | {f.country} | altitude {f.altitude:.0f} m | speed {f.velocity} m/s"
        )
    return "\n".join(lines)


def bucket(n: int) -> int:
    """Groups a count into ~10% steps, so 842 -> 851 is 'unchanged'."""
    return 0 if n <= 0 else round(math.log(n) / math.log(1.1))


def fingerprint(stats: TrafficStats) -> tuple[object, ...]:
    """What has to change for a new briefing to say something different."""
    return (
        bucket(stats.total),
        bucket(stats.on_ground),
        bucket(stats.low_flyers_count),
        tuple(name for name, _ in stats.countries[:3]),
        tuple(code for code, _ in stats.airlines[:3]),
    )
