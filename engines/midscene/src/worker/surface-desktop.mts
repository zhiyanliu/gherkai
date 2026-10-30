// 桌面浏览器的界面接缝实现（ADR 0052 决策 2）：Bedrock AgentCore 云端浏览器会话、Playwright 的 CDP 建连与 PlaywrightAgent。
//
// 建连、会话跟踪、并行释放与会话预热是原先 run-scope 主流程里这几段代码的原样搬移（ADR 0028 的建连重试与网络专用退出码的
// 归因、ADR 0024 的释放优先、ADR 0051 决策 13 的会话预热），桌面路径的行为不变。在此之上只加了 ADR 0051 决策 4 的会话事件：
//   - 每次 StartBrowserSession 都带会话名，按 device/session-name.mts 的规则生成、长度上限取 AgentCore 的 100，尝试序号从 1 起、
//     每次建连尝试加一（与日志里的 attempt 编号一致）；取代原先的固定名，控制台据此能按名核对结果未知的尝试属于哪次运行的哪个 scope；
//   - Start 返回后、一切长耗时动作之前发 session_opened（origin 为 created，sessionId 与 name 都取 AgentCore 会话 id，不带 device）；
//   - 每个发过 session_opened 的会话在处置最终结束时发恰一条 session_closed：Stop 成功返回即 confirmed；最终语义的清理里 Stop 失败
//     或超时即 unconfirmed。建连重试丢弃的 attempt 在丢弃那次清理里 Stop 没成功时先不发：会话留在待清理集里，之后的清理再 Stop
//     一次、按那次的处置发；
//   - 停止信号到达时 StartBrowserSession 仍在途、等 INFLIGHT_SETTLE_MS 仍未返回：发一对 attempted 事件（sessionId 为 null，name 取
//     这次请求的会话名），release 报释放失败，退出码因此为 1。
// 四项边界义务在桌面上都是空操作，界面快照只在 AI step 上取 page.url()（ADR 0052 决策 2）。
//
// 本文件不 import 任何设备依赖：device/session-name.mts 只依赖 node:crypto，是桌面路径允许加载的两个设备模块之一（另一个是
// device/limits.mts，ADR 0052 决策 3），由 worker/no-device-deps.test.mts 守。
import { PlaywrightAgent } from "@midscene/web/playwright";
import { chromium, type Browser, type Page } from "playwright";
import {
  BedrockAgentCoreClient,
  StartBrowserSessionCommand,
  StopBrowserSessionCommand,
} from "@aws-sdk/client-bedrock-agentcore";
import type { Agent } from "@midscene/core";
import { signCdpUpgrade, getRegion } from "../lib/agentcore-sigv4.mjs";
import { EXTRA_HTTP_HEADERS_ENV, warmupSession } from "../lib/tunnel-warmup.mjs";
import { AGENTCORE_SESSION_NAME_MAX, encode as encodeSessionName, runIdFromEnv } from "../device/session-name.mjs";
import type { SelectedHandler } from "./deterministic.mjs";
import {
  attachClassification,
  type AcquireResult, type AddressReading, type HandlerCall, type ReleaseMode, type ReleaseOutcome, type ScopeTermination,
  type SnapshotResult, type StepFacts, type StepFailure, type SurfaceDeps, type TargetSurface,
} from "./surface.mjs";

