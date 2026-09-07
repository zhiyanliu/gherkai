// 包的公开 API（ADR 0037 决策 4）——**使用方 `steps/` 目录里的 step 文件唯一该 import 的东西**：
//
//     import { deterministic, DeterministicAssertion } from "@gherkai/worker-midscene";
//
//     deterministic('页面地址匹配 "(?<pattern>[^"]+)"', ({ page }, { pattern }) => { … },
//                   { description: "…", example: 'Then 页面地址匹配 "/wiki/OpenAI"' });
//
// 这里只做**再导出**、不含逻辑：注册表实现在 `worker/deterministic.mts`（单一事实源，
// ADR 0022/0036）。**不变量**：本模块与 worker 自身 import 的是同一个 `worker/deterministic.mjs`
// URL——使用方的注册与 worker 派发时查的必须是同一张表（同一模块实例）。裸 specifier
// `@gherkai/worker-midscene` 在使用方目录下能解析到「worker 自己这一份」靠 bin 注册的
// resolve hook（见 `resolve-hook.mts` 的头注释）。
//
// 导出面刻意窄：只给写一个 handler 真正需要的东西。`match` / `matchBatch` / `listRegistry`
// 是 worker 内部的派发与自述面（ADR 0036），不对使用方开放。
export { deterministic, DeterministicAssertion } from "./worker/deterministic.mjs";
export type {
  DeterministicCtx,      // handler 第一参：{ page: Playwright Page }
  DeterministicHandler,  // handler 签名（写类型注解时用）
  DeterministicMeta,     // { description, example }，注册必填（ADR 0036）
} from "./worker/deterministic.mjs";
