import { describe, expect, it } from "vitest";
import { interpolate } from "@/lib/i18n/interpolate";
import { en } from "@/lib/i18n/locales/en";
import type { StringKey } from "@/lib/i18n/strings";
import { activityLabel } from "./activityLabel";

const t = (key: StringKey, vars?: Record<string, string | number>) => interpolate(en[key], vars);

describe("activityLabel", () => {
  it("names the airport, region or place being checked", () => {
    expect(activityLabel({ name: "get_metar", arguments: { icao_code: "sbgr" } }, t)).toBe(
      "Checking the METAR for SBGR…",
    );
    expect(activityLabel({ name: "count_aircraft", arguments: { region: "EUROPE" } }, t)).toBe(
      "Counting aircraft over Europe…",
    );
    expect(activityLabel({ name: "count_aircraft_near", arguments: { place: "London" } }, t)).toBe(
      "Looking for aircraft near London…",
    );
  });

  it("falls back to a generic label for unknown tools or arguments", () => {
    expect(activityLabel({ name: "count_aircraft", arguments: { region: "mars" } }, t)).toBe(
      "Checking live data…",
    );
    expect(activityLabel({ name: "new_tool", arguments: {} }, t)).toBe("Checking live data…");
  });
});
