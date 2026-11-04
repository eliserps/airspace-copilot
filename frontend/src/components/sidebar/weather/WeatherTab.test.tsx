import { describe, expect, it } from "vitest";
import { HttpResponse, http } from "msw";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { api, server } from "@/test/server";
import { renderWithProviders } from "@/test/render";
import { WeatherTab } from "./WeatherTab";

describe("WeatherTab", () => {
  it("loads the region's default airport", async () => {
    renderWithProviders(<WeatherTab defaultIcao="SBGR" />);
    expect(await screen.findByText(/SBGR 091800Z/)).toBeInTheDocument();
    expect(await screen.findByText("Wind")).toBeInTheDocument();
  });

  it("rejects IATA codes without calling the API", async () => {
    renderWithProviders(<WeatherTab defaultIcao="SBGR" />);
    const user = userEvent.setup();
    const input = screen.getByLabelText("Airport ICAO code");
    await user.clear(input);
    await user.type(input, "GRU{Enter}");
    expect(screen.getByText(/SBGR, not GRU/)).toBeInTheDocument();
    expect(input).toHaveAttribute("aria-invalid", "true");
  });

  it("explains when a station has no report", async () => {
    server.use(
      http.get(api("/weather/:icao"), () =>
        HttpResponse.json(
          { error: "no_metar", message: "No METAR available for ZZZZ right now.", icao: "ZZZZ" },
          { status: 404 },
        ),
      ),
    );
    renderWithProviders(<WeatherTab defaultIcao="ZZZZ" />);
    expect(await screen.findByText("No METAR available for ZZZZ right now.")).toBeInTheDocument();
  });

  it("asks for the decoding in the selected language", async () => {
    let lang: string | null = null;
    server.use(
      http.get(api("/weather/:icao"), ({ request }) => {
        lang = new URL(request.url).searchParams.get("lang");
        return HttpResponse.json({
          icao: "SBGR",
          language: "pt",
          raw: "SBGR",
          decoded: "Bom",
          source: "AWC",
        });
      }),
    );
    renderWithProviders(<WeatherTab defaultIcao="SBGR" />, { locale: "pt" });
    expect(await screen.findByText("Bom")).toBeInTheDocument();
    expect(lang).toBe("pt");
  });
});
