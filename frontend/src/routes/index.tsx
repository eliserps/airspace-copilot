import { createFileRoute } from "@tanstack/react-router";
import { ClientOnly } from "@tanstack/react-router";
import { Suspense, lazy, useMemo, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "motion/react";
import {
  Radar,
  RefreshCw,
  Radio,
  MessageSquare,
  FileText,
  CloudSun,
  Plane,
  TriangleAlert,
} from "lucide-react";
import { REGIONS, DEFAULT_REGION, MAX_GLOBE_MARKERS, type Region } from "@/config";
import { sampleSpread } from "@/lib/markers";
import { api, ApiError } from "@/lib/api";
import { ChatPanel } from "@/components/ChatPanel";
import { BriefingPanel } from "@/components/BriefingPanel";
import { WeatherCard } from "@/components/WeatherCard";
import { TrafficList } from "@/components/TrafficList";
import { AircraftDetail } from "@/components/AircraftDetail";
import { ErrorState, LoadingState } from "@/components/StatePanels";
import { Logo } from "@/components/Logo";
import { useI18n } from "@/lib/i18n-context";
import type { Locale, StringKey } from "@/lib/i18n-strings";
import { cn } from "@/lib/utils";

const GlobeView = lazy(() => import("@/components/GlobeView"));

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Airspace Copilot" },
      {
        name: "description",
        content:
          "Track live aircraft on a 3D globe, ask a copilot about traffic, and read regional briefings and decoded METAR weather.",
      },
      { property: "og:title", content: "Airspace Copilot" },
      {
        property: "og:description",
        content:
          "A 3D globe with live aircraft markers, a copilot chat, regional briefings in EN/PT-BR, and decoded METAR weather.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

type TabId = "copilot" | "traffic" | "briefing" | "weather";

const TABS: Array<{ id: TabId; labelKey: StringKey; icon: typeof Radar; tone: string }> = [
  { id: "copilot", labelKey: "tab.copilot", icon: MessageSquare, tone: "text-violet" },
  { id: "traffic", labelKey: "tab.traffic", icon: Plane, tone: "text-orange" },
  { id: "briefing", labelKey: "tab.briefing", icon: FileText, tone: "text-yellow" },
  { id: "weather", labelKey: "tab.weather", icon: CloudSun, tone: "text-primary" },
];

function Index() {
  const [region, setRegion] = useState<Region>(DEFAULT_REGION);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [tab, setTab] = useState<TabId>("copilot");
  const [live, setLive] = useState(true);
  const { t, locale, setLocale } = useI18n();

  const traffic = useQuery({
    queryKey: ["aircraft", region.id],
    queryFn: () => api.aircraftMap(region.id),
    refetchInterval: live ? 60_000 : false,
    staleTime: 45_000,
    placeholderData: keepPreviousData,
    retry: 2,
  });

  const aircraft = useMemo(() => traffic.data?.aircraft ?? [], [traffic.data]);
  const selected = aircraft.find((a) => a.icao24 === selectedId) ?? null;

  const globeAircraft = useMemo(() => {
    if (aircraft.length <= MAX_GLOBE_MARKERS) return aircraft;
    const sample = sampleSpread(aircraft, MAX_GLOBE_MARKERS);
    if (selected && !sample.includes(selected)) sample.push(selected);
    return sample;
  }, [aircraft, selected]);

  return (
    <main className="flex min-h-screen flex-col lg:h-screen">
      <header className="sticky top-0 z-30 border-b border-border bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-[1800px] flex-wrap items-center gap-3 px-4 py-3">
          <div className="flex items-center gap-2.5">
            <span className="flex size-9 items-center justify-center">
              <Logo className="size-8" />
            </span>
            <div>
              <h1 className="text-sm leading-tight font-semibold tracking-tight text-foreground sm:text-base">
                Airspace Copilot
              </h1>
              <p className="label-caps">{t("app.tagline")}</p>
            </div>
          </div>

          <div className="ml-auto flex flex-wrap items-center gap-2">
            <div
              className="flex items-center gap-0.5 rounded-lg border border-input bg-surface p-0.5"
              role="group"
              aria-label={t("app.language")}
            >
              {(["en", "pt"] as Locale[]).map((l) => (
                <button
                  key={l}
                  onClick={() => setLocale(l)}
                  aria-pressed={locale === l}
                  className={cn(
                    "rounded-md px-2 py-1 text-[11px] font-semibold tracking-wide transition-colors",
                    locale === l
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {l === "en" ? "EN" : "PT"}
                </button>
              ))}
            </div>

            <label className="sr-only" htmlFor="region-select">
              {t("app.region")}
            </label>
            <select
              id="region-select"
              value={region.id}
              onChange={(e) => {
                const next = REGIONS.find((r) => r.id === e.target.value);
                if (next) {
                  setRegion(next);
                  setSelectedId(null);
                }
              }}
              className="rounded-lg border border-input bg-surface px-2.5 py-1.5 text-xs font-medium text-foreground outline-none focus:border-primary"
            >
              {REGIONS.map((r) => (
                <option key={r.id} value={r.id}>
                  {t(`region.${r.id}` as StringKey)}
                </option>
              ))}
            </select>

            <button
              onClick={() => setLive((v) => !v)}
              aria-pressed={live}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors",
                live
                  ? "border-primary/50 bg-primary/10 text-primary"
                  : "border-border bg-secondary text-muted-foreground",
              )}
            >
              <Radio className={cn("size-3.5", live && "animate-pulse")} />
              {live ? t("app.live") : t("app.paused")}
            </button>

            <button
              onClick={() => void traffic.refetch()}
              aria-label={t("app.refreshTraffic")}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-secondary px-2.5 py-1.5 text-xs font-medium text-secondary-foreground transition-colors hover:bg-muted"
            >
              <RefreshCw className={cn("size-3.5", traffic.isFetching && "animate-spin")} />
              <span className="hidden sm:inline">{t("app.refresh")}</span>
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-[1800px] flex-1 flex-col gap-4 p-4 lg:min-h-0 lg:flex-row">
        <section className="panel relative h-[52vh] min-h-[320px] overflow-hidden lg:h-auto lg:min-h-[560px] lg:flex-1">
          <div className="absolute inset-0">
            <ClientOnly fallback={<LoadingState label={t("state.globe")} />}>
              <Suspense fallback={<LoadingState label={t("state.globe")} />}>
                <GlobeView
                  aircraft={globeAircraft}
                  region={region}
                  selectedId={selectedId}
                  onSelect={(id) => setSelectedId(id)}
                />
              </Suspense>
            </ClientOnly>
          </div>

          <div className="pointer-events-none absolute inset-x-0 top-0 flex items-start justify-between gap-2 p-3">
            <div className="panel pointer-events-auto flex items-center gap-4 px-3 py-2">
              <div>
                <p className="label-caps">{t("app.aircraft")}</p>
                <p className="font-mono text-sm font-semibold text-orange">
                  {traffic.isPending ? "—" : String(aircraft.length)}
                </p>
              </div>
              {traffic.isError && aircraft.length > 0 ? (
                <span
                  className="rounded-full bg-amber-500/15 px-2 py-0.5 text-[11px] font-medium text-amber-500"
                  title={traffic.error instanceof ApiError ? traffic.error.message : undefined}
                >
                  {t("state.stale")}
                </span>
              ) : null}
            </div>

            {traffic.isError ? (
              <div className="panel pointer-events-auto flex max-w-xs items-start gap-2 px-3 py-2">
                <TriangleAlert className="mt-0.5 size-4 shrink-0 text-warning" />
                <p className="text-[11px] leading-snug text-muted-foreground">
                  {traffic.error instanceof ApiError
                    ? traffic.error.message
                    : t("state.trafficUnavailable")}
                </p>
                <button
                  onClick={() => void traffic.refetch()}
                  className="shrink-0 rounded-md bg-secondary px-2 py-1 text-[11px] font-medium text-secondary-foreground transition-colors hover:bg-muted"
                >
                  {t("state.retry")}
                </button>
              </div>
            ) : null}
          </div>

          <div className="panel pointer-events-auto absolute bottom-3 left-3 flex max-w-[calc(100%-1.5rem)] flex-wrap items-center gap-x-3 gap-y-1 px-3 py-1.5">
            <LegendDot tone="bg-yellow" label={t("legend.low")} />
            <LegendDot tone="bg-orange" label={t("legend.mid")} />
            <LegendDot tone="bg-violet" label={t("legend.high")} />
            {globeAircraft.length < aircraft.length ? (
              <span className="font-mono text-[10px] text-muted-foreground/80">
                {t("legend.sampled").replace("{shown}", String(MAX_GLOBE_MARKERS))}
              </span>
            ) : null}
            {traffic.data?.source ? (
              <span
                className="font-mono text-[10px] text-muted-foreground/80"
                title={t("source.coverage")}
              >
                {t("source.label")}: {traffic.data.source}
              </span>
            ) : null}
          </div>

          <div className="pointer-events-none absolute right-3 bottom-3">
            <AnimatePresence>
              {selected ? (
                <AircraftDetail aircraft={selected} onClose={() => setSelectedId(null)} />
              ) : null}
            </AnimatePresence>
          </div>
        </section>

        <section className="panel flex h-[70vh] min-h-[420px] flex-col overflow-hidden lg:h-auto lg:w-[26rem] lg:shrink-0">
          <nav className="flex items-center gap-1 border-b border-border p-2">
            {TABS.map((tabDef) => {
              const Icon = tabDef.icon;
              const active = tab === tabDef.id;
              return (
                <button
                  key={tabDef.id}
                  onClick={() => setTab(tabDef.id)}
                  aria-pressed={active}
                  className="relative flex flex-1 items-center justify-center gap-1.5 rounded-lg px-2 py-2 text-xs font-medium"
                >
                  {active ? (
                    <motion.span
                      layoutId="tab-pill"
                      className="absolute inset-0 rounded-lg bg-secondary"
                      transition={{ type: "spring", stiffness: 420, damping: 34 }}
                    />
                  ) : null}
                  <Icon
                    className={cn(
                      "relative size-3.5",
                      active ? tabDef.tone : "text-muted-foreground",
                    )}
                  />
                  <span
                    className={cn(
                      "relative hidden sm:inline",
                      active ? "text-foreground" : "text-muted-foreground",
                    )}
                  >
                    {t(tabDef.labelKey)}
                  </span>
                </button>
              );
            })}
          </nav>

          <div className="min-h-0 flex-1 overflow-hidden">
            {tab === "copilot" ? (
              <ChatPanel region={t(`region.${region.id}` as StringKey)} />
            ) : null}
            {tab === "traffic" ? (
              <div className="h-full overflow-y-auto">
                {traffic.isPending ? (
                  <LoadingState label={t("state.scanning")} />
                ) : traffic.isError && aircraft.length === 0 ? (
                  <ErrorState
                    message={
                      traffic.error instanceof ApiError
                        ? traffic.error.message
                        : t("state.trafficUnavailable")
                    }
                    onRetry={() => void traffic.refetch()}
                  />
                ) : (
                  <TrafficList
                    aircraft={aircraft}
                    selectedId={selectedId}
                    onSelect={(id) => setSelectedId(id)}
                  />
                )}
              </div>
            ) : null}
            {tab === "briefing" ? (
              <BriefingPanel
                region={region.id}
                regionLabel={t(`region.${region.id}` as StringKey)}
              />
            ) : null}
            {tab === "weather" ? <WeatherCard defaultIcao={region.metar} /> : null}
          </div>
        </section>
      </div>
    </main>
  );
}

function LegendDot({ tone, label }: { tone: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className={cn("size-2 rounded-full", tone)} />
      <span className="font-mono text-[10px] text-muted-foreground">{label}</span>
    </span>
  );
}