const BROWSER_ID = "aws.browser.v1";
// 建连重试上限（ADR 0028）；退避 [0.5,1,2]s，总 ~3.5s，远小于本 worker 自报的 grace 下限（见 run-scope 的 minGraceSeconds）。
const CONNECT_ATTEMPTS = 4;
const CONNECT_BACKOFF_MS: readonly number[] = [500, 1000, 2000];
// SIGTERM cleanup 里单个 StopBrowserSession 的超时预算（ADR 0028）：退化网络下 Stop 可能挂很久
// （共享 client maxAttempts=3、无显式超时），超过 schedule grace 会被 SIGKILL 打断到一半 → 会话泄漏。
// 套这个预算：挂死时及时放弃，至少让 worker 干净退出、不被强杀。须 < grace——本段是自报下限
// minGraceSeconds（run-scope）的加数之一，故「够执行完」由那个下限保证、不靠人对数字。
export const STOP_SESSION_BUDGET_MS = 3000;
// StartBrowserSession 已发出 RPC 但 sessionId 未返回的在途窗口兜底（ADR 0028；ADR 0051 决策 5 桌面收尾的「等在途 Start」一段）：
// SIGTERM 落在这一瞬时服务端可能已建会话但客户端没拿到 id。给一小段时间让 Start 的 await 返回、id 落进待清理集，再 cleanup；
// 到点仍未返回即按结果未知的尝试发一对 attempted 事件（ADR 0051 决策 4）。本段同样是 minGraceSeconds 的加数之一。
export const INFLIGHT_SETTLE_MS = 1500;
// SIGTERM cleanup 末尾关本地 browser 的超时预算（会话已 Stop 之后才执行，见下 cleanupRun）：close 易挂起，
// 套预算别让它吃掉 grace 里留给后面几段的份额。本段同样是 minGraceSeconds 的加数之一。
export const BROWSER_CLOSE_BUDGET_MS = 3000;
// 内建导航的单次导航上限（ADR 0020 第 3 条）：等到 domcontentloaded。
const NAVIGATE_TIMEOUT_MS = 60_000;

// AWS SDK v3 服务端瞬时故障的错误 name 集（ADR 0028，节流+瞬时超时类）——与 Nova _BOTO_TRANSIENT_CODES
// 逐字对齐（18 项，保两个引擎对称）。AgentCore 起会话（StartBrowserSessionCommand）是 AWS SDK v3 调用，
// 服务端瞬时不可用/限流时抛的 error 带 name（如 ThrottlingException）+ $metadata.httpStatusCode + 可选 $retryable。
const AWS_TRANSIENT_NAMES = new Set([
  "RequestTimeout", "RequestTimeoutException", "PriorRequestNotComplete",  // 瞬时
  "ThrottlingException", "Throttling", "ThrottledException", "RequestThrottledException",  // 节流
  "TooManyRequestsException", "ProvisionedThroughputExceededException", "TransactionInProgressException",
  "RequestLimitExceeded", "BandwidthLimitExceeded", "LimitExceededException", "RequestThrottled",
  "SlowDown", "EC2ThrottledException", "ServiceUnavailable", "ServiceUnavailableException",
]);
const AWS_TRANSIENT_STATUS = new Set([500, 502, 503, 504]);

/** 是否网络/SSL 瞬时故障（可重试，ADR 0028）。Node 侧按 error code / TLS 错 / AWS SDK v3 服务端瞬时识别。
 *  遍历 error.cause 链：SDK 常把底层 socket/TLS 错、或 AWS 服务端错包成自有 Error，只看最外层会漏判（防环：限 8 层）。
 *
 *  两处调用：本文件的建连重试判定，与 run-scope 对执行异常的分类里「没有归类标记」那一支（桌面路径的全部异常，ADR 0052
 *  决策 6）。connecting=true（仅建连阶段传，ADR 0028）：额外认 Playwright TargetClosedError 的 message
 *  "...has been closed"——CDP 连接被网络断掉后的下游症状（Playwright 把底层 socket 故障吞掉、只留这句）。
 *  与 Nova 侧对称（Nova SDK 建连时主动 CDPSession.send 会撞出它；Midscene connectOverCDP 通常招 websocket
 *  TLS 错、已被下面正则命中，故此路径 Midscene 实际少见——防御性对称）。因语义模糊（网络断/会话正常关/浏览器真崩
 *  同报一句），**只建连阶段认**（此阶段 act 无副作用、重试安全）；act 中途（connecting=false）不认，守铁律。 */
