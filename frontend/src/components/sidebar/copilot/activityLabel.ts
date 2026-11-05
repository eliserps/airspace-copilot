import type { ToolActivity } from "@/api/copilot";
import { REGION_IDS, type RegionId } from "@/config";
import type { I18nValue } from "@/lib/i18n/context";

export function activityLabel({ name, arguments: args }: ToolActivity, t: I18nValue["t"]) {
  if (name === "get_metar") {
    return t("copilot.tool.get_metar", { icao: String(args["icao_code"] ?? "").toUpperCase() });
  }
  if (name === "count_aircraft") {
    const region = String(args["region"] ?? "").toLowerCase() as RegionId;
    if (REGION_IDS.includes(region)) {
      return t("copilot.tool.count_aircraft", { region: t(`region.${region}`) });
    }
  }
  if (name === "count_aircraft_near" && typeof args["place"] === "string") {
    return t("copilot.tool.count_aircraft_near", { place: args["place"] });
  }
  return t("copilot.tool.other");
}
