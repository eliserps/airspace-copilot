import { Loader2 } from "lucide-react";
import { useI18n } from "@/lib/i18n/context";

export function LoadingState({ label }: { label?: string }) {
  const { t } = useI18n();
  return (
    <div
      role="status"
      className="flex flex-col items-center justify-center gap-3 px-6 py-10 text-center"
    >
      <Loader2 className="size-5 animate-spin text-primary" aria-hidden />
      <p className="label-caps">{label ?? t("state.fetching")}</p>
    </div>
  );
}
