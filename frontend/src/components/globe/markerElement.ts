import type { Aircraft } from "@/api/client";
import { PLANE_SVG, altitudeBand } from "./markers";

export type MarkerDatum = Aircraft & { lat: number; lng: number };

export function toMarkerData(aircraft: Aircraft[]): MarkerDatum[] {
  return aircraft.map((a) => ({ ...a, lat: a.latitude, lng: a.longitude }));
}

export function applyMarkerState(el: HTMLElement, d: MarkerDatum, selected: boolean) {
  el.dataset["selected"] = String(selected);
  el.dataset["ground"] = String(d.on_ground);
  el.dataset["band"] = altitudeBand(d.altitude_m);
  const svg = el.firstElementChild as SVGElement | null;
  if (svg) svg.style.transform = `rotate(${d.heading_deg ?? 0}deg)`;
}

export function createMarkerElement(
  d: MarkerDatum,
  selected: boolean,
  onPick: (icao24: string) => void,
): HTMLElement {
  const el = document.createElement("div");
  const name = d.callsign?.trim() || d.icao24;
  el.className = "ac-marker";
  el.dataset["icao"] = d.icao24;
  el.title = name;
  el.setAttribute("role", "button");
  el.setAttribute("tabindex", "0");
  el.setAttribute("aria-label", name);
  el.innerHTML = PLANE_SVG;
  applyMarkerState(el, d, selected);

  const pick = (e: Event) => {
    e.stopPropagation();
    onPick(d.icao24);
  };
  el.addEventListener("click", pick);
  el.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      pick(e);
    }
  });
  return el;
}
