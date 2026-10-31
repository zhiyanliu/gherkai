// Appium 建连与上下文切换（ADR 0052 决策 3 的「Appium 建连与上下文切换」块、决策 5、决策 6；ADR 0051 决策 3、9、11）：实现
// device/surface.mts 的 AppiumConnector 与 AppiumSession 端口。
//
// 三个 WebdriverIO 实例，超时与重试各自显式设定，不依赖 SDK 缺省（ADR 0052 决策 6 超时分层表 ⑤ ⑥ ⑪）：
//   - 建连实例：只为 newSession 而建。单请求超时取 NEW_SESSION_TIMEOUT_FLOOR_MS 与剩余获取预算的较小者（封顶优先），传输层 0 次重试；
//   - 执行实例：connectionRetryCount 0、单请求超时 EXEC_REQUEST_TIMEOUT_MS，交给命令守卫、获取期的应用启动与生命周期通道；
//   - 探测实例：单请求超时 PROBE_TIMEOUT_MS、0 次重试，只交给能力探测与 scenario 前的存活截图。
// 三者的日志级别都是 error，建第一个实例之前经 device/wdio-log 装上凭据掩码（ADR 0051 决策 11）。directConnect 显式关闭：全部请求
// 只发往 Device Farm 给出的端点。W3C pageLoad 超时（超时分层表 ⑦）只对网页目标有意义，由执行实例在建好会话后设一次。
//
// 连接池与第一条会话命令（ADR 0052 决策 6 的不变量段）：webdriver 按会话 id 共享一个 undici 连接池，池的超时取第一个对该会话发命令的
// 实例的值，之后其它实例的有效超时是自身与它的较小值。所以 connect 返回之前先由执行实例发出第一条会话命令（读一次当前上下文），
// 之后才建探测实例。建连实例的 newSession 不进连接池，但 WebdriverIO 的 remote() 在 iOS Safari 会话上返回之前由建连实例自己读一次
// 当前上下文（它的上下文管理器初始化），这条请求先于执行实例建起连接池；建连实例被预算封顶时超时可能远小于执行实例，池的超时随之
// 变小，整个会话里执行实例的长命令都会被提前切断。为此 newSession 返回之后、remote() 返回之前，经 remote() 的修饰函数把建连实例
// 此后的单请求超时改成执行实例的值：池无论由谁建起，超时都与执行实例相同。appium.test.mts 在真实的 webdriver 上锁定这一点。
//
// 截止信号（端口 pageSource、readWebAddress 的参数与获取预算的 signal）：WebdriverIO 的命令不接收中止信号。本模块经客户端的
// transformRequest 钩子，把调用方用 withDeadline 声明的截止信号并进每个请求自己的中止信号：到期即中止 HTTP 请求本身，与客户端超时
// 是同一种机制，不是放弃式等待（被拒方案「探测用 Promise.race」）。信号经 AsyncLocalStorage 沿调用链传到钩子里，同一实例上其它调用链
// 的请求不受影响。进入终结时获取预算的 signal 中止，在途的 newSession 与探测命令随之中止，停止信号由此穿透到 Appium 一侧。
//
// 状态码与传输故障（ADR 0052 决策 6）：服务端回非 2xx 时 webdriver 抛出的错误只带错误名与消息。三个实例的 transformResponse 钩子经
// device/guard.mts 的 recordHttpStatus 把状态码记到请求选项上（错误对象的 opts 就是它），读取一律经守卫的 httpStatusOf；连接层错误码、
// 超时码与网关类状态码也只取守卫导出的那一份，newSession 的瞬时失败与 commandFailureKind 的失败种类都据此判定。
//
// 生命周期通道上的只读原语（scenario 前的存活截图、控件树、为 evidence 读地址时的列上下文与读地址）对连接层错误与 502 / 503 / 504
// 重试一次，超时与 500 不重试：与守卫的只读白名单是同一条规则、同一个函数（守卫的 retryReadOnce，ADR 0052 决策 6 的只读白名单
// 「由设备模块重试 1 次」）。切换上下文不在白名单里，不重试。
//
// 能力集（ADR 0052 决策 3）由 newSessionCapabilities 单点组装。会话回报的 automationName 与系统版本只在 readSessionCapabilities 读一次
// （ADR 0052 决策 1 的唯一读取点），系统版本只进诊断与句柄上下文。
//
// 获取期的归因（ADR 0051 决策 3、4）：
//   - 设备单元拒装驱动辅助包（错误文本带 INSTALL_FAILED_USER_RESTRICTED）：返回 replace_device，换不换台由接缝按剩余预算决定；
//   - 被预算封顶的客户端超时：acquire_timeout；
//   - 未封顶的客户端超时与传输层失败（连接层错误、HTTP 502 / 503 / 504）是瞬时失败：预算允许时只重试 newSession 一次，否则
//     acquire_timeout；重试之后仍是瞬时失败同样归 acquire_timeout；
//   - 其余失败（服务端拒绝建会话，含安装失败）是非瞬时失败：precheck_failed，消息带脱敏后的服务端原因，以区分形态。
// newSession 之后的准备（建执行实例与探测实例、执行实例的第一条命令）失败时，本模块先尽力删掉刚建好的 Appium 会话再抛出，由接缝按
// 未归类的获取期失败处置；获取预算已中止（到期或进入终结）时不再发命令。
//
// 端点与预签名地址是凭证（ADR 0051 决策 11）：只交给 WebdriverIO，进消息之前经 worker/error-text 的一行化（先脱敏再截断）。
import { AsyncLocalStorage } from "node:async_hooks";
import { attach as wdioAttach, remote as wdioRemote, type Browser } from "webdriverio";
import type { Device } from "../worker/deterministic.mjs";
import { errorText, oneLineError } from "../worker/error-text.mjs";
import type { ScopeTermination } from "../worker/surface.mjs";
import {
  DELETE_SESSION_TIMEOUT_MS, EXEC_REQUEST_TIMEOUT_MS, NEW_COMMAND_TIMEOUT_S, NEW_SESSION_TIMEOUT_FLOOR_MS, PAGE_LOAD_TIMEOUT_MS,
  PROBE_TIMEOUT_MS,
} from "./limits.mjs";
import {
  ACQUIRE_TIMEOUT_MESSAGE,
  type AcquireBudget, type AddressAttempt, type AppiumConnector, type AppiumSession, type ConnectOutcome, type ConnectRequest,
} from "./surface.mjs";
import {
  CONNECTION_ERROR_CODES, GATEWAY_STATUS_CODES, TIMEOUT_ERROR_CODES, hasConnectionCode, httpStatusOf, isTimeout, recordHttpStatus,
  retryReadOnce,
} from "./guard.mjs";
import { NATIVE_CONTEXT, locateError, locateWebContext } from "./web-context.mjs";
import { WDIO_LOG_LEVEL, installWdioLogMasking } from "./wdio-log.mjs";

