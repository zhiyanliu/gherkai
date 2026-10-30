// 真机重新探测工具（ADR 0052 决策 8）：在一条真实的远程访问会话里逐项执行能力探测与驱动适配器的原语，把结果写成能力矩阵
// capability-matrix.json，并与适配器的命令契约快照（engines/midscene/src/device/adapters/fixtures/<适配器>.commands.json）及控件树
// 样例做差集：快照里哪些命令形态被真机拒绝、哪些没有执行到、真机上发出了快照里没有的哪些形态、控件树样例里的哪些属性真机控件树
// 里没有。升级 Midscene 或 WebdriverIO、Device Farm 的 Appium 服务端版本变化时，在真机验收矩阵之前执行（矩阵见
// engines/midscene/DEVELOPMENT.md「真机验收矩阵」节）。用法、前置、费用与判读见同目录 device_reprobe.md。
//
// 会话怎样建立：直接用设备侧接缝（device/surface.mts 的 createDeviceSurface）与缺省部件装配，获取、能力探测、释放与 worker 执行
// 设备 scope 时走同一条路径；本工具只在装配上加一层记录（接缝构造项 parts）：命令守卫拿到的执行实例外包一层命令记录，选出的适配器、
// 探测结论与界面实现的构造参数在经过时记下。原语在接缝的执行窗口（execute）里经命令守卫下发，每条用例前后各做一次 step 前核对与
// 复原核对，与 worker 执行一个 step 的次序相同。不调模型：设备 Agent 照常构造（借它列出向模型注册的动作），不执行任何 AI 动作。
//
// 差集的口径：
//   - 命令形态指方法名，execute 类命令另加脚本名与参数对象的键集合（ADR 0052 决策 8「命令名与参数形态」）；
//   - 用例级比对：归一后的命令序列与快照逐条相同。归一有两处：元素句柄按出现次序换成 active-1、active-2……（快照的假 driver 就是这样
//     命名的）；连续重复的同一条命令按一条比较（轮询次数随真机应答变化，例如 DeepLink 之后核对前台包名）；
//   - 快照用例的输入照原样执行（坐标、文本与上下文取快照里的值），只有 DeepLink 的地址与应用标识换成 --deep-link 与本次目标的值；
//     真机的坐标比例与输入上下文另记在 probe 段，不改用例的输入，否则命令序列无法与快照逐条比对。
// 快照用例的解读（原语名到适配器方法的映射）与 adapters/adapters.contract.test.mts 的 runCase 相同，加原语时两处一起改。
//
// --offline：不连设备，用按快照应答的假 driver 重放两份快照的全部用例，再拿两份控件树样例各自与自身比较，核对本工具的记录、归一与
// 差集逻辑（结果应为零差异）。改了本工具或快照格式之后先执行它。
//
// 本文件不写 `mobile:` 命令字面量、不构造 Device Farm 客户端、不直接 import WebdriverIO 与 Device Farm SDK：这些都只经设备模块的
// 导出（ADR 0052 决策 4、8，ADR 0051 决策 10）。常量取 device/limits.mts。
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { parseArgs } from "node:util";
import {
  createDeviceSurface,
  type AppiumSession, type DeviceParts, type DevicePartsEnv, type Outcome, type ProbeConclusion,
} from "../engines/midscene/src/device/surface.mjs";
import { defaultDeviceParts } from "../engines/midscene/src/device/parts.mjs";
import {
  createAppiumInterface, scanXmlElements, type DeviceAdapter, type InputContext, type PrimitiveContext,
} from "../engines/midscene/src/device/interface.mjs";
import { createUiAutomator2Adapter } from "../engines/midscene/src/device/adapters/uiautomator2.mjs";
import { activeAppInfo, createXcuitestAdapter, deviceScreenInfo } from "../engines/midscene/src/device/adapters/xcuitest.mjs";
import { applicationLongEdge, pngLongEdge, scaleFromSizes } from "../engines/midscene/src/device/probe.mjs";
import { probeClientOf } from "../engines/midscene/src/device/appium.mjs";
import { contextNames, webContextCandidates } from "../engines/midscene/src/device/web-context.mjs";
import {
  DEEP_LINK_FOREGROUND_POLL_ATTEMPTS, DEEP_LINK_FOREGROUND_POLL_INTERVAL_MS, SNAPSHOT_CAPTURE_BUDGET_MS,
} from "../engines/midscene/src/device/limits.mjs";
import { DEVICES, UI_KINDS, type Device, type UiKind } from "../engines/midscene/src/worker/deterministic.mjs";
import { readClassification, type SurfaceDeps, type TargetSurface } from "../engines/midscene/src/worker/surface.mjs";
import { PROTOCOL_SCHEMA_VERSION } from "../engines/midscene/src/lib/job-source.mjs";
import { redactSecrets } from "../engines/midscene/src/lib/redact.mjs";
import { errorText } from "../engines/midscene/src/worker/error-text.mjs";

type Browser = AppiumSession["exec"];

