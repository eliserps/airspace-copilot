import type { ReactNode } from "react";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { useI18n } from "@/lib/i18n/context";
import { ErrorState } from "./ErrorState";

function PanelCrashed({ reset }: { reset: () => void }) {
  const { t } = useI18n();
  return (
    <ErrorState message={t("state.panelCrashed")} onRetry={reset} retryLabel={t("state.reload")} />
  );
}

export function PanelBoundary({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary fallback={(reset) => <PanelCrashed reset={reset} />}>{children}</ErrorBoundary>
  );
}
