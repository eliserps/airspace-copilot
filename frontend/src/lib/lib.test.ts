import { describe, expect, it } from "vitest";
import { HttpResponse, http as mock } from "msw";
import { altitudeBand, sampleSpread } from "@/components/globe/markers";
import { formatAltitude, formatHeading, formatSpeed } from "@/lib/units";
import { interpolate } from "@/lib/i18n/interpolate";
import { ApiError, http, unwrap } from "@/api/client";
import { api, server } from "@/test/server";

describe("interpolate", () => {
  it("replaces known placeholders and keeps unknown ones", () => {
    expect(interpolate("Showing {shown} of {total}", { shown: 3, total: 10 })).toBe(
      "Showing 3 of 10",
    );
    expect(interpolate("{a} {b}", { a: 1 })).toBe("1 {b}");
  });
});

describe("units", () => {
  it("formats metric values in aviation units", () => {
    expect(formatAltitude(10000, "en")).toBe("32,808 ft");
    expect(formatAltitude(10000, "pt")).toBe("32.808 ft");
    expect(formatSpeed(100)).toBe("194 kt");
    expect(formatHeading(89.6)).toBe("90°");
  });

  it("renders a dash for missing values", () => {
    expect(formatAltitude(null)).toBe("—");
    expect(formatSpeed(undefined)).toBe("—");
    expect(formatHeading(Number.NaN)).toBe("—");
  });
});

describe("markers", () => {
  it("bands altitude like the legend", () => {
    expect(altitudeBand(null)).toBe("low");
    expect(altitudeBand(2999)).toBe("low");
    expect(altitudeBand(5000)).toBe("mid");
    expect(altitudeBand(9000)).toBe("high");
  });

  it("samples across grid cells instead of taking the first N", () => {
    const crowded = Array.from({ length: 100 }, () => ({ latitude: 1, longitude: 1 }));
    const remote = { latitude: 60, longitude: 60 };
    const sample = sampleSpread([...crowded, remote], 10);
    expect(sample).toHaveLength(10);
    expect(sample).toContain(remote);
  });
});

describe("api client", () => {
  it("surfaces the backend error message and status", async () => {
    server.use(
      mock.get(api("/aircraft/map"), () =>
        HttpResponse.json({ error: "rate_limited", message: "Quota reached." }, { status: 429 }),
      ),
    );
    const error = await unwrap(
      http.GET("/aircraft/map", { params: { query: { region: "europe" } } }),
    ).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ message: "Quota reached.", status: 429, code: "rate_limited" });
  });

  it("reports an unreachable API", async () => {
    server.use(mock.get(api("/health"), () => HttpResponse.error()));
    await expect(unwrap(http.GET("/health"))).rejects.toThrow(/Could not reach/);
  });
});
