// 确定性 step 注册表（ADR 0022）——Midscene 引擎（Nova 引擎 deterministic.py 的对称 TS 版）。
//
// 测试开发用 `deterministic(pattern, handler, meta)` 把「正则 → handler」登记进一张表（meta 必填，
// ADR 0036）。worker 派发每个 step 时**先查这张表**：命中走精确 handler（拿 Playwright page 判定、
// **不投票、可复现**），未命中才落到 AI catch-all（ADR 0020/0024）。内建导航也是这张表里的一条
// （ADR 0020 第 3 条：Given / When 后整句是一个地址），不再是派发里的独立分支。
//
// 为什么匹配放 worker 不放 core（ADR 0022）：确定性 handler 引擎特定（碰 Playwright page），匹配表
// 跟着 handler 走最内聚；core 只解析结构 + 调度，对 step 语义无知。
//
// 角色边界（ADR 0020）：QA 永远只写自然语言（默认走 AI）；确定性 step 由测试开发注册（QA 不碰）——
// 脚手架 deterministic.steps.mts 只承载内建导航条目，项目专属的写在使用方 `steps/` 目录（ADR 0037 决策 4，
// 经本模块的公开导出面 index.mts 注册进**同一张**表）。
//
// handler 约定：
//   - 签名 (ctx, groups) => void | Promise<void>：ctx.page 是 Playwright Page，ctx.navigate(url) 是引擎的导航原语；
//     groups 是正则具名组 (?<name>...) 的对象。
//   - 判定失败抛 DeterministicAssertion（或 node:assert 的 AssertionError）→ step 记 failed；
//     抛其它 → step 记 error。
//   - 不投票（确定性即无抖动，与 AI 断言的 votes 区分）。
//   - meta.keywords 可声明这条 step 接受的 Gherkin 关键字（ADR 0050 决策 1）：缺省 Given / When / Then 全部；
//     step 文本命中模式但关键字不在集合内时 step 记 error、不转 AI、不顺延到别的模式。
import type { Page } from "playwright";

export interface DeterministicCtx {
  page: Page;
  /** 引擎的导航原语（内建导航条目用它打开地址，ADR 0020 第 3 条）：Playwright 的 page.goto，等页面 domcontentloaded。 */
  navigate(url: string): Promise<void>;
}

export type DeterministicHandler = (
  ctx: DeterministicCtx,
  groups: Record<string, string>,
) => void | Promise<void>;

/** core 已把 And / But 折叠成这三者之一（ADR 0025）。 */
export const KEYWORDS = ["Given", "When", "Then"] as const;
export type Keyword = (typeof KEYWORDS)[number];

/** 人话元数据（ADR 0036）：注册即暴露——缺元数据的能力不可被 feature 作者发现，故必填、fail-loud。 */
export interface DeterministicMeta {
  description: string; // 这步做什么（一句话，给 feature 作者读）
  example: string; // feature 里怎么写（可直接抄的 step 文本）
  keywords?: readonly Keyword[]; // 接受的关键字子集（ADR 0050 决策 1），缺省全部
}

interface Entry {
  pattern: RegExp;
  handler: DeterministicHandler;
  raw: string;
  meta: DeterministicMeta;
  keywords: readonly Keyword[];
}

const REGISTRY: Entry[] = [];

/** 校验并归一 keywords 声明：封闭集合、非空、不重复；缺省为全部三个关键字，按规范顺序排列（便于自述与跨语言对拍）。 */
function normalizeKeywords(pattern: string, keywords: readonly Keyword[] | undefined): readonly Keyword[] {
  if (keywords === undefined) return KEYWORDS;
  if (keywords.length === 0) {
    throw new Error(`deterministic(${JSON.stringify(pattern)}) 的 keywords 不能为空：缺省（不传）即接受全部关键字`);
  }
  const unknown = keywords.filter((k) => !(KEYWORDS as readonly string[]).includes(k));
  if (unknown.length > 0) {
    throw new Error(`deterministic(${JSON.stringify(pattern)}) 的 keywords 含未知取值 ${JSON.stringify(unknown)}：只能是 ${JSON.stringify(KEYWORDS)}`);
  }
  if (new Set(keywords).size !== keywords.length) {
    throw new Error(`deterministic(${JSON.stringify(pattern)}) 的 keywords 有重复：${JSON.stringify(keywords)}`);
  }
  return KEYWORDS.filter((k) => keywords.includes(k));
}

