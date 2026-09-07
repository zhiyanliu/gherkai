// **内建**确定性锚点（ADR 0020/0022）——随包发布、零使用方内容（ADR 0037 决策 5 基底镜像同理）。
//
// 用途：少数"必须精确、不容 AI 抖动"的断言（如 URL 精确、关键 DOM 存在/文本），
// 用底层 Playwright（ctx.page）直接查、**不走 AI、不投票**。这是 ADR 0015 的"确定性逃生舱"。
//
// 机制（ADR 0022）：worker 派发每个 step 时**先查确定性注册表**（命中走 handler），未命中才落 AI catch-all。
// `deterministic(正则, handler, { description, example })` 注册（元数据必填、缺则 fail-loud——ADR 0036
// 「注册即暴露」）；worker 启动时 import 本模块，顶层的 deterministic(...) 副作用把锚点登记进表。
//
// **本文件不是使用方的定制面**（ADR 0037 决策 4 起）：test engineer 的项目专属锚点写在**使用方项目的
// `steps/` 目录**（`*.mts`，`import { deterministic } from "@gherkai/worker-midscene"`），由 worker 启动时
// 加载（见 user-steps.mts）——不再靠改本文件（那是 clone-repo 分发时代的 fork 模式）。这里只留框架自带的
// 那一条，兼作写法样例。角色边界不变（ADR 0020）：QA 永远只在 .feature 写自然语言、默认走 AI。
//
// handler 约定（见 deterministic.mts）：
//   - 签名 (ctx, groups) => void | Promise<void>：ctx.page = Playwright Page；groups = 正则具名组。
//   - 判定失败抛 DeterministicAssertion（或 node:assert AssertionError）→ step 记 failed；抛其它 → error。
//
// Nova Act 侧的对称内建锚点见 gherkai_worker_novaact 的 deterministic_steps 模块。
import { deterministic, DeterministicAssertion } from "./deterministic.mjs";

// 确定性 URL 断言：当前页 URL 须匹配给定正则（精确、不走 AI）。
// .feature 写法（test engineer 约定的带关键词措辞，与 QA 的纯自然语言 Then 区分）：
//     Then 页面地址匹配 "/wiki/OpenAI"
deterministic(
  '页面地址(?:精确)?匹配 "(?<pattern>[^"]+)"', // [^"]+（非 .+）：防 step 里出现第二对引号时贪婪跨引号捕获
  ({ page }, { pattern }) => {
    const url = page.url();
    if (!new RegExp(pattern).test(url)) {
      throw new DeterministicAssertion(`URL 应匹配 ${JSON.stringify(pattern)}，实际 ${JSON.stringify(url)}`);
    }
  },
  {
    description: "断言当前页面 URL 匹配给定正则（精确判定，不走 AI、不投票）",
    example: 'Then 页面地址匹配 "/wiki/OpenAI"',
  },
);

// 更多锚点示例（需要时取消注释并改成你的项目所需）：
//
// deterministic('元素 "(?<sel>[^"]+)" 可见', async ({ page }, { sel }) => {
//   if (!(await page.locator(sel).isVisible())) {
//     throw new DeterministicAssertion(`元素 ${JSON.stringify(sel)} 应可见`);
//   }
// }, { description: "断言选择器命中的元素可见", example: 'Then 元素 "#submit" 可见' });

export {}; // ESM 模块标记
