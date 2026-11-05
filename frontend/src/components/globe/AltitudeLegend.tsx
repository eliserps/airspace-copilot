import { MAX_GLOBE_MARKERS } from "@/config";
import { cn } from "@/lib/cn";
import { useI18n } from "@/lib/i18n/context";

export function AltitudeLegend({
  sampled,
  source,
}: {
  sampled: boolean;
  source: string | undefined;
}) {
  const { t } = useI18n();
  return (
    <div className="panel pointer-events-auto absolute bottom-3 left-3 flex max-w-[calc(100%-1.5rem)] flex-wrap items-center gap-x-3 gap-y-1 px-3 py-1.5">
      <LegendDot tone="bg-yellow" label={t("legend.low")} />
      <LegendDot tone="bg-orange" label={t("legend.mid")} />
      <LegendDot tone="bg-violet" label={t("legend.high")} />
      {sampled ? (
        <span className="font-mono text-[10px] text-muted-foreground/80">
          {t("legend.sampled", { shown: MAX_GLOBE_MARKERS })}
        </span>
      ) : null}
      {source ? (
        <span
          className="font-mono text-[10px] text-muted-foreground/80"
          title={t("source.coverage")}
        >
          {t("source.label")}: {source}
        </span>
      ) : null}
      <a
        href="https://www.esri.com"
        target="_blank"
        rel="noreferrer"
        className="font-mono text-[10px] text-muted-foreground/80 hover:text-foreground"
      >
        {t("legend.imagery")}: Esri, Maxar, Earthstar Geographics
      </a>
    </div>
  );
}

function LegendDot({ tone, label }: { tone: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className={cn("size-2 rounded-full", tone)} aria-hidden />
      <span className="font-mono text-[10px] text-muted-foreground">{label}</span>
    </span>
  );
}