export function isTransientNetwork(e: unknown, connecting = false, byMessage = true): boolean {
  let cur = e as {
    code?: string; name?: string; message?: string; cause?: unknown;
    $metadata?: { httpStatusCode?: number }; $retryable?: { throttling?: boolean };
  } | undefined;
  for (let depth = 0; cur && depth < 8; depth++) {
    const code = cur.code ?? "";
    if (code === "ENOTFOUND") return false; // DNS 未找到（永久），此层直接否决
    if (["ECONNRESET", "ECONNREFUSED", "ETIMEDOUT", "EPIPE", "EAI_AGAIN", "ECONNABORTED"].includes(code)) {
      return true; // EAI_AGAIN 即 DNS 临时失败，当瞬时
    }
    // AWS SDK v3 服务端瞬时（AgentCore 起会话节流/5xx，ADR 0028）：name 节流集 / 5xx 状态 / $retryable.throttling
    if (cur.name && AWS_TRANSIENT_NAMES.has(cur.name)) return true;
    if (cur.$metadata?.httpStatusCode != null && AWS_TRANSIENT_STATUS.has(cur.$metadata.httpStatusCode)) return true;
    if (cur.$retryable?.throttling === true) return true;
    const msg = cur.message ?? "";
    // byMessage=false 时跳过消息文本启发（确定性 handler 抛的错常把 step 原文——地址、选择器——嵌进消息，其中的
    // ssl / timeout 字样不是网络故障的证据；Nova 侧按异常类型分类，两侧由此对齐）
    if (byMessage && /\b(socket hang up|ssl|tls|econnreset|epipe|timeout|handshake|UNEXPECTED_EOF)\b/i.test(msg)) return true;
    // 建连阶段额外认 Playwright 连接被关（下游症状）——精确匹配 "has been closed"（TargetClosedError），
    // 不用宽 "closed"（正常关闭也含）。TS Playwright 无稳定异常类可 instanceof，故按 message。
    if (connecting && /has been closed/i.test(msg)) return true;
    cur = cur.cause as typeof cur;
  }
  return false;
}

// 建连重试耗尽时 acquire 抛出的那个异常（原样抛出、不包装，bin 的 fatal 行与改动前一字不差）。run-scope 据此判退出码：
// 会话已全部确认停止即网络专用退出码，有会话没能确认停止则改为重抛（释放优先，ADR 0028）。
const connectRetriesExhausted = new WeakSet<object>();

/** 这个异常是不是建连重试耗尽时 acquire 抛出的那个（ADR 0028）。设备实现不产生它，设备路径因此不会以网络专用退出码退出。 */
export function isConnectRetriesExhausted(e: unknown): boolean {
  return typeof e === "object" && e !== null && connectRetriesExhausted.has(e);
}

// cleanup 的重入守卫（ADR 0024 终止契约）——抽成纯函数供单测：信号 handler 与主流程 finally 会先后各调一次
// cleanup，守卫既要「不重复发 StopBrowserSession」，又不能让重入者提前返回到「会话其实还没释放」。故记的是
// **在途 promise**、不是一个布尔：
//   ① 无在途 → 起一次清理，记住它的 promise；
//   ② 有在途、本次是丢弃中间建连 attempt 的语义（discardAttempt）→ 直接等在途那次，不再发一遍 Stop；
//   ③ 有在途、本次是 final 语义 → 等在途结束，若 hasLeftovers()（仍有未确认释放的会话）则忘掉记忆、以
//      final 语义再清一次。缺这一步时，在途那次若是 discardAttempt 语义（其 Stop 失败只记日志、按约定不点亮
//      最终态的泄漏标记），最终态会话的泄漏就永远不被记账、退出码照旧是 0；会话已全部确认释放则直接返回。
//   ④ reset() 忘掉在途记忆（建连重试分支用：本次 attempt 的清理已结束，下一次要能再清）。
// 布尔守卫的两处失真即上面②③要挡的：重入者见「已清过」立刻返回，而在途那次还在 await Stop（调用方据此
// 以为会话已释放，接着做提前上传与退出）；且丢弃语义的一次清理会把后续 final 语义的清理整个吞掉。
export function makeGuardedCleanup(
  run: (discardAttempt: boolean) => Promise<void>,
  hasLeftovers: () => boolean,
): { cleanup: (discardAttempt?: boolean) => Promise<void>; reset: () => void } {
  let inFlight: Promise<void> | null = null;
  const start = (discardAttempt: boolean): Promise<void> => {
    const p = run(discardAttempt);
    inFlight = p;
    return p;
  };
  return {
    cleanup: async (discardAttempt = false): Promise<void> => {
      const pending = inFlight;
      if (pending === null) return await start(discardAttempt);
      if (discardAttempt) return await pending;  // 丢弃语义的重入：在途那次已覆盖本次诉求
      // final 语义的重入：在途那次的异常归它自己的调用方处置，这里只关心「会话到底释放没有」，故吞掉它再看
      // leftovers——否则在途那次一抛，本次连补清一刀的机会都没有。
      await pending.catch(() => {});
      if (!hasLeftovers()) return;
      inFlight = null;
      await start(false);
    },
    reset: () => { inFlight = null; },
  };
}

