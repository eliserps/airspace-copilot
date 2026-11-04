import { Radar } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useI18n } from "@/lib/i18n/context";
import type { StringKey } from "@/lib/i18n/strings";

const SUGGESTION_KEYS: StringKey[] = ["copilot.suggest1", "copilot.suggest2", "copilot.suggest3"];

export function CopilotWelcome({
  regionLabel,
  onAsk,
}: {
  regionLabel: string;
  onAsk: (question: string) => void;
}) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col items-start gap-3 py-6">
      <div className="flex items-center gap-2 text-primary">
        <Radar className="size-4" aria-hidden />
        <p className="label-caps text-primary">{t("copilot.standingBy")}</p>
      </div>
      <p className="text-sm text-muted-foreground">
        {t("copilot.ask")} <span className="font-mono text-foreground">{regionLabel}</span>.
      </p>
      <div className="flex flex-wrap gap-2">
        {SUGGESTION_KEYS.map((key) => (
          <Button key={key} variant="chip" onClick={() => onAsk(t(key))}>
            {t(key)}
          </Button>
        ))}
      </div>
    </div>
  );
}
