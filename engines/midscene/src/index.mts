// 包的公开 API（ADR 0037 决策 4）——**使用方 `steps/` 目录里的 step 文件唯一该 import 的东西**：
//
//     import { deterministic, DeterministicAssertion } from "@gherkai/worker-midscene";
//
//     deterministic('页面地址匹配 "(?<pattern>[^"]+)"', ({ page }, { pattern }) => { … },
//                   { description: "…", example: 'Then 页面地址匹配 "/wiki/OpenAI"', keywords: ["Then"] });
//
// 多句柄写法（ADR 0050 决策 1）：第二参按句柄种类分键，playwright 给桌面浏览器、webdriver 给设备会话；每个 webdriver 条目
// 用 uiKinds（web / app）与 devices（android / ios）声明适用范围、两者各自独立覆盖全部组合，缺省为全部取值；要只在
// 设备网页上下文里核对的条目声明 requires: ["web_context"]（此时 uiKinds 只能是 ["web"]）：
//
//     deterministic('页面地址匹配 "(?<pattern>[^"]+)"', {
//       playwright: ({ page }, { pattern }) => { … },
//       webdriver: [{ uiKinds: ["web"], requires: ["web_context"],
//                     handler: (ctx, { pattern }) => ctx.withWebContext(async () => { … await ctx.driver.getUrl() … }) }],
//     }, { description: "…", example: 'Then 页面地址匹配 "/wiki/OpenAI"', keywords: ["Then"] });
//
// 这里只做**再导出**、不含逻辑：注册表实现在 `worker/deterministic.mts`（单一事实源，
// ADR 0022/0036）。**不变量**：本模块与 worker 自身 import 的是同一个 `worker/deterministic.mjs`
// URL——使用方的注册与 worker 派发时查的必须是同一张表（同一模块实例）。裸 specifier
// `@gherkai/worker-midscene` 在使用方目录下能解析到「worker 自己这一份」靠 bin 注册的
// resolve hook（见 `resolve-hook.mts` 的头注释）。
//
// 导出面刻意窄：只给写一个 handler 真正需要的东西。`match` / `matchBatch` / `listRegistry`
// 是 worker 内部的派发面与两个非 job 入口（`--capabilities` 自述 / `--match-steps` 查询，ADR 0036
// 「5.」/「4.」）的数据源，不对使用方开放。
export { deterministic, DeterministicAssertion } from "./worker/deterministic.mjs";
export type {
  DeterministicCtx,      // playwright handler 第一参：{ page: Playwright Page, navigate(url) }
  DeterministicHandler,  // playwright handler 签名（写类型注解时用）
  DeterministicHandlers, // 第二参的多句柄形态：{ playwright?, webdriver? }（ADR 0050 决策 1）
  WebdriverEntry,        // 一个 webdriver 条目：{ uiKinds?, devices?, requires?, handler }
  WebdriverCtx,          // webdriver handler 第一参的七个字段（ADR 0050 决策 2）
  WebdriverHandler,      // webdriver handler 签名
  WebdriverDevice,       // ctx.device：{ platform, osVersion, scale }
  DeterministicMeta,     // { description, example, keywords? }，前两者注册必填（ADR 0036），keywords 见 ADR 0050 决策 1
} from "./worker/deterministic.mjs";
