import { expect, test } from "@playwright/test";
import path from "node:path";

const screenshotPath = path.resolve(
  process.cwd(),
  "../../../output/verification/frontend-screenshot.png",
);

test("general company recommendation demo renders auditable comparison output", async ({ page }) => {
  await page.goto("/company/recommendation-demo");

  await expect(
    page.getByRole("heading", { name: "육아휴직 지원금 조합 비교" }),
  ).toBeVisible();

  const checkButton = page.getByRole("button", { name: "지원금 확인" });
  await expect(checkButton).toBeVisible();
  await checkButton.click();

  await expect(page.getByText("적용 가능한 조합 수")).toBeVisible();
  await expect(page.getByText("제외된 조합 수")).toBeVisible();
  await expect(page.getByText("가장 높은 총지원금")).toBeVisible();
  await expect(page.getByText("유효 조합 목록")).toBeVisible();
  await expect(page.getByText("제외 조합 목록")).toBeVisible();

  await expect(page.locator(".combination-list").first()).toContainText("POLICY-PARENTAL-LEAVE");
  await expect(page.locator(".combination-list").nth(1)).toContainText("mutually_exclusive");
  await expect(page.getByText("계산 불가").first()).toBeVisible();

  await page.getByRole("button", { name: "상세 보기" }).first().click();
  await expect(page.getByRole("heading", { name: "evidence_snippets" })).toBeVisible();
  await expect(page.getByText("육아휴직을 허용한 사업주에게 월 정액 지원금을 지급합니다.").first()).toBeVisible();

  await expect(page.getByText("최적 추천")).toHaveCount(0);
  await expect(page.getByText("가장 유리한 조합")).toHaveCount(0);

  await page.screenshot({
    path: screenshotPath,
    fullPage: true,
  });
});
