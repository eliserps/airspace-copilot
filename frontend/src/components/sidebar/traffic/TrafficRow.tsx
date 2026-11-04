import { Plane } from "lucide-react";
import type { Aircraft } from "@/api/client";
import { cn } from "@/lib/cn";
import { useI18n } from "@/lib/i18n/context";
import { formatAltitude, formatHeading, formatSpeed } from "@/lib/units";

export function TrafficRow({
  aircraft,
  selected,
  onSelect,
}: {
  aircraft: Aircraft;
  selected: boolean;
  onSelect: () => void;
}) {
  const { t, locale } = useI18n();
  return (
    <button
      type="button"
      aria-current={selected || undefined}
      onClick={onSelect}
      className={cn(
        "flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors hover:bg-surface-2/60",
        selected && "bg-surface-2/80",
      )}
    >
      <Plane
        className={cn(
          "size-4 shrink-0 transition-transform",
          aircraft.on_ground ? "text-muted-foreground" : "text-primary",
          selected && "text-warning",
        )}
        style={{ transform: `rotate(${aircraft.heading_deg ?? 0}deg)` }}
      />
      <div className="min-w-0 flex-1">
        <p className="truncate font-mono text-sm font-semibold text-foreground">
          {aircraft.callsign?.trim() || aircraft.icao24}
        </p>
        <p className="truncate text-[11px] text-muted-foreground">
          {aircraft.country || t("aircraft.unknown")} · {aircraft.icao24}
        </p>
      </div>
      <div className="shrink-0 text-right font-mono text-[11px] text-muted-foreground">
        <p className="text-foreground">{formatAltitude(aircraft.altitude_m, locale)}</p>
        <p>
          {formatSpeed(aircraft.velocity_ms, locale)} · {formatHeading(aircraft.heading_deg)}
        </p>
      </div>
    </button>
  );
}
