import { motion } from "motion/react";
import { Plane } from "lucide-react";
import type { Aircraft } from "@/lib/api";
import { formatAltitude, formatHeading, formatSpeed } from "@/lib/units";
import { EmptyState } from "@/components/StatePanels";
import { cn } from "@/lib/utils";
import { useI18n } from "@/lib/i18n-context";

export function TrafficList({
  aircraft,
  selectedId,
  onSelect,
}: {
  aircraft: Aircraft[];
  selectedId: string | null;
  onSelect: (icao24: string) => void;
}) {
  const { t, locale } = useI18n();

  if (aircraft.length === 0) {
    return <EmptyState label={t("state.noAircraft")} hint={t("state.tryAnotherRegion")} />;
  }

  return (
    <ul className="divide-y divide-border">
      {aircraft.map((a, i) => (
        <motion.li
          key={a.icao24}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.18, delay: Math.min(i, 20) * 0.01 }}
        >
          <button
            onClick={() => onSelect(a.icao24)}
            className={cn(
              "flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors hover:bg-surface-2/60",
              selectedId === a.icao24 && "bg-surface-2/80",
            )}
          >
            <Plane
              className={cn(
                "size-4 shrink-0 transition-transform",
                a.on_ground ? "text-muted-foreground" : "text-primary",
                selectedId === a.icao24 && "text-warning",
              )}
              style={{ transform: `rotate(${a.heading_deg ?? 0}deg)` }}
            />
            <div className="min-w-0 flex-1">
              <p className="truncate font-mono text-sm font-semibold text-foreground">
                {a.callsign?.trim() || a.icao24}
              </p>
              <p className="truncate text-[11px] text-muted-foreground">
                {a.country || t("aircraft.unknown")} · {a.icao24}
              </p>
            </div>
            <div className="shrink-0 text-right font-mono text-[11px] text-muted-foreground">
              <p className="text-foreground">{formatAltitude(a.altitude_m, locale)}</p>
              <p>
                {formatSpeed(a.velocity_ms, locale)} · {formatHeading(a.heading_deg)}
              </p>
            </div>
          </button>
        </motion.li>
      ))}
    </ul>
  );
}
