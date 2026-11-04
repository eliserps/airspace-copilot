import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";
import { useI18n } from "@/lib/i18n/context";

export function RefreshButton({
  refreshing,
  onRefresh,
}: {
  refreshing: boolean;
  onRefresh: () => void;
}) {
  const { t } = useI18n();
  return (
    <Button onClick={onRefresh} aria-label={t("app.refreshTraffic")}>
      <RefreshCw className={cn("size-3.5", refreshing && "animate-spin")} aria-hidden />
      <span className="hidden sm:inline">{t("app.refresh")}</span>
    </Button>
  );
}
