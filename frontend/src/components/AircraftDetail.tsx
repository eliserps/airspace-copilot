import { motion } from "motion/react";
import { X, Plane } from "lucide-react";
import type { Aircraft } from "@/lib/api";
import { formatAltitude, formatHeading, formatSpeed } from "@/lib/units";
import { useI18n } from "@/lib/i18n-context";

export function AircraftDetail({ aircraft, onClose }: { aircraft: Aircraft; onClose: () => void }) {
  const { t, locale } = useI18n();
  const stats: Array<[string, string]> = [
    [t("aircraft.altitude"), formatAltitude(aircraft.altitude_m, locale)],
    [t("aircraft.speed"), formatSpeed(aircraft.velocity_ms, locale)],
    [t("aircraft.heading"), formatHeading(aircraft.heading_deg)],
    [t("aircraft.status"), aircraft.on_ground ? t("aircraft.onGround") : t("aircraft.airborne")],
    [t("aircraft.latitude"), `${aircraft.latitude.toFixed(3)}°`],
    [t("aircraft.longitude"), `${aircraft.longitude.toFixed(3)}°`],
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 12, scale: 0.98 }}
      transition={{ type: "spring", stiffness: 340, damping: 30 }}
      className="panel pointer-events-auto w-[min(19rem,calc(100vw-2rem))] p-4"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <Plane
            className="size-4 text-warning"
            style={{ transform: `rotate(${aircraft.heading_deg ?? 0}deg)` }}
          />
          <div>
            <p className="font-mono text-sm font-semibold text-foreground">
              {aircraft.callsign?.trim() || aircraft.icao24}
            </p>
            <p className="text-[11px] text-muted-foreground">
              {aircraft.country || t("aircraft.unknownOrigin")}
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          aria-label={t("aircraft.close")}
          className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
        >
          <X className="size-4" />
        </button>
      </div>

      <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-2">
        {stats.map(([k, v]) => (
          <div key={k}>
            <dt className="label-caps">{k}</dt>
            <dd className="font-mono text-sm text-foreground">{v}</dd>
          </div>
        ))}
      </dl>
    </motion.div>
  );
}
