import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { mockApi } from "./fixtures";

const TABS = ["copilot", "traffic", "briefing", "weather"] as const;

test.beforeEach(async ({ page }) => {
  await mockApi(page);
});

for (const tab of TABS) {
  test(`${tab} tab has no WCAG A/AA violations`, async ({ page }) => {
    await page.goto(`/?tab=${tab}`);
    await expect(page.getByRole("tab", { selected: true })).toBeVisible();
    await page.waitForLoadState("networkidle");

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .exclude("canvas")
      .analyze();

    expect(results.violations.map((v) => `${v.id}: ${v.nodes.length} node(s)`)).toEqual([]);
  });
}
