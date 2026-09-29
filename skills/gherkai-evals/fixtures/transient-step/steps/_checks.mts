// 待办清单页的判定逻辑（Midscene 引擎用；与 _checks.py 成对）。注册在 todo.mts。运行期不 import playwright。
import type { Page } from "playwright";
import { DeterministicAssertion } from "@gherkai/worker-midscene";

export const SEL_ITEM = "#todos li";
export const SEL_UNDO = "#undo";
const TIMEOUT_MS = 3000;

function where(page: Page, selector: string): string {
  return `页面 ${page.url()}，选择器 ${selector}`;
}

export async function deleteThenUndoKeepsItem(page: Page, text: string): Promise<void> {
  const item = page.locator(SEL_ITEM, { hasText: text });
  try {
    await item.waitFor({ state: "visible", timeout: TIMEOUT_MS });
  } catch {
    throw new DeterministicAssertion(`要删除的条目 ${JSON.stringify(text)} 不在列表里（${where(page, SEL_ITEM)}）`);
  }
  await item.locator("button.del").click();
  const undo = page.locator(SEL_UNDO);
  try {
    await undo.waitFor({ state: "visible", timeout: TIMEOUT_MS });
  } catch {
    throw new DeterministicAssertion(`删除后撤销按钮未出现（${where(page, SEL_UNDO)}）`);
  }
  await undo.click();
  try {
    await page.locator(SEL_ITEM, { hasText: text }).waitFor({ state: "visible", timeout: TIMEOUT_MS });
  } catch {
    throw new DeterministicAssertion(`撤销后条目 ${JSON.stringify(text)} 没有回到列表（${where(page, SEL_ITEM)}）`);
  }
}
