import { TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useI18n } from "@/lib/i18n/context";
import { useErrorMessage } from "@/lib/i18n/useErrorMessage";

export function TrafficAlert({ error, onRetry }: { error: unknown; onRetry: () => void }) {
  const { t } = useI18n();
  const errorMessage = useErrorMessage();
  return (
    <div className="panel pointer-events-auto flex max-w-xs items-start gap-2 px-3 py-2">
      <TriangleAlert className="mt-0.5 size-4 shrink-0 text-warning" aria-hidden />
      <p className="text-[11px] leading-snug text-muted-foreground">
        {errorMessage(error, "state.trafficUnavailable")}
      </p>
      <Button size="xs" onClick={onRetry}>
        {t("state.retry")}
      </Button>
    </div>
  );
}
