import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MAX_LIST_ROWS } from "@/config";
import { aircraft } from "@/test/server";
import { renderWithProviders } from "@/test/render";
import { TrafficList } from "./TrafficList";

describe("TrafficList", () => {
  it("falls back to the transponder code when there is no callsign", () => {
    renderWithProviders(
      <TrafficList
        aircraft={[aircraft({ icao24: "e4801a", callsign: null })]}
        selectedId={null}
        onSelect={() => {}}
      />,
    );
    expect(screen.getAllByText(/e4801a/)).toHaveLength(2);
  });

  it("selects an aircraft on click and marks it as current", async () => {
    const onSelect = vi.fn();
    renderWithProviders(
      <TrafficList
        aircraft={[aircraft({ icao24: "a" }), aircraft({ icao24: "b", callsign: "GLO1" })]}
        selectedId="a"
        onSelect={onSelect}
      />,
    );
    await userEvent.setup().click(screen.getByRole("button", { name: /GLO1/ }));
    expect(onSelect).toHaveBeenCalledWith("b");
    expect(screen.getByRole("button", { current: true })).toHaveTextContent("TAM3456");
  });

  it("caps the list and says how many are hidden", () => {
    const many = Array.from({ length: MAX_LIST_ROWS + 5 }, (_, i) => aircraft({ icao24: `x${i}` }));
    renderWithProviders(<TrafficList aircraft={many} selectedId={null} onSelect={() => {}} />);
    expect(
      screen.getByText(`Showing ${MAX_LIST_ROWS} of ${MAX_LIST_ROWS + 5} aircraft.`),
    ).toBeInTheDocument();
  });

  it("shows an empty state", () => {
    renderWithProviders(<TrafficList aircraft={[]} selectedId={null} onSelect={() => {}} />);
    expect(screen.getByText("No aircraft in view")).toBeInTheDocument();
  });
});
