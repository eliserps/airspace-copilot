import type { ReactNode } from "react";
import { useI18n } from "@/lib/i18n/context";

export function BriefingStats({
  regionLabel,
  aircraftCount,
  generatedAt,
  stale,
}: {
  regionLabel: string;
  aircraftCount: number;
  generatedAt: number;
  stale: boolean;
}) {
  const { t, locale } = useI18n();
  const updatedAt = generatedAt
    ? new Date(generatedAt * 1000).toLocaleTimeString(locale === "pt" ? "pt-BR" : "en-US", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : "—";

  return (
    <dl className="grid grid-cols-3 gap-px border-b border-border bg-border">
      <Stat label={t("briefing.region")} value={regionLabel} tone="truncate text-violet" />
      <Stat label={t("briefing.tracked")} value={String(aircraftCount)} tone="text-orange" />
      <Stat label={t("briefing.updated")} value={updatedAt} tone="text-foreground">
        {stale ? (
          <span
            className="ml-2 rounded-full bg-warning/15 px-2 py-0.5 font-sans text-[11px] font-medium text-warning"
            title={t("state.staleHint")}
          >
            {t("state.stale")}
          </span>
        ) : null}
      </Stat>
    </dl>
  );
}

function Stat({
  label,
  value,
  tone,
  children,
}: {
  label: string;
  value: string;
  tone: string;
  children?: ReactNode;
}) {
  return (
    <div className="bg-background px-4 py-2.5">
      <dt className="label-caps">{label}</dt>
      <dd className={`mt-0.5 font-mono text-sm font-semibold ${tone}`}>
        {value}
        {children}
      </dd>
    </div>
  );
}
