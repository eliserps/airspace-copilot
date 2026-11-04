import type { Aircraft } from "@/api/client";
import { useI18n } from "@/lib/i18n/context";
import { formatAltitude, formatHeading, formatSpeed } from "@/lib/units";

export function AircraftStats({ aircraft }: { aircraft: Aircraft }) {
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
    <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-2">
      {stats.map(([label, value]) => (
        <div key={label}>
          <dt className="label-caps">{label}</dt>
          <dd className="font-mono text-sm text-foreground">{value}</dd>
        </div>
      ))}
    </dl>
  );
}