// ---- 能力集与会话能力的读取 ----

const PLATFORM_NAMES: Record<Device, string> = { android: "Android", ios: "iOS" };
const AUTOMATION_NAMES: Record<Device, string> = { android: "UiAutomator2", ios: "XCUITest" };
const BROWSER_NAMES: Record<Device, string> = { android: "Chrome", ios: "Safari" };

/** newSession 的能力集（ADR 0052 决策 3）。两种目标都带平台名、自动化驱动名与 appium:newCommandTimeout（超时分层表 ⑧）；网页目标带
 *  browserName（iOS 不带它就没有网页上下文）；应用目标带预签名的安装包地址，关掉自动启动与重置（启动由 worker 显式 activateApp
 *  并采样，ADR 0051 决策 9）。应用标识不进能力集：Device Farm 的交互端点把 appium:appPackage / appium:bundleId 当作「用已安装
 *  应用」路线的信号，与 appium:app 同发时跳过安装包的下载、却仍把 appium:app 改写成主机本地路径，驱动随即报文件不存在
 *  （Android 真机实测，ADR 0051 决策 9）；驱动从安装包本身读包名或 bundle id，worker 启停应用用的标识另走 app 模块的命令参数。
 *  应用目标缺地址或应用标识时抛出（接缝保证给齐；标识虽不进能力集，但建会话之后的启动采样立刻要用）。 */
