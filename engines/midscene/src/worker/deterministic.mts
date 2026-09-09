// 确定性 step 注册表（ADR 0022）——Midscene 引擎（Nova 引擎 deterministic.py 的对称 TS 版）。
//
// 测试开发用 `deterministic(pattern, handler, meta)` 把「正则 → handler」登记进一张表（meta 必填，
// ADR 0036）。worker 派发每个 step 时**先查这张表**：命中走精确 handler（拿 Playwright page 判定、
// **不投票、可复现**），未命中才落到内建 URL 导航 / AI catch-all（ADR 0020/0024）。
//
// 为什么匹配放 worker 不放 core（ADR 0022）：确定性 handler 引擎特定（碰 Playwright page），匹配表
// 跟着 handler 走最内聚；core 只解析结构 + 调度，对 step 语义无知。
//
// 角色边界（ADR 0020）：QA 永远只写自然语言（默认走 AI）；确定性 step 由测试开发注册（QA 不碰）——
// 框架内建的那几条在 deterministic.steps.mts，项目专属的写在使用方 `steps/` 目录（ADR 0037 决策 4，
// 经本模块的公开导出面 index.mts 注册进**同一张**表）。
//
// handler 约定：
//   - 签名 (ctx, groups) => void | Promise<void>：ctx.page = Playwright Page；
//     groups = 正则具名组 (?<name>...) 的对象。
//   - 判定失败抛 DeterministicAssertion（或 node:assert 的 AssertionError）→ step 记 failed；
//     抛其它 → step 记 error。
//   - 不投票（确定性 = 无抖动，与 AI 断言的 votes 区分）。
import type { Page } from "playwright";

export interface DeterministicCtx {
  page: Page;
}

export type DeterministicHandler = (
  ctx: DeterministicCtx,
  groups: Record<string, string>,
) => void | Promise<void>;

/** 人话元数据（ADR 0036）：注册即暴露——缺元数据的能力不可被 feature 作者发现，故必填、fail-loud。 */
export interface DeterministicMeta {
  description: string; // 这步做什么（一句话，给 feature 作者读）
  example: string; // feature 里怎么写（可直接抄的 step 文本）
}

interface Entry {
  pattern: RegExp;
  handler: DeterministicHandler;
  raw: string;
  meta: DeterministicMeta;
}

const REGISTRY: Entry[] = [];

/** 注册：把 handler 按正则 pattern 登记进注册表。pattern 用具名组 (?<name>...) 提取参数。
 * meta 必填（ADR 0036：注册契约含人话元数据——description/example 缺失即 fail-loud）。 */
export function deterministic(pattern: string, handler: DeterministicHandler, meta: DeterministicMeta): void {
  if (!meta?.description || !meta?.example) {
    throw new Error(`deterministic(${JSON.stringify(pattern)}) 注册缺 description/example：`
      + `两者必填——缺了这条 step 不会出现在能力清单里，feature 作者发现不了它`);
  }
  REGISTRY.push({ pattern: new RegExp(pattern), handler, raw: pattern, meta });
}

/** 注册表当前条数。用于 `worker/user-steps.mts` 的零注册检查（ADR 0037 决策 4 的双实例守卫）：
 * 加载使用方 step 文件前后各取一次，没涨即该文件没注册进**这张**表 → fail-loud。 */
export function registrySize(): number {
  return REGISTRY.length;
}

/** 注册表自述（ADR 0036）：worker --list-deterministic 时 dump 成 JSON 给 CLI 转述。 */
export function listRegistry(): Array<{ pattern: string; description: string; example: string }> {
  return REGISTRY.map((e) => ({ pattern: e.raw, description: e.meta.description, example: e.meta.example }));
}

/** 判定失败用的断言错误（handler 也可用 node:assert，两者都被 worker 当作 failed）。 */
export class DeterministicAssertion extends Error {}

/** 命中多条模式（ADR 0022：最多一条）。冲突模式清单**只内联在 message**（worker 派发侧只取 name/message）；
 * 结构化冲突清单是 matchBatch 的职责（ADR 0036 `{conflict:[patterns]}`，走 --match-steps、不经异常）。 */
export class DeterministicConflict extends Error {}

export interface Match {
  handler: DeterministicHandler;
  groups: Record<string, string>;
}

/** 扫注册表收**全部**命中——match（真跑派发）与 matchBatch（plan 预检）唯一的扫描实现面。
 * 两个消费者只在「命中数怎么处置」上分叉，匹配语义本身不复制成两份：ADR 0036 的「同一注册表、同一
 * exec 实现」由此结构保证，改匹配面（加锚定/归一化/优先级）不会漏改一处让 plan 标注对真跑撒谎。 */
function scan(text: string): Array<{ entry: Entry; m: RegExpExecArray }> {
  const hits: Array<{ entry: Entry; m: RegExpExecArray }> = [];
  for (const entry of REGISTRY) {
    const m = entry.pattern.exec(text);
    if (m) hits.push({ entry, m });
  }
  return hits;
}

/** 在注册表里找命中 text 的唯一 handler。返回 Match 或 null（未命中走 AI）。命中多条 → 抛 DeterministicConflict。 */
export function match(text: string): Match | null {
  const hits = scan(text);
  if (hits.length === 0) return null;
  if (hits.length > 1) {
    const raws = hits.map((h) => JSON.stringify(h.entry.raw)).join(", ");
    throw new DeterministicConflict(
      `step ${JSON.stringify(text)} 命中多条确定性模式 [${raws}]：一个 step 只能命中一条，请收紧模式`);
  }
  return { handler: hits[0].entry.handler, groups: hits[0].m.groups ?? {} };
}

/** 批量 match 查询（ADR 0036 决策 4）：plan 命中标注用——对每条 step 文本回答「命中哪条 / 冲突 / 未命中」。
 * 与 match() 共用 scan()（同一扫描实现面），冲突不抛、结构化返回（plan 是预检不是执行）。 */
export type MatchProbe = null | { pattern: string; description: string } | { conflict: string[] };

export function matchBatch(texts: string[]): MatchProbe[] {
  return texts.map((text) => {
    const hits = scan(text);
    if (hits.length === 0) return null;
    if (hits.length > 1) return { conflict: hits.map((h) => h.entry.raw) };
    return { pattern: hits[0].entry.raw, description: hits[0].entry.meta.description };
  });
}

/** 清空注册表（仅供测试隔离用）。 */
export function _clear(): void {
  REGISTRY.length = 0;
}
