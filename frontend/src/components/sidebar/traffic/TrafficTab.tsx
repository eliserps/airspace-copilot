import type { Traffic } from "@/api/traffic";
import { ErrorState } from "@/components/ui/state/ErrorState";
import { LoadingState } from "@/components/ui/state/LoadingState";
import { useI18n } from "@/lib/i18n/context";
import { useErrorMessage } from "@/lib/i18n/useErrorMessage";
import { TrafficList } from "./TrafficList";

export function TrafficTab({
  traffic,
  selectedId,
  onSelect,
}: {
  traffic: Traffic;
  selectedId: string | null;
  onSelect: (icao24: string) => void;
}) {
  const { t } = useI18n();
  const errorMessage = useErrorMessage();
  const { query, aircraft } = traffic;

  return (
    <div className="h-full overflow-y-auto">
      {query.isPending ? (
        <LoadingState label={t("state.scanning")} />
      ) : query.isError && aircraft.length === 0 ? (
        <ErrorState
          message={errorMessage(query.error, "state.trafficUnavailable")}
          onRetry={() => void query.refetch()}
        />
      ) : (
        <TrafficList aircraft={aircraft} selectedId={selectedId} onSelect={onSelect} />
      )}
    </div>
  );
}