const FIXTURE_DIR = path.resolve(import.meta.dirname, "../engines/midscene/src/device/adapters/fixtures");
const MATRIX_FILE = "capability-matrix.json";
const MATRIX_SCHEMA = "gherkai-device-reprobe/1";
const SCOPE_ID = "device-reprobe";
// 与命令行工具的 acquire-timeout-s 缺省值相同（core/gherkai_core/model.py 的 DEFAULT_ACQUIRE_TIMEOUT_S）。
const DEFAULT_ACQUIRE_TIMEOUT_S = 600;
const W3C_ELEMENT_KEYS = ["element-6066-11e4-a52f-4f735466cecf", "ELEMENT"];
const SCRIPT_METHODS = new Set(["execute", "executeScript"]);
const INPUT_CALLS = new Set(["typeText", "keyboardPress", "clearInput"]);
// 用例的执行次序：输入类紧跟聚焦，手势之后才是会离开当前页面的 DeepLink 与系统键，主屏键最后。
const CALL_ORDER = ["typeText", "clearInput", "keyboardPress", "tap", "longPress", "scroll", "deepLink", "back", "home"];
const PAGE_SOURCE_FIXTURE: Record<Device, string> = { android: "android-page-source.xml", ios: "ios-page-source.xml" };

// ---- 快照的格式 ----

type Recorded = { method: string; args: unknown[] } | { withWebContext: Recorded[] };

interface ContractCase {
  name: string;
  call: string;
  context?: { scale?: number; inputContext?: InputContext | null };
  input?: Record<string, unknown>;
  responses?: Record<string, unknown[]>;
  commands: Recorded[];
}

interface ContractFixture {
  automationName: string;
  cases: ContractCase[];
}

function fixtureFiles(): string[] {
  return fs.readdirSync(FIXTURE_DIR).filter((f) => f.endsWith(".commands.json")).sort();
}

function loadFixture(file: string): ContractFixture {
  return JSON.parse(fs.readFileSync(path.join(FIXTURE_DIR, file), "utf-8")) as ContractFixture;
}

/** 按会话回报的 automationName 取对应的快照（不分大小写）；没有时为 null。 */
function fixtureFor(automationName: string): { file: string; fixture: ContractFixture } | null {
  for (const file of fixtureFiles()) {
    const fixture = loadFixture(file);
    if (fixture.automationName.toLowerCase() === automationName.toLowerCase()) return { file, fixture };
  }
  return null;
}

// ---- 命令记录 ----

interface FlatCommand {
  method: string;
  args: unknown[];
  /** 这条命令失败时的一行原因（已脱敏）；成功为 null。 */
  error: string | null;
}

/** 命令记录：记录开启期间，经 wrap 出的 driver 发出的每条命令按发出次序记下（方法名、归一后的参数、成败），再原样交给被包的对象。
 *  记录关闭时只转发、不记。withWebContext 的形态与快照相同：网页上下文里发出的命令收在一个 withWebContext 节点下，进出网页上下文的
 *  定位与切换命令不记，它们不属于原语。 */
class CommandRecorder {
  private recording = false;
  private tree: Recorded[] = [];
  private current: Recorded[] = this.tree;
  private flat: FlatCommand[] = [];
  private readonly elementIds = new Map<string, string>();

  wrap(target: Browser): Browser {
    const recorder = this;
    return new Proxy(target, {
      get(t, prop) {
        const value: unknown = Reflect.get(t, prop, t);
        if (typeof value !== "function" || typeof prop !== "string") return value;
        return function recordedCommand(...args: unknown[]): unknown {
          return recorder.call(prop, () => Reflect.apply(value as (...a: unknown[]) => unknown, t, args), args);
        };
      },
    });
  }

  begin(): void {
    this.tree = [];
    this.current = this.tree;
    this.flat = [];
    this.elementIds.clear();
    this.recording = true;
  }

  end(): { tree: Recorded[]; flat: FlatCommand[] } {
    this.recording = false;
    return { tree: this.tree, flat: this.flat };
  }

  /** ctx.withWebContext 的记录形态。enter 负责进出网页上下文并在其中调用传给它的函数；只有 fn 里发出的命令进 withWebContext 节点。 */
  async nested<T>(enter: (inner: () => Promise<T>) => Promise<T>, fn: () => Promise<T> | T): Promise<T> {
    if (!this.recording) return enter(async () => fn());
    const node: Recorded[] = [];
    const outer = this.current;
    outer.push({ withWebContext: node });
    this.recording = false;
    try {
      return await enter(async () => {
        this.recording = true;
        this.current = node;
        try {
          return await fn();
        } finally {
          this.recording = false;
          this.current = outer;
        }
      });
    } finally {
      this.recording = true;
      this.current = outer;
    }
  }

  private call(method: string, run: () => unknown, args: unknown[]): unknown {
    if (!this.recording) return run();
    const entry = { method, args: this.normalize(args) };
    this.current.push(entry);
    const flat: FlatCommand = { ...entry, error: null };
    this.flat.push(flat);
    let result: unknown;
    try {
      result = run();
    } catch (e) {
      flat.error = errorText(e);
      throw e;
    }
    if (isThenable(result)) {
      return Promise.resolve(result).then(
        (value) => { this.learnElement(value); return value; },
        (e: unknown) => { flat.error = errorText(e); throw e; },
      );
    }
    this.learnElement(result);
    return result;
  }

  private normalize(args: unknown[]): unknown[] {
    const copy = JSON.parse(JSON.stringify(args ?? [])) as unknown[];
    return copy.map((a) => (typeof a === "string" && this.elementIds.has(a) ? this.elementIds.get(a)! : a));
  }

