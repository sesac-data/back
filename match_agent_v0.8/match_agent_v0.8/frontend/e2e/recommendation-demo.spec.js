import { expect, test } from "@playwright/test";
import path from "node:path";

const screenshotPath = path.resolve(
  process.cwd(),
  "../../../output/verification/frontend-screenshot.png",
);

test("general company recommendation demo renders auditable comparison output", async ({ page }) => {
  await page.goto("/company/recommendation-demo");

  await expect(page.locator(".recommendation-demo")).toBeVisible();
  await expect(page.locator(".demo-hero-panel h2")).toBeVisible();

  const checkButton = page.locator(".recommendation-demo button.primary.small").first();
  await expect(checkButton).toBeVisible();
  await checkButton.click();

  await expect(page.locator(".metric-card")).toHaveCount(4);
  await expect(page.locator(".demo-result-grid .panel").first()).toBeVisible();
  await expect(page.locator(".demo-result-grid .panel").nth(1)).toBeVisible();

  const isApiAdapter = await page.getByText("API adapter 사용 중").count();

  if (isApiAdapter) {
    await expect(page.getByText("데모 정책 데이터 기준 결과입니다.").first()).toBeVisible();
    await expect(page.getByText("추천 조합")).toBeVisible();
    await expect(page.locator(".combination-list").first()).toContainText("smoke-optimal-a");
    await expect(page.getByText("사업주 순비용").first()).toBeVisible();
  } else {
    await expect(page.locator(".combination-list").first()).toContainText("POLICY-PARENTAL-LEAVE");
    await expect(page.locator(".combination-list").nth(1)).toContainText("mutually_exclusive");
    await expect(page.getByText("계산 불가").first()).toBeVisible();
  }

  await page.getByRole("button", { name: "상세 보기" }).first().click();
  await expect(page.getByRole("heading", { name: "evidence_snippets" })).toBeVisible();

  if (isApiAdapter) {
    await expect(page.getByText("TEST FIXTURE evidence:").first()).toBeVisible();
  } else {
    await expect(page.locator(".detail-panel")).toContainText("evidence_snippets");
  }

  await expect(page.getByText("최적 추천")).toHaveCount(0);
  await expect(page.getByText("가장 유리한 조합")).toHaveCount(0);

  await page.screenshot({
    path: screenshotPath,
    fullPage: true,
  });
});
