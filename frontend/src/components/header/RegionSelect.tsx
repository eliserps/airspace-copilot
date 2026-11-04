import { REGIONS, type RegionId } from "@/config";
import { useI18n } from "@/lib/i18n/context";
import type { StringKey } from "@/lib/i18n/strings";

export function RegionSelect({
  value,
  onChange,
}: {
  value: RegionId;
  onChange: (region: RegionId) => void;
}) {
  const { t } = useI18n();
  return (
    <>
      <label className="sr-only" htmlFor="region-select">
        {t("app.region")}
      </label>
      <select
        id="region-select"
        value={value}
        onChange={(e) => onChange(e.target.value as RegionId)}
        className="rounded-lg border border-input bg-surface px-2.5 py-1.5 text-xs font-medium text-foreground outline-none focus:border-primary"
      >
        {REGIONS.map((r) => (
          <option key={r.id} value={r.id}>
            {t(`region.${r.id}` as StringKey)}
          </option>
        ))}
      </select>
    </>
  );
}