  private learnElement(value: unknown): void {
    if (value === null || typeof value !== "object") return;
    for (const key of W3C_ELEMENT_KEYS) {
      const id = (value as Record<string, unknown>)[key];
      if (typeof id === "string" && !this.elementIds.has(id)) this.elementIds.set(id, `active-${this.elementIds.size + 1}`);
    }
  }
}

function isThenable(value: unknown): value is PromiseLike<unknown> {
  return value !== null && (typeof value === "object" || typeof value === "function")
    && typeof (value as { then?: unknown }).then === "function";
}

// ---- 命令形态与比对 ----

function flatten(commands: Recorded[]): Array<{ method: string; args: unknown[] }> {
  return commands.flatMap((c) => ("withWebContext" in c ? flatten(c.withWebContext) : [c]));
}

/** 命令形态：方法名；execute 类命令另加脚本名与参数对象的键集合。 */
function formOf(c: { method: string; args: unknown[] }): string {
  if (!SCRIPT_METHODS.has(c.method)) return c.method;
  const [script, params] = c.args;
  const name = typeof script === "string" ? ` ${script}` : "";
  const keys = params !== null && typeof params === "object" && !Array.isArray(params)
    ? ` {${Object.keys(params as Record<string, unknown>).sort().join(",")}}` : "";
  return `${c.method}${name}${keys}`;
}

/** 连续重复的同一条命令收成一条；网页上下文节点逐层收。 */
function collapse(commands: Recorded[]): Recorded[] {
  const out: Recorded[] = [];
  for (const c of commands) {
    const item: Recorded = "withWebContext" in c ? { withWebContext: collapse(c.withWebContext) } : c;
    if (out.length > 0 && JSON.stringify(out[out.length - 1]) === JSON.stringify(item)) continue;
    out.push(item);
  }
  return out;
}

/** 把值里与 from 逐字相等的字符串换成 to（DeepLink 用例的地址与应用标识换成本次的值）。 */
function substitute<T>(value: T, swaps: ReadonlyMap<string, string | null>): T {
  if (typeof value === "string") return (swaps.has(value) ? swaps.get(value) : value) as T;
  if (Array.isArray(value)) return value.map((v) => substitute(v, swaps)) as T;
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, substitute(v, swaps)])) as T;
  }
  return value;
}

// ---- 执行一条快照用例 ----

type CaseStatus = "ok" | "failed" | "skipped";

interface CaseResult {
  name: string;
  call: string;
  status: CaseStatus;
  /** skipped 的原因。 */
  reason?: string;
  error?: string;
  /** 异常上挂着的归类（命令守卫与设备模块给出）；没有为 null。 */
  error_type?: string | null;
  commands?: Recorded[];
  expected: Recorded[];
  /** 归一后与快照逐条相同；没有执行或执行失败为 null。 */
  matches_fixture: boolean | null;
  flat?: FlatCommand[];
}

/** 快照用例的原语名到适配器方法（与 adapters.contract.test.mts 的 runCase 同一解读）。 */
async function runPrimitive(adapter: DeviceAdapter, ctx: PrimitiveContext, call: string, input: Record<string, unknown>): Promise<void> {
  const i = input as Record<string, any>;
  switch (call) {
    case "tap": return adapter.tap(ctx, i.point);
    case "longPress": return adapter.longPress(ctx, i.point, i.durationMs);
    case "scroll": return adapter.scroll(ctx, { direction: i.direction, distance: i.distance ?? null, screen: i.screen });
    case "typeText": return adapter.typeText(ctx, i.text);
    case "keyboardPress": return adapter.keyboardPress(ctx, i.keyName);
    case "clearInput": return adapter.clearInput(ctx);
    case "home": return adapter.systemButtons.home.press(ctx);
    case "back": {
      const back = adapter.systemButtons.back;
      if (back === null) throw new Error("这个适配器没有系统返回键");
      return back.press(ctx);
    }
    case "deepLink": return adapter.deepLink(ctx.driver, i.address, i.appId ?? null);
    default: throw new Error(`快照里的原语名 ${JSON.stringify(call)} 不认识`);
  }
}

function contextOf(c: ContractCase, driver: Browser, withWebContext: PrimitiveContext["withWebContext"]): PrimitiveContext {
  return { driver, scale: c.context?.scale ?? 1, inputContext: c.context?.inputContext ?? null, withWebContext };
}

function finishCase(
  c: ContractCase, expected: Recorded[], recorded: { tree: Recorded[]; flat: FlatCommand[] }, error: unknown | null,
): CaseResult {
  const base = { name: c.name, call: c.call, expected, commands: recorded.tree, flat: recorded.flat };
  if (error !== null) {
    return {
      ...base, status: "failed", error: errorText(error), error_type: readClassification(error)?.errorType ?? null,
      matches_fixture: null,
    };
  }
  const same = JSON.stringify(collapse(recorded.tree)) === JSON.stringify(collapse(expected));
  return { ...base, status: "ok", matches_fixture: same };
}

// ---- 差集 ----

interface Diff {
  fixture: string;
  /** 快照里的形态被真机拒绝：形态、出现在哪些用例、真机给的原因。 */
  rejected: Array<{ form: string; cases: string[]; error: string }>;
  /** 快照里的形态这一次没有执行到，附没有执行到的原因。 */
  not_exercised: Array<{ form: string; reasons: string[] }>;
  /** 执行中发出了快照里没有的形态。 */
  unexpected: Array<{ form: string; cases: string[] }>;
  /** 执行成功但归一后的命令序列与快照不同的用例。 */
  mismatched_cases: string[];
  /** 执行失败、却不是某条命令被拒的用例（例如被命令守卫拒绝、适配器在发命令前判定不提供）。 */
  failed_cases: Array<{ name: string; error_type: string | null; error: string }>;
}

