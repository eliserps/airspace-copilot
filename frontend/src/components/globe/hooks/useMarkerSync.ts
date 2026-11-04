import { useEffect, type RefObject } from "react";
import { applyMarkerState, type MarkerDatum } from "../markerElement";

export function useMarkerSync(
  containerRef: RefObject<HTMLElement | null>,
  data: MarkerDatum[],
  selectedId: string | null,
) {
  useEffect(() => {
    const byId = new Map(data.map((d) => [d.icao24, d]));
    containerRef.current?.querySelectorAll<HTMLElement>(".ac-marker").forEach((el) => {
      const icao = el.dataset["icao"] ?? "";
      const datum = byId.get(icao);
      if (datum) applyMarkerState(el, datum, icao === selectedId);
      else el.dataset["selected"] = String(icao === selectedId);
    });
  }, [containerRef, data, selectedId]);
}