export function newSessionCapabilities(
  req: Pick<ConnectRequest, "device" | "uiKind" | "appId" | "appUrl">,
): Record<string, unknown> {
  const caps: Record<string, unknown> = {
    platformName: PLATFORM_NAMES[req.device],
    "appium:automationName": AUTOMATION_NAMES[req.device],
    "appium:newCommandTimeout": NEW_COMMAND_TIMEOUT_S,
  };
  if (req.uiKind === "web") {
    caps.browserName = BROWSER_NAMES[req.device];
    return caps;
  }
  if (!req.appUrl || !req.appId) throw new Error("应用目标建立 Appium 会话时缺少安装包地址或应用标识");
  caps["appium:app"] = req.appUrl;
  caps["appium:autoLaunch"] = false;
  caps["appium:noReset"] = true;
  return caps;
}

/** 会话回报的、本模块要用的两项事实。 */
export interface SessionFacts {
  /** 选驱动适配器用；回报里没有时为空串（选不到适配器，接缝按不受支持的驱动处置）。 */
  automationName: string;
  /** 只进诊断与句柄上下文；没有时为 null。 */
  platformVersion: string | null;
}

/** 会话能力对象的唯一读取点（ADR 0052 决策 1）：automationName 与系统版本只在这里读，带不带 appium: 前缀都认。 */
export function readSessionCapabilities(capabilities: unknown): SessionFacts {
  const caps = (capabilities !== null && typeof capabilities === "object" ? capabilities : {}) as Record<string, unknown>;
  const automation = caps["appium:automationName"] ?? caps.automationName;
  const version = caps.platformVersion ?? caps["appium:platformVersion"];
  return {
    automationName: typeof automation === "string" ? automation : "",
    platformVersion: typeof version === "string" && version !== "" ? version : typeof version === "number" ? String(version) : null,
  };
}

// ---- 截止信号与失败种类 ----

const deadlines = new AsyncLocalStorage<AbortSignal>();

/** 在 signal 的约束下执行 fn：fn 调用链上经本模块建的客户端发出的每个请求，在 signal 中止时随之中止（见模块头「截止信号」）。可嵌套，
 *  内外两层的信号取先到者。 */
export function withDeadline<T>(signal: AbortSignal, fn: () => Promise<T>): Promise<T> {
  const outer = deadlines.getStore();
  return deadlines.run(outer === undefined ? signal : AbortSignal.any([outer, signal]), fn);
}

function joinDeadline(requestOptions: RequestInit): RequestInit {
  const deadline = deadlines.getStore();
  if (deadline !== undefined) {
    const own = requestOptions.signal ?? null;
    requestOptions.signal = own === null ? deadline : AbortSignal.any([own, deadline]);
  }
  return requestOptions;
}

// webdriver 10.0.2 客户端超时的消息（WebDriverRequestError）。
const CLIENT_TIMEOUT_TEXT = "Request timed out!";
// webdriver 对 newSession 的 ECONNREFUSED 改写出的消息开头（getSessionError），原错误码随改写丢失。
const UNABLE_TO_CONNECT_TEXT = "Unable to connect to";
const FAILED_WITH_CODE = /Request failed with error code ([A-Z_]+)/;

/** 一次命令失败的种类：客户端超时、连接层错误、网关类状态码、服务端的其它错误响应，或都不是（如被截止信号中止）。 */
export type CommandFailureKind = "client_timeout" | "connection" | "gateway" | "server" | "other";

