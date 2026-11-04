import type { RegionId } from "@/config";
import { Brand } from "./Brand";
import { LanguageToggle } from "./LanguageToggle";
import { LiveToggle } from "./LiveToggle";
import { RefreshButton } from "./RefreshButton";
import { RegionSelect } from "./RegionSelect";

export function Header({
  region,
  onRegionChange,
  live,
  onLiveChange,
  refreshing,
  onRefresh,
}: {
  region: RegionId;
  onRegionChange: (region: RegionId) => void;
  live: boolean;
  onLiveChange: (live: boolean) => void;
  refreshing: boolean;
  onRefresh: () => void;
}) {
  return (
    <header className="sticky top-0 z-30 border-b border-border bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-[1800px] flex-wrap items-center gap-3 px-4 py-3">
        <Brand />
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <LanguageToggle />
          <RegionSelect value={region} onChange={onRegionChange} />
          <LiveToggle live={live} onChange={onLiveChange} />
          <RefreshButton refreshing={refreshing} onRefresh={onRefresh} />
        </div>
      </div>
    </header>
  );
}
