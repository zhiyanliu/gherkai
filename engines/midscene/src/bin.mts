#!/usr/bin/env node
// 包的唯一入口（ADR 0037 决策 3）：npm bin `gherkai-worker-midscene`，同时是 Dockerfile 的 CMD。
//
// **本进程就是 worker 进程**（ADR 0024 铁律）：这里只做「装 loader + 注册 resolve hook + 调 run-scope 的
// main」，**绝不 spawn 子 node**——core 经 `pass_fds` 把事件通道 fd（EVENTS_FD）继承给它直接 spawn 的那个
// 进程，中间多一层包装进程就把 fd3 吞掉（`node --import tsx` 那次踩过的坑，见 ADR 0037 决策 3 Python 侧那条）。
//
// 三件事，顺序 load-bearing：
//   ① 进程内注册 tsx 的 ESM loader——发布形态下进程由 `node dist/bin.mjs` 启动（不再是 `node --import tsx`），
//      但使用方 `steps/` 里的 `.mts` step 文件仍要在运行期被 import，须有 TS 转译能力（ADR 0037 决策 3）；
//   ② 注册裸 specifier 的 resolve hook（见 resolve-hook.mts 头注释：为什么 Node 默认解析够不到）；
//      **须在 ① 之后**——hook 链后注册者先跑，我们要抢在 tsx 的 resolve 之前截住那个裸 specifier；
//   ③ 动态 import run-scope 的 main 并跑（argv 原样透传：--list-deterministic / --match-steps / job 模式
//      的判定都在 main 里读 process.argv，本文件不解析、不过滤任何 flag）。
import { register as registerLoaderHook } from "node:module";
import { register as registerTsx } from "tsx/esm/api";

// ① tsx loader 进程内注册（使用方 step 文件的 .mts 靠它转译）。
registerTsx();

// ② resolve hook：目标 URL 必须是**worker 自己这一份**的公开入口——发布形态取包自引用
// （`import.meta.resolve`，即 package.json `exports` 的 `.`）。**禁止用 cwd/argv 推算**：ADR 0037 决策 4
// 的不变量是「使用方注册的 step 必须落进 worker 派发时查的同一张表（同一模块实例）」，解析到第二份副本
// 会让全部确定性 step 静默落回 AI catch-all。
// **dev（未 build）形态**：`node src/bin.mts` 直跑时 `exports` 指的是 `dist/index.mjs`——它可能不存在，
// 更糟的是**存在但与正在跑的源码是两份**（源码树一个实例、dist 一个实例 → 使用方注册进 dist 那张表，
// 正是上面那条不变量要防的分裂）。故按「本进程自身跑的是哪一份」取同一份的公开入口：bin 与 index 恒同目录
// （src/ 或 dist/ 各自成套），从 `import.meta.url` 取兄弟文件即天然同一份（仍不碰 cwd/argv）。
// 发布形态（bin = `dist/bin.mjs`）走自引用那条，与 `exports` 保持一致。
const fromSource = import.meta.url.endsWith(".mts");
const target = fromSource
  ? new URL("./index.mts", import.meta.url).href
  : import.meta.resolve("@gherkai/worker-midscene");
// hook 是随 dist 发布的独立入口文件（跑在 loader 线程、不能是闭包）；dev 未 build 时文件名是 `.mts`。
const hookSpec = new URL(fromSource ? "./resolve-hook.mts" : "./resolve-hook.mjs", import.meta.url);
registerLoaderHook(hookSpec, { parentURL: import.meta.url, data: { target } });

// ③ 跑 worker 主流程。退出码统一由这里落地（run-scope.main 只返回码、不自己退——便于单测）。
try {
  const { main } = await import("./worker/run-scope.mjs");
  process.exit(await main());
} catch (e) {
  // 「没开跑就被拒」类启动失败（steps 加载失败等）与运行期 fatal 都走这里：一行 stderr + 非零退出。
  // 码用 1（**不能是 80**——80 是 ADR 0028 的网络专用码，core 会翻成可重试的 WorkerNetworkError）。
  process.stderr.write(`worker fatal: ${e}\n`);
  process.exit(1);
}
