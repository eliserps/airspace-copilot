import type { Page } from "@playwright/test";

const plane = (icao24: string, callsign: string) => ({
  icao24,
  callsign,
  country: "Brazil",
  latitude: -23.5,
  longitude: -46.6,
  altitude_m: 10000,
  on_ground: false,
  velocity_ms: 230,
  heading_deg: 90,
});

export async function mockApi(page: Page) {
  await page.route(/arcgisonline|fonts\.(googleapis|gstatic)/, (route) => route.abort());
  await page.route("http://api.test/aircraft/map**", (route) =>
    route.fulfill({
      json: {
        region: new URL(route.request().url()).searchParams.get("region"),
        count: 2,
        bounds: { lat_min: -56, lat_max: 13, lon_min: -82, lon_max: -34 },
        aircraft: [plane("abc123", "TAM3456"), plane("def456", "GLO1234")],
        fetched_at: 1_700_000_000,
        stale: false,
        source: "OpenSky (partial volunteer coverage)",
      },
    }),
  );
  await page.route("http://api.test/weather/**", (route) =>
    route.fulfill({
      json: {
        icao: "SBGR",
        language: "en",
        raw: "SBGR 091800Z 19011KT CAVOK 22/19 Q1015",
        decoded: "Ceiling and visibility OK. Good conditions for landing.",
        source: "Aviation Weather Center",
      },
    }),
  );
  await page.route("http://api.test/briefing**", (route) =>
    route.fulfill({
      json: {
        region: "south_america",
        language: "en",
        aircraft_count: 2,
        briefing: "**2 aircraft** detected over South America. Coverage is partial.",
        generated_at: 1_700_000_000,
        source: "OpenSky (partial volunteer coverage)",
      },
    }),
  );
  await page.route("http://api.test/ask/stream", (route) =>
    route.fulfill({
      headers: { "Content-Type": "text/event-stream" },
      body: [
        'event: meta\ndata: {"flagged": false}\n\n',
        'event: delta\ndata: {"text": "Two aircraft "}\n\n',
        'event: delta\ndata: {"text": "over South America."}\n\n',
        "event: done\ndata: {}\n\n",
      ].join(""),
    }),
  );
}
