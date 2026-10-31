// 能力探测（ADR 0052 决策 5；决策 2 的失败归级）：实现 device/surface.mts 的 CapabilityProbe 端口。建连后、预热前执行一次，
// 只缓存结论（网页上下文提供 / 不提供 / 探测出错、候选数、输入路线、坐标比例与它的来源、Appium 版本），不缓存上下文句柄：之后每次
// 进入网页上下文都经 device/web-context.mts 重新定位。择路在交给 AI 之前一次定下，不在运行期试错回落（失败的路线有的不抛错、
// 只是空等，模型还会重试到重规划上限）。
//
// 探测项与次序：
//   1. 回到原生上下文（网页目标的会话建好时处在网页上下文，后面的控件树读取要在原生上下文）；失败先查会话状态，丢失即 session_lost；
//   2. Appium 版本：探测实例读 /status，只记诊断，读不到为 null；
//   3. 坐标比例（只 iOS；Android 恒为 1）：经探测实例读设备屏幕信息的 scale。读不到时回退为截图长边除以窗口长边、取整，窗口长边取
//      原生控件树里 XCUIElementTypeApplication 节点的宽与高中的较大者（真机控件树的根是不带属性的 AppiumAUT，这个节点是它的第一个
//      子节点）；不取 getWindowRect（iOS 26.3 上两种上下文都报错，被拒方案）。
//      回退也失败是执行前失败：先查会话状态，丢失归 session_lost，否则 engine_error「无法确定坐标比例」——猜错的比例会让每个手势
//      都落空，所以没有缺省值；
//   4. 网页上下文（只网页目标）：见下；
//   5. 输入路线：iOS 网页上下文可用时在网页上下文取活动元素，否则在原生上下文；Android 固定为 mobile 输入命令、不探测，记 null。
//
// 网页上下文的判据是在短预算内成功执行一条只读命令，列得出、切得进都不算。列上下文、切入与只读命令（读当前地址）都由探测实例发出：
// 它自带 PROBE_TIMEOUT_MS 的客户端超时，一条挂住的网页命令到点由客户端中止，不靠放弃式等待（被拒方案「探测用 Promise.race」）。
// 有界重试一次（重新定位后再切入、再读），以区分瞬时故障与确认不提供；零候选的重试就是定位规则里的「等一会儿再列一次」。每次尝试
// 记下失败在哪一环（列上下文、切入、只读命令），按证据性质归类：
//   - 重试后候选仍为零：不提供；
//   - 两次尝试都切入成功、只读命令都失败，最后一次是超时或服务端报错（不是传输层错误），而原生上下文的只读命令正常（逐条路线实测中
//     iOS 26.3 切入成功、网页命令立即返回检查器错误的样本属于这种）：不提供。只读命令只失败过一次（另一次失败在列上下文或切入）
//     不够这条证据；
//   - 切入本身失败（重试之后仍切不进，从未执行只读命令）、列上下文的调用本身失败、最后一次失败是传输层错误（连接层错误码、
//     HTTP 502 / 503 / 504，或没有错误码与状态码的失败）：探测出错。真机验收中 iOS 26.3 属于这种：切入本身在服务端挂住约 150 秒
//     才返回，PROBE_TIMEOUT_MS（当前 15 秒）先于它到期，失败落在切入一环；
//   - 原生只读命令也失败（会话异常）：先查会话状态，丢失归 session_lost，否则探测出错；
//   - 多个候选：定位规则拒绝歧义、无法确定被测页面，同样是无法区分设备能力的情形，记探测出错，不按第一个去猜。
// 会话丢失发生在 scope_started 之前，消息用执行前的那句（surface.mts 的 SESSION_LOST_BEFORE_START_MESSAGE）。
// 原生一侧的核对（切回原生上下文与原生截图）经生命周期通道的执行实例发出：它的超时是单条命令的真实上界，探测实例的网页命令挂住时
// 不会因为短超时把原生命令误判为失败：Appium 服务端对同一会话的命令串行执行，真机验收中 iOS 26.3 上探测实例的切入挂住期间，执行
// 实例发出的原生只读命令曾被延迟约 105 秒。两种否定结论下导航都不走 url（接缝据此选 deepLink 路线）。
//
// 获取预算：整个探测在 Appium 块的 withDeadline 之下执行，预算到期或进入终结时在途命令随之中止；每一步之后核对一次，中止即停、归
// acquire_timeout（进入终结时这个结果不会被使用）。
//
// mobile 命令只出现在驱动适配器里（ADR 0052 决策 4）：设备屏幕信息由部件装配方从 XCUITest 适配器的导出注入（ProbeDeps）。会话状态的
// 查询经 run 的第四个参数注入（Device Farm 会话块的 status 绑定到当前会话 ARN）；不传时命令失败不判会话丢失。
import type { Browser } from "webdriverio";
import type { Device, UiKind } from "../worker/deterministic.mjs";
import { errorText } from "../worker/error-text.mjs";
import type { ScaleSource } from "./device-session.mjs";
import {
  commandFailureKind, defaultSleep, probeClientOf, withDeadline, type CommandFailureKind, type Sleep,
} from "./appium.mjs";
import {
  ACQUIRE_TIMEOUT_MESSAGE, SESSION_LOST_BEFORE_START_MESSAGE,
  type AcquireBudget, type AppiumSession, type CapabilityProbe, type Outcome, type ProbeConclusion, type WebContextVerdict,
} from "./surface.mjs";
import { NATIVE_CONTEXT, locateWebContext } from "./web-context.mjs";

