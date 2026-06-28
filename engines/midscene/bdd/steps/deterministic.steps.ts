// 确定性锚点脚手架（ADR 0020）—— 给 TEST ENGINEER（会写代码的角色），不是 QA。
//
// 用途：少数"必须精确、不容 AI 抖动"的断言（如 URL 精确、关键 DOM 存在/文本），
// 用 Playwright 直接查、**不走 AI**。这是 ADR 0015 的"确定性逃生舱"。
//
// 设计（ADR 0020）：
//   - 本文件**默认空**，不预置任何具体锚点 step——预置就等于要求 QA 学特定措辞，违背"QA 零预设"。
//   - QA 永远只在 .feature 写人话（默认走 AI，见 generic.steps.ts）；"零代码"对 QA 成立。
//   - 仅当某断言确需精确、不能容忍 AI 非确定性时，test engineer 在此加一个项目专属 step。
//
// 怎么加（示例，需要时取消注释并改成你的项目所需）：
//   1) 在 .feature 里用一个**带前缀关键词**的 Then（与默认 AI 的纯 `Then "{string}"` 区分开）：
//        Then 页面地址包含 "/wiki/OpenAI"
//   2) 在此实现该 step，用底层 Playwright page 精确查：
//
//   import { Then, World } from "@cucumber/cucumber";
//   import assert from "node:assert";
//   interface W extends World { page?: import("playwright").Page; }
//   Then("页面地址包含 {string}", function (this: W, fragment: string) {
//     assert.ok(this.page!.url().includes(fragment), `url 应含 "${fragment}"，实际 ${this.page!.url()}`);
//   });
//
// 注意：本侧 `page` 由 generic.steps.ts 的 Before hook 挂在 World 上（this.page），可直接复用。
// Nova Act 侧的对齐脚手架见 novaact/bdd/deterministic_steps.py。

export {}; // 保持本文件为 ESM 模块（当前无导出的 step）
