// 确定性 step 注册表（ADR 0022）——Midscene 引擎（Nova 引擎 deterministic.py 的对称 TS 版）。
//
// 测试开发用 `deterministic(pattern, handlers, meta)` 把「正则 → 句柄集合」登记进一张表（meta 必填，
// ADR 0036）。worker 派发每个 step 时**先查这张表**：命中走精确 handler（**不投票、可复现**），未命中才落到
// AI catch-all（ADR 0020/0024）。内建导航也是这张表里的一条（ADR 0020 第 3 条：Given / When 后整句是一个地址），
// 不再是派发里的独立分支。
//
// 为什么匹配放 worker 不放 core（ADR 0022）：确定性 handler 引擎特定（碰 Playwright page 或远程访问会话），匹配表
// 跟着 handler 走最内聚；core 只解析结构 + 调度，对 step 语义无知。
//
// 角色边界（ADR 0020）：QA 永远只写自然语言（默认走 AI）；确定性 step 由测试开发注册（QA 不碰）——
// 脚手架 deterministic.steps.mts 只承载内建导航条目，项目专属的写在使用方 `steps/` 目录（ADR 0037 决策 4，
// 经本模块的公开导出面 index.mts 注册进**同一张**表）。
//
// 内建条目带内建标记（ADR 0050 决策 1）：脚手架经 registerBuiltin 注册（不在公开导出面上，使用方注册的条目一律不带标记），
// match() 的结果带出命中条目的标记，run-scope 据此把 step_kind 定为 navigation。判别只看命中的是哪个条目、不比对 pattern
// 原文：使用方 handler 自己调导航，这条 step 仍是 deterministic。标记不进自述清单与 matchBatch 的形态。
//
// 句柄按种类分键（ADR 0050 决策 1）：`playwright`（桌面浏览器）与 `webdriver`（远程访问会话）。`handlers` 传单个函数等价于
// 只有 playwright（已有项目的 steps/ 不需要改）。每个 webdriver 条目用 uiKinds（web / app）与 devices（android / ios）
// 声明适用范围，两个数组各自独立、覆盖它们的全部组合，缺省为全部取值；Android 与 iOS 的选择器不同就写两个条目，不在
// 一个 handler 里按设备分支——适用范围必须在执行前对注册表可见，才能推出 step 的 targets、让 plan 逐目标标注。
// 条目可声明前提 requires（1.5 只有 web_context）：设备不提供网页上下文时不调用、step 记 error（ADR 0048 决策 6）。
//
// 匹配与派发分两步（ADR 0050 决策 1「跨 step 的命中与目标无关」）：match() 只看文本命中哪条 pattern（多条即冲突），
// 不看目标；selectHandler() 再按当前目标在命中条目的句柄集合里取句柄，取不到即走 AI、**绝不顺延**到下一条能匹配的
// pattern——顺延会让同一段文本在不同目标上执行不同语义的实现，plan 与能力自述按 pattern 关联目标，顺延后都对不上。
//
// handler 约定：
//   - playwright 句柄签名 (ctx, groups)：ctx.page 是 Playwright Page，ctx.navigate(url) 是引擎的导航原语；
//     groups 是正则具名组 (?<name>...) 的对象。
//   - webdriver 句柄签名 (ctx, groups)：ctx 是 WebdriverCtx 的七个字段（ADR 0050 决策 2），实现随设备模块落地。
//   - 判定失败抛 DeterministicAssertion（或 node:assert 的 AssertionError）→ step 记 failed；抛其它 → step 记 error。
//   - 不投票（确定性即无抖动，与 AI 断言的 votes 区分）。
//   - meta.keywords 可声明这条 step 接受的 Gherkin 关键字（ADR 0050 决策 1）：缺省 Given / When / Then 全部；
//     step 文本命中模式但关键字不在集合内时 step 记 error、不转 AI、不顺延到别的模式。
import type { Page } from "playwright";
import type { Browser } from "webdriverio";

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

/** 测试目标的两个维度（ADR 0048 决策 1）：取值与 Job 的 target 同名同值。desktop 不在 DEVICES 里——它只有 playwright 句柄。 */
export const UI_KINDS = ["web", "app"] as const;
export type UiKind = (typeof UI_KINDS)[number];
export const DEVICES = ["android", "ios"] as const;
export type Device = (typeof DEVICES)[number];
/** webdriver 条目可声明的运行期前提（ADR 0050 决策 1）：封闭集合，1.5 只有 web_context。 */
export const REQUIREMENTS = ["web_context"] as const;
export type Requirement = (typeof REQUIREMENTS)[number];
/** 自述里 targets 的固定写出顺序（ADR 0050 决策 1）：只管输出，不参与匹配与派发。 */
const TARGET_DEVICE_ORDER: readonly string[] = ["desktop", ...DEVICES];

