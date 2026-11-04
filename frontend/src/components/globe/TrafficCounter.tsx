import type { Traffic } from "@/api/traffic";
import { useI18n } from "@/lib/i18n/context";
import { useErrorMessage } from "@/lib/i18n/useErrorMessage";

export function TrafficCounter({ traffic }: { traffic: Traffic }) {
  const { t } = useI18n();
  const errorMessage = useErrorMessage();
  const { query, aircraft, stale } = traffic;
  return (
    <div className="panel pointer-events-auto flex items-center gap-4 px-3 py-2">
      <div>
        <p className="label-caps">{t("app.aircraft")}</p>
        <p className="font-mono text-sm font-semibold text-orange" aria-live="polite">
          {query.isPending ? "—" : String(aircraft.length)}
        </p>
      </div>
      {stale ? (
        <span
          className="rounded-full bg-warning/15 px-2 py-0.5 text-[11px] font-medium text-warning"
          title={errorMessage(query.error, "state.staleHint")}
        >
          {t("state.stale")}
        </span>
      ) : null}
    </div>
  );
}