function diffAgainstFixture(file: string, results: CaseResult[]): Diff {
  const fixtureForms = new Map<string, Set<string>>();  // 形态 → 快照里出现它的用例
  for (const r of results) {
    for (const cmd of flatten(r.expected)) {
      const form = formOf(cmd);
      if (!fixtureForms.has(form)) fixtureForms.set(form, new Set());
      fixtureForms.get(form)!.add(r.name);
    }
  }
  const accepted = new Set<string>();
  const rejected = new Map<string, { cases: Set<string>; error: string }>();
  const seen = new Map<string, Set<string>>();
  const failed: Diff["failed_cases"] = [];
  for (const r of results) {
    if (r.status === "skipped") continue;
    let commandRejected = false;
    for (const cmd of r.flat ?? []) {
      const form = formOf(cmd);
      if (!seen.has(form)) seen.set(form, new Set());
      seen.get(form)!.add(r.name);
      if (cmd.error === null) { accepted.add(form); continue; }
      commandRejected = true;
      const hit = rejected.get(form) ?? { cases: new Set<string>(), error: cmd.error };
      hit.cases.add(r.name);
      rejected.set(form, hit);
    }
    if (r.status === "failed" && !commandRejected) failed.push({ name: r.name, error_type: r.error_type ?? null, error: r.error ?? "" });
  }
  const notExercised: Diff["not_exercised"] = [];
  for (const [form, cases] of fixtureForms) {
    if (accepted.has(form) || rejected.has(form)) continue;
    const reasons = new Set<string>();
    for (const r of results) {
      if (!cases.has(r.name)) continue;
      reasons.add(r.status === "skipped" ? `${r.name}：${r.reason ?? ""}`
        : r.status === "failed" ? `${r.name}：执行中途失败，没有发到这条命令`
        : `${r.name}：执行成功，但发出的命令里没有这一形态（见 mismatched_cases）`);
    }
    notExercised.push({ form, reasons: [...reasons] });
  }
  return {
    fixture: file,
    rejected: [...rejected].map(([form, v]) => ({ form, cases: [...v.cases], error: v.error })),
    not_exercised: notExercised,
    unexpected: [...seen].filter(([form]) => !fixtureForms.has(form)).map(([form, cases]) => ({ form, cases: [...cases] })),
    mismatched_cases: results.filter((r) => r.status === "ok" && r.matches_fixture === false).map((r) => r.name),
    failed_cases: failed,
  };
}

interface PageSourceDiff {
  fixture: string;
  fixture_root: string;
  device_root: string;
  /** 样例控件树里出现、真机控件树里一次都没有的属性名（适配器抽取控件摘要读这些属性）。 */
  missing_attributes: string[];
}

function pageSourceDiff(fixtureFile: string, fixtureXml: string, deviceXml: string): PageSourceDiff {
  const fx = scanXmlElements(fixtureXml);
  const dv = scanXmlElements(deviceXml);
  const names = (els: ReturnType<typeof scanXmlElements>): Set<string> => new Set(els.flatMap((e) => [...e.attrs.keys()]));
  const onDevice = names(dv);
  return {
    fixture: fixtureFile,
    fixture_root: fx[0].tag,
    device_root: dv[0].tag,
    missing_attributes: [...names(fx)].filter((n) => !onDevice.has(n)).sort(),
  };
}

function diffIsClean(d: Diff): boolean {
  return d.rejected.length === 0 && d.unexpected.length === 0 && d.mismatched_cases.length === 0 && d.failed_cases.length === 0;
}

function pageSourceIsClean(d: PageSourceDiff | null): boolean {
  return d === null || (d.missing_attributes.length === 0 && d.fixture_root === d.device_root);
}

// ---- 离线自检 ----

/** 按快照应答的假 driver：每条命令依次取 responses 里的应答（Error 实例表示这一次抛出它），缺省时活动元素返回 active-1。 */
function fakeDriver(responses: Record<string, unknown[]> = {}): Browser {
  const queues = new Map(Object.entries(responses).map(([k, v]) => [k, [...v]]));
  return new Proxy({}, {
    get(_t, prop) {
      if (typeof prop !== "string" || prop === "then") return undefined;
      return async () => {
        const queue = queues.get(prop);
        if (queue && queue.length > 0) {
          const next = queue.shift();
          if (next instanceof Error) throw next;
          return next;
        }
        return prop === "getActiveElement" ? { [W3C_ELEMENT_KEYS[0]]: "active-1" } : undefined;
      };
    },
  }) as unknown as Browser;
}

function offlineAdapter(automationName: string): DeviceAdapter {
  if (automationName.toLowerCase() === "uiautomator2") {
    return createUiAutomator2Adapter({
      foregroundPoll: { attempts: DEEP_LINK_FOREGROUND_POLL_ATTEMPTS, intervalMs: DEEP_LINK_FOREGROUND_POLL_INTERVAL_MS },
      sleep: async () => {},
    });
  }
  if (automationName.toLowerCase() === "xcuitest") return createXcuitestAdapter();
  throw new Error(`快照的 automationName ${JSON.stringify(automationName)} 没有对应的适配器`);
}