/** 注册：把 handler 按正则 pattern 登记进注册表。pattern 用具名组 (?<name>...) 提取参数。
 * meta 必填（ADR 0036：注册契约含人话元数据——description/example 缺失即 fail-loud）。 */
export function deterministic(pattern: string, handler: DeterministicHandler, meta: DeterministicMeta): void {
  if (!meta?.description || !meta?.example) {
    throw new Error(`deterministic(${JSON.stringify(pattern)}) 注册缺 description/example：`
      + `两者必填——缺了这条 step 不会出现在能力清单里，feature 作者发现不了它`);
  }
  const keywords = normalizeKeywords(pattern, meta.keywords);
  REGISTRY.push({ pattern: new RegExp(pattern), handler, raw: pattern, meta, keywords });
}

/** 注册表当前条数。用于 `worker/user-steps.mts` 的零注册检查（ADR 0037 决策 4 的双实例守卫）：
 * 加载使用方 step 文件前后各取一次，没涨即该文件没注册进**这张**表 → fail-loud。 */
export function registrySize(): number {
  return REGISTRY.length;
}

/** 条目有实现的一个测试目标（ADR 0049 决策 1）：协议面的 snake_case 键；requires 是该句柄在此目标上的运行期前提（1.5 只有
 *  web_context），不同 requires 的条目拆开列、不聚合。 */
export interface StepTarget {
  device: string;
  ui_kinds: string[];
  requires?: string[];
}

/** 条目有实现的测试目标由句柄推出（ADR 0050 决策 1）：本模块的条目目前只有 playwright 一种句柄，对应桌面网页；
 *  worker 原样报出、不与自己的顶层 targets 求交（交集由 CLI 在契约校验处算，ADR 0049 决策 3）。 */
export const PLAYWRIGHT_TARGET: Readonly<StepTarget> = { device: "desktop", ui_kinds: ["web"] };

export interface RegistryEntry {
  pattern: string;
  description: string;
  example: string;
  keywords: Keyword[];
  targets: StepTarget[];
}

/** 注册表自述（ADR 0036「2.」）：这份清单就是 worker `--capabilities` 自述对象的 `deterministic_steps`
 * 键（唯一出口——没有独立的清单 flag），CLI 取出后转述给 feature 作者。 */
export function listRegistry(): RegistryEntry[] {
  return REGISTRY.map((e) => ({
    pattern: e.raw, description: e.meta.description, example: e.meta.example, keywords: [...e.keywords],
    targets: [{ device: PLAYWRIGHT_TARGET.device, ui_kinds: [...PLAYWRIGHT_TARGET.ui_kinds] }],
  }));
}

/** 判定失败用的断言错误（handler 也可用 node:assert，两者都被 worker 当作 failed）。 */
export class DeterministicAssertion extends Error {}

/** 命中多条模式（ADR 0022：最多一条）。冲突模式清单**只内联在 message**（worker 派发侧只取 name/message）；
 * 结构化冲突清单是 matchBatch 的职责（ADR 0036 `{conflict:[patterns]}`，走 --match-steps、不经异常）。 */
export class DeterministicConflict extends Error {}

/** step 文本命中了一条模式，但当前关键字不在该条目声明的 keywords 里（ADR 0050 决策 1）。
 * 派发侧据此记 error、不转 AI、不顺延（典型：`Then` 后只写一个地址——裸地址已是导航语法，Then 没有断言谓词）。
 * 结构化形态是 matchBatch 的 `{keyword_mismatch, keywords}`。 */
