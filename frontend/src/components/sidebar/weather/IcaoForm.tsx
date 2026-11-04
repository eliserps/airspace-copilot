import { useState } from "react";
import { CloudSun, Search } from "lucide-react";
import { ICAO } from "@/api/weather";
import { Button } from "@/components/ui/Button";
import { useI18n } from "@/lib/i18n/context";

export function IcaoForm({
  defaultValue,
  invalid,
  onInvalidChange,
  onSubmit,
}: {
  defaultValue: string;
  invalid: boolean;
  onInvalidChange: (invalid: boolean) => void;
  onSubmit: (icao: string) => void;
}) {
  const { t } = useI18n();
  const [value, setValue] = useState(defaultValue);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const next = value.trim().toUpperCase();
        const ok = ICAO.test(next);
        onInvalidChange(!ok);
        if (ok) onSubmit(next);
      }}
      className="flex items-center gap-2 border-b border-border px-4 py-2.5"
    >
      <CloudSun className="size-4 shrink-0 text-primary" aria-hidden />
      <input
        value={value}
        onChange={(e) => {
          setValue(e.target.value.toUpperCase());
          onInvalidChange(false);
        }}
        aria-invalid={invalid}
        maxLength={4}
        placeholder={t("weather.icao")}
        aria-label={t("weather.icaoLabel")}
        className="w-24 rounded-md border border-input bg-background/60 px-2 py-1 font-mono text-sm tracking-widest text-foreground outline-none focus:border-primary focus:shadow-glow"
      />
      <Button type="submit">
        <Search className="size-3.5" aria-hidden /> METAR
      </Button>
    </form>
  );
}
