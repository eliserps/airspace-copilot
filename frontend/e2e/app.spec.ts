import { expect, test } from "@playwright/test";
import { mockApi } from "./fixtures";

test.beforeEach(async ({ page }) => {
  await mockApi(page);
});

test("shows live traffic on the globe and in the list", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Airspace Copilot" })).toBeVisible();
  await expect(page.locator("canvas").first()).toBeVisible();
  await expect(page.locator(".ac-marker")).toHaveCount(2);

  await page.getByRole("tab", { name: "Traffic" }).click();
  await page
    .getByRole("tabpanel")
    .getByRole("button", { name: /GLO1234/ })
    .click();

  await expect(page.getByRole("button", { name: "Close aircraft details" })).toBeVisible();
  await expect(page).toHaveURL(/tab=traffic/);
  await expect(page).toHaveURL(/aircraft=def456/);
});

test("decodes the weather for the region's airport", async ({ page }) => {
  await page.goto("/?tab=weather");
  await expect(page.getByText("Good conditions for landing.")).toBeVisible();
});

test("streams a copilot answer", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Ask the airspace copilot…").fill("How many planes here?");
  await page.getByRole("button", { name: "Send question" }).click();
  await expect(page.getByText("Two aircraft over South America.")).toBeVisible();
});

test("keeps the selected region in the URL", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Region").selectOption("europe");
  await expect(page).toHaveURL(/region=europe/);
  await page.reload();
  await expect(page.getByLabel("Region")).toHaveValue("europe");
});