/** 失败种类，判定与命令守卫是同一份（沿 cause 链取错误码，超时优先）。 */
export function commandFailureKind(error: unknown): CommandFailureKind {
  if (isTimeout(error)) return "client_timeout";
  if (hasConnectionCode(error)) return "connection";
  const status = httpStatusOf(error);
  if (status !== null) return GATEWAY_STATUS_CODES.has(status) ? "gateway" : "server";
  return "other";
}

function errorCode(error: unknown): string | null {
  const code = error !== null && typeof error === "object" ? (error as { code?: unknown }).code : undefined;
  return typeof code === "string" ? code : null;
}

function messageOf(error: unknown): string {
  if (error instanceof Error) return error.message;
  return typeof error === "string" ? error : "";
}

// ---- 建连 ----

/** 设备单元拒装驱动辅助包的错误文本标记（ADR 0051 决策 3 记下的厂商 ROM 形态）。 */
export const HELPER_INSTALL_REFUSED_MARKERS: readonly string[] = ["INSTALL_FAILED_USER_RESTRICTED"];

type NewSessionFailure = "helper_refused" | "client_timeout" | "transient" | "rejected";

// webdriver 把 newSession 的失败改写成只带消息的普通 Error（错误码与请求选项都丢了），所以这里按消息与建连实例钩子记下的状态码判。
function newSessionFailureKind(error: unknown, status: number | null): NewSessionFailure {
  const text = messageOf(error);
  if (HELPER_INSTALL_REFUSED_MARKERS.some((m) => text.includes(m))) return "helper_refused";
  if (text.includes(CLIENT_TIMEOUT_TEXT)) return "client_timeout";
  const code = errorCode(error) ?? FAILED_WITH_CODE.exec(text)?.[1] ?? null;
  if (code !== null && code !== "ETIMEDOUT" && TIMEOUT_ERROR_CODES.has(code)) return "client_timeout";
  if (code === "ETIMEDOUT" || (code !== null && CONNECTION_ERROR_CODES.has(code))) return "transient";
  if (text.startsWith(UNABLE_TO_CONNECT_TEXT)) return "transient";
  if (status !== null && GATEWAY_STATUS_CODES.has(status)) return "transient";
  return "rejected";
}

/** 服务端给出的原因：去掉 webdriver 追加的「when running … with method … and args …」尾巴（其中有端点地址与整份能力集），一行化并
 *  脱敏。 */
function serverReason(error: unknown): string {
  const text = messageOf(error).split(' when running "')[0]!.replace(/^WebDriverError: /, "");
  return oneLineError(text);
}

/** newSession 被服务端拒绝（非瞬时失败）时给使用方的消息：precheck_failed，带服务端原因以区分形态（ADR 0051 决策 4）。 */
export function newSessionRejectedMessage(reason: string): string {
  const head = "设备未能建立执行测试所需的 Appium 会话";
  const tail = "请换一台设备后重试；应用目标请同时确认安装包能在这台设备上安装";
  return reason === "" ? `${head}；${tail}` : `${head}：${reason}；${tail}`;
}

/** 三个实例的单请求超时（毫秒）。 */
export interface ClientTimeouts {
  /** newSession 单请求超时的下限；实际取它与剩余获取预算的较小者。 */
  newSessionFloorMs: number;
  execRequestMs: number;
  probeRequestMs: number;
}

export const CLIENT_TIMEOUTS: ClientTimeouts = {
  newSessionFloorMs: NEW_SESSION_TIMEOUT_FLOOR_MS,
  execRequestMs: EXEC_REQUEST_TIMEOUT_MS,
  probeRequestMs: PROBE_TIMEOUT_MS,
};

/** WebdriverIO 的两个入口。 */
export interface WdioEntry {
  remote: typeof wdioRemote;
  attach: typeof wdioAttach;
}

export type Sleep = (ms: number, signal?: AbortSignal) => Promise<void>;

