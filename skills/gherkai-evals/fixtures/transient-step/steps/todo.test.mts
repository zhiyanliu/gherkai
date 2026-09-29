// _checks.mts 的本地单测：真浏览器打开 app/index.html。运行：node --test steps/todo.test.mts
import { test } from "node:test";
import assert from "node:assert/strict";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { deleteThenUndoKeepsItem } from "./_checks.mts";

const APP = "file://" + path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "app", "index.html");

test("删除后立刻撤销，条目仍在", async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(APP);
  await deleteThenUndoKeepsItem(page, "买牛奶");
  assert.equal(await page.locator("#todos li", { hasText: "买牛奶" }).count(), 1);
  await browser.close();
});
