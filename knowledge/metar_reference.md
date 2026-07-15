# METAR Reference
## Structure
A METAR is a routine aviation weather report issued hourly by airports.
Format: STATION TIME WIND VISIBILITY WEATHER CLOUDS TEMP/DEWPOINT PRESSURE
## Station and time
- 4-letter ICAO code (SBGR = Guarulhos, SBPA = Porto Alegre, SBGL = Galeao).
- Time: DDHHMMZ. Day of month, hour, minute, in UTC (Z = Zulu = UTC).
## Wind
- Format: DDDSSKT. Direction in degrees, speed in knots.
- 17006KT = wind from 170 degrees at 6 knots.
- VRB = variable direction. 00000KT = calm.
- 210V270 = direction varying between 210 and 270 degrees.
- G = gusts. 18010G25KT = 10 knots gusting to 25.
## Visibility
- In meters. 9999 = 10 km or more (excellent).
- 8000 = 8 km. 4000 = 4 km (reduced). Below 1000 m is very poor.
- CAVOK = Ceiling And Visibility OK: visibility 10 km+, no significant
 clouds below 5000 ft, no significant weather. Ideal conditions.
## Weather phenomena
- BR = mist (visibility 1000-5000 m)
- FG = fog (visibility below 1000 m)
- RA = rain, DZ = drizzle, TS = thunderstorm, SH = showers
- Prefix - = light, + = heavy. -RA = light rain.
## Clouds
- Coverage in eighths (oktas), followed by height in HUNDREDS of feet.
- FEW = few (1-2 oktas), SCT = scattered (3-4), BKN = broken (5-7),
 OVC = overcast (8, fully covered)
- BKN007 = broken clouds at 700 feet. OVC003 = overcast at 300 feet (very low).
- NSC = no significant clouds.
## Ceiling
- The ceiling is the height of the lowest BKN or OVC layer.
- A low ceiling (below 1000 ft) is operationally significant and may
 restrict landings.
## Temperature and dewpoint
- Format: TT/DD in Celsius. M prefix = negative. 17/16 = temp 17, dewpoint 16.
- When temperature and dewpoint are equal, the air is saturated: fog or
 mist is likely.
## Pressure
- Q1013 = QNH 1013 hPa (hectopascals). A1013 = inches of mercury.
## Operational reading
- Low ceiling + low visibility = poor conditions, possible holding,
 diversions or delays.
- CAVOK = clear conditions for landing.