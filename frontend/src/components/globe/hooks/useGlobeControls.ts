import { useEffect, type RefObject } from "react";
import type { GlobeMethods } from "react-globe.gl";

const RESUME_SPIN_AFTER_MS = 4000;

export function useGlobeControls(globeRef: RefObject<GlobeMethods | undefined>, ready: boolean) {
  useEffect(() => {
    const controls = globeRef.current?.controls();
    if (!ready || !controls) return;

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
      clearTimeout(idleTimer);
    };
    const resumeSpin = () => {
      clearTimeout(idleTimer);
      idleTimer = setTimeout(() => {
        controls.autoRotate = true;
      }, RESUME_SPIN_AFTER_MS);
    };

    controls.addEventListener("start", stopSpin);
    controls.addEventListener("end", resumeSpin);
    return () => {
      clearTimeout(idleTimer);
      controls.removeEventListener("start", stopSpin);
      controls.removeEventListener("end", resumeSpin);
    };
  }, [globeRef, ready]);
}
