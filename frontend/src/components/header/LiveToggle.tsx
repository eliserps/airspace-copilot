import { Radio } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";
import { useI18n } from "@/lib/i18n/context";

export function LiveToggle({
  live,
  onChange,
}: {
  live: boolean;
  onChange: (live: boolean) => void;
}) {
  const { t } = useI18n();
  return (
    <Button variant="toggle" aria-pressed={live} onClick={() => onChange(!live)}>
      <Radio className={cn("size-3.5", live && "animate-pulse")} aria-hidden />
      {live ? t("app.live") : t("app.paused")}
    </Button>
  );
}
