import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CloudSun, Search } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Markdown } from "@/components/Markdown";
import { EmptyState, ErrorState, SkeletonLines } from "@/components/StatePanels";
import { useI18n } from "@/lib/i18n-context";

export function WeatherCard({ defaultIcao }: { defaultIcao: string }) {
  const { t, locale } = useI18n();
  const [icao, setIcao] = useState(defaultIcao);
  const [query, setQuery] = useState(defaultIcao);

  const q = useQuery({
    queryKey: ["weather", query, locale],
    queryFn: () => api.weather(query, locale),
    enabled: query.length >= 3,
    staleTime: 15 * 60_000,
  });

  return (
    <div className="flex h-full min-h-0 flex-col">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          const next = icao.trim().toUpperCase();
          if (next.length >= 3) setQuery(next);
        }}
        className="flex items-center gap-2 border-b border-border px-4 py-2.5"
      >
        <CloudSun className="size-4 shrink-0 text-primary" />
        <input
          value={icao}
          onChange={(e) => setIcao(e.target.value.toUpperCase())}
          maxLength={4}
          placeholder={t("weather.icao")}
          aria-label={t("weather.icaoLabel")}
          className="w-24 rounded-md border border-input bg-background/60 px-2 py-1 font-mono text-sm tracking-widest text-foreground outline-none focus:border-primary focus:shadow-glow"
        />
        <button
          type="submit"
          className="inline-flex items-center gap-1.5 rounded-md bg-secondary px-2.5 py-1.5 text-xs font-medium text-secondary-foreground transition-colors hover:bg-muted"
        >
          <Search className="size-3.5" /> METAR
        </button>
      </form>

      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        {query.length < 3 ? (
          <EmptyState label={t("weather.enterIcao")} hint={t("weather.example")} />
        ) : q.isPending ? (
          <SkeletonLines rows={5} />
        ) : q.isError ? (
          <ErrorState
            message={q.error instanceof ApiError ? q.error.message : t("state.weatherUnavailable")}
            onRetry={() => void q.refetch()}
          />
        ) : !q.data?.raw && !q.data?.decoded ? (
          <EmptyState label={`${t("weather.noReport")} ${query}`} />
        ) : (
          <div className="flex flex-col gap-3">
            <section className="rounded-lg border border-border bg-surface-2/40 px-3 py-2">
              <p className="label-caps mb-1">{t("weather.raw")}</p>
              <pre className="font-mono text-[0.78rem] leading-relaxed break-words whitespace-pre-wrap text-primary">
                {q.data.raw || "—"}
              </pre>
            </section>
            <section className="rounded-lg border border-border bg-surface/40 p-3">
              <p className="label-caps mb-2">{t("weather.decoded")}</p>
              {q.data.decoded ? (
                <Markdown>{q.data.decoded}</Markdown>
              ) : (
                <p className="text-sm text-muted-foreground">{t("weather.noDecoded")}</p>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