export interface AppiumConnectorOptions {
  /** worker 日志，只记不影响判定的诊断（如未能设置页面加载超时）；不传时不记。 */
  log?: (line: string) => void;
  /** 以下只供测试注入：WebdriverIO 入口、三个实例的超时、装凭据掩码、网页上下文零候选之后的等待。 */
  wdio?: WdioEntry;
  timeouts?: ClientTimeouts;
  installLogMasking?: () => void;
  sleep?: Sleep;
}

interface EndpointParts {
  protocol: string;
  hostname: string;
  port: number;
  path: string;
}

function endpointParts(endpoint: string): EndpointParts {
  const url = new URL(endpoint);
  const protocol = url.protocol.replace(/:$/, "");
  return {
    protocol,
    hostname: url.hostname,
    port: url.port ? Number(url.port) : protocol === "https" ? 443 : 80,
    path: url.pathname + url.search,
  };
}

function clientOptions(endpoint: EndpointParts, timeoutMs: number, onStatus?: (status: number) => void) {
  return {
    ...endpoint,
    logLevel: WDIO_LOG_LEVEL,
    connectionRetryTimeout: timeoutMs,
    connectionRetryCount: 0,
    enableDirectConnect: false,
    transformRequest: joinDeadline,
    transformResponse: (response: { statusCode: number }, requestOptions: RequestInit) => {
      recordHttpStatus(response, requestOptions);
      onStatus?.(response.statusCode);
      return response;
    },
  };
}

// 消息常量来自 surface.mts；接线后两者可能形成静态 import 循环，模块顶层不读它们（暂时性死区），每次调用时再组装。
function acquireTimedOut(): ConnectOutcome {
  return { kind: "terminated", termination: { errorType: "acquire_timeout", message: ACQUIRE_TIMEOUT_MESSAGE } };
}

function terminated(termination: ScopeTermination): ConnectOutcome {
  return { kind: "terminated", termination };
}

/** 缺省的等待：到时或 signal 中止时结束（不抛出，调用方自己核对 signal）。 */
export const defaultSleep: Sleep = (ms, signal) => new Promise((resolve) => {
  if (signal?.aborted) return resolve();
  const timer = setTimeout(done, ms);
  function done(): void {
    clearTimeout(timer);
    signal?.removeEventListener("abort", done);
    resolve();
  }
  signal?.addEventListener("abort", done, { once: true });
});

