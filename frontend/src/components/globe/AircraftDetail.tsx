import { motion } from "motion/react";
import { Plane, X } from "lucide-react";
import type { Aircraft } from "@/api/client";
import { Button } from "@/components/ui/Button";
import { useI18n } from "@/lib/i18n/context";
import { AircraftStats } from "./AircraftStats";

export function AircraftDetail({ aircraft, onClose }: { aircraft: Aircraft; onClose: () => void }) {
  const { t } = useI18n();

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
            aria-hidden
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
        <Button variant="ghost" size="iconSm" onClick={onClose} aria-label={t("aircraft.close")}>
          <X className="size-4" />
        </Button>
      </div>

      <AircraftStats aircraft={aircraft} />
    </motion.div>
  );
}
