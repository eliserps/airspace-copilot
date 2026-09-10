import { AlertTriangle, Loader2, Inbox, RotateCw } from "lucide-react";
import { useI18n } from "@/lib/i18n-context";

export function LoadingState({ label }: { label?: string }) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-10 text-center">
      <Loader2 className="size-5 animate-spin text-primary" />
      <p className="label-caps">{label ?? t("state.fetching")}</p>
    </div>
  );
}

export function EmptyState({ label, hint }: { label: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-6 py-10 text-center">
      <Inbox className="size-5 text-muted-foreground" />
      <p className="text-sm font-medium text-foreground">{label}</p>
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: (() => void) | undefined;
}) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-10 text-center">
      <AlertTriangle className="size-5 text-destructive" />
      <p className="text-sm font-medium text-foreground">{t("state.error")}</p>
      <p className="max-w-xs text-xs text-muted-foreground">{message}</p>
      {onRetry ? (
        <button
          onClick={onRetry}
          className="mt-1 inline-flex items-center gap-1.5 rounded-md border border-border bg-secondary px-3 py-1.5 text-xs font-medium text-secondary-foreground transition-colors hover:bg-muted"
        >
          <RotateCw className="size-3.5" /> {t("state.retry")}
        </button>
      ) : null}
    </div>
  );
}

export function SkeletonLines({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-2 p-4">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-3 animate-pulse rounded bg-muted"
          style={{ width: `${90 - i * 12}%`, animationDelay: `${i * 90}ms` }}
        />
      ))}
    </div>
  );
}
