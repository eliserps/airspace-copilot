import { Markdown } from "@/components/ui/Markdown";
import { useI18n } from "@/lib/i18n/context";

export function MetarReport({ raw, decoded }: { raw: string; decoded: string }) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col gap-3">
      <section className="rounded-lg border border-border bg-surface-2/40 px-3 py-2">
        <p className="label-caps mb-1">{t("weather.raw")}</p>
        <pre className="font-mono text-[0.78rem] leading-relaxed break-words whitespace-pre-wrap text-primary">
          {raw || "—"}
        </pre>
      </section>
      <section className="rounded-lg border border-border bg-surface/40 p-3">
        <p className="label-caps mb-2">{t("weather.decoded")}</p>
        {decoded ? (
          <Markdown>{decoded}</Markdown>
        ) : (
          <p className="text-sm text-muted-foreground">{t("weather.noDecoded")}</p>
        )}
      </section>
    </div>
  );
}
