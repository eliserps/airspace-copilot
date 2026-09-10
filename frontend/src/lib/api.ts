import { API_BASE_URL } from "@/config";

export type Aircraft = {
  icao24: string;
  callsign: string | null;
  country: string;
  latitude: number;
  longitude: number;
  altitude_m: number | null;
  on_ground: boolean;
  velocity_ms: number | null;
  heading_deg: number | null;
};

export type AircraftSummaryResponse = {
  region: string;
  summary: string;
  source: string;
};

export type Bounds = {
  lat_min: number;
  lat_max: number;
  lon_min: number;
  lon_max: number;
};

export type AircraftMapResponse = {
  region: string;
  count: number;
  bounds: Bounds;
  aircraft: Aircraft[];
  source: string;
};

export type BriefingResponse = {
  region: string;
  language: string;
  aircraft_count: number;
  briefing: string;
  source: string;
};

export type WeatherResponse = {
  icao: string;
  language: string;
  raw: string;
  decoded: string;
  source: string;
};

export type AskResponse = {
  question: string;
  answer: string;
  flagged: boolean;
};

export type HealthResponse = {
  status: string;
  regions: string[];
  languages: string[];
};

type ApiErrorBody = {
  error: string;
  message: string;
  [key: string]: unknown;
};

export class ApiError extends Error {
  status?: number | undefined;
  code?: string | undefined;

  constructor(message: string, status?: number, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { Accept: "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiError("Could not reach the airspace API. Check your connection or API_BASE_URL.");
  }

  const text = await res.text();

  if (!res.ok) {
    let body: ApiErrorBody | undefined;
    try {
      body = JSON.parse(text) as ApiErrorBody;
    } catch {
      body = undefined;
    }
    throw new ApiError(
      body?.message || `Request failed (${res.status} ${res.statusText || "error"})`,
      res.status,
      body?.error,
    );
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    throw new ApiError("The API returned malformed JSON.");
  }
}

export type Lang = "en" | "pt";

export function toApiLang(lang: string): Lang {
  return lang.toLowerCase().startsWith("pt") ? "pt" : "en";
}

export const api = {
  health: () => request<HealthResponse>(`/health`),

  aircraft: (region: string) =>
    request<AircraftSummaryResponse>(`/aircraft?region=${encodeURIComponent(region)}`),

  aircraftMap: (region: string) =>
    request<AircraftMapResponse>(`/aircraft/map?region=${encodeURIComponent(region)}`),

  briefing: (region: string, lang: string) =>
    request<BriefingResponse>(
      `/briefing?region=${encodeURIComponent(region)}&lang=${toApiLang(lang)}`,
    ),

  weather: (icao: string, lang: string = "en") =>
    request<WeatherResponse>(`/weather/${encodeURIComponent(icao)}?lang=${toApiLang(lang)}`),

  ask: (question: string) =>
    request<AskResponse>(`/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }),
};