/** 坐标比例回退之后仍无法确定：ADR 0052 决策 5 的原文。 */
export const SCALE_UNKNOWN_MESSAGE = "无法确定坐标比例";

export interface ProbeDeps {
  /** iOS 的设备屏幕信息：执行只读的 mobile 命令 deviceScreenInfo 并返回它的结果（XCUITest 适配器的导出）。探测经探测实例调用。 */
  deviceScreenInfo(driver: Browser): Promise<unknown>;
  /** worker 日志：探测里不影响结论走向的失败原因（经一行化与脱敏）。不传时不记。 */
  log?: (line: string) => void;
  /** 零候选之后再列一次之前的等待，只供测试注入。 */
  sleep?: Sleep;
}

/** 会话状态的查询（GetRemoteAccessSession 的状态值）：查询失败返回 null 或抛出，此时不据此判会话丢失。 */
export type SessionStatusQuery = () => Promise<string | null>;

/** 端口 CapabilityProbe 的实现，run 另收可选的会话状态查询。 */
export interface DeviceCapabilityProbe extends CapabilityProbe {
  run(
    session: AppiumSession, target: { device: Device; uiKind: UiKind }, budget: AcquireBudget, sessionStatus?: SessionStatusQuery,
  ): Promise<Outcome<ProbeConclusion>>;
}

export function createCapabilityProbe(deps: ProbeDeps): DeviceCapabilityProbe {
  return {
    run(session, target, budget, sessionStatus) {
      if (budget.signal.aborted) return Promise.resolve(stoppedOutcome());
      const probe = probeClientOf(session);
      const run: ProbeRun = { session, probe, target, budget, sessionStatus, deps, sleep: deps.sleep ?? defaultSleep };
      return withDeadline(budget.signal, () => runProbe(run));
    },
  };
}

// ---- 实现 ----

interface ProbeRun {
  session: AppiumSession;
  probe: Browser;
  target: { device: Device; uiKind: UiKind };
  budget: AcquireBudget;
  sessionStatus: SessionStatusQuery | undefined;
  deps: ProbeDeps;
  sleep: Sleep;
}

