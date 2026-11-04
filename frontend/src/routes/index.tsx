import { createFileRoute, stripSearchParams } from "@tanstack/react-router";
import { useState } from "react";
import { z } from "zod";
import { DEFAULT_REGION, REGION_IDS, regionById } from "@/config";
import { useTraffic } from "@/api/traffic";
import { GlobePanel } from "@/components/globe/GlobePanel";
import { Header } from "@/components/header/Header";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { TAB_IDS } from "@/components/sidebar/tabs";

const defaults = { region: DEFAULT_REGION.id, tab: "copilot" } as const;

const searchSchema = z.object({
  region: z.enum(REGION_IDS).default(defaults.region).catch(defaults.region),
  tab: z.enum(TAB_IDS).default(defaults.tab).catch(defaults.tab),
  aircraft: z.string().optional().catch(undefined),
});

export const Route = createFileRoute("/")({
  validateSearch: searchSchema,
  search: { middlewares: [stripSearchParams(defaults)] },
  component: Index,
});

function Index() {
  const search = Route.useSearch();
  const navigate = Route.useNavigate();
  const [live, setLive] = useState(true);

  const region = regionById(search.region);
  const traffic = useTraffic(region.id, live);
  const selected = traffic.aircraft.find((a) => a.icao24 === search.aircraft) ?? null;

  function update(patch: Partial<z.infer<typeof searchSchema>>) {
    void navigate({ search: (prev) => ({ ...prev, ...patch }), replace: true });
  }

  return (
    <main className="flex min-h-screen flex-col lg:h-screen">
      <Header
        region={region.id}
        onRegionChange={(id) => update({ region: id, aircraft: undefined })}
        live={live}
        onLiveChange={setLive}
        refreshing={traffic.query.isFetching}
        onRefresh={() => void traffic.query.refetch()}
      />
      <div className="mx-auto flex w-full max-w-[1800px] flex-1 flex-col gap-4 p-4 lg:min-h-0 lg:flex-row">
        <GlobePanel
          region={region}
          traffic={traffic}
          selected={selected}
          onSelect={(icao24) => update({ aircraft: icao24 })}
        />
        <Sidebar
          region={region}
          tab={search.tab}
          onTabChange={(tab) => update({ tab })}
          traffic={traffic}
          selectedId={selected?.icao24 ?? null}
          onSelect={(icao24) => update({ aircraft: icao24 })}
        />
      </div>
    </main>
  );
}
