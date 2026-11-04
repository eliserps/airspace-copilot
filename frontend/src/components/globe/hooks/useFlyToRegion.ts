import { useEffect, type RefObject } from "react";
import type { GlobeMethods } from "react-globe.gl";
import type { Region } from "@/config";

const FLIGHT_MS = 1400;

export function useFlyToRegion(
  globeRef: RefObject<GlobeMethods | undefined>,
  region: Region,
  ready: boolean,
) {
  useEffect(() => {
    const globe = globeRef.current;
    if (!ready || !globe) return;
    globe.pointOfView({ lat: region.lat, lng: region.lng, altitude: region.altitude }, FLIGHT_MS);
    const timer = setTimeout(() => {
      globe.controls().autoRotate = true;
    }, FLIGHT_MS + 100);
    return () => clearTimeout(timer);
  }, [globeRef, region, ready]);
}