/** Appium 块的建连面（端口 AppiumConnector）。 */
export function createAppiumConnector(options: AppiumConnectorOptions = {}): AppiumConnector {
  const wdio = options.wdio ?? { remote: wdioRemote, attach: wdioAttach };
  const timeouts = options.timeouts ?? CLIENT_TIMEOUTS;
  const installMasking = options.installLogMasking ?? installWdioLogMasking;
  const sleep = options.sleep ?? defaultSleep;
  const log = options.log ?? (() => {});

  async function establish(
    client: Browser, req: ConnectRequest, endpoint: EndpointParts, budget: AcquireBudget,
  ): Promise<AppiumSession> {
    const sessionId = client.sessionId;
    const capabilities = client.capabilities;
    try {
      return await withDeadline(budget.signal, async () => {
        const exec = await wdio.attach({ sessionId, capabilities, ...clientOptions(endpoint, timeouts.execRequestMs) });
        // 执行实例的第一条会话命令，之后才建探测实例（见模块头「连接池与第一条会话命令」）。
        await exec.getContext();
        if (req.uiKind === "web") {
          try {
            await exec.setTimeout({ pageLoad: PAGE_LOAD_TIMEOUT_MS });
          } catch (e) {
            if (budget.signal.aborted) throw e;
            log(`worker: 未能设置页面加载超时，导航只受单条命令的请求超时约束（不影响判定）：${errorText(e)}`);
          }
        }
        const probe = await wdio.attach({ sessionId, capabilities, ...clientOptions(endpoint, timeouts.probeRequestMs) });
        return createAppiumSession({ clients: { exec, probe }, device: req.device, capabilities, sleep });
      });
    } catch (e) {
      if (!budget.signal.aborted) {
        await withDeadline(AbortSignal.timeout(DELETE_SESSION_TIMEOUT_MS), () => client.deleteSession()).catch(() => {});
      }
      throw e;
    }
  }

  return {
    async connect(req, budget) {
      installMasking();
      const endpoint = endpointParts(req.endpoint);
      const capabilities = newSessionCapabilities(req);
      for (let attempt = 1; ; attempt++) {
        if (budget.signal.aborted || budget.remainingMs() <= 0) return acquireTimedOut();
        const timeoutMs = Math.min(timeouts.newSessionFloorMs, budget.remainingMs());
        const capped = timeoutMs < timeouts.newSessionFloorMs;
        let newSessionStatus: number | null = null;
        let client: Browser;
        try {
          client = await withDeadline(budget.signal, () => wdio.remote(
            { ...clientOptions(endpoint, timeoutMs, (s) => { newSessionStatus ??= s; }), capabilities },
            (c, o) => {
              // 建连实例此后的请求（iOS Safari 上 remote() 返回前自己读的一次当前上下文）用执行实例的超时，见模块头。
              o.connectionRetryTimeout = timeouts.execRequestMs;
              return c;
            },
          ));
        } catch (e) {
          if (budget.signal.aborted) return acquireTimedOut();
          const kind = newSessionFailureKind(e, newSessionStatus);
          if (kind === "helper_refused") return { kind: "replace_device", reason: serverReason(e) };
          if (kind === "rejected") {
            return terminated({ errorType: "precheck_failed", message: newSessionRejectedMessage(serverReason(e)) });
          }
          if (kind === "client_timeout" && capped) return acquireTimedOut();
          if (attempt === 1) continue;  // 瞬时失败只重试 newSession 一次；循环开头核对预算是否还允许
          return acquireTimedOut();
        }
        return { kind: "connected", session: await establish(client, req, endpoint, budget) };
      }
    },
  };
}

// ---- 建好的会话 ----

/** 能力探测要用的会话面：端口 AppiumSession 之外另带探测实例。探测实例只交给能力探测与 scenario 前的存活截图。 */
export interface ProbeableAppiumSession extends AppiumSession {
  readonly probe: Browser;
}

/** 取会话的探测实例；会话不是本模块建的（没有探测实例）时抛出。 */
export function probeClientOf(session: AppiumSession): Browser {
  const probe = (session as Partial<ProbeableAppiumSession>).probe;
  if (probe === undefined) throw new Error("这个 Appium 会话没有探测用的客户端，无法执行能力探测");
  return probe;
}

export interface AppiumSessionArgs {
  clients: { exec: Browser; probe: Browser };
  /** 网页上下文按设备筛选候选（web-context.mts）。 */
  device: Device;
  /** 会话能力对象（newSession 的回报），经 readSessionCapabilities 读一次。 */
  capabilities: unknown;
  sleep?: Sleep;
}

/** 由已建好的执行实例与探测实例组成会话（connect 内部用；测试经它把假客户端装成会话）。 */
export function createAppiumSession(args: AppiumSessionArgs): ProbeableAppiumSession {
  return new WdioAppiumSession(args);
}

function contextNameOf(raw: unknown): string {
  if (typeof raw === "string") return raw;
  if (raw !== null && typeof raw === "object" && typeof (raw as { id?: unknown }).id === "string") return (raw as { id: string }).id;
  return "";
}

class WdioAppiumSession implements ProbeableAppiumSession {
  readonly exec: Browser;
  readonly probe: Browser;
  readonly automationName: string;
  readonly platformVersion: string | null;
  private readonly device: Device;
  private readonly sleep: Sleep;

