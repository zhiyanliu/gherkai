// 确定性锚点脚手架（ADR 0020/0022）—— 给 TEST ENGINEER（会写代码的角色），不是 QA。
//
// 用途：少数"必须精确、不容 AI 抖动"的断言（如 URL 精确、关键 DOM 存在/文本），
// 用底层 Playwright（ctx.page）直接查、**不走 AI、不投票**。这是 ADR 0015 的"确定性逃生舱"。
//
// 机制（ADR 0022）：worker 派发每个 step 时**先查确定性注册表**（命中走这里的 handler），
// 未命中才落 AI catch-all。在此用 `deterministic(正则, handler)` 注册即可——worker 启动时
// import 本模块，顶层的 deterministic(...) 副作用把锚点登记进表。
//
// 角色边界（ADR 0020）：
//   - 本文件由 test engineer 维护；QA 永远只在 .feature 写人话（默认走 AI，见 generic.steps.ts）。
//   - 仅当某断言确需精确、不能容忍 AI 非确定性时，test engineer 在此加一个项目专属锚点。
//
// handler 约定（见 worker/deterministic.ts）：
//   - 签名 (ctx, groups) => void | Promise<void>：ctx.page = Playwright Page；groups = 正则具名组。
//   - 判定失败抛 DeterministicAssertion（或 node:assert AssertionError）→ step 记 failed；抛其它 → error。
//
// Nova Act 侧的对齐脚手架见 engines/novaact/bdd/deterministic_steps.py。
import { deterministic, DeterministicAssertion } from "../../worker/deterministic.js";

// 确定性 URL 断言：当前页 URL 须匹配给定正则（精确、不走 AI）。
// .feature 写法（test engineer 约定的带关键词措辞，与 QA 的纯人话 Then 区分）：
//     Then 页面地址匹配 "/wiki/OpenAI"
deterministic('页面地址(?:精确)?匹配 "(?<pattern>.+)"', ({ page }, { pattern }) => {
  const url = page.url();
  if (!new RegExp(pattern).test(url)) {
    throw new DeterministicAssertion(`URL 应匹配 ${JSON.stringify(pattern)}，实际 ${JSON.stringify(url)}`);
  }
});

// 更多锚点示例（需要时取消注释并改成你的项目所需）：
//
// deterministic('元素 "(?<sel>.+)" 可见', async ({ page }, { sel }) => {
//   if (!(await page.locator(sel).isVisible())) {
//     throw new DeterministicAssertion(`元素 ${JSON.stringify(sel)} 应可见`);
//   }
// });

export {}; // ESM 模块标记