/** PlaywrightAgent 的构造项类型。 */
export type DesktopAgentOpts = NonNullable<ConstructorParameters<typeof PlaywrightAgent>[1]>;

/** createDesktopSurface 仅供测试注入的部分（SurfaceFactory 允许的可选参数）：缺省即生产实现。回归测试据此注入假的 AgentCore
 *  控制面与假的 CDP 建连，锁住建连重试、退出码与收尾次序，而不连 AWS。 */
export interface DesktopSurfaceHooks {
  /** AgentCore 控制面客户端，只用 send 发 Start 与 Stop；缺省按 AWS_REGION 新建。 */
  client?: Pick<BedrockAgentCoreClient, "send">;
  /** CDP 升级请求的签名；缺省用默认凭证链按 SigV4 签。 */
  signCdpUpgrade?: (wsUrl: string) => Promise<Record<string, string>>;
  /** CDP 建连；缺省 chromium.connectOverCDP。 */
  connectOverCDP?: (wsUrl: string, opts: { headers: Record<string, string> }) => Promise<Browser>;
  /** Agent 构造；缺省 new PlaywrightAgent。opts 是交给 PlaywrightAgent 的完整构造项。 */
  createAgent?: (page: Page, opts: DesktopAgentOpts) => Agent;
  /** 本次运行的编号；缺省读 env RUN_ID，缺失即构造期报错。 */
  runId?: string;
  /** 建连重试的退避序列与在途 Start 的等待窗口；缺省为本文件的常量。 */
  backoffMs?: readonly number[];
  settleMs?: number;
}

/** 桌面实现的构造函数（导出名由 worker/surface.mts 的 SurfaceFactory 约定）。只组装、不做 I/O；本次运行的编号缺失（env RUN_ID）
 *  或 AWS_REGION 未设时同步报错——前者是起 worker 一方的装配错误，在建会话之前报出、不发任何事件、以 1 退出（与 Nova Act worker
 *  对称）。PlaywrightAgent 的构造项是 deps.agentOpts（两种 Agent 共用的项）加 forceChromeSelectRendering。 */