async function offlineSelfCheck(): Promise<number> {
  let clean = true;
  const report: Record<string, unknown> = {};
  for (const file of fixtureFiles()) {
    const fixture = loadFixture(file);
    const results: CaseResult[] = [];
    for (const c of fixture.cases) {
      const recorder = new CommandRecorder();
      const driver = recorder.wrap(fakeDriver(c.responses));
      const ctx = contextOf(c, driver, (fn) => recorder.nested((inner) => inner(), fn));
      const input = c.input ?? {};
      recorder.begin();
      let error: unknown | null = null;
      try {
        await runPrimitive(offlineAdapter(fixture.automationName), ctx, c.call, input);
      } catch (e) {
        error = e;
      }
      results.push(finishCase(c, c.commands, recorder.end(), error));
    }
    const diff = diffAgainstFixture(file, results);
    report[file] = { cases: results.length, ...diff };
    if (!diffIsClean(diff) || diff.not_exercised.length > 0) clean = false;
  }
  for (const file of Object.values(PAGE_SOURCE_FIXTURE)) {
    const xml = fs.readFileSync(path.join(FIXTURE_DIR, file), "utf-8");
    const d = pageSourceDiff(file, xml, xml);
    report[file] = d;
    if (!pageSourceIsClean(d)) clean = false;
  }
  process.stdout.write(JSON.stringify(report, null, 2) + "\n");
  log(clean ? "离线自检通过：两份快照与两份控件树样例都是零差异" : "离线自检有差异，见标准输出");
  return clean ? 0 : 1;
}

// ---- 真机重新探测 ----

interface Options {
  platform: Device;
  uiKind: UiKind;
  projectArn: string;
  deviceArn: string | null;
  osVersion: string | null;
  billingMethod: string;
  acquireTimeoutS: number;
  app: { bucket: string; key: string; appId: string } | null;
  url: string | null;
  focus: { x: number; y: number } | null;
  deepLink: string | null;
  out: string;
}

interface Captured {
  adapter: DeviceAdapter | null;
  probe: Outcome<ProbeConclusion> | null;
  agent: { driver: Browser; session: AppiumSession; scale: number; inputContext: InputContext | null } | null;
  actionSpace: string[] | null;
}

/** 缺省装配外加一层记录：命令守卫的执行实例包上命令记录，选出的适配器、探测结论与界面实现的构造参数在经过时记下。 */
function recordingParts(captured: Captured, recorder: CommandRecorder): (env: DevicePartsEnv) => DeviceParts {
  return (env) => {
    const real = defaultDeviceParts(env);
    return {
      ...real,
      probe: {
        async run(session, target, budget, sessionStatus) {
          captured.probe = await real.probe.run(session, target, budget, sessionStatus);
          return captured.probe;
        },
      },
      adapters: {
        select(automationName) {
          captured.adapter = real.adapters.select(automationName);
          return captured.adapter;
        },
      },
      guards: {
        create(args) {
          return real.guards.create({ ...args, exec: recorder.wrap(args.exec) });
        },
      },
      agents: {
        // 注入的部件按端口的最小面定型，界面实现块要的是完整面：两者是同一次装配选出的同一个实例，这里取记下的那个。
        create: (args) => {
          const adapter = captured.adapter;
          if (adapter === null || adapter !== args.adapter) throw new Error("界面实现收到的适配器不是适配器清单选出的那个实例");
          const full = { ...args, adapter };
          captured.agent = { driver: args.driver, session: args.session, scale: args.scale, inputContext: args.inputContext };
          captured.actionSpace = createAppiumInterface(full).actionSpace().map((a) => a.name);
          return real.agents.create(full);
        },
      },
    };
  };
}

type Attempt<T> = { value: T } | { error: string };

async function attempt<T>(fn: () => Promise<T>): Promise<Attempt<T>> {
  try {
    return { value: await fn() };
  } catch (e) {
    return { error: errorText(e) };
  }
}

const valueOf = <T,>(a: Attempt<T>): T | null => ("value" in a ? a.value : null);

/** 能力探测的逐项事实，经生命周期通道（执行实例与探测实例直接发出，不经命令守卫）读取。 */
async function probeFacts(session: AppiumSession, device: Device): Promise<Record<string, unknown>> {
  const facts: Record<string, unknown> = {};
  facts.current_context = await attempt(() => session.currentContext());
  const names = await attempt(async () => contextNames(await session.exec.getContexts()));
  facts.contexts = names;
  const list = valueOf(names);
  facts.web_context_candidates = list === null ? null : webContextCandidates(list, device);
  facts.switch_to_native = await attempt(() => session.switchToNative());
  if (device === "ios") {
    const probe = probeClientOf(session);
    facts.device_screen_info_scale = await attempt(async () => (await deviceScreenInfo(probe)).scale);
    const shot = await attempt(async () => pngLongEdge(await session.exec.takeScreenshot()));
    const win = await attempt(async () => applicationLongEdge(await session.pageSource(AbortSignal.timeout(SNAPSHOT_CAPTURE_BUDGET_MS))));
    facts.screenshot_long_edge = shot;
    facts.window_long_edge = win;
    facts.page_source_scale = scaleFromSizes(valueOf(shot), valueOf(win));
    facts.active_app_bundle_id = await attempt(async () => (await activeAppInfo(probe)).bundleId);
  } else {
    facts.current_package = await attempt(() => session.exec.getCurrentPackage());
  }
  return facts;
}

