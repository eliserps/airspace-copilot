import { useCallback, useMemo, useRef } from "react";
import Globe, { type GlobeMethods } from "react-globe.gl";
import type { Aircraft } from "@/api/client";
import type { Region } from "@/config";
import { useElementSize } from "./hooks/useElementSize";
import { useFlyToRegion } from "./hooks/useFlyToRegion";
import { useGlobeControls } from "./hooks/useGlobeControls";
import { useMarkerSync } from "./hooks/useMarkerSync";
import { usePreventPageScroll } from "./hooks/usePreventPageScroll";
import { useSunLight } from "./hooks/useSunLight";
import { createMarkerElement, toMarkerData, type MarkerDatum } from "./markerElement";

const tileUrl = (x: number, y: number, level: number) =>
  `https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${level}/${y}/${x}`;

const markerLat = (d: object) => (d as MarkerDatum).lat;
const markerLng = (d: object) => (d as MarkerDatum).lng;

export default function GlobeView({
  aircraft,
  region,
  selectedId,
  onSelect,
}: {
  aircraft: Aircraft[];
  region: Region;
  selectedId: string | null;
  onSelect: (icao24: string) => void;
}) {
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const globeRef = useRef<GlobeMethods | undefined>(undefined);
  const size = useElementSize(wrapRef);
  const ready = size.width > 0;

  const selectedRef = useRef(selectedId);
  selectedRef.current = selectedId;
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

  const data = useMemo(() => toMarkerData(aircraft), [aircraft]);

  useGlobeControls(globeRef, ready);
  useFlyToRegion(globeRef, region, ready);
  useSunLight(globeRef, ready);
  useMarkerSync(wrapRef, data, selectedId);
  usePreventPageScroll(wrapRef);

  const markerElement = useCallback(
    (obj: object) =>
      createMarkerElement(
        obj as MarkerDatum,
        selectedRef.current === (obj as MarkerDatum).icao24,
        (id) => onSelectRef.current(id),
      ),
    [],
  );

  return (
    <div ref={wrapRef} className="absolute inset-0 touch-none">
      {ready && (
        <Globe
          ref={globeRef}
          width={size.width}
          height={size.height}
          backgroundColor="rgba(0,0,0,0)"
          globeImageUrl={null}
          globeTileEngineUrl={tileUrl}
          atmosphereColor="#8ab6ff"
          atmosphereAltitude={0.22}
          animateIn={true}
          htmlElementsData={data}
          htmlLat={markerLat}
          htmlLng={markerLng}
          htmlAltitude={0.012}
          htmlTransitionDuration={0}
          htmlElement={markerElement}
        />
      )}
    </div>
  );
}
