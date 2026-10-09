import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Globe, { type GlobeMethods } from "react-globe.gl";
import { AmbientLight, DirectionalLight } from "three";
import type { Aircraft } from "@/lib/api";
import type { Region } from "@/config";
import { PLANE_SVG, altitudeBand } from "@/lib/markers";
import { latLngToVector3, subsolarPoint } from "@/lib/sun";

type Props = {
  aircraft: Aircraft[];
  region: Region;
  selectedId: string | null;
  onSelect: (icao24: string) => void;
};

type MarkerDatum = Aircraft & { lat: number; lng: number };

const tileUrl = (x: number, y: number, level: number) =>
  `https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${level}/${y}/${x}`;

const markerLat = (d: object) => (d as MarkerDatum).lat;
const markerLng = (d: object) => (d as MarkerDatum).lng;

export default function GlobeView({ aircraft, region, selectedId, onSelect }: Props) {
  const wrapRef = useRef<HTMLDivElement | null>(null);

  const globeRef = useRef<GlobeMethods | undefined>(undefined);
  const [size, setSize] = useState({ width: 0, height: 0 });
  const selectedRef = useRef<string | null>(selectedId);
  selectedRef.current = selectedId;
  const markerDataRef = useRef(new Map<string, MarkerDatum>());
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      setSize({ width: el.clientWidth, height: el.clientHeight });
    });
    ro.observe(el);
    setSize({ width: el.clientWidth, height: el.clientHeight });
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    const g = globeRef.current;
    if (!g) return;
    const controls = g.controls();

    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.25;

    controls.enableDamping = true;
    controls.dampingFactor = 0.12;

    controls.enableZoom = true;
    controls.zoomSpeed = 1.6;
    controls.minDistance = 101;
    controls.maxDistance = 400;

    let idleTimer: ReturnType<typeof setTimeout> | undefined;

    const stopSpin = () => {
      controls.autoRotate = false;
      if (idleTimer) clearTimeout(idleTimer);
    };

    const resumeSpin = () => {
      if (idleTimer) clearTimeout(idleTimer);
      idleTimer = setTimeout(() => {
        controls.autoRotate = true;
      }, 4000);
    };

    controls.addEventListener("start", stopSpin);
    controls.addEventListener("end", resumeSpin);

    return () => {
      if (idleTimer) clearTimeout(idleTimer);
      controls.removeEventListener("start", stopSpin);
      controls.removeEventListener("end", resumeSpin);
    };
  }, [size.width]);

  useEffect(() => {
    const g = globeRef.current;
    if (!g) return;
    g.pointOfView({ lat: region.lat, lng: region.lng, altitude: region.altitude }, 1400);
    const timer = setTimeout(() => {
      g.controls().autoRotate = true;
    }, 1500);
    return () => clearTimeout(timer);
  }, [region]);

  useEffect(() => {
    if (size.width === 0) return;
    const g = globeRef.current;
    if (!g) return;

    const sunLight = new DirectionalLight(0xffffff, 3.2);
    const ambient = new AmbientLight(0xbfd4ff, 0.22);
    g.lights([ambient, sunLight]);

    const place = () => {
      const sun = subsolarPoint();
      const v = latLngToVector3(sun.lat, sun.lng, 800);
      sunLight.position.set(v.x, v.y, v.z);
    };

    place();
    const interval = setInterval(place, 60_000);
    return () => clearInterval(interval);
  }, [size.width]);

  const data = useMemo<MarkerDatum[]>(() => {
    const next = aircraft.map((a) => ({ ...a, lat: a.latitude, lng: a.longitude }));
    markerDataRef.current = new Map(next.map((d) => [d.icao24, d]));
    return next;
  }, [aircraft]);

  useEffect(() => {
    const nodes = wrapRef.current?.querySelectorAll<HTMLElement>(".ac-marker");
    nodes?.forEach((n) => {
      const d = markerDataRef.current.get(n.dataset["icao"] ?? "");
      n.dataset["selected"] = String(n.dataset["icao"] === selectedId);
      if (d) {
        n.dataset["ground"] = String(d.on_ground);
        n.dataset["band"] = altitudeBand(d.altitude_m);
        const svg = n.firstElementChild as SVGElement | null;
        if (svg) svg.style.transform = `rotate(${d.heading_deg ?? 0}deg)`;
      }
    });
  }, [selectedId, data]);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const swallow = (e: WheelEvent) => e.preventDefault();
    el.addEventListener("wheel", swallow, { passive: false });
    return () => el.removeEventListener("wheel", swallow);
  }, []);

  const markerElement = useCallback((obj: object) => {
    const d = obj as MarkerDatum;
    const el = document.createElement("div");
    el.className = "ac-marker";
    el.dataset["icao"] = d.icao24;
    el.dataset["ground"] = String(d.on_ground);
    el.dataset["band"] = altitudeBand(d.altitude_m);
    el.dataset["selected"] = String(selectedRef.current === d.icao24);
    const name = d.callsign?.trim() || d.icao24;
    el.title = name;
    el.setAttribute("role", "button");
    el.setAttribute("tabindex", "0");
    el.setAttribute("aria-label", name);
    el.innerHTML = PLANE_SVG;
    const svg = el.firstElementChild as SVGElement | null;
    if (svg) svg.style.transform = `rotate(${d.heading_deg ?? 0}deg)`;
    const pick = (e: Event) => {
      e.stopPropagation();
      onSelectRef.current(d.icao24);
    };
    el.addEventListener("click", pick);
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        pick(e);
      }
    });
    return el;
  }, []);

  return (
    <div ref={wrapRef} className="absolute inset-0 touch-none">
      {size.width > 0 && (
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
