// 确定性 step 注册表（ADR 0022）——Midscene 腿（Nova 腿 deterministic.py 的对称 TS 版）。
//
// test engineer 用 `deterministic(pattern, handler)` 把「正则 → handler」登记进一张表。worker
// 派发每个 step 时**先查这张表**：命中走精确 handler（拿 Playwright page 判定、**不投票、可复现**），
// 未命中才落到内建 URL 导航 / AI catch-all（ADR 0020/0024）。
//
// 为什么匹配放 worker 不放 core（ADR 0022）：确定性 handler 引擎特定（碰 Playwright page），匹配表
// 跟着 handler 走最内聚；core 只解析结构 + 调度，对 step 语义无知。
//
// 角色边界（ADR 0020）：QA 永远只写人话（默认走 AI）；确定性 step 由 test engineer 在
// bdd/steps/deterministic.steps.ts 注册（QA 不碰）。
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

interface Entry {
  pattern: RegExp;
  handler: DeterministicHandler;
  raw: string;
}

const REGISTRY: Entry[] = [];

/** 注册：把 handler 按正则 pattern 登记进注册表。pattern 用具名组 (?<name>...) 提取参数。 */
export function deterministic(pattern: string, handler: DeterministicHandler): void {
  REGISTRY.push({ pattern: new RegExp(pattern), handler, raw: pattern });
}

/** 判定失败用的断言错误（handler 也可用 node:assert，两者都被 worker 当作 failed）。 */
export class DeterministicAssertion extends Error {}

export class DeterministicConflict extends Error {}

export interface Match {
  handler: DeterministicHandler;
  groups: Record<string, string>;
}

/** 在注册表里找命中 text 的唯一 handler。返回 Match 或 null（未命中走 AI）。命中多条 → 抛 DeterministicConflict。 */
export function match(text: string): Match | null {
  const hits: Array<{ entry: Entry; m: RegExpExecArray }> = [];
  for (const entry of REGISTRY) {
    const m = entry.pattern.exec(text);
    if (m) hits.push({ entry, m });
  }
  if (hits.length === 0) return null;
  if (hits.length > 1) {
    const raws = hits.map((h) => JSON.stringify(h.entry.raw)).join(", ");
    throw new DeterministicConflict(
      `step ${JSON.stringify(text)} 命中多条确定性模式 [${raws}]（ADR 0022：最多命中一条，请收紧模式）`,
    );
  }
  return { handler: hits[0].entry.handler, groups: hits[0].m.groups ?? {} };
}

/** 清空注册表（仅供测试隔离用）。 */
export function _clear(): void {
  REGISTRY.length = 0;
}
