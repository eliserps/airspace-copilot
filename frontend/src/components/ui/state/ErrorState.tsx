import { AlertTriangle, RotateCw } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useI18n } from "@/lib/i18n/context";

export function ErrorState({
  message,
  onRetry,
  retryLabel,
}: {
  message: string;
  onRetry?: (() => void) | undefined;
  retryLabel?: string;
}) {
  const { t } = useI18n();
  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center gap-3 px-6 py-10 text-center"
    >
      <AlertTriangle className="size-5 text-destructive" aria-hidden />
      <p className="text-sm font-medium text-foreground">{t("state.error")}</p>
      <p className="max-w-xs text-xs text-muted-foreground">{message}</p>
      {onRetry ? (
        <Button onClick={onRetry} className="mt-1">
          <RotateCw className="size-3.5" aria-hidden /> {retryLabel ?? t("state.retry")}
        </Button>
      ) : null}
    </div>
  );
}
