import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/render";
import { AltitudeLegend } from "./AltitudeLegend";

describe("AltitudeLegend", () => {
  it("credits the satellite imagery", () => {
    renderWithProviders(<AltitudeLegend sampled={false} source={undefined} />, { locale: "pt" });
    expect(
      screen.getByRole("link", { name: "Imagens: Esri, Maxar, Earthstar Geographics" }),
    ).toHaveAttribute("href", "https://www.esri.com");
  });
});