/** 本次要执行的用例与跳过的原因。 */
function planCases(fixture: ContractFixture, opts: Options, conclusion: ProbeConclusion): Array<{ c: ContractCase; skip: string | null }> {
  const ordered = [...fixture.cases].sort((a, b) => rank(a.call) - rank(b.call));
  return ordered.map((c) => ({ c, skip: skipReason(c, opts, conclusion) }));
}

function rank(call: string): number {
  const i = CALL_ORDER.indexOf(call);
  return i < 0 ? CALL_ORDER.length : i;
}

function skipReason(c: ContractCase, opts: Options, conclusion: ProbeConclusion): string | null {
  if (INPUT_CALLS.has(c.call) && opts.focus === null) return "没有给 --focus：输入类原语需要一个已获得焦点的输入框";
  if (c.context?.inputContext === "web" && conclusion.webContext !== "available") {
    return "这台设备的网页上下文结论不是「提供」，网页上下文里的输入用例无法执行";
  }
  if (c.call === "deepLink") {
    if (opts.deepLink === null) return "没有给 --deep-link";
    const caseForApp = (c.input?.appId ?? null) !== null;
    if (caseForApp !== (opts.uiKind === "app")) return "这条用例针对另一种界面类型的 DeepLink";
  }
  return null;
}

async function runOnDevice(opts: Options): Promise<number> {
  fs.mkdirSync(opts.out, { recursive: true });
  const runId = `device-reprobe-${new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+Z$/, "Z")}`;
  const matrix: Record<string, unknown> = {
    schema: MATRIX_SCHEMA,
    generated_at: new Date().toISOString(),
    run_id: runId,
    target: { platform: opts.platform, ui_kind: opts.uiKind, app_id: opts.app?.appId ?? null },
    request: {
      device_arn: opts.deviceArn, os_version: opts.osVersion, billing_method: opts.billingMethod, project_arn: opts.projectArn,
      acquire_timeout_s: opts.acquireTimeoutS,
    },
  };
  const events: Array<Record<string, unknown>> = [];
  const captured: Captured = { adapter: null, probe: null, agent: null, actionSpace: null };
  const recorder = new CommandRecorder();
  const job: SurfaceDeps["job"] = {
    schemaVersion: PROTOCOL_SCHEMA_VERSION,
    scope: { id: SCOPE_ID, name: SCOPE_ID },
    engine: "midscene",
    assertionVotes: 1,
    timeoutS: null,
    target: {
      device: opts.platform, uiKind: opts.uiKind,
      ...(opts.app ? { app: { alias: SCOPE_ID, bucket: opts.app.bucket, key: opts.app.key, sha256: null, appId: opts.app.appId } } : {}),
    },
    deviceRequest: {
      provider: "aws-device-farm",
      ...(opts.deviceArn ? { deviceArn: opts.deviceArn } : { osVersion: opts.osVersion! }),
      billingMethod: opts.billingMethod, projectArn: opts.projectArn, acquireTimeoutS: opts.acquireTimeoutS,
    },
  };
  let finishing: Promise<number> | null = null;
  let surface: TargetSurface | null = null;
  const interrupt = (code: number, why: string): void => {
    finishing ??= (async () => {
      log(`${why}：进入终结，停止本次建立的远程访问会话`);
      const outcome = surface ? await surface.release("interrupt") : null;
      matrix.release = outcome ? { mode: "interrupt", release_failed: outcome.releaseFailed } : null;
      matrix.session_events = events;
      writeMatrix(opts.out, matrix);
      process.exit(code);
    })();
  };
  process.on("SIGINT", () => interrupt(130, "收到 SIGINT"));
  process.on("SIGTERM", () => interrupt(143, "收到 SIGTERM"));
  const deps: SurfaceDeps = {
    job,
    emit: async (event) => {
      events.push(event);
      log(`会话事件 ${String(event.type)}：${String(event.name ?? "")}（${String(event.origin ?? event.release ?? "")}）`);
    },
    log,
    agentOpts: { generateReport: false, persistExecutionDump: false },
    uploader: { refFor: (p) => pathToFileURL(p).href, toReportRef: async (p) => pathToFileURL(p).href },
    artifactRoot: opts.out,
    requestFinalization: () => interrupt(1, "进程级异常"),
  };
  surface = createDeviceSurface(deps, { parts: recordingParts(captured, recorder), env: { ...process.env, RUN_ID: runId } });

  let clean = false;
  try {
    log(`获取设备（等待上限 ${opts.acquireTimeoutS} 秒）`);
    const acquired = await surface.acquire();
    if (!acquired.ready) {
      matrix.acquire = { ready: false, error_type: acquired.termination.errorType, message: acquired.termination.message };
      log(`没有就绪：${acquired.termination.errorType}：${acquired.termination.message}`);
    } else {
      matrix.acquire = { ready: true, session_arn: acquired.sessionId };
      clean = await exerciseSession(surface, captured, recorder, opts, matrix);
      await attempt(() => acquired.agent.destroy());
    }
  } catch (e) {
    matrix.error = errorText(e);
    log(`重新探测中途出错：${errorText(e)}`);
  } finally {
    if (finishing === null) {
      const outcome = await surface.release("normal");
      matrix.release = { mode: "normal", release_failed: outcome.releaseFailed, report_refs: outcome.reportRefs };
      matrix.session_events = events;
      if (outcome.releaseFailed) clean = false;
      writeMatrix(opts.out, matrix);
    }
  }
  if (finishing !== null) return finishing;
  const pending = (matrix.diff as { not_exercised?: unknown[] } | undefined)?.not_exercised?.length ?? 0;
  log(clean
    ? (pending > 0 ? `差集为空，但有 ${pending} 个快照形态没有执行到（见 diff.not_exercised）` : "差集为空")
    : "差集不为空、会话未就绪或释放未确认，见能力矩阵");
  return clean ? 0 : 1;
}

