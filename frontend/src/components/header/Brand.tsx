import { Logo } from "@/components/ui/Logo";
import { useI18n } from "@/lib/i18n/context";

export function Brand() {
  const { t } = useI18n();
  return (
    <div className="flex items-center gap-2.5">
      <span className="flex size-9 items-center justify-center">
        <Logo className="size-8" />
      </span>
      <div>
        <h1 className="text-sm leading-tight font-semibold tracking-tight text-foreground sm:text-base">
          Airspace Copilot
        </h1>
        <p className="label-caps">{t("app.tagline")}</p>
      </div>
    </div>
  );
}
