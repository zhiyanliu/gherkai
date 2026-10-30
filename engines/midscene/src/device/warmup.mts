// 设备上的会话预热（ADR 0051 决策 13；ADR 0052 决策 3 的「会话预热」块、决策 6）：实现 device/surface.mts 的 DeviceWarmup 端口。
//
// 在能力探测之后、scope_started 之前对网页目标执行一次：按传入的路线导航 worker 收到的预热地址，在原生控件树里查找页面标记。
// 路线由设备侧接缝按探测结论选定（网页上下文「提供」走 url，否则走 deepLink），本模块不按平台、系统版本或导航结果换路线，
// 重试也沿用同一条路线（ADR 0051 被拒方案「按系统版本选择导航路线」；ADR 0052 决策 5）。应用目标不预热，由接缝跳过。
//
// 归因与桌面预热是同一条判据，标记与消息取自 lib/tunnel-warmup.mts（与 engines/fixtures/tunnel-warmup.json 对拍）：
//   - READY：就绪；
//   - DENIED、AUTH REQUIRED：确定性拒绝，precheck_failed，不重试；
//   - ERROR、标记等待期内没有任何标记、导航本身失败（含执行实例的客户端超时）、切回原生上下文或读取控件树失败：原地重导航，
//     共 DEVICE_WARMUP_ATTEMPTS 次，耗尽归 engine_error。
// 永不归 network_error（ADR 0028 的分类红线；设备路径没有 network_error 出口）。命令失败时先查一次会话状态，不是 RUNNING 即
// session_lost（ADR 0051 决策 4「会话丢失的判定靠查状态」）；预热在 scope_started 之前，消息用执行前的那句（surface.mts 的
// SESSION_LOST_BEFORE_START_MESSAGE）。
//
// 预算（ADR 0052 决策 6）：导航以执行实例的单请求超时（limits 的 EXEC_REQUEST_TIMEOUT_MS，由 Appium 块设在执行实例上）为上界，
// 本模块不另设导航超时、不做放弃式等待，也不套用桌面预热的 30 秒导航超时——单条命令的上界只能由客户端实例的请求超时给出
// （被拒方案「探测用 Promise.race」同理）。标记等待期与尝试次数与桌面预热共用同一常量。整个预热计入获取预算：预算的中止信号
// 穿进控件树的读取；导航不接受中止信号，只能等它返回。预算到期或进入终结后不再向设备发命令（device/surface.mts 的「进入终结
// 即停」）：不发起新的尝试，导航返回后不再切回原生上下文，url 路线读到 READY 后也不离开预热页、离开的导航返回时已中止则不再切回
// 原生上下文；此时返回的 engine_error 由接缝按预算改写为 acquire_timeout。
//
// 通道（ADR 0052 决策 2、6）：预热发生在 scope_started 之前、尚无执行令牌，经生命周期通道执行，导航命令由执行实例 session.exec
// 发出，不经命令守卫。
//
// 读标记之前切回原生上下文：网页上下文里的 page source 是 HTML，预热页面的脚本正文里写着全部四个标记，在那里查找会误判；原生控件树
// 只暴露渲染出来的正文。标记等待期内读到 ERROR 不提前结束本次尝试：deepLink 立即返回、iOS 上 url 也可能在页面加载完之前返回，这时
// 界面上可能还是上一次尝试留下的 ERROR 页，等待期内变成 READY 即就绪；等待期结束时最后一次读到的仍是 ERROR，才按 ERROR 重导航。
// 控件树相邻两次读取之间不另加间隔：每次读取本身是一次设备往返。
//
// 就绪后离开（ADR 0051 决策 13）：url 路线导航到 about:blank、再切回原生上下文，离开失败只记日志、不影响判定；deepLink 路线不离开，
// 令牌留在设备浏览器的当前地址，是该决策记下的残留面。
//
// 脱敏（ADR 0051 决策 11）：预热地址带令牌。本模块不把地址写进任何日志与消息；导航与读取的错误文本经 worker/error-text.mts 的一行化
// （先脱敏再截断）进入日志与消息。
import { errorText, oneLineError } from "../worker/error-text.mjs";
import { readClassification, type ScopeTermination } from "../worker/surface.mjs";
import {
  WARMUP_AUTH_REQUIRED_MESSAGE, WARMUP_DENIED_MESSAGE, WARMUP_MARKER_WAIT_MS, WARMUP_MARKERS, warmupErrorMessage,
} from "../lib/tunnel-warmup.mjs";
import { SESSION_LOST_BEFORE_START_MESSAGE } from "./surface.mjs";
import { DEVICE_WARMUP_ATTEMPTS } from "./limits.mjs";
import type { AppiumSession, DeviceWarmup } from "./surface.mjs";

