export const API_BASE_URL: string =
  (import.meta.env["VITE_API_BASE_URL"] as string | undefined)?.replace(/\/+$/, "") ||
  "https://airspace-copilot-api.onrender.com";

export type Region = {
  id: string;
  label: string;
  lat: number;
  lng: number;
  altitude: number;
  metar: string;
};

export const REGIONS: Region[] = [
  {
    id: "south_america",
    label: "South America",
    lat: -20.0,
    lng: -60.0,
    altitude: 2.1,
    metar: "SBGR",
  },
  {
    id: "north_america",
    label: "North America",
    lat: 42.0,
    lng: -95.0,
    altitude: 2.1,
    metar: "KJFK",
  },
  { id: "europe", label: "Europe", lat: 48.0, lng: 10.0, altitude: 1.7, metar: "EDDF" },
  { id: "africa", label: "Africa", lat: 2.0, lng: 18.0, altitude: 2.2, metar: "FAOR" },
  { id: "asia", label: "Asia", lat: 30.0, lng: 100.0, altitude: 2.3, metar: "RJTT" },
  { id: "oceania", label: "Oceania", lat: -27.0, lng: 140.0, altitude: 2.1, metar: "YSSY" },
];

export const DEFAULT_REGION = REGIONS[0]!;
