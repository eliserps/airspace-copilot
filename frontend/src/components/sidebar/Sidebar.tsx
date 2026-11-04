import type { Region } from "@/config";
import type { Traffic } from "@/api/traffic";
import { PanelBoundary } from "@/components/ui/state/PanelBoundary";
import { TabList, TabPanel } from "@/components/ui/Tabs";
import { useI18n } from "@/lib/i18n/context";
import type { StringKey } from "@/lib/i18n/strings";
import { BriefingTab } from "./briefing/BriefingTab";
import { CopilotTab } from "./copilot/CopilotTab";
import { TABS, type TabId } from "./tabs";
import { TrafficTab } from "./traffic/TrafficTab";
import { WeatherTab } from "./weather/WeatherTab";

export function Sidebar({
  region,
  tab,
  onTabChange,
  traffic,
  selectedId,
  onSelect,
}: {
  region: Region;
  tab: TabId;
  onTabChange: (tab: TabId) => void;
  traffic: Traffic;
  selectedId: string | null;
  onSelect: (icao24: string) => void;
}) {
  const { t } = useI18n();
  const regionLabel = t(`region.${region.id}` as StringKey);
  const items = TABS.map((item) => ({ ...item, label: t(`tab.${item.id}` as StringKey) }));

  return (
    <section className="panel flex h-[70vh] min-h-[420px] flex-col overflow-hidden lg:h-auto lg:w-[26rem] lg:shrink-0">
      <TabList items={items} active={tab} onChange={onTabChange} label={t("app.panels")} />

      <div className="min-h-0 flex-1 overflow-hidden">
        <TabPanel id="copilot" active={tab === "copilot"} keepMounted>
          <PanelBoundary>
            <CopilotTab regionId={region.id} regionLabel={regionLabel} />
          </PanelBoundary>
        </TabPanel>
        <TabPanel id="traffic" active={tab === "traffic"}>
          <PanelBoundary>
            <TrafficTab traffic={traffic} selectedId={selectedId} onSelect={onSelect} />
          </PanelBoundary>
        </TabPanel>
        <TabPanel id="briefing" active={tab === "briefing"}>
          <PanelBoundary>
            <BriefingTab region={region.id} regionLabel={regionLabel} />
          </PanelBoundary>
        </TabPanel>
        <TabPanel id="weather" active={tab === "weather"}>
          <PanelBoundary>
            <WeatherTab key={region.metar} defaultIcao={region.metar} />
          </PanelBoundary>
        </TabPanel>
      </div>
    </section>
  );
}
