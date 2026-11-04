import { useEffect, type RefObject } from "react";
import type { GlobeMethods } from "react-globe.gl";
import { AmbientLight, DirectionalLight } from "three";
import { latLngToVector3, subsolarPoint } from "../sun";

const SUN_DISTANCE = 800;
const UPDATE_MS = 60_000;

export function useSunLight(globeRef: RefObject<GlobeMethods | undefined>, ready: boolean) {
  useEffect(() => {
    const globe = globeRef.current;
    if (!ready || !globe) return;

    const sunLight = new DirectionalLight(0xffffff, 3.2);
    globe.lights([new AmbientLight(0xbfd4ff, 0.22), sunLight]);

    const place = () => {
      const sun = subsolarPoint();
      const v = latLngToVector3(sun.lat, sun.lng, SUN_DISTANCE);
      sunLight.position.set(v.x, v.y, v.z);
    };
    place();
    const interval = setInterval(place, UPDATE_MS);
    return () => clearInterval(interval);
  }, [globeRef, ready]);
}
