import { HttpResponse, http } from "msw";
import { setupServer } from "msw/node";
import { API_BASE_URL } from "@/config";
import type { Aircraft, AircraftMapResponse, Schemas } from "@/api/client";

export const api = (path: string) => `${API_BASE_URL}${path}`;

export function aircraft(overrides: Partial<Aircraft> = {}): Aircraft {
  return {
    icao24: "abc123",
    callsign: "TAM3456",
    country: "Brazil",
    latitude: -23.5,
    longitude: -46.6,
    altitude_m: 10000,
    on_ground: false,
    velocity_ms: 230,
    heading_deg: 90,
    ...overrides,
  };
}

export function aircraftMap(planes: Aircraft[], stale = false): AircraftMapResponse {
  return {
    region: "south_america",
    count: planes.length,
    bounds: { lat_min: -56, lat_max: 13, lon_min: -82, lon_max: -34 },
    aircraft: planes,
    fetched_at: 1_700_000_000,
    stale,
    source: "OpenSky (partial volunteer coverage)",
  };
}

export function sseResponse(events: Array<[string, unknown]>) {
  const encoder = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const [event, data] of events) {
        controller.enqueue(encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`));
      }
      controller.close();
    },
  });
  return new HttpResponse(body, { headers: { "Content-Type": "text/event-stream" } });
}

const weather: Schemas["WeatherResponse"] = {
  icao: "SBGR",
  language: "en",
  raw: "SBGR 091800Z 19011KT CAVOK 22/19 Q1015",
  decoded: "**Wind** from 190° at 11 kt. Good conditions.",
  source: "Aviation Weather Center",
};

export const handlers = [
  http.get(api("/aircraft/map"), () => HttpResponse.json(aircraftMap([aircraft()]))),
  http.get(api("/weather/:icao"), ({ params }) => {
    const icao = String(params["icao"]);
    return HttpResponse.json({ ...weather, icao, raw: weather.raw.replace("SBGR", icao) });
  }),
  http.get(api("/briefing"), () =>
    HttpResponse.json({
      region: "south_america",
      language: "en",
      aircraft_count: 1,
      briefing: "One aircraft detected.",
      generated_at: 1_700_000_000,
      source: "OpenSky (partial volunteer coverage)",
    }),
  ),
  http.post(api("/ask/stream"), () =>
    sseResponse([
      ["meta", { flagged: false }],
      ["delta", { text: "One plane " }],
      ["delta", { text: "over Brazil." }],
      ["done", {}],
    ]),
  ),
];

export const server = setupServer(...handlers);
