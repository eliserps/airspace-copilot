import { describe, expect, it } from "vitest";
import { useState } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CloudSun, Plane } from "lucide-react";
import { TabList, TabPanel } from "./Tabs";

function Harness() {
  const [tab, setTab] = useState<"a" | "b">("a");
  return (
    <>
      <TabList
        label="Panels"
        active={tab}
        onChange={setTab}
        items={[
          { id: "a", label: "Traffic", icon: Plane, tone: "" },
          { id: "b", label: "Weather", icon: CloudSun, tone: "" },
        ]}
      />
      <TabPanel id="a" active={tab === "a"}>
        traffic panel
      </TabPanel>
      <TabPanel id="b" active={tab === "b"}>
        weather panel
      </TabPanel>
    </>
  );
}

describe("Tabs", () => {
  it("exposes the WAI-ARIA tab pattern", () => {
    render(<Harness />);
    const traffic = screen.getByRole("tab", { name: "Traffic" });
    expect(screen.getByRole("tablist", { name: "Panels" })).toBeInTheDocument();
    expect(traffic).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tabpanel")).toHaveAccessibleName("Traffic");
    expect(screen.getByRole("tab", { name: "Weather" })).toHaveAttribute("tabindex", "-1");
  });

  it("moves selection and focus with the arrow keys", async () => {
    render(<Harness />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("tab", { name: "Traffic" }));
    await user.keyboard("{ArrowRight}");
    const weather = screen.getByRole("tab", { name: "Weather" });
    expect(weather).toHaveFocus();
    expect(weather).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tabpanel")).toHaveTextContent("weather panel");
    await user.keyboard("{ArrowRight}");
    expect(screen.getByRole("tab", { name: "Traffic" })).toHaveFocus();
  });
});
