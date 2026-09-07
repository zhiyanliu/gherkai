// 使用方 `steps/` 目录的加载（ADR 0037 决策 4；Nova 引擎侧 `*.py` 遍历是其对称版）。
//
// 契约（约定逻辑**不在这里**）：目录由组合根解析（`--steps-dir` > env > `./steps`）、随 definition 持久化、
// 经 env `GHERKAI_STEPS_DIR` 注给 worker。worker 只认这个 env、不认约定、不重解析——保持薄（ADR 0016 分层）。
//
// 加载规则：**排序**递归遍历 `*.mts` / `*.mjs`（排除 `*.test.*`），逐个 `await import(fileURL)`，文件顶层
// `deterministic(...)` 的副作用完成注册。排序保证 conflict 清单可复现（ADR 0036）。
//
// 两条 fail-loud（本项目最忌静默降级——跳过一个 step 文件 = 把确定性判定静默换成 AI catch-all、run 可能「通过」）：
//   ① import 失败（语法/依赖错）→ 立刻抛，带文件名与原异常；
//   ② **零注册检查**：某文件加载后注册表条数没涨 → 抛。这是 ADR 0037 决策 4「双实例」的显式化——
//      裸 specifier 若解析到第二份包副本，注册会落进 worker 永远不读的表，症状本来是「全部 step 静默走 AI」；
//      这条把它变成起不来的显式失败。（副作用：使用方写了个一条都不注册的文件也会被拒——正确，
//      那个文件对 worker 毫无意义、多半是写错了。）
//
// 抛出而非自己 `process.exit`：退出码由入口（`bin.mts`）统一落地（非零、且不是 ADR 0028 的网络专用 80），
// 本模块保持可单测。
import * as fs from "node:fs";
import * as path from "node:path";
import { pathToFileURL } from "node:url";
import { registrySize } from "./deterministic.mjs";

const STEP_EXTS = [".mts", ".mjs"];

/** 排序递归收集 step 文件（同层按名字排序、目录深度优先，保加载次序可复现）。 */
export function collectStepFiles(root: string): string[] {
  const out: string[] = [];
  const entries = fs.readdirSync(root, { withFileTypes: true });
  entries.sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0));
  for (const e of entries) {
    const full = path.join(root, e.name);
    if (e.isDirectory()) {
      out.push(...collectStepFiles(full));
      continue;
    }
    if (!e.isFile()) continue;
    if (!STEP_EXTS.includes(path.extname(e.name))) continue;
    if (/\.test\./.test(e.name)) continue; // 使用方的测试文件不是 step 文件
    out.push(full);
  }
  return out;
}

export interface LoadUserStepsDeps {
  stepsDir?: string | undefined;                       // 默认取 env GHERKAI_STEPS_DIR
  importer?: (url: string) => Promise<unknown>;        // 默认真 dynamic import（测试可注入）
  size?: () => number;                                 // 默认真注册表条数（测试可注入）
  logFn?: (m: string) => void;                         // 默认 stderr
}

/** 加载使用方 steps 目录。env 未设 / 目录不存在 → no-op（组合根只在目录存在时才注入，这里再兜一层）。
 * 返回加载了的文件列表（诊断用）。 */
export async function loadUserSteps(deps: LoadUserStepsDeps = {}): Promise<string[]> {
  const stepsDir = deps.stepsDir ?? process.env.GHERKAI_STEPS_DIR;
  if (!stepsDir) return [];
  const size = deps.size ?? registrySize;
  const importer = deps.importer ?? ((url: string) => import(url));
  const logFn = deps.logFn ?? ((m: string) => process.stderr.write(m + "\n"));
  if (!fs.existsSync(stepsDir) || !fs.statSync(stepsDir).isDirectory()) {
    // 目录不存在不是静默降级面：组合根解析时已确认存在才注入，走到这里说明提交后目录被移走/写错，
    // 属「没开跑就被拒」——报错退出，不装作没有确定性 step。
    throw new Error(`GHERKAI_STEPS_DIR 不是目录：${stepsDir}`);
  }
  const files = collectStepFiles(stepsDir);
  for (const file of files) {
    const before = size();
    try {
      await importer(pathToFileURL(file).href);
    } catch (e) {
      // ① 加载失败 fail-loud（带文件名 + 原因）。原因压成一行：转译器/Node 的报错常自带多行
      // （esbuild 的 "Transform failed…" 就是），诊断行留成多行会把 stderr 撕散、不便定位。
      const why = String((e as Error).message ?? e).replace(/\s*\n\s*/g, " | ");
      throw new Error(`steps 文件加载失败 ${file}：${why}`);
    }
    if (size() === before) {
      // ② 零注册 fail-loud（双实例守卫，ADR 0037 决策 4）。
      throw new Error(
        `steps 文件 ${file} 一条确定性 step 都没注册——` +
          `请确认它 import 的是 "@gherkai/worker-midscene" 并在顶层调用了 deterministic(...)`,
      );
    }
  }
  if (files.length > 0) logFn(`worker: 已加载使用方 steps ${files.length} 个文件（${stepsDir}）`);
  return files;
}
