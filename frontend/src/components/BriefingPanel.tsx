import { useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import { FileText } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Markdown } from "@/components/Markdown";
import { EmptyState, ErrorState, SkeletonLines } from "@/components/StatePanels";
import { useI18n } from "@/lib/i18n-context";

export function BriefingPanel({ region, regionLabel }: { region: string; regionLabel: string }) {
  const { t, locale } = useI18n();

  const q = useQuery({
    queryKey: ["briefing", region, locale],
    queryFn: () => api.briefing(region, locale),
    staleTime: 5 * 60_000,
  });

  const updatedAt = q.data?.generated_at
    ? new Date(q.data.generated_at * 1000).toLocaleTimeString(locale === "pt" ? "pt-BR" : "en-US", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-2 border-b border-border px-4 py-2.5">
        <FileText className="size-3.5 text-yellow" />
        <span className="label-caps">{t("briefing.title")}</span>
      </div>

      {q.isSuccess ? (
        <dl className="grid grid-cols-3 gap-px border-b border-border bg-border">
          <div className="bg-background px-4 py-2.5">
            <dt className="label-caps">{t("briefing.region")}</dt>
            <dd className="mt-0.5 truncate font-mono text-sm font-semibold text-violet">
              {regionLabel}
            </dd>
          </div>
          <div className="bg-background px-4 py-2.5">
            <dt className="label-caps">{t("briefing.tracked")}</dt>
            <dd className="mt-0.5 font-mono text-sm font-semibold text-orange">
              {q.data.aircraft_count}
            </dd>
          </div>
          <div className="bg-background px-4 py-2.5">
            <dt className="label-caps">{t("briefing.updated")}</dt>
            <dd className="mt-0.5 font-mono text-sm font-semibold text-foreground">
              {updatedAt ?? "—"}
            </dd>
          </div>
        </dl>
      ) : null}

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-3">
        {q.isPending ? <SkeletonLines rows={6} /> : null}
        {q.isError ? (
          <ErrorState
            message={q.error instanceof ApiError ? q.error.message : t("state.briefingUnavailable")}
            onRetry={() => void q.refetch()}
          />
        ) : null}
        {q.isSuccess ? (
          q.data.briefing.trim().length > 0 ? (
            <motion.div key={locale} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}>
              <Markdown>{q.data.briefing}</Markdown>
            </motion.div>
          ) : (
            <EmptyState label={t("state.noBriefing")} hint={t("state.tryAnotherRegion")} />
          )
        ) : null}
      </div>

      {q.isSuccess && q.data.source ? (
        <p
          className="border-t border-border px-4 py-2 font-mono text-[10px] text-muted-foreground"
          title={t("source.coverage")}
        >
          {t("source.label")}: {q.data.source}
        </p>
      ) : null}
    </div>
  );
}