export type WarmupMarker = keyof typeof WARMUP_MARKERS;

const RUNNING = "RUNNING";
const LEAVE_ADDRESS = "about:blank";
// 获取预算中止时的原因；接缝随后按预算改写归因。
const BUDGET_SPENT_REASON = "获取设备的等待时间已用完";
// 同一棵原生控件树里只会渲染出一个标记，查找次序只为结果确定。四个标记只含大写字母与空格，不受 XML 实体转义影响；按大小写精确
// 匹配，地址栏里的预热路径与页面标题（小写连字符形态）都不会命中。
const MARKER_ORDER: readonly WarmupMarker[] = ["ready", "auth_required", "denied", "error"];

/** 在原生控件树（page source 的 XML 文本）里查找预热页面的正文标记；没有任何标记时返回 null。 */
export function findWarmupMarker(pageSource: string): WarmupMarker | null {
  for (const marker of MARKER_ORDER) if (pageSource.includes(WARMUP_MARKERS[marker])) return marker;
  return null;
}

/** run 的参数：端口的六项，其中会话状态查询在本块可缺。sessionStatus 查一次当前远程访问会话的状态（Device Farm 会话块的 status
 *  绑定到当前会话 ARN；查询失败返回 null 或抛出，此时不据此判会话丢失）。不传时命令失败只认异常上的 session_lost 归类标记；设备侧
 *  接缝总是传入。 */
export type DeviceWarmupArgs = Omit<Parameters<DeviceWarmup["run"]>[0], "sessionStatus"> & {
  sessionStatus?: () => Promise<string | null>;
};

/** 会话预热块：满足 DeviceWarmup 端口（sessionStatus 可缺）。 */
export interface DeviceWarmupBlock {
  run(args: DeviceWarmupArgs): Promise<ScopeTermination | null>;
}

// 编译期核对：本块可以直接装进 DeviceParts.warmup。
type _BlockIsPort = DeviceWarmupBlock extends DeviceWarmup ? true : never;
const _blockIsPort: _BlockIsPort = true;
void _blockIsPort;

export interface DeviceWarmupDeps {
  /** worker 日志（部件工厂环境里的 log）。 */
  log: (line: string) => void;
  /** 与接缝同一时钟（毫秒），只供测试注入。 */
  now?: () => number;
}

/** 构造会话预热块。只组装、不做 I/O。 */
export function createDeviceWarmup(deps: DeviceWarmupDeps): DeviceWarmupBlock {
  const now = deps.now ?? Date.now;
  return { run: (args) => warmup(args, deps.log, now) };
}

type AttemptResult =
  | { kind: "ready" }
  | { kind: "rejected"; termination: ScopeTermination }
  | { kind: "lost" }
  | { kind: "retry"; reason: string };

async function warmup(args: DeviceWarmupArgs, log: (line: string) => void, now: () => number): Promise<ScopeTermination | null> {
  let attempts = 0;
  let last = BUDGET_SPENT_REASON;
  while (attempts < DEVICE_WARMUP_ATTEMPTS && !args.budget.signal.aborted) {
    attempts += 1;
    const result = await attempt(args, attempts, log, now);
    if (result.kind === "lost") return { errorType: "session_lost", message: SESSION_LOST_BEFORE_START_MESSAGE };
    if (result.kind === "rejected") return result.termination;
    if (result.kind === "ready") {
      log(`worker: 会话预热已确认就绪（${args.route === "url" ? "在网页上下文中打开" : "交给系统浏览器打开"}，第 ${attempts} 次尝试）`);
      if (args.route === "url" && !args.budget.signal.aborted) await leaveWarmupPage(args.session, args.budget.signal, log);
      return null;
    }
    last = result.reason;
    log(`worker: 会话预热第 ${attempts} 次尝试未能确认就绪：${result.reason}`);
  }
  return { errorType: "engine_error", message: warmupErrorMessage(attempts, last) };
}