// 消息常量来自 surface.mts，模块顶层不读（理由同 appium.mts 的 acquireTimedOut）。
const stoppedOutcome = (): Outcome<ProbeConclusion> => ({
  ok: false, termination: { errorType: "acquire_timeout", message: ACQUIRE_TIMEOUT_MESSAGE },
});
const lostOutcome = (): Outcome<ProbeConclusion> => ({
  ok: false, termination: { errorType: "session_lost", message: SESSION_LOST_BEFORE_START_MESSAGE },
});
const RUNNING = "RUNNING";

function log(r: ProbeRun, line: string): void {
  r.deps.log?.(`worker: 能力探测：${line}`);
}

async function runProbe(r: ProbeRun): Promise<Outcome<ProbeConclusion>> {
  const stopped = (): boolean => r.budget.signal.aborted;

  // 1. 回到原生上下文
  let nativeOk = true;
  try {
    await ensureNative(r.session);
  } catch (e) {
    if (stopped()) return stoppedOutcome();
    if (await sessionLost(r)) return lostOutcome();
    nativeOk = false;
    log(r, `未能切回原生界面：${errorText(e)}`);
  }

  // 2. Appium 版本
  const appiumVersion = await readAppiumVersion(r.probe);
  if (stopped()) return stoppedOutcome();

  // 3. 坐标比例
  const scale = await probeScale(r, nativeOk);
  if (stopped()) return stoppedOutcome();
  if (scale === null) {
    if (await sessionLost(r)) return lostOutcome();
    return { ok: false, termination: { errorType: "engine_error", message: SCALE_UNKNOWN_MESSAGE } };
  }

  // 4. 网页上下文
  let webContext: WebContextVerdict | null = null;
  let webContextCandidates: number | null = null;
  if (r.target.uiKind === "web") {
    const web = await probeWebContext(r, nativeOk);
    if (web.kind === "stopped") return stoppedOutcome();
    if (web.kind === "lost") return lostOutcome();
    webContext = web.verdict;
    webContextCandidates = web.candidates;
  }

  // 5. 输入路线
  const inputContext = r.target.device === "ios" ? (webContext === "available" ? "web" : "native") : null;
  return {
    ok: true,
    value: { webContext, webContextCandidates, inputContext, scale: scale.value, scaleSource: scale.source, appiumVersion },
  };
}

async function ensureNative(session: AppiumSession): Promise<void> {
  if (await session.currentContext() !== NATIVE_CONTEXT) await session.switchToNative();
}

/** 会话是否已结束：查到的状态不是 RUNNING（查询失败或没有查询函数不算）。 */
async function sessionLost(r: ProbeRun): Promise<boolean> {
  if (r.sessionStatus === undefined) return false;
  try {
    const status = await r.sessionStatus();
    return status !== null && status !== RUNNING;
  } catch {
    return false;
  }
}

async function readAppiumVersion(probe: Browser): Promise<string | null> {
  try {
    const status = await probe.status() as { build?: { version?: unknown } } | null;
    const version = status?.build?.version;
    return typeof version === "string" && version !== "" ? version : null;
  } catch {
    return null;
  }
}

// ---- 坐标比例 ----

async function probeScale(r: ProbeRun, nativeOk: boolean): Promise<{ value: number; source: ScaleSource } | null> {
  if (r.target.device === "android") return { value: 1, source: "fixed" };
  try {
    const scale = scaleFromScreenInfo(await r.deps.deviceScreenInfo(r.probe));
    if (scale !== null) return { value: scale, source: "device_screen_info" };
    log(r, "设备屏幕信息里没有坐标比例，改由截图与应用窗口的尺寸换算");
  } catch (e) {
    if (r.budget.signal.aborted) return null;
    log(r, `读取设备屏幕信息失败，改由截图与应用窗口的尺寸换算：${errorText(e)}`);
  }
  if (!nativeOk) return null;
  try {
    const source = await r.session.pageSource(r.budget.signal);
    const screenshot = await r.session.exec.takeScreenshot();
    const scale = scaleFromSizes(pngLongEdge(screenshot), applicationLongEdge(source));
    if (scale !== null) return { value: scale, source: "page_source" };
    log(r, "截图或应用窗口没有可用的尺寸，坐标比例无法换算");
  } catch (e) {
    if (!r.budget.signal.aborted) log(r, `换算坐标比例所需的截图或原生控件树读取失败：${errorText(e)}`);
  }
  return null;
}

