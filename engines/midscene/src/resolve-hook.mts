// 裸 specifier `@gherkai/worker-midscene` 的解析 hook（ADR 0037 决策 4「midscene 裸 specifier 的解析」）。
//
// **为什么不能靠 Node 默认解析**：使用方 step 文件（`<项目>/steps/*.mts`）里写
// `import { deterministic } from "@gherkai/worker-midscene"`，Node 解析裸 specifier 只沿**该文件所在目录**
// 上溯找 `node_modules`——不认全局安装根（`npm i -g`）、也不认 `npx` 的临时缓存目录。使用方是 Python CLI
// 的用户，其项目只有 `features/` + `steps/`，根本没有 `node_modules` → 默认解析必 `ERR_MODULE_NOT_FOUND`。
// （云镜像里恰好能解析——`/app/steps` 上溯命中 `/app/node_modules`——那是巧合，不能当机制。）
//
// **机制**：worker 进程（`bin.mts`）在 import 使用方 step 文件之前注册本 hook，把这一个裸 specifier
// 映射到**worker 自身已加载的那个 URL**（`import.meta.resolve("@gherkai/worker-midscene")`，包自引用）。
//
// **不变量（load-bearing）**：`target` 必须就是 worker 自己加载注册表模块的同一个 URL。ESM 缓存按 URL 分裂：
// 若解析到第二份副本，使用方的 `deterministic(...)` 会注册进一张 worker 永远不读的表，全部确定性 step
// **静默**落回 AI catch-all（本项目最忌的静默降级）。因此 `target` 由 bin 传入、且只能从 `import.meta.resolve`
// 派生，**禁止**用 cwd / argv 推算。第二道防线是 `worker/user-steps.mts` 的零注册检查（把静默降级变显式失败）。
//
// **为什么是独立入口文件而非闭包**：`module.register` 的 hook 跑在独立的 loader 线程里，只能按 URL 加载模块、
// 拿不到主线程闭包；跨线程数据只能经 `register(spec, parent, { data })` 传（下面的 `initialize`）。

let target: string | undefined;

/** loader 线程侧的初始化：接 bin 经 `register(..., { data })` 传来的目标 URL。 */
export function initialize(data: { target: string }): void {
  target = data.target;
}

export function resolve(
  specifier: string,
  context: unknown,
  next: (specifier: string, context: unknown) => unknown,
): unknown {
  // 只截这一个裸 specifier；子路径（未来若开 exports 子路径）与其它一切原样交给下一环（含 tsx 的 hook）。
  if (specifier === "@gherkai/worker-midscene" && target) {
    return { url: target, shortCircuit: true };
  }
  return next(specifier, context);
}
