import { describe, expect, it } from "vitest";
import { HttpResponse, http } from "msw";
import { screen } from "@testing-library/react";
import { api, server } from "@/test/server";
import { renderWithProviders } from "@/test/render";
import { BriefingTab } from "./BriefingTab";

function briefing(stale: boolean) {
  return {
    region: "south_america",
    language: "en",
    aircraft_count: 42,
    briefing: "Busy skies.",
    generated_at: 1_700_000_000,
    stale,
    source: "OpenSky (partial volunteer coverage)",
  };
}

describe("BriefingTab", () => {
  it("shows the briefing and the current aircraft count", async () => {
    server.use(http.get(api("/briefing"), () => HttpResponse.json(briefing(false))));
    renderWithProviders(<BriefingTab region="south_america" regionLabel="South America" />);
    expect(await screen.findByText("Busy skies.")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.queryByText("Stale")).not.toBeInTheDocument();
  });

  it("marks briefings written from stale traffic", async () => {
    server.use(http.get(api("/briefing"), () => HttpResponse.json(briefing(true))));
    renderWithProviders(<BriefingTab region="south_america" regionLabel="South America" />);
    expect(await screen.findByText("Stale")).toBeInTheDocument();
  });
});