function scaleFromScreenInfo(info: unknown): number | null {
  const scale = info !== null && typeof info === "object" ? (info as { scale?: unknown }).scale : undefined;
  return typeof scale === "number" && Number.isFinite(scale) && scale > 0 ? scale : null;
}

/** 截图长边除以窗口长边、取整；任一边缺失或结果小于 1 时为 null。 */
export function scaleFromSizes(screenshotLongEdge: number | null, windowLongEdge: number | null): number | null {
  if (screenshotLongEdge === null || windowLongEdge === null || windowLongEdge <= 0) return null;
  const scale = Math.round(screenshotLongEdge / windowLongEdge);
  return Number.isFinite(scale) && scale >= 1 ? scale : null;
}

const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

/** PNG 截图（base64）的长边像素：读文件头里 IHDR 块的宽与高；不是 PNG 时为 null。 */
export function pngLongEdge(base64: unknown): number | null {
  if (typeof base64 !== "string") return null;
  const head = Buffer.from(base64.slice(0, 44), "base64");
  if (head.length < 24 || !head.subarray(0, 8).equals(PNG_SIGNATURE) || head.toString("ascii", 12, 16) !== "IHDR") return null;
  const longEdge = Math.max(head.readUInt32BE(16), head.readUInt32BE(20));
  return longEdge > 0 ? longEdge : null;
}

const APPLICATION_TAG = /<XCUIElementTypeApplication\b[^>]*>/;

/** 原生控件树里第一个 XCUIElementTypeApplication 节点的宽与高中的较大者（单位为点）；找不到这个节点或尺寸时为 null。真机控件树的根
 *  是不带属性的 AppiumAUT，这个节点是它的第一个子节点，所以按标签名找节点，不取根节点。 */
export function applicationLongEdge(pageSource: unknown): number | null {
  if (typeof pageSource !== "string") return null;
  const tag = APPLICATION_TAG.exec(pageSource)?.[0];
  if (tag === undefined) return null;
  const size = (name: string): number | null => {
    const m = new RegExp(`\\s${name}="([0-9]+(?:\\.[0-9]+)?)"`).exec(tag);
    const value = m ? Number(m[1]) : NaN;
    return Number.isFinite(value) && value > 0 ? value : null;
  };
  const width = size("width");
  const height = size("height");
  return width === null || height === null ? null : Math.max(width, height);
}

// ---- 网页上下文 ----

type WebAttempt =
  | { kind: "stopped" }
  | { kind: "available" }
  | { kind: "none" }
  | { kind: "many"; candidates: number }
  /** 两次尝试都没有成功读到地址。confirmsUnavailable：两次都切入成功、只读命令都失败、最后一次不是传输层错误。 */
  | { kind: "failed"; candidates: number | null; confirmsUnavailable: boolean };

/** 一次尝试失败在哪一环，以及失败种类。 */
interface AttemptFailure {
  stage: "list" | "switch" | "read";
  kind: CommandFailureKind;
}

/** 网页上下文的尝试次数：首次加有界重试一次（ADR 0052 决策 5）。 */
const WEB_READ_ATTEMPTS = 2;

type WebResult =
  | { kind: "stopped" }
  | { kind: "lost" }
  | { kind: "verdict"; verdict: WebContextVerdict; candidates: number | null };

const TRANSPORT_FAILURES: readonly CommandFailureKind[] = ["connection", "gateway", "other"];