async function exerciseSession(
  surface: TargetSurface, captured: Captured, recorder: CommandRecorder, opts: Options, matrix: Record<string, unknown>,
): Promise<boolean> {
  const { adapter, agent, probe } = captured;
  if (adapter === null || agent === null || probe === null || !probe.ok) throw new Error("接缝就绪了，却没有记下适配器、探测结论或界面实现的参数");
  const conclusion = probe.value;
  const session = agent.session;
  matrix.automation_name = adapter.automationName;
  matrix.platform_version = session.platformVersion;
  matrix.action_space = captured.actionSpace;
  matrix.probe = { conclusion, items: await probeFacts(session, opts.platform) };

  // 1. 打开测试页（可选）：经接缝的导航，路线按探测结论定，与内建导航 step 相同。
  if (opts.url !== null) {
    const opened = await attempt(() => surface.execute(() => surface.navigate(opts.url!)));
    await surface.restore({ status: "error" in opened ? "error" : "passed", message: "error" in opened ? opened.error : null });
    matrix.page = {
      url: opts.url,
      route: opts.uiKind === "app" || conclusion.webContext !== "available" ? "deep_link" : "url",
      ...("error" in opened ? { error: opened.error } : {}),
    };
  }

  // 2. 控件树：接缝的界面快照（与失败 step 的证据同一条采集路径）与样例的属性差集。
  const facts = { kind: "deterministic", status: "failed" } as const;
  const address = await surface.readAddress(facts);
  const snap = await surface.snapshot(facts, address);
  matrix.snapshot = { ...snap.snapshot, failure: snap.failure };
  let psDiff: PageSourceDiff | null = null;
  const fixtureXmlFile = PAGE_SOURCE_FIXTURE[opts.platform];
  const deviceXml = await attempt(() => session.pageSource(AbortSignal.timeout(SNAPSHOT_CAPTURE_BUDGET_MS)));
  if ("value" in deviceXml) {
    psDiff = pageSourceDiff(fixtureXmlFile, fs.readFileSync(path.join(FIXTURE_DIR, fixtureXmlFile), "utf-8"), deviceXml.value);
    matrix.page_source = { controls_total: adapter.extractControls(deviceXml.value).total, diff: psDiff };
  } else {
    matrix.page_source = { error: deviceXml.error };
  }

  // 3. 快照用例。
  const found = fixtureFor(adapter.automationName);
  if (found === null) throw new Error(`没有 automationName 为 ${adapter.automationName} 的命令契约快照`);
  const realCtx: PrimitiveContext = {
    driver: agent.driver, scale: conclusion.scale, inputContext: conclusion.inputContext,
    withWebContext: (fn) => session.withWebContext(agent.driver, fn),
  };
  const results: CaseResult[] = [];
  let lost = false;
  for (const { c, skip } of planCases(found.fixture, opts, conclusion)) {
    const swaps = new Map<string, string | null>();
    let input = c.input ?? {};
    if (c.call === "deepLink" && skip === null) {
      if (typeof input.address === "string") swaps.set(input.address, opts.deepLink);
      if (typeof input.appId === "string") swaps.set(input.appId, opts.app?.appId ?? null);
      input = { ...input, address: opts.deepLink, appId: opts.app?.appId ?? null };
    }
    const expected = substitute(c.commands, swaps);
    if (skip !== null || lost) {
      results.push({ name: c.name, call: c.call, status: "skipped", reason: lost ? "会话已丢失" : skip!, expected, matches_fixture: null });
      continue;
    }
    if (INPUT_CALLS.has(c.call) && opts.focus !== null) {
      const focus = opts.focus;
      await attempt(() => surface.execute(() => adapter.tap(realCtx, focus)));
      await surface.restore({ status: "passed", message: null });
    }
    const pre = await surface.preStep();
    if (pre !== null) {
      results.push({ name: c.name, call: c.call, status: "failed", error: pre.message, error_type: pre.errorType, expected, matches_fixture: null });
      lost = pre.errorType === "session_lost";
      continue;
    }
    const ctx = contextOf(c, agent.driver, (fn) => recorder.nested((inner) => session.withWebContext(agent.driver, inner), fn));
    recorder.begin();
    let error: unknown | null = null;
    try {
      await surface.execute(() => runPrimitive(adapter, ctx, c.call, input));
    } catch (e) {
      error = e;
    }
    const result = finishCase(c, expected, recorder.end(), error);
    results.push(result);
    const restored = await surface.restore({
      status: result.status === "ok" ? "passed" : "error", message: result.status === "ok" ? null : result.error ?? null,
    });
    log(`用例 ${c.name}：${result.status}${result.error ? `（${result.error}）` : ""}`);
    if (result.error_type === "session_lost" || restored?.errorType === "session_lost") lost = true;
  }
  const diff = diffAgainstFixture(found.file, results);
  matrix.cases = results;
  matrix.diff = diff;
  return diffIsClean(diff) && pageSourceIsClean(psDiff) && !lost;
}

