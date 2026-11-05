import { ClientOnly } from "@tanstack/react-router";
import { AnimatePresence } from "motion/react";
import { Suspense, lazy, useMemo } from "react";
import { MAX_GLOBE_MARKERS, type Region } from "@/config";
import type { Aircraft } from "@/api/client";
import type { Traffic } from "@/api/traffic";
import { LoadingState } from "@/components/ui/state/LoadingState";
import { PanelBoundary } from "@/components/ui/state/PanelBoundary";
import { useI18n } from "@/lib/i18n/context";
import { AircraftDetail } from "./AircraftDetail";
import { AltitudeLegend } from "./AltitudeLegend";
import { TrafficAlert } from "./TrafficAlert";
import { TrafficCounter } from "./TrafficCounter";
import { sampleSpread } from "./markers";

const GlobeView = lazy(() => import("./GlobeView"));

export function GlobePanel({
  region,
  traffic,
  selected,
  onSelect,
}: {
  region: Region;
  traffic: Traffic;
  selected: Aircraft | null;
  onSelect: (icao24: string | undefined) => void;
}) {
  const { t } = useI18n();
  const { aircraft, query } = traffic;

  const globeAircraft = useMemo(() => {
    if (aircraft.length <= MAX_GLOBE_MARKERS) return aircraft;
    const sample = sampleSpread(aircraft, MAX_GLOBE_MARKERS);
    if (selected && !sample.includes(selected)) sample.push(selected);
    return sample;
  }, [aircraft, selected]);

  return (
    <section
      aria-label={t("app.aircraft")}
      className="panel relative h-[52vh] min-h-[320px] overflow-hidden lg:h-auto lg:min-h-[560px] lg:flex-1"
    >
      <div className="absolute inset-0 isolate">
        <PanelBoundary>
          <ClientOnly fallback={<LoadingState label={t("state.globe")} />}>
            <Suspense fallback={<LoadingState label={t("state.globe")} />}>
              <GlobeView
                aircraft={globeAircraft}
                region={region}
                selectedId={selected?.icao24 ?? null}
                onSelect={onSelect}
              />
            </Suspense>
          </ClientOnly>
        </PanelBoundary>
      </div>

      <div className="pointer-events-none absolute inset-x-0 top-0 flex items-start justify-between gap-2 p-3">
        <TrafficCounter traffic={traffic} />
        {query.isError ? (
          <TrafficAlert error={query.error} onRetry={() => void query.refetch()} />
        ) : null}
      </div>

      <AltitudeLegend
        sampled={globeAircraft.length < aircraft.length}
        source={query.data?.source}
      />

      <div className="pointer-events-none absolute right-3 bottom-3">
        <AnimatePresence>
          {selected ? (
            <AircraftDetail aircraft={selected} onClose={() => onSelect(undefined)} />
          ) : null}
        </AnimatePresence>
      </div>
    </section>
  );
}
