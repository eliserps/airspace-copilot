import type { components } from "@/api/schema.gen";

export const API_BASE_URL: string =
  (import.meta.env["VITE_API_BASE_URL"] as string | undefined)?.replace(/\/+$/, "") ||
  "http://localhost:8000";

export type RegionId = NonNullable<components["schemas"]["AskRequest"]["region"]>;

export type Region = {
  id: RegionId;
  lat: number;
  lng: number;
  altitude: number;
  metar: string;
};

export const REGIONS: Region[] = [
  { id: "south_america", lat: -20.0, lng: -60.0, altitude: 2.1, metar: "SBGR" },
  { id: "north_america", lat: 42.0, lng: -95.0, altitude: 2.1, metar: "KJFK" },
  { id: "europe", lat: 48.0, lng: 10.0, altitude: 1.7, metar: "EDDF" },
  { id: "africa", lat: 2.0, lng: 18.0, altitude: 2.2, metar: "FAOR" },
  { id: "asia", lat: 30.0, lng: 100.0, altitude: 2.3, metar: "RJTT" },
  { id: "oceania", lat: -27.0, lng: 140.0, altitude: 2.1, metar: "YSSY" },
  { id: "world", lat: 20.0, lng: -30.0, altitude: 2.8, metar: "SBGR" },
];

export const REGION_IDS = REGIONS.map((r) => r.id) as [RegionId, ...RegionId[]];

export const DEFAULT_REGION = REGIONS[0]!;

export function regionById(id: RegionId): Region {
  return REGIONS.find((r) => r.id === id) ?? DEFAULT_REGION;
}

export const MAX_GLOBE_MARKERS = 1500;
export const MAX_LIST_ROWS = 300;
