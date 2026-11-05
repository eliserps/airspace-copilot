import { describe, expect, it, vi } from "vitest";
import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryHistory, createRouter } from "@tanstack/react-router";
import { routeTree } from "@/routeTree.gen";
import { testQueryClient } from "@/test/render";
import { App } from "./App";

vi.mock("@/components/globe/GlobeView", () => ({
  default: ({ aircraft }: { aircraft: unknown[] }) => (
    <div>globe with {aircraft.length} markers</div>
  ),
}));

async function renderAt(url: string) {
  const router = createRouter({
    routeTree,
    history: createMemoryHistory({ initialEntries: [url] }),
  });
  await act(() => router.load());
  render(<App router={router} queryClient={testQueryClient()} locale="en" />);
  return router;
}

describe("App", { timeout: 20_000 }, () => {
  it("restores region and tab from the URL", async () => {
    await renderAt("/?region=europe&tab=weather");
    expect(await screen.findByLabelText("Region")).toHaveValue("europe");
    expect(screen.getByRole("tab", { name: "Weather" })).toHaveAttribute("aria-selected", "true");
    expect(await screen.findByText(/EDDF 091800Z/)).toBeInTheDocument();
  });

  it("falls back to defaults for invalid search params", async () => {
    await renderAt("/?region=mars&tab=nope");
    expect(await screen.findByLabelText("Region")).toHaveValue("south_america");
    expect(screen.getByRole("tab", { name: "Copilot" })).toHaveAttribute("aria-selected", "true");
  });

  it("writes tab and selection changes back to the URL", async () => {
    const router = await renderAt("/");
    const user = userEvent.setup();

    expect(await screen.findByText("globe with 1 markers")).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: "Traffic" }));
    await user.click(within(screen.getByRole("tabpanel")).getByRole("button", { name: /TAM3456/ }));

    expect(router.state.location.search).toEqual({ tab: "traffic", aircraft: "abc123" });
    expect(screen.getByRole("button", { name: "Close aircraft details" })).toBeInTheDocument();
  });

  it("shows a 404 page for unknown routes", async () => {
    await renderAt("/nowhere");
    expect(await screen.findByText("404")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to the map" })).toBeInTheDocument();
  });
});
