/**
 * TradeIQ Full Feature E2E Test
 * Tests: Login, Behavior, Market, Account, Agent, Prediction, and remaining features
 */

import { test, expect } from "@playwright/test";

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000";

test.describe("TradeIQ Full Feature Test", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
  });

  test("1. Login page loads and shows Google sign-in", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await expect(page.getByText("Welcome to TradeIQ")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Continue with Google")).toBeVisible();
    await expect(page.getByRole("link", { name: "Try Demo Mode" })).toBeVisible();
  });

  test("2. Demo Mode - access dashboard without login", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.getByRole("link", { name: /Try Demo Mode/i }).click();
    await page.waitForURL(/\/$/);
    await expect(page.getByRole("button", { name: "Overview" })).toBeVisible({ timeout: 15000 });
  });

  test("3. Dashboard (LIVE) - overview tabs and metrics", async ({ page }) => {
    await page.goto(`${BASE_URL}/`);
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole("button", { name: "Overview" })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole("heading", { name: "Portfolio Value" })).toBeVisible();
  });

  test("4. Behavior analysis page", async ({ page }) => {
    await page.goto(`${BASE_URL}/behavior`);
    await expect(page).toHaveURL(/\/behavior/);
    await expect(page.getByRole("heading", { name: "Behavioral Coach" })).toBeVisible({ timeout: 15000 });
  });

  test("5. Market sentiment page", async ({ page }) => {
    await page.goto(`${BASE_URL}/market`);
    await expect(page).toHaveURL(/\/market/);
    await expect(page.getByRole("link", { name: "MARKET" })).toBeVisible({ timeout: 15000 });
  });

  test("6. Account - Navbar shows SIGN IN when not logged in", async ({ page }) => {
    await page.goto(`${BASE_URL}/`);
    await expect(page.getByRole("link", { name: "SIGN IN" })).toBeVisible({ timeout: 10000 });
  });

  test("7. Agent mode (Pipeline) page", async ({ page }) => {
    await page.goto(`${BASE_URL}/pipeline`);
    await expect(page).toHaveURL(/\/pipeline/);
    await expect(page.getByRole("link", { name: "AGENTS" })).toBeVisible({ timeout: 15000 });
  });

  test("8. Copytrading page", async ({ page }) => {
    await page.goto(`${BASE_URL}/copytrading`);
    await expect(page).toHaveURL(/\/copytrading/);
    await expect(page.getByRole("heading", { name: "COPY TRADING" })).toBeVisible({ timeout: 15000 });
  });

  test("9. Trading page", async ({ page }) => {
    await page.goto(`${BASE_URL}/trading`);
    await expect(page).toHaveURL(/\/trading/);
    await expect(page.getByRole("heading", { name: "DEMO TRADING" })).toBeVisible({ timeout: 15000 });
  });

  test("10. Content generation page", async ({ page }) => {
    await page.goto(`${BASE_URL}/content`);
    await expect(page).toHaveURL(/\/content/);
    await expect(page.getByRole("heading", { name: "Content Engine" })).toBeVisible({ timeout: 15000 });
  });

  test("11. Demo page", async ({ page }) => {
    await page.goto(`${BASE_URL}/demo`);
    await expect(page).toHaveURL(/\/demo/);
    await expect(page.getByRole("heading", { name: "DEMO COMMAND CENTER" })).toBeVisible({ timeout: 15000 });
  });

  test("12. Navigation between all main pages", async ({ page }) => {
    const routes = ["/", "/market", "/behavior", "/copytrading", "/trading", "/content", "/pipeline"];
    for (const route of routes) {
      await page.goto(`${BASE_URL}${route}`);
      await expect(page).toHaveURL(new RegExp(route === "/" ? "\\/$" : route));
      await page.waitForLoadState("domcontentloaded");
    }
  });

  test("13. Behavior - Scenario selection visible", async ({ page }) => {
    await page.goto(`${BASE_URL}/behavior`);
    await expect(page.getByText(/scenario|overtrading|revenge/i).first()).toBeVisible({ timeout: 10000 });
  });

  test("14. Market - Instrument selection and sentiment/technicals load", async ({ page }) => {
    await page.goto(`${BASE_URL}/market`);
    await page.waitForLoadState("domcontentloaded");
    await expect(page.getByRole("button", { name: /EUR|BTC|GOLD|Volatility|cry|frx/i }).first()).toBeVisible({ timeout: 15000 });
  });

  test("15. Dashboard - AI Signals tab", async ({ page }) => {
    await page.goto(`${BASE_URL}/`);
    await page.getByRole("button", { name: "AI Signals" }).click();
    await expect(page.getByRole("button", { name: "AI Signals" })).toHaveAttribute("class", /\bbg-white\b/);
  });

  test("16. Pipeline - Run pipeline button visible", async ({ page }) => {
    await page.goto(`${BASE_URL}/pipeline`);
    await expect(page.getByRole("button", { name: /run|start|BTC/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test("17. Content - Generate content input visible", async ({ page }) => {
    await page.goto(`${BASE_URL}/content`);
    await expect(page.getByRole("heading", { name: "CONTENT INPUT" })).toBeVisible({ timeout: 10000 });
  });

  test("18. Trading - Demo trading interface", async ({ page }) => {
    await page.goto(`${BASE_URL}/trading`);
    await expect(page.getByText(/DEMO ACCOUNT|virtual money|Instrument/i).first()).toBeVisible({ timeout: 10000 });
  });
});