/** webdriver 句柄拿到的设备描述（ADR 0050 决策 2）：字段不叫 target，避免与 Job 携带的测试目标同名。
 *  这是句柄上下文的类型透传：设备模块读取点护栏对系统版本字段的显式豁免之一（ADR 0052 决策 8）。 */
export interface WebdriverDevice {
  platform: Device;
  osVersion: string;
  scale: number;
}

/** 只在 app 目标上有值：唯一方法 restart()，terminate 加 activate 加启动采样（原语归 ADR 0052 决策 3）。 */
export interface WebdriverApp {
  restart(): Promise<void>;
}

/** webdriver 句柄的 ctx（ADR 0050 决策 2）：七个字段、一条不变量——step 结束时会话处在原生上下文。
 *  driver 以类型引用 WebdriverIO 客户端（只在编译期）；实现随设备模块落地，桌面路径不会构造它。 */
export interface WebdriverCtx {
  /** 受命令守卫的 WebdriverIO 客户端代理（守卫归 ADR 0052 决策 6）。 */
  driver: Browser;
  device: WebdriverDevice;
  uiKind: UiKind;
  /** 包名或 bundle id，只在 app 目标上有值。 */
  appId: string | null;
  /** 只在 app 目标上有值。 */
  app: WebdriverApp | null;
  /** 写进本 step 诊断的日志函数。 */
  log(message: string): void;
  /** 每次重新定位属于被测对象的网页上下文、切入后执行 fn，结束（含抛错）后切回原生上下文；多个或零候选时抛错、不猜。 */
  withWebContext<T>(fn: () => Promise<T> | T): Promise<T>;
}

export type WebdriverHandler = (
  ctx: WebdriverCtx,
  groups: Record<string, string>,
) => void | Promise<void>;

/** 一个 webdriver 条目（ADR 0050 决策 1）：uiKinds 与 devices 各自独立、覆盖全部组合，缺省为全部取值；requires 缺省为无。 */
export interface WebdriverEntry {
  uiKinds?: readonly UiKind[];
  devices?: readonly Device[];
  requires?: readonly Requirement[];
  handler: WebdriverHandler;
}

/** 注册面的第二参：按句柄种类分键；单个函数等价于 { playwright: fn }。 */
export interface DeterministicHandlers {
  playwright?: DeterministicHandler;
  webdriver?: WebdriverEntry | readonly WebdriverEntry[];
}

/** 供 feature 作者阅读的元数据（ADR 0036）：注册即暴露——缺元数据的能力不可被 feature 作者发现，故必填、fail-loud。 */
export interface DeterministicMeta {
  description: string; // 这步做什么（一句话，给 feature 作者读）
  example: string; // feature 里怎么写（可直接抄的 step 文本）
  keywords?: readonly Keyword[]; // 接受的关键字子集（ADR 0050 决策 1），缺省全部
}

/** 规范化后的 webdriver 条目：三个数组都已展开为显式取值、按封闭集合的顺序排列。 */
export interface NormalizedWebdriverEntry {
  uiKinds: readonly UiKind[];
  devices: readonly Device[];
  requires: readonly Requirement[];
  handler: WebdriverHandler;
}

/** 一条 step 的句柄集合：playwright 可空、webdriver 零到多条（注册期已保证不覆盖同一个（设备, 界面类型）组合）。 */
export interface EntryHandles {
  playwright: DeterministicHandler | null;
  webdriver: readonly NormalizedWebdriverEntry[];
}

/** 内建条目的标记（ADR 0050 决策 1「内建条目带内建标记」）：封闭集合，1.5 只有导航。 */
export const BUILTIN_KINDS = ["navigation"] as const;
export type BuiltinKind = (typeof BUILTIN_KINDS)[number];