function writeMatrix(dir: string, matrix: Record<string, unknown>): void {
  const file = path.join(dir, MATRIX_FILE);
  fs.writeFileSync(file, redactSecrets(JSON.stringify(matrix, null, 2)) + "\n", "utf-8");
  log(`能力矩阵：${file}`);
}

function log(line: string): void {
  process.stderr.write(redactSecrets(`device_reprobe: ${line}`) + "\n");
}

// ---- 命令行 ----

const USAGE = `用法（在 engines/midscene 目录下执行）：
  node_modules/.bin/tsx ../../tools/device_reprobe.mts --offline
  node_modules/.bin/tsx ../../tools/device_reprobe.mts --platform android|ios --project-arn <ARN> (--device-arn <ARN> | --os-version <版本>)
      [--ui-kind web|app] [--app-bucket <桶> --app-key <键> --app-id <包名或 bundle id>] [--url <地址>] [--focus <x>,<y>]
      [--deep-link <地址>] [--billing-method METERED|UNMETERED] [--acquire-timeout-s <秒>] [--out <目录>]
选项说明与判读见 tools/device_reprobe.md。`;

class UsageError extends Error {}

function parseOptions(argv: string[]): Options | "offline" {
  const { values } = parseArgs({
    args: argv,
    options: {
      offline: { type: "boolean" }, help: { type: "boolean" },
      platform: { type: "string" }, "ui-kind": { type: "string" }, "project-arn": { type: "string" },
      "device-arn": { type: "string" }, "os-version": { type: "string" }, "billing-method": { type: "string" },
      "acquire-timeout-s": { type: "string" }, "app-bucket": { type: "string" }, "app-key": { type: "string" },
      "app-id": { type: "string" }, url: { type: "string" }, focus: { type: "string" }, "deep-link": { type: "string" },
      out: { type: "string" },
    },
  });
  if (values.help) throw new UsageError("");
  if (values.offline) return "offline";
  const platform = values.platform;
  if (!(DEVICES as readonly string[]).includes(platform ?? "")) throw new UsageError("--platform 须为 android 或 ios");
  const uiKind = values["ui-kind"] ?? "web";
  if (!(UI_KINDS as readonly string[]).includes(uiKind)) throw new UsageError("--ui-kind 须为 web 或 app");
  const projectArn = values["project-arn"] ?? process.env.GHERKAI_DEVICE_FARM_PROJECT_ARN ?? "";
  if (projectArn === "") throw new UsageError("缺 --project-arn（或环境变量 GHERKAI_DEVICE_FARM_PROJECT_ARN）");
  const deviceArn = values["device-arn"] ?? null;
  const osVersion = values["os-version"] ?? null;
  if ((deviceArn === null) === (osVersion === null)) throw new UsageError("--device-arn 与 --os-version 须给且只给一个");
  const acquireTimeoutS = values["acquire-timeout-s"] === undefined ? DEFAULT_ACQUIRE_TIMEOUT_S : Number(values["acquire-timeout-s"]);
  if (!Number.isFinite(acquireTimeoutS) || acquireTimeoutS <= 0) throw new UsageError("--acquire-timeout-s 须为正数秒");
  let app: Options["app"] = null;
  if (uiKind === "app") {
    const bucket = values["app-bucket"]; const key = values["app-key"]; const appId = values["app-id"];
    if (!bucket || !key || !appId) throw new UsageError("应用目标须给 --app-bucket、--app-key 与 --app-id");
    app = { bucket, key, appId };
  }
  let focus: Options["focus"] = null;
  if (values.focus !== undefined) {
    const m = /^\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*$/.exec(values.focus);
    if (m === null) throw new UsageError("--focus 须写成 <x>,<y>（截图像素坐标）");
    focus = { x: Number(m[1]), y: Number(m[2]) };
  }
  return {
    platform: platform as Device, uiKind: uiKind as UiKind, projectArn, deviceArn, osVersion,
    billingMethod: values["billing-method"] ?? "METERED", acquireTimeoutS, app,
    url: values.url ?? null, focus, deepLink: values["deep-link"] ?? null,
    out: values.out ? path.resolve(values.out) : fs.mkdtempSync(path.join(os.tmpdir(), "gherkai-device-reprobe-")),
  };
}

async function main(): Promise<number> {
  let parsed: Options | "offline";
  try {
    parsed = parseOptions(process.argv.slice(2));
  } catch (e) {
    if (e instanceof UsageError) {
      if (e.message) process.stderr.write(`device_reprobe: ${e.message}\n`);
      process.stderr.write(USAGE + "\n");
      return 2;
    }
    process.stderr.write(`device_reprobe: ${errorText(e)}\n${USAGE}\n`);
    return 2;
  }
  return parsed === "offline" ? offlineSelfCheck() : runOnDevice(parsed);
}

const code = await main();
process.exitCode = code;
// WebdriverIO 与 SDK 的连接池可能在会话结束后仍留着句柄：给输出留一点时间写完，再显式退出（计时器不阻止进程自然结束）。
setTimeout(() => process.exit(code), 1000).unref();