async function probeWebContext(r: ProbeRun, nativeOk: boolean): Promise<WebResult> {
  // 连原生上下文都回不去时，网页一侧的任何结果都区分不了设备能力
  if (!nativeOk) return { kind: "verdict", verdict: "probe_error", candidates: null };
  const attempt = await tryWebRead(r);
  switch (attempt.kind) {
    case "stopped":
      return attempt;
    case "none":
      return { kind: "verdict", verdict: "unavailable", candidates: 0 };
    case "many":
      log(r, `设备上有 ${attempt.candidates} 个网页页面，无法确定被测页面`);
      return { kind: "verdict", verdict: "probe_error", candidates: attempt.candidates };
    case "available": {
      // 读成功之后回不到原生上下文，同样是会话异常
      const back = await nativeCheck(r, false);
      if (back === "stopped" || back === "lost") return { kind: back };
      return verdict(back === "ok" ? "available" : "probe_error", 1);
    }
    case "failed": {
      const native = await nativeCheck(r, true);
      if (native === "stopped" || native === "lost") return { kind: native };
      if (native === "failed") return verdict("probe_error", attempt.candidates);
      return verdict(attempt.confirmsUnavailable ? "unavailable" : "probe_error", attempt.candidates);
    }
  }
}

function verdict(v: WebContextVerdict, candidates: number | null): WebResult {
  return { kind: "verdict", verdict: v, candidates };
}

/** 经探测实例定位、切入、读一次当前地址，有界重试一次；每次失败记下失败在哪一环。 */
async function tryWebRead(r: ProbeRun): Promise<WebAttempt> {
  const signal = r.budget.signal;
  let candidates: number | null = null;
  const failures: AttemptFailure[] = [];
  for (let attempt = 1; attempt <= WEB_READ_ATTEMPTS; attempt++) {
    if (signal.aborted) return { kind: "stopped" };
    let location;
    try {
      location = await locateWebContext(() => r.probe.getContexts(), r.target.device, { sleep: (ms) => r.sleep(ms, signal) });
    } catch (e) {
      if (signal.aborted) return { kind: "stopped" };
      failures.push({ stage: "list", kind: commandFailureKind(e) });
      log(r, `列出上下文失败（第 ${attempt} 次）：${errorText(e)}`);
      continue;
    }
    if (signal.aborted) return { kind: "stopped" };
    candidates = location.count;
    if (location.kind === "none") return { kind: "none" };
    if (location.kind === "many") return { kind: "many", candidates: location.count };
    try {
      await r.probe.switchContext(location.name);
    } catch (e) {
      if (signal.aborted) return { kind: "stopped" };
      failures.push({ stage: "switch", kind: commandFailureKind(e) });
      log(r, `切入网页上下文失败（第 ${attempt} 次）：${errorText(e)}`);
      continue;
    }
    if (signal.aborted) return { kind: "stopped" };
    try {
      await r.probe.getUrl();
      return { kind: "available" };
    } catch (e) {
      if (signal.aborted) return { kind: "stopped" };
      failures.push({ stage: "read", kind: commandFailureKind(e) });
      log(r, `网页上下文里的只读命令失败（第 ${attempt} 次）：${errorText(e)}`);
    }
  }
  const last = failures.at(-1);
  const confirmsUnavailable = last !== undefined && failures.every((f) => f.stage === "read")
    && !TRANSPORT_FAILURES.includes(last.kind);
  return { kind: "failed", candidates, confirmsUnavailable };
}

/** 经生命周期通道回到原生上下文；withScreenshot 时再在原生上下文截图一次，作「原生只读命令正常」的证据。失败先查会话状态。 */
async function nativeCheck(r: ProbeRun, withScreenshot: boolean): Promise<"ok" | "failed" | "lost" | "stopped"> {
  try {
    await ensureNative(r.session);
    if (withScreenshot) await r.session.exec.takeScreenshot();
    return "ok";
  } catch (e) {
    if (r.budget.signal.aborted) return "stopped";
    if (await sessionLost(r)) return "lost";
    log(r, `原生界面上的只读命令也失败：${errorText(e)}`);
    return "failed";
  }
}
