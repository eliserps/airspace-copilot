import { motion } from "motion/react";
import { MAX_LIST_ROWS } from "@/config";
import type { Aircraft } from "@/api/client";
import { EmptyState } from "@/components/ui/state/EmptyState";
import { useI18n } from "@/lib/i18n/context";
import { TrafficRow } from "./TrafficRow";

export function TrafficList({
  aircraft,
  selectedId,
  onSelect,
}: {
  aircraft: Aircraft[];
  selectedId: string | null;
  onSelect: (icao24: string) => void;
}) {
  const { t } = useI18n();

  if (aircraft.length === 0) {
    return <EmptyState label={t("state.noAircraft")} hint={t("state.tryAnotherRegion")} />;
  }

  const rows = aircraft.length > MAX_LIST_ROWS ? aircraft.slice(0, MAX_LIST_ROWS) : aircraft;

  return (
    <ul className="divide-y divide-border">
      {rows.map((plane, i) => (
        <motion.li
          key={plane.icao24}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.18, delay: Math.min(i, 20) * 0.01 }}
        >
          <TrafficRow
            aircraft={plane}
            selected={selectedId === plane.icao24}
            onSelect={() => onSelect(plane.icao24)}
          />
        </motion.li>
      ))}
      {rows.length < aircraft.length ? (
        <li className="px-4 py-3 text-center text-[11px] text-muted-foreground">
          {t("traffic.truncated", { shown: rows.length, total: aircraft.length })}
        </li>
      ) : null}
    </ul>
  );
}