/** 一次尝试：导航、切回原生上下文、在标记等待期内读控件树。 */
async function attempt(args: DeviceWarmupArgs, n: number, log: (line: string) => void, now: () => number): Promise<AttemptResult> {
  const { session } = args;
  try {
    if (args.route === "url") await session.openUrl(session.exec, args.url);
    else await args.adapter.deepLink(session.exec, args.url, null);
  } catch (e) {
    log(`worker: 会话预热第 ${n} 次导航失败：${errorText(e)}`);
    return (await sessionEnded(e, args)) ? { kind: "lost" } : { kind: "retry", reason: `预热导航失败：${reasonOf(e)}` };
  }
  // 导航未返回期间预算可能已到期或已进入终结，此后不再向设备发命令。
  if (args.budget.signal.aborted) return { kind: "retry", reason: BUDGET_SPENT_REASON };
  try {
    await session.switchToNative();
  } catch (e) {
    log(`worker: 会话预热第 ${n} 次导航后未能切回原生上下文：${errorText(e)}`);
    return (await sessionEnded(e, args)) ? { kind: "lost" } : { kind: "retry", reason: `预热导航后未能切回原生界面：${reasonOf(e)}` };
  }
  return waitForMarker(args, n, log, now);
}

async function waitForMarker(args: DeviceWarmupArgs, n: number, log: (line: string) => void, now: () => number): Promise<AttemptResult> {
  const deadline = now() + WARMUP_MARKER_WAIT_MS;
  let latest: WarmupMarker | null = null;
  for (;;) {
    const left = deadline - now();
    if (left <= 0 || args.budget.signal.aborted) break;
    const signal = AbortSignal.any([args.budget.signal, AbortSignal.timeout(left)]);
    let source: string;
    try {
      source = await args.session.pageSource(signal);
    } catch (e) {
      if (signal.aborted) break;  // 等待期到点或获取预算中止：按等待期结束处理
      log(`worker: 会话预热第 ${n} 次尝试读取原生控件树失败：${errorText(e)}`);
      return (await sessionEnded(e, args)) ? { kind: "lost" } : { kind: "retry", reason: `读取设备界面失败：${reasonOf(e)}` };
    }
    latest = findWarmupMarker(source);
    if (latest === "ready") return { kind: "ready" };
    if (latest === "auth_required") return { kind: "rejected", termination: { errorType: "precheck_failed", message: WARMUP_AUTH_REQUIRED_MESSAGE } };
    if (latest === "denied") return { kind: "rejected", termination: { errorType: "precheck_failed", message: WARMUP_DENIED_MESSAGE } };
  }
  return {
    kind: "retry",
    reason: latest === "error" ? `预热页面标记为 ${WARMUP_MARKERS.error}`
      : `预热页面在 ${WARMUP_MARKER_WAIT_MS / 1000} 秒内没有给出任何标记`,
  };
}

/** url 路线就绪后离开预热页：令牌不留在网页上下文的当前地址；之后切回原生上下文，离开的导航返回时获取预算已中止则不再切。失败只记
 *  日志（ADR 0051 决策 13）。 */
async function leaveWarmupPage(session: AppiumSession, signal: AbortSignal, log: (line: string) => void): Promise<void> {
  try {
    await session.openUrl(session.exec, LEAVE_ADDRESS);
    if (signal.aborted) return;
    await session.switchToNative();
  } catch (e) {
    log(`worker: 未能离开预热页，预热地址可能留在设备浏览器的当前地址（不影响判定）：${errorText(e)}`);
  }
}

/** 命令失败后的会话丢失判定：异常已带 session_lost 归类即是；否则查一次会话状态，查得到且不是 RUNNING 即是。 */
async function sessionEnded(e: unknown, args: DeviceWarmupArgs): Promise<boolean> {
  if (readClassification(e)?.errorType === "session_lost") return true;
  if (args.sessionStatus === undefined) return false;
  let status: string | null;
  try {
    status = await args.sessionStatus();
  } catch {
    status = null;
  }
  return status !== null && status !== RUNNING;
}

/** 失败原因的一句：异常带归类标记时用标记的消息（已是产品语言），否则取错误信息；两者都取一行（先脱敏再截断）。 */
function reasonOf(e: unknown): string {
  const mark = readClassification(e);
  if (mark !== null) return oneLineError(mark.message);
  const text = oneLineError(e instanceof Error ? e.message : e);
  return text === "" ? errorText(e) : text;
}