  constructor(args: AppiumSessionArgs) {
    this.exec = args.clients.exec;
    this.probe = args.clients.probe;
    this.device = args.device;
    this.sleep = args.sleep ?? defaultSleep;
    const facts = readSessionCapabilities(args.capabilities);
    this.automationName = facts.automationName;
    this.platformVersion = facts.platformVersion;
  }

  async currentContext(): Promise<string> {
    return contextNameOf(await this.exec.getContext());
  }

  async switchToNative(): Promise<void> {
    await this.exec.switchContext(NATIVE_CONTEXT);
  }

  /** 存活截图：经探测实例发出，受它的短超时约束；连接层错误与 502 / 503 / 504 重试一次（见模块头）。 */
  async probeScreenshot(): Promise<void> {
    await retryReadOnce(() => this.probe.takeScreenshot());
  }

  /** 原生上下文的控件树：受 signal 约束；连接层错误与 502 / 503 / 504 在 signal 未中止时重试一次。 */
  pageSource(signal: AbortSignal): Promise<string> {
    return withDeadline(signal, () => retryReadOnce(() => this.exec.getPageSource(), () => !signal.aborted));
  }

  /** 为 evidence 读地址：多候选与零候选、命令出错都只给出读不到的原因，不抛出；signal 已中止的记 timeout。列上下文与读地址各自按
   *  只读原语重试一次，切入不重试。读完尽力切回原生上下文，切不回由随后的复原核对处置。 */
  async readWebAddress(signal: AbortSignal): Promise<AddressAttempt> {
    if (signal.aborted) return { missing: "timeout" };
    const live = (): boolean => !signal.aborted;
    try {
      return await withDeadline(signal, async () => {
        const location = await locateWebContext(() => retryReadOnce(() => this.exec.getContexts(), live), this.device, {
          sleep: (ms) => this.sleep(ms, signal),
        });
        if (location.kind !== "one") return { missing: signal.aborted ? "timeout" : "error" } as const;
        await this.exec.switchContext(location.name);
        try {
          return { url: await retryReadOnce(() => this.exec.getUrl(), live) };
        } finally {
          await this.exec.switchContext(NATIVE_CONTEXT).catch(() => {});
        }
      });
    } catch {
      return { missing: signal.aborted ? "timeout" : "error" };
    }
  }

  /** ctx.withWebContext（ADR 0050 决策 2）：经传入的 driver 重新定位、切入、执行 fn 一次（不重试，fn 可能已有副作用），结束（含抛错）
   *  后切回原生上下文；切回失败不掩盖 fn 的结果，由 step 后的复原核对处置。多候选与零候选抛出带 engine_error 标记的异常。 */
  async withWebContext<T>(driver: Browser, fn: () => Promise<T> | T): Promise<T> {
    const location = await locateWebContext(() => driver.getContexts(), this.device, { sleep: (ms) => this.sleep(ms) });
    if (location.kind !== "one") throw locateError(location);
    await driver.switchContext(location.name);
    try {
      return await fn();
    } finally {
      await driver.switchContext(NATIVE_CONTEXT).catch(() => {});
    }
  }

  /** 网页目标且能力结论为「提供」时的导航：经传入的 driver 重新定位、切入网页上下文、打开地址。导航后停在网页上下文，回到原生上下文
   *  由 step 后的复原核对（预热由预热块自己）负责。 */
  async openUrl(driver: Browser, address: string): Promise<void> {
    const location = await locateWebContext(() => driver.getContexts(), this.device, { sleep: (ms) => this.sleep(ms) });
    if (location.kind !== "one") throw locateError(location);
    await driver.switchContext(location.name);
    await driver.url(address);
  }

  /** 正常收尾的 deleteSession：DELETE_SESSION_TIMEOUT_MS 截止，不重试（ADR 0051 决策 5）。 */
  deleteSession(): Promise<void> {
    return withDeadline(AbortSignal.timeout(DELETE_SESSION_TIMEOUT_MS), () => this.exec.deleteSession()).then(() => {});
  }
}