export function createDesktopSurface(deps: SurfaceDeps, hooks: DesktopSurfaceHooks = {}): TargetSurface {
  const { emit, log } = deps;
  const agentOpts = {
    ...deps.agentOpts,
    // SDK 默认开的「强制 Chrome 用 base-select 渲染原生下拉」（往页面注入一个 style 标签，让 select 在截图里
    // 可见）——**我们显式关掉**：本 worker 连的是 AgentCore 云端浏览器（CDP 远连），注入用的 page.evaluate 常
    // 撞上 "Execution context was destroyed"，SDK 每个 run 因此往 stderr 打一整段报错栈，纯噪声；而功能面这边
    // 用不到它（AI 看的是截图里的元素、不依赖原生 select 的外观兼容）。只对桌面：设备 Agent 没有 Playwright 页面可注入。
    forceChromeSelectRendering: false,
  };
  const scopeId = deps.job.scope.id;
  const runId = hooks.runId ?? runIdFromEnv();
  const client = hooks.client ?? new BedrockAgentCoreClient({ region: getRegion() });
  const sign = hooks.signCdpUpgrade ?? signCdpUpgrade;
  const connectOverCDP = hooks.connectOverCDP ?? ((wsUrl, opts) => chromium.connectOverCDP(wsUrl, opts));
  const createAgent = hooks.createAgent ?? ((page, opts) => new PlaywrightAgent(page, opts));
  const backoffMs = hooks.backoffMs ?? CONNECT_BACKOFF_MS;
  const settleMs = hooks.settleMs ?? INFLIGHT_SETTLE_MS;

  // 待清理会话集（ADR 0028 会话跟踪重构）：每次 StartBrowserSession 成功即把 id 加进来——含被重试丢弃的
  // 中间 attempt 会话。SIGTERM handler / cleanup 遍历它逐个 Stop，**不再靠单一 sessionId 快照**（旧实现：
  // 重试时 sessionId 被后一个 attempt 覆盖/置空，handler 只能 Stop 到当前快照 → 在途/已弃的 attempt 会话泄漏）。
  const pendingSessions = new Set<string>();
  // 会话事件的配对（ADR 0051 决策 4）：发过 session_opened 的会话，与已发过 session_closed 的会话（每个会话恰一条，
  // 不先发 unconfirmed 再补 confirmed）。
  const opened = new Set<string>();
  const closed = new Set<string>();
  let sessionId: string | undefined; // 最终成功会话 id（血缘，进 scope_started / scope_done；非清理依据——清理看 pendingSessions）
  // StartBrowserSession RPC 已发出、await 未返回的那次请求（SIGTERM 在途等待的精确信号，ADR 0028）；reported 表示已按结果未知的
  // 尝试发过 attempted 事件。
  let startInFlight: { name: string; reported: boolean } | null = null;
  let attemptedReported = false;  // 发过 attempted 事件 → 释放失败、退出码 1（ADR 0051 决策 5）
  let browser: Browser | undefined;
  let page: Page | undefined;
  let cleanupFailed = false; // StopBrowserSession 失败 → worker 非 0 退出，让泄漏可观测（对照 Nova）
  let terminated = false;    // 已进入终结（停止信号）：建连重试循环不再重试
  let onTerminate: (() => void) | undefined;  // 重试退避用：进入终结即 resolve、打断退避（对称 Nova 的 sleep 被信号打断）

  /** 发一条会话事件：发出失败不抛（释放绝不抛），记为释放失败让退出码为 1——事件没送到，core 看到的就是没有确认停止的会话。 */
  async function emitSessionEvent(ev: Record<string, unknown>): Promise<void> {
    try {
      await emit(ev);
    } catch (e) {
      cleanupFailed = true;
      log(`worker: 会话事件 ${String(ev.type)} 未能发出（退出码将为 1）：${(e as Error).message}`);
    }
  }

  /** 一个会话的处置最终结束：发恰一条 session_closed（只给发过 session_opened 的会话）。 */
  async function closeSession(sid: string, release: "confirmed" | "unconfirmed"): Promise<void> {
    if (!opened.has(sid) || closed.has(sid)) return;
    closed.add(sid);
    await emitSessionEvent({ type: "session_closed", scopeId, sessionId: sid, name: sid, release });
  }

  async function stopSession(sid: string): Promise<boolean> {
    // 单个会话 Stop，套超时预算（ADR 0028）：退化网络下 Stop 可能挂死、超 grace 被 SIGKILL 打断 → 泄漏。
    // 超时即放弃（返回 false 表示未确认释放），让 worker 能干净退出。timedOut 哨兵区分「超时」与「Stop 成功」。
    const timedOut = Symbol("timeout");
    try {
      const r = await Promise.race([
        client.send(new StopBrowserSessionCommand({ browserIdentifier: BROWSER_ID, sessionId: sid })).then(() => true),
        new Promise<typeof timedOut>((res) => setTimeout(() => res(timedOut), STOP_SESSION_BUDGET_MS)),
      ]);
      if (r === timedOut) {
        log(`worker: StopBrowserSession TIMEOUT >${STOP_SESSION_BUDGET_MS}ms (会话可能泄漏，需排查): session=${sid}`);
        return false;
      }
      return true;
    } catch (e) {
      log(`worker: StopBrowserSession FAILED (会话可能泄漏，需排查): ${(e as Error).message}`);
      return false;
    }
  }

  // 会话清理（ADR 0024 终止契约，对照 Nova 在 _run_session 的 finally 里的释放）：
  //   顺序——**先发 StopBrowserSession 释放会话（最重要、优先）**，再关 browser；
  //   理由——不让易挂起的 browser.close 挟持会话释放。close 套超时预算，避免耗尽 grace。
  //   重入：在途 promise 记忆（makeGuardedCleanup）——信号 handler 与 finally 先后双调时，后来者等在途那次
  //   执行完，既不重复发 Stop、也不提前返回到「会话其实还没释放」；见该函数头。
  //   **并行** Stop pendingSessions（每个套超时预算）；任一未确认释放 → cleanupFailed（除非 discardAttempt）。
  //   并行（Promise.all）而非串行：N 个会话累积时墙钟 ≈ 单个预算（3s）而非 N×3s——串行会让重试积累的
  //   多个泄漏会话把 cleanup 拖过 grace 被 SIGKILL 截断（正是 ADR 0028「重试放大的 in-flight 会话窗口」条
  //   要防的泄漏）。
  //   discardAttempt=true（丢弃中间建连 attempt 的部分会话，ADR 0028）：Stop 失败只 log、**不点亮
  //   final cleanupFailed**——那个会话本就要丢、与「最终态会话是否泄漏」无关；否则一次中间失败会毒化
  //   后续成功 attempt 的退出码（误报泄漏 → core 当 engine_error）。final cleanup（默认）才管 cleanupFailed。
  //   会话事件（ADR 0051 决策 4）：Stop 成功即发 confirmed；final 语义下 Stop 失败即发 unconfirmed；丢弃语义下 Stop 失败不发，
  //   会话留在集里等之后的清理，按最终处置发。session_closed 都在关 browser 之前发出（释放 → session_closed，ADR 0051 决策 5）。
  async function cleanupRun(discardAttempt: boolean): Promise<void> {
    await Promise.all([...pendingSessions].map(async (sid) => {
      const ok = await stopSession(sid);
      if (ok) {
        pendingSessions.delete(sid);
        await closeSession(sid, "confirmed");
      } else if (!discardAttempt) {
        cleanupFailed = true;
        await closeSession(sid, "unconfirmed");
      }
    }));
    // 会话已释放，再尽力关本地 browser；套超时，挂住也不拖垮（会话已停，close 失败无计费影响）
    if (browser) {
      await Promise.race([
        browser.close().catch(() => {}),
        new Promise<void>((r) => setTimeout(r, BROWSER_CLOSE_BUDGET_MS)),
      ]);
    }
  }
  // 重入守卫（语义见 makeGuardedCleanup）：leftovers 指 pendingSessions 里还有没确认释放的会话，
  // 有则 final 语义的重入者补清一次，让 Stop 失败点亮 cleanupFailed、泄漏可观测。
  const cleanupGuard = makeGuardedCleanup(cleanupRun, () => pendingSessions.size > 0);
  const cleanup = cleanupGuard.cleanup;

  /** 停止信号到达时 Start 仍在途、等待窗口内没有返回：服务端可能已建会话，id 却不在手里（ADR 0051 决策 4 与设备的待核尝试同义；
   *  ADR 0028 血缘窗口条）。发一对 attempted 事件，core 据此判 release_failed、给出会话名；会话若已建立，由 AgentCore 会话超时回收。 */
  async function reportUnresolvedStart(request: { name: string; reported: boolean }): Promise<void> {
    if (request.reported) return;
    request.reported = true;
    attemptedReported = true;
    log(`worker: 收到停止信号时浏览器会话的创建请求仍未返回，无法确认会话是否已建立（会话名 ${request.name}），可能仍在计费；`
      + "请在 Amazon Bedrock AgentCore 控制台按会话名核对，退出码将为 1");
    await emitSessionEvent({ type: "session_opened", scopeId, sessionId: null, name: request.name, origin: "attempted" });
    await emitSessionEvent({ type: "session_closed", scopeId, sessionId: null, name: request.name, release: "unconfirmed" });
  }

  // 建连段（ADR 0028）：StartBrowserSession → CDP 握手 → connectOverCDP → PlaywrightAgent。
  // 整段可被重试；scope_started 一 emit（会话已起、act 即将执行）即跳出重试域，绝不重试 act。
  // 每次 attempt 前若上次部分建起了会话/browser，先 cleanup 释放（防泄漏 + 不重复占用）。
  async function connect(attemptNo: number): Promise<{ page: Page; agent: Agent }> {
    const name = encodeSessionName(runId, scopeId, attemptNo, { maxLength: AGENTCORE_SESSION_NAME_MAX });
    const request = { name, reported: false };
    startInFlight = request;  // Start RPC 在途（SIGTERM 兜底信号）；返回/抛错后清
    let started;
    try {
      started = await client.send(new StartBrowserSessionCommand({ browserIdentifier: BROWSER_ID, name }));
    } finally {
      if (startInFlight === request) startInFlight = null;
    }
    const sid = started.sessionId!;
    sessionId = sid;
    pendingSessions.add(sid);  // 立即入待清理集 → SIGTERM handler 能 Stop 本次（含被重试丢弃的）会话
    // 血缘先行（ADR 0051 决策 4；ADR 0028 血缘窗口条）：会话自 Start 返回起即在计费，建连与预热被打断时 core 也记得到它。
    // 先登记再发：发出期间到达的停止信号也会为它发配对的 session_closed（事件序号在调用 emit 时即已分配）。
    opened.add(sid);
    await emit({ type: "session_opened", scopeId, sessionId: sid, name: sid, origin: "created" });
    const wsUrl = started.streams?.automationStream?.streamEndpoint!;
    const headers = await sign(wsUrl);
    browser = await connectOverCDP(wsUrl, { headers });
    const ctx = browser.contexts()[0] ?? (await browser.newContext());
    // 额外请求头（ADR 0035，如 ngrok-skip-browser-warning）：组合根经 env 注入，context 级对所有请求生效。
    // 纯 CDP Network.setExtraHTTPHeaders，无回调、不涉 route——与 AI 驱动零交互。无 env → 零行为变化。
    const extraHeaders = process.env[EXTRA_HTTP_HEADERS_ENV];
    if (extraHeaders) await ctx.setExtraHTTPHeaders(JSON.parse(extraHeaders));
    const connectedPage = ctx.pages()[0] ?? (await ctx.newPage());
    // 页面里补一个 `__name` 空实现（ADR 0037 决策 4 的 tsx loader 副作用）：worker 用 tsx 转译使用方的 `.mts` step 文件，
    // esbuild 的 keepNames 会把函数包成 `__name(fn, "fn")`；这样的函数一旦经 page.evaluate / waitForFunction 序列化进页面，
    // 页面里没有 `__name` 就抛 ReferenceError。使用方本地单测（node 直接执行、无 tsx）撞不到、云端一执行就全红，故由 worker
    // 在每个文档里预置一个恒等实现：context 级 addInitScript 管此后的每次导航，evaluate 管当前已打开的文档。两处都传字符串——
    // 本文件同样经 tsx 转译，传函数会把同一个问题带进去。
    const NAME_SHIM = "globalThis.__name = globalThis.__name || ((fn) => fn);";
    await ctx.addInitScript(NAME_SHIM);
    await connectedPage.evaluate(NAME_SHIM).catch(() => {});
    const agent = createAgent(connectedPage, agentOpts);
    return { page: connectedPage, agent };
  }

  function currentPage(): Page {
    if (page === undefined) throw new Error("浏览器会话还没有建立，无法执行这一步");
    return page;
  }

  const surface: TargetSurface = {
    async acquire(): Promise<AcquireResult> {
      let conn: { page: Page; agent: Agent } | undefined;
      for (let attempt = 0; attempt < CONNECT_ATTEMPTS; attempt++) {
        try {
          conn = await connect(attempt + 1);
          break; // 建连成功
        } catch (e) {
          // 丢弃本次 attempt 部分建起的会话/browser（如 connectOverCDP 失败但 StartBrowserSession 成功）。
          // discardAttempt=true：Stop 失败不污染 final cleanupFailed（这个会话本就要丢，ADR 0028）。
          // cleanup 遍历 pendingSessions 逐个 Stop，成功的从集里删；未删的（Stop 失败/超时）留到后续 cleanup 再试。
          cleanupGuard.reset(); // 忘掉上一次 attempt 的清理记忆，允许对本次 attempt 的部分会话再清一次
          await cleanup(true);
          browser = undefined;
          const sid = sessionId; sessionId = undefined; // 清血缘：失败 attempt 的 id 不该进 scope_done
          cleanupGuard.reset(); // 重置守卫：让后续 attempt 成功后的 final cleanup 从「无在途」起（本次这趟丢弃语义的清理已结束，不必再等它）
          if (terminated) throw e;  // 已收 SIGTERM → 不重试
          // connecting=true：本分支即建连域，额外认 Playwright "has been closed"（连接被网络断的下游症状，ADR 0028，对称 Nova）
          if (!isTransientNetwork(e, true) || attempt >= CONNECT_ATTEMPTS - 1) {
            if (isTransientNetwork(e, true)) {
              if (typeof e === "object" && e !== null) connectRetriesExhausted.add(e);
              log(`worker: 建连重试耗尽（${attempt + 1} 次）：${(e as Error).message}`);
            }
            throw e; // 非瞬时 / 重试耗尽 → 冒泡
          }
          log(`worker: 建连失败（attempt ${attempt + 1}, session=${sid ?? "—"}），重试：${(e as Error).message}`);
          // 退避：与 SIGTERM 竞速——进入终结即提前结束退避，使循环顶部 terminated 检查尽快生效（对称 Nova）
          await new Promise<void>((resolve) => {
            const t = setTimeout(resolve, backoffMs[Math.min(attempt, backoffMs.length - 1)]);
            onTerminate = () => { clearTimeout(t); resolve(); };
          });
          if (terminated) throw e;  // 退避被 SIGTERM 打断 → 不再重连
        }
      }
      page = conn!.page;
      return { ready: true, agent: conn!.agent, sessionId: sessionId! };
    },

    async warmup(url: string): Promise<ScopeTermination | null> {
      // 隧道会话预热（ADR 0051 决策 13）：lib/tunnel-warmup.mts 的 warmupSession 原样调用，归因与离开预热页都在它内部。
      return await warmupSession(currentPage(), url, { log });
    },

    sessionId: () => sessionId ?? null,

    // 桌面的三项核对都是空操作（ADR 0052 决策 2）：浏览器只有一个上下文，没有要切回的界面。
    preScenarioCheck: async () => null,
    preStep: async (): Promise<StepFailure | null> => null,
    restore: async (): Promise<StepFailure | null> => null,

    bindHandler(selected: SelectedHandler): HandlerCall {
      if (selected.kind !== "playwright") {
        // selectHandler 在桌面目标上只会给 playwright 句柄；走到这里是派发出了错，按执行出错记、不调 handler
        throw attachClassification(new Error("这条确定性 step 的句柄不适用于桌面浏览器"),
          { errorType: "engine_error", message: "这条确定性 step 的句柄不适用于桌面浏览器" });
      }
      const fn = selected.fn;
      return async (groups) => {
        await fn({ page: currentPage(), navigate: (url) => surface.navigate(url) }, groups);
      };
    },

    // 桌面没有执行令牌（ADR 0052 决策 6 的命令守卫只在设备上）：直接执行，原样返回或抛出。
    execute: (run) => run(undefined),

    async navigate(address: string): Promise<void> {
      await currentPage().goto(address, { waitUntil: "domcontentloaded", timeout: NAVIGATE_TIMEOUT_MS });
    },

    async readAddress(step: StepFacts): Promise<AddressReading | null> {
      // 桌面只在 AI step 末取一次 page.url()（同 step 各票之间页面通常不变），其余 step 不产 evidence、不读
      if (step.kind !== "ai") return null;
      try {
        return { url: page?.url() ?? null, url_missing: null };
      } catch {
        return { url: null, url_missing: null };  // 页面已关/CDP 断连：URL 缺了不影响其余证据
      }
    },

    async snapshot(_step: StepFacts, address: AddressReading | null): Promise<SnapshotResult> {
      // 桌面快照只有地址两键（不带 step_kind），evidence 因此不加任何设备键、与引入快照之前逐字节一致
      return { snapshot: { url: address?.url ?? null, url_missing: null }, failure: null };
    },

    async release(mode: ReleaseMode): Promise<ReleaseOutcome> {
      if (mode === "interrupt") {
        terminated = true;
        onTerminate?.();  // 立即唤醒正在退避的重试循环，使其尽快停（不再 reconnect/执行 act）
        // 在途窗口兜底（ADR 0028）：Start 在途则先等一小段，让 id 落进待清理集再 cleanup；仍未返回即发 attempted 事件。
        // 不要再加「待清理集为空」的条件：上一 attempt Stop 失败的遗留会话会让集非空，那恰恰是重试场景下最需要兜底的时刻；
        // 这段已计入 minGraceSeconds 的加数，等它不超 grace。
        const pendingStart = startInFlight;
        if (pendingStart !== null) {
          await new Promise<void>((r) => setTimeout(r, settleMs));
          if (startInFlight === pendingStart) await reportUnresolvedStart(pendingStart);
        }
      }
      await cleanup();
      return { releaseFailed: cleanupFailed || attemptedReported, reportRefs: [] };
    },
  };
  return surface;
}
