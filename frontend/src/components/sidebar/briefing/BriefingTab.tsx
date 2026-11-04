import { useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import { FileText } from "lucide-react";
import type { RegionId } from "@/config";
import { briefingQuery } from "@/api/briefing";
import { Markdown } from "@/components/ui/Markdown";
import { EmptyState } from "@/components/ui/state/EmptyState";
import { ErrorState } from "@/components/ui/state/ErrorState";
import { SkeletonLines } from "@/components/ui/state/SkeletonLines";
import { useI18n } from "@/lib/i18n/context";
import { useErrorMessage } from "@/lib/i18n/useErrorMessage";
import { BriefingStats } from "./BriefingStats";

export function BriefingTab({ region, regionLabel }: { region: RegionId; regionLabel: string }) {
  const { t, locale } = useI18n();
  const errorMessage = useErrorMessage();
  const q = useQuery(briefingQuery(region, locale));

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-2 border-b border-border px-4 py-2.5">
        <FileText className="size-3.5 text-yellow" aria-hidden />
        <span className="label-caps">{t("briefing.title")}</span>
      </div>

      {q.isSuccess ? (
        <BriefingStats
          regionLabel={regionLabel}
          aircraftCount={q.data.aircraft_count}
          generatedAt={q.data.generated_at}
        />
      ) : null}

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-3">
        {q.isPending ? <SkeletonLines rows={6} /> : null}
        {q.isError ? (
          <ErrorState
            message={errorMessage(q.error, "state.briefingUnavailable")}
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