interface Entry {
  pattern: RegExp;
  raw: string;
  meta: DeterministicMeta;
  keywords: readonly Keyword[];
  handles: EntryHandles;
  /** 内建条目的标记；使用方条目为 null。 */
  builtin: BuiltinKind | null;
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

/** 条目字段的封闭集合校验与归一（与 keywords 同一套规则）：未知取值、重复即抛；缺省展开为全集；按集合顺序排列。
 *  allowEmpty 只对 requires 为真（空数组与缺省同义：没有前提）。 */
function closedSet<T extends string>(pattern: string, field: string, values: readonly string[] | undefined,
                                      allowed: readonly T[], allowEmpty: boolean): readonly T[] {
  if (values === undefined) return allowEmpty ? [] : allowed;
  if (!Array.isArray(values)) {  // null 也走这里：显式空值不是缺省（与 Nova 侧一致，缺省只认缺键）
    throw new Error(`deterministic(${JSON.stringify(pattern)}) 的 webdriver 条目 ${field} 不是数组（null 也不行：缺省就不要给这个字段）`);
  }
  if (values.length === 0 && !allowEmpty) {
    throw new Error(`deterministic(${JSON.stringify(pattern)}) 的 webdriver 条目 ${field} 不能为空：缺省（不给）即全部取值`);
  }
  const unknown = values.filter((v) => !(allowed as readonly string[]).includes(v));
  if (unknown.length > 0) {
    throw new Error(`deterministic(${JSON.stringify(pattern)}) 的 webdriver 条目 ${field} 含未知取值 ${JSON.stringify(unknown)}：只能是 ${JSON.stringify(allowed)}`);
  }
  if (new Set(values).size !== values.length) {
    throw new Error(`deterministic(${JSON.stringify(pattern)}) 的 webdriver 条目 ${field} 有重复：${JSON.stringify(values)}`);
  }
  return allowed.filter((v) => values.includes(v));
}

const HANDLER_KINDS = ["playwright", "webdriver"] as const;
const ENTRY_FIELDS = ["uiKinds", "devices", "requires", "handler"] as const;

/** 注册面第二参的规范化与注册期校验（ADR 0050 决策 1）：违反即抛、按 ADR 0037 决策 4 的加载失败处理。
 *  校验项与 Nova 侧逐项一致（跨语言 fixture 对拍）：未知句柄种类、没有任何句柄、句柄不是函数、webdriver 列表为空、
 *  条目字段的封闭集合、含 web_context 的条目 uiKinds 必须恰为 ["web"]、两个条目覆盖同一个（设备, 界面类型）组合。 */
function normalizeHandlers(pattern: string, handlers: DeterministicHandler | DeterministicHandlers): EntryHandles {
  const p = JSON.stringify(pattern);
  if (typeof handlers === "function") return { playwright: handlers, webdriver: [] };
  if (handlers === null || typeof handlers !== "object" || Array.isArray(handlers)) {
    throw new Error(`deterministic(${p}) 的 handlers 既不是函数也不是对象：传一个 playwright handler 函数，或 { playwright?, webdriver? } 对象`);
  }
  const unknownKinds = Object.keys(handlers).filter((k) => !(HANDLER_KINDS as readonly string[]).includes(k));
  if (unknownKinds.length > 0) {
    throw new Error(`deterministic(${p}) 的 handlers 含未知句柄种类 ${JSON.stringify(unknownKinds)}：只能是 ${JSON.stringify(HANDLER_KINDS)}`);
  }
  if (handlers.playwright === undefined && handlers.webdriver === undefined) {
    throw new Error(`deterministic(${p}) 的 handlers 没有任何句柄：至少给 playwright 或 webdriver 之一`);
  }
  if (handlers.playwright !== undefined && typeof handlers.playwright !== "function") {
    throw new Error(`deterministic(${p}) 的 playwright 句柄不是函数`);
  }
  const rawEntries = handlers.webdriver === undefined ? [] : Array.isArray(handlers.webdriver) ? handlers.webdriver : [handlers.webdriver];
  if (handlers.webdriver !== undefined && rawEntries.length === 0) {
    throw new Error(`deterministic(${p}) 的 webdriver 条目列表不能为空：缺省（不给 webdriver 键）即没有设备句柄`);
  }
  const entries: NormalizedWebdriverEntry[] = [];
  const covered = new Map<string, true>();  // "device/uiKind" → 已有条目覆盖
  for (const e of rawEntries) {
    if (e === null || typeof e !== "object" || Array.isArray(e)) {
      throw new Error(`deterministic(${p}) 的 webdriver 条目不是对象`);
    }
    const unknownFields = Object.keys(e).filter((k) => !(ENTRY_FIELDS as readonly string[]).includes(k));
    if (unknownFields.length > 0) {
      throw new Error(`deterministic(${p}) 的 webdriver 条目含未知字段 ${JSON.stringify(unknownFields)}：只能是 ${JSON.stringify(ENTRY_FIELDS)}`);
    }
    if (typeof e.handler !== "function") {
      throw new Error(`deterministic(${p}) 的 webdriver 条目缺 handler 或 handler 不是函数`);
    }
    const uiKinds = closedSet(pattern, "uiKinds", e.uiKinds, UI_KINDS, false);
    const devices = closedSet(pattern, "devices", e.devices, DEVICES, false);
    const requires = closedSet(pattern, "requires", e.requires, REQUIREMENTS, true);
    if (requires.includes("web_context") && !(uiKinds.length === 1 && uiKinds[0] === "web")) {
      throw new Error(`deterministic(${p}) 的 webdriver 条目声明了 requires web_context，uiKinds 必须恰为 ["web"]（应用目标固定原生上下文，前提没有定义）`);
    }
    for (const d of devices) {
      for (const k of uiKinds) {
        const key = `${d}/${k}`;
        if (covered.has(key)) {
          throw new Error(`deterministic(${p}) 的两个 webdriver 条目覆盖同一个（设备, 界面类型）组合 ${key}：一个 step 在一个目标上只能有一份实现，不论 requires 是否相同`);
        }
        covered.set(key, true);
      }
    }
    entries.push({ uiKinds, devices, requires, handler: e.handler });
  }
  return { playwright: handlers.playwright ?? null, webdriver: entries };
}

/** 注册：把句柄集合按正则 pattern 登记进注册表。pattern 用具名组 (?<name>...) 提取参数。
 * handlers 传单个函数等价于只有 playwright（ADR 0050 决策 1）。
 * meta 必填（ADR 0036：注册契约含供 feature 作者阅读的元数据——description/example 缺失即 fail-loud）。 */
export function deterministic(pattern: string, handlers: DeterministicHandler | DeterministicHandlers, meta: DeterministicMeta): void {
  register(pattern, handlers, meta, null);
}

/** 内建条目的注册入口：只有随包发布的脚手架（deterministic.steps.mts）调用，不经 index.mts 再导出——内建标记不是使用方
 *  可声明的元数据。校验与 deterministic() 同一套，只多记一个标记（ADR 0050 决策 1）。 */
export function registerBuiltin(builtin: BuiltinKind, pattern: string, handlers: DeterministicHandler | DeterministicHandlers,
                                meta: DeterministicMeta): void {
  if (!(BUILTIN_KINDS as readonly string[]).includes(builtin)) {
    throw new Error(`内建条目的内建标记 ${JSON.stringify(builtin)} 不是已知取值：只能是 ${JSON.stringify(BUILTIN_KINDS)}`);
  }
  register(pattern, handlers, meta, builtin);
}

function register(pattern: string, handlers: DeterministicHandler | DeterministicHandlers, meta: DeterministicMeta,
                  builtin: BuiltinKind | null): void {
  if (!meta?.description || !meta?.example) {
    throw new Error(`deterministic(${JSON.stringify(pattern)}) 注册缺 description/example：`
      + `两者必填——缺了这条 step 不会出现在能力清单里，feature 作者发现不了它`);
  }
  const keywords = normalizeKeywords(pattern, meta.keywords);
  const handles = normalizeHandlers(pattern, handlers);
  REGISTRY.push({ pattern: new RegExp(pattern), raw: pattern, meta, keywords, handles, builtin });
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

/** playwright 句柄对应的目标：桌面网页。 */
export const PLAYWRIGHT_TARGET: Readonly<StepTarget> = { device: "desktop", ui_kinds: ["web"] };

/** 由句柄集合推出 step 的 targets（ADR 0050 决策 1）：playwright → desktop/web；每个 webdriver 条目按 devices × uiKinds 展开，
 *  再按（设备, requires）聚合、界面类型收进 ui_kinds。写出顺序固定（设备 desktop → android → ios，ui_kinds web → app，同一设备下
 *  无 requires 在前、有的按取值字典序）；worker 原样报出、不与自己的顶层 targets 求交（交集由命令行工具一侧算，ADR 0049 决策 3）。 */
export function stepTargets(handles: EntryHandles): StepTarget[] {
  const acc = new Map<string, { device: string; requires: readonly string[]; kinds: Set<string> }>();
  const add = (device: string, requires: readonly string[], kinds: readonly string[]) => {
    const key = `${device}|${requires.join(",")}`;
    const slot = acc.get(key) ?? { device, requires, kinds: new Set<string>() };
    for (const k of kinds) slot.kinds.add(k);
    acc.set(key, slot);
  };
  if (handles.playwright) add(PLAYWRIGHT_TARGET.device, [], PLAYWRIGHT_TARGET.ui_kinds);
  for (const e of handles.webdriver) for (const d of e.devices) add(d, e.requires, e.uiKinds);
  return [...acc.values()]
    .sort((a, b) => {
      const byDevice = TARGET_DEVICE_ORDER.indexOf(a.device) - TARGET_DEVICE_ORDER.indexOf(b.device);
      if (byDevice !== 0) return byDevice;
      const ra = a.requires.join(","), rb = b.requires.join(",");
      return ra === rb ? 0 : ra === "" ? -1 : rb === "" ? 1 : ra < rb ? -1 : 1;
    })
    .map((t) => ({
      device: t.device,
      ui_kinds: UI_KINDS.filter((k) => t.kinds.has(k)),
      ...(t.requires.length > 0 ? { requires: [...t.requires] } : {}),
    }));
}

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
    targets: stepTargets(e.handles),
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

/** 命中结果：命中条目的句柄集合、具名组与内建标记。句柄要再经 selectHandler 按当前目标取——命中与目标无关（ADR 0050 决策 1）。 */
export interface Match {
  handles: EntryHandles;
  groups: Record<string, string>;
  /** 命中条目的内建标记（使用方条目为 null）：run-scope 据此定 step_kind，navigation 只来自这里（ADR 0050 决策 1）。 */
  builtin: BuiltinKind | null;
}

/** 扫注册表收**全部**命中——match（实际运行中派发）与 matchBatch（用例预检）唯一的扫描实现面。
 * 两个消费者只在「命中数怎么处置」上分叉，匹配语义本身不复制成两份：ADR 0036 的「同一注册表、同一
 * exec 实现」由此结构保证，改匹配面（加锚定/归一化/优先级）不会漏改一处让 plan 标注对实际运行撒谎。
 * 关键字不进匹配，只在命中之后核对条目的声明；目标也不进匹配。 */
function scan(text: string): Array<{ entry: Entry; m: RegExpExecArray }> {
  const hits: Array<{ entry: Entry; m: RegExpExecArray }> = [];
  for (const entry of REGISTRY) {
    const m = entry.pattern.exec(text);
    if (m) hits.push({ entry, m });
  }
  return hits;
}

/** 在注册表里找命中 text 的唯一条目。返回 Match 或 null（未命中走 AI）。命中多条 → 抛 DeterministicConflict；
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
  return { handles: entry.handles, groups: m.groups ?? {}, builtin: entry.builtin };
}

/** 当前目标（ADR 0048 决策 1 的 device 与 ui_kind）。 */
export interface StepTargetKey {
  device: string;
  uiKind: string;
}

export type SelectedHandler =
  | { kind: "playwright"; fn: DeterministicHandler }
  | { kind: "webdriver"; fn: WebdriverHandler; requires: readonly Requirement[] };

/** 命中之后按当前目标取句柄（ADR 0050 决策 1）：desktop/web 取 playwright；设备目标取覆盖这个（设备, 界面类型）组合的那条
 *  webdriver 条目（注册期已保证至多一条）。null 表示命中的 pattern 在当前目标上没有句柄——调用方走 AI，**绝不顺延**到下一条
 *  能匹配的 pattern、也不记 error。 */
export function selectHandler(hit: Match, target: StepTargetKey): SelectedHandler | null {
  if (target.device === "desktop") {
    return target.uiKind === "web" && hit.handles.playwright ? { kind: "playwright", fn: hit.handles.playwright } : null;
  }
  const entry = hit.handles.webdriver.find((e) =>
    (e.devices as readonly string[]).includes(target.device) && (e.uiKinds as readonly string[]).includes(target.uiKind));
  return entry ? { kind: "webdriver", fn: entry.handler, requires: entry.requires } : null;
}

/** 批量 match 查询（ADR 0036 决策 4）：plan 命中标注用——对每条 step 回答「命中哪条 / 冲突 / 关键字不符 / 未命中」。
 * 每项是 `{keyword, text}`；也接受裸字符串（旧版命令行工具的形态，此时不核对关键字）。
 * 与 match() 共用 scan()（同一扫描实现面），冲突不抛、结构化返回（plan 是用例预检、不是执行）。输出不带目标信息：
 * plan 用命中的 pattern 关联自述清单里该条目的 targets，再按 scope 的目标标注（ADR 0049 决策 3）。 */
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

/** 注册表快照与还原（仅供测试隔离用）：用例临时注册条目后恢复原表，不清掉别的用例还要用的内建条目。 */
export function _snapshot(): unknown[] {
  return [...REGISTRY];
}

export function _restore(saved: unknown[]): void {
  REGISTRY.length = 0;
  REGISTRY.push(...(saved as Entry[]));
}
