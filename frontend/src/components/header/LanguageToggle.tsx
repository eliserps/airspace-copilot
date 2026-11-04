import { cn } from "@/lib/cn";
import { useI18n } from "@/lib/i18n/context";
import type { Locale } from "@/lib/i18n/strings";

const LOCALES: Locale[] = ["en", "pt"];

export function LanguageToggle() {
  const { t, locale, setLocale } = useI18n();
  return (
    <div
      className="flex items-center gap-0.5 rounded-lg border border-input bg-surface p-0.5"
      role="group"
      aria-label={t("app.language")}
    >
      {LOCALES.map((l) => (
        <button
          key={l}
          type="button"
          onClick={() => setLocale(l)}
          aria-pressed={locale === l}
          className={cn(
            "rounded-md px-2 py-1 text-[11px] font-semibold tracking-wide transition-colors",
            locale === l
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