export class DeterministicKeywordMismatch extends Error {
  constructor(text: string, keyword: string, public readonly pattern: string, public readonly keywords: readonly Keyword[], description: string) {
    super(`step ${JSON.stringify(text)} 命中确定性 step「${description}」，但这条写法只在 ${keywords.join(" / ")} 下有意义（当前关键字是 ${keyword}）：改用这些关键字之一，或改写这一步`);
  }
}

export interface Match {
  handler: DeterministicHandler;
  groups: Record<string, string>;
}

/** 扫注册表收**全部**命中——match（实际运行中派发）与 matchBatch（用例预检）唯一的扫描实现面。
 * 两个消费者只在「命中数怎么处置」上分叉，匹配语义本身不复制成两份：ADR 0036 的「同一注册表、同一
 * exec 实现」由此结构保证，改匹配面（加锚定/归一化/优先级）不会漏改一处让 plan 标注对实际运行撒谎。
 * 关键字不进匹配，只在命中之后核对条目的声明。 */
function scan(text: string): Array<{ entry: Entry; m: RegExpExecArray }> {
  const hits: Array<{ entry: Entry; m: RegExpExecArray }> = [];
  for (const entry of REGISTRY) {
    const m = entry.pattern.exec(text);
    if (m) hits.push({ entry, m });
  }
  return hits;
}

/** 在注册表里找命中 text 的唯一 handler。返回 Match 或 null（未命中走 AI）。命中多条 → 抛 DeterministicConflict；
 * 命中一条但 keyword 不在其声明里 → 抛 DeterministicKeywordMismatch（keyword 缺省时不核对）。 */
export function match(text: string, keyword?: string): Match | null {
  const hits = scan(text);
  if (hits.length === 0) return null;
  if (hits.length > 1) {
    const raws = hits.map((h) => JSON.stringify(h.entry.raw)).join(", ");
    throw new DeterministicConflict(
      `step ${JSON.stringify(text)} 命中多条确定性模式 [${raws}]：一个 step 只能命中一条，请收紧模式`);
  }
  const { entry, m } = hits[0];
  if (keyword !== undefined && !(entry.keywords as readonly string[]).includes(keyword)) {
    throw new DeterministicKeywordMismatch(text, keyword, entry.raw, entry.keywords, entry.meta.description);
  }
  return { handler: entry.handler, groups: m.groups ?? {} };
}

/** 批量 match 查询（ADR 0036 决策 4）：plan 命中标注用——对每条 step 回答「命中哪条 / 冲突 / 关键字不符 / 未命中」。
 * 每项是 `{keyword, text}`；也接受裸字符串（旧版命令行工具的形态，此时不核对关键字）。
 * 与 match() 共用 scan()（同一扫描实现面），冲突不抛、结构化返回（plan 是用例预检、不是执行）。 */
export type MatchItem = string | { keyword?: string | null; text: string };
export type MatchProbe =
  | null
  | { pattern: string; description: string }
  | { conflict: string[] }
  | { keyword_mismatch: string; keywords: Keyword[] };

export function matchBatch(items: MatchItem[]): MatchProbe[] {
  return items.map((item) => {
    const keyword = typeof item === "string" ? undefined : (item.keyword ?? undefined);  // null 与缺键同义（对齐 Nova 侧 is not None）
    const text = typeof item === "string" ? item : item.text;
    const hits = scan(text);
    if (hits.length === 0) return null;
    if (hits.length > 1) return { conflict: hits.map((h) => h.entry.raw) };
    const { entry } = hits[0];
    if (keyword !== undefined && !(entry.keywords as readonly string[]).includes(keyword)) {
      return { keyword_mismatch: entry.raw, keywords: [...entry.keywords] };
    }
    return { pattern: entry.raw, description: entry.meta.description };
  });
}

/** 清空注册表（仅供测试隔离用）。 */
export function _clear(): void {
  REGISTRY.length = 0;
}
