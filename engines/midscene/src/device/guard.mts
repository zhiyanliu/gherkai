// 命令守卫（ADR 0052 决策 3 的「命令守卫」块；决策 6 的「执行期关闭传输层自动重试」「命令守卫」「执行异常的归类由守卫带给
// runStep」「结果未知的命令」；ADR 0051 决策 4「会话丢失的判定靠查状态」与决策 12；ADR 0050 决策 2 的 ctx.driver）：实现
// device/surface.mts 的 GuardFactory / CommandGuard 端口。
//
// 守卫是会话级的 driver 代理：交给 handler、内建导航与界面实现的都是它，执行实例本身不交出去。代理是一层膜：经它取得的方法、
// 元素句柄、链式查询、元素列表、动作构造器，以及 WebdriverIO 调用使用方回调时传进去的元素，都仍在膜内，每一次调用过同一道检查；
// 交给使用方的纯数据（字符串、数字、只含数据的对象与数组、Buffer）原样返回，不受约束。膜内对象上的命令以执行实例一侧的原对象为
// this 执行，WebdriverIO 内部互相调用的命令因此不重复检查。
//
// 两件状态（ADR 0052 决策 6）：
//   - 执行令牌：openWindow 发出，closeWindow 与 shutdown 撤销。一次调用必须同时满足两个来源的令牌都是当前令牌：
//       ① 派生令牌：经膜取得的方法、元素与链在取得时记下当时的令牌，缓存的元素与解构出的方法带进下一个 step 即不匹配；
//       ② 异步上下文令牌：openWindow 用 AsyncLocalStorage 把令牌绑进本次执行的异步上下文，handler 与 Midscene 由此发起的
//          异步延续（await 之后恢复、定时器与 promise 回调）都带着它，step 结束后才恢复的 handler 与晚到的回调即便落在下一个
//          step 里，带的也是旧令牌。openWindow 只能用 enterWith 绑定（端口的形状是先开窗口、再由调用方执行），它作用于调用方
//          此后的同步执行与由此派生的异步延续，设备侧接缝的 execute 正是在开窗口之后紧接着调用执行函数。
//     不满足的调用不发出，返回一个被拒绝的结果：被 await 时抛出带归类标记的异常，没人 await 时不产生未处理的拒绝。
//   - 结果未知标志：有副作用的命令遇到客户端超时或传输层故障即置位、中止当前 act，本窗口内此后有副作用的命令一律不发出，
//     只读白名单照常放行。传输层故障指连接层错误码（下方 CONNECTION_ERROR_CODES：ADR 0052 决策 6 列出的 ECONNRESET、
//     ECONNREFUSED、EPIPE、UND_ERR_SOCKET、UND_ERR_CLOSED，另含域名解析与路由失败）与 HTTP 502、503、504：ADR 0052 决策 6 把它们
//     与「服务端已处理并报错」的 500 区分为传输故障，网关一侧的这三种状态码同样说明请求可能已到达设备而回应丢失，所以对有副作用的
//     命令一并按结果未知处理（宁可短路本 scenario，也不让 handler 在同一 step 里重发一次点击或输入）。解析与路由失败时请求多半尚未
//     发出，与 ECONNREFUSED 一样按保守处理。
//
// 只读白名单按原语列、不按 HTTP 方法判（ADR 0052 决策 6）：截图、取上下文列表、page source、网页上下文中的读地址、Android 的
// 前台应用查询、/status，以及驱动适配器导出的只读 mobile 命令集合（含 iOS 的前台应用查询与屏幕信息；集合的元素是 execute 的
// 完整脚本串，守卫整串比对，mobile 命令的前缀只在适配器里出现，ADR 0052 决策 4）。只对执行实例本身发出的这些命令放行，元素上的
// 命令一律按有副作用处理。「网页上下文中」的判定：窗口打开时会话在原生上下文（step 前核对的义务），此后经守卫成功切入的非原生
// 上下文即视为网页上下文。端口把守卫代理作为 driver 参数交给 AppiumSession 的 withWebContext 与 openUrl，它们经这个参数切入的、
// 按 ADR 0052 决策 5 重新定位确认过的被测页面由此被认出；经执行实例直接切换（生命周期通道）守卫看不到，读地址此时按有副作用
// 处理，只会更保守。
//
// 失败的分流（ADR 0052 决策 6；ADR 0051 决策 4）：
//   - 只读命令遇到连接层错误码或 502 / 503 / 504 由守卫重试一次（执行实例的传输层重试为 0，有副作用的命令任何情况都不补发）；
//     一切超时（含 webdriver 自身的 ETIMEDOUT 客户端超时）与 500 不重试。这条规则写成 retryReadOnce，生命周期通道上的同类只读
//     原语（appium.mts 的存活截图、控件树与为 evidence 读地址）用的是同一个函数。
//   - 经守卫的命令失败（重试之后仍失败、或不重试）一律先查一次会话状态：不是 RUNNING 即会话丢失，锁存，中止当前 act，本窗口与之后
//     的窗口里经代理的命令都按会话丢失拒绝；查询本身失败不据此判会话丢失。仍在运行时：有副作用的命令遇到传输层故障为结果未知，
//     消息用 ADR 原文；只读命令超时为执行出错；其余（服务端已报错、结果已知）为执行出错并保留原因。
//   - 守卫抛出的每个异常都带归类标记（worker/surface.mts 的 attachClassification），runStep 先认标记，设备路径因此没有
//     network_error 出口；标记挂在原异常对象上，驱动适配器仍可按原消息再归类（已有标记的异常守卫原样透传）。查到会话仍为 RUNNING
//     的结果已知失败，标记另带 sessionRunningConfirmed 这项事实，适配器只在它成立时按实测过的驱动错误文本再归类；晚到的失败、
//     查询本身失败、会话丢失与结果未知都不带。
// 传输故障的判定是设备模块的单一事实源，放在本模块（不 import 任何 SDK 的值）：HTTP 状态码的读写（recordHttpStatus 与
// httpStatusOf）、连接层错误码、超时码与网关类状态码三个集合，以及只读原语的一次重试。webdriver 10.0.2 对服务端非 2xx 抛出的错误
// 只带错误名与消息，appium.mts 给三个客户端实例设的 transformResponse 钩子调 recordHttpStatus 把状态码记到请求选项上，错误对象的
// opts 就是那个请求选项，经 httpStatusOf 读回；appium.mts 的 newSession 归因与失败种类（能力探测按它归类）用的也是这里的集合与
// 判定。
//
// 生命周期通道（step 前核对、复原与核对、界面快照、scenario 前核对、预热、终结）经执行实例直接执行，不经守卫代理、不受令牌与结果
// 未知标志约束（ADR 0052 决策 2），只借用上面的传输故障判定与只读原语的重试。守卫不改动执行实例，它的状态只约束经 driver 代理发出
// 的命令。
import { AsyncLocalStorage } from "node:async_hooks";
import { types } from "node:util";
import type { Browser } from "webdriverio";
import { errorText } from "../worker/error-text.mjs";
import { attachClassification, readClassification, type StepClassification, type StepFailure } from "../worker/surface.mjs";
// 循环引用说明：装配设备部件的模块可能被 surface.mts 静态导入，而本模块又从 surface.mts 取会话丢失的消息。这时本模块先于
// surface.mts 求值，所以这个值只在函数体内读取，模块顶层不读取 surface.mts 的任何绑定。
import {
  SESSION_LOST_MESSAGE, type CommandGuard, type DriverAdapter, type GuardFactory, type WindowOutcome,
} from "./surface.mjs";

// ---- 给使用方看的消息（ADR 0039；ADR 给了原文整句的照原文）----

/** 结果未知（ADR 0052 决策 6 的原文）。 */
export const RESULT_UNKNOWN_MESSAGE = "设备在等待时间内没有回应，这一步可能已执行也可能未执行";
/** 不带当前令牌的调用：step 结束后才发出、或用了上一个 step 取得的元素与方法。 */
export const STALE_COMMAND_MESSAGE =
  "这条设备命令在它所属的 step 结束之后才发出，没有执行；请在 handler 返回之前等待全部设备命令完成，" +
  "step 结束后不要再使用 ctx.driver 或从它取得的元素";
/** 进入终结之后的调用。 */
export const FINALIZING_COMMAND_MESSAGE = "测试已进入收尾，这条设备命令没有执行";
/** 结果未知之后被拒绝的有副作用命令（异常消息；归类标记沿用本窗口的判定）。 */
export const AFTER_RESULT_UNKNOWN_MESSAGE = "这一步已有设备命令没有回应、结果未知，之后有副作用的设备命令没有执行";
/** 只读命令超时（会话仍在运行）。 */
export const READ_ONLY_TIMEOUT_MESSAGE = "设备在等待时间内没有回应读取信息的命令";

/** 结果已知的命令失败（会话仍在运行）：保留一行原因。 */
export function commandFailedMessage(reason: string): string {
  return reason === "" ? "设备命令执行失败" : `设备命令执行失败：${reason}`;
}

// ---- HTTP 状态码的读写约定 ----

// 记在请求选项对象上的键：不可枚举，不进 fetch 的选项展开，也不进日志。Symbol.for 让模块被重复加载时两侧认得同一个键。
const HTTP_STATUS_KEY = Symbol.for("gherkai.worker-midscene.http-status");
// cause 链的查找上限，与 worker/surface.mts 读归类标记的上限相同，同时防环。
const MAX_CAUSE_DEPTH = 8;

/** 客户端实例的 transformResponse 钩子要做的记录（ADR 0052 决策 6）：把这次响应的 HTTP 状态码记到同一次请求的选项对象上，原样
 *  返回响应。webdriver 10.0.2 调这个钩子时传入的选项对象，正是随后抛出的 WebDriverResponseError 挂在 opts 上的那一个，经
 *  httpStatusOf 读回。appium.mts 的 clientOptions 是唯一的生产调用点。 */
export function recordHttpStatus<R extends { statusCode?: number }>(response: R, requestOptions: object): R {
  const status = response?.statusCode;
  if (typeof status === "number" && requestOptions !== null && typeof requestOptions === "object"
      && Object.isExtensible(requestOptions)) {
    Object.defineProperty(requestOptions, HTTP_STATUS_KEY, { value: status, enumerable: false, configurable: true, writable: true });
  }
  return response;
}

/** 读错误上的 HTTP 状态码：沿 cause 链取第一个——错误自身的数值 statusCode（webdriver 在响应体无法解析时从 cause 带上来），
 *  或 recordHttpStatus 记在错误 opts 上的值。读不到返回 null。 */
export function httpStatusOf(error: unknown): number | null {
  let current: unknown = error;
  for (let depth = 0; depth < MAX_CAUSE_DEPTH; depth++) {
    if (current === null || typeof current !== "object") return null;
    const own = (current as { statusCode?: unknown }).statusCode;
    if (typeof own === "number") return own;
    const opts = (current as { opts?: unknown }).opts;
    if (opts !== null && typeof opts === "object") {
      const recorded = (opts as { [HTTP_STATUS_KEY]?: unknown })[HTTP_STATUS_KEY];
      if (typeof recorded === "number") return recorded;
    }
    current = (current as { cause?: unknown }).cause;
  }
  return null;
}

// ---- 错误形态 ----

/** 连接层错误的错误码（ADR 0052 决策 6 列出的五个，另含域名解析与路由失败）。不含任何超时码：一切超时都不重试。 */
export const CONNECTION_ERROR_CODES: ReadonlySet<string> = new Set([
  "ECONNRESET", "ECONNREFUSED", "EPIPE", "EHOSTUNREACH", "ENETUNREACH", "ENOTFOUND", "EAI_AGAIN", "UND_ERR_SOCKET", "UND_ERR_CLOSED",
]);
/** 网关类状态码：与连接层错误一样属于传输故障（ADR 0052 决策 6）。 */
export const GATEWAY_STATUS_CODES: ReadonlySet<number> = new Set([502, 503, 504]);
/** 超时的错误码：webdriver 的 ETIMEDOUT（客户端超时与底层网络超时同码）与 undici 的连接、响应头、响应体超时（连接池的超时取第一个
 *  对会话发命令的实例的值，见 appium.mts 的模块头）。一切超时都不重试（ADR 0052 决策 6）。 */
export const TIMEOUT_ERROR_CODES: ReadonlySet<string> = new Set([
  "ETIMEDOUT", "UND_ERR_CONNECT_TIMEOUT", "UND_ERR_HEADERS_TIMEOUT", "UND_ERR_BODY_TIMEOUT",
]);

/** 沿 cause 链是否有满足条件的一层。 */
function someLayer(error: unknown, test: (layer: { code?: unknown; name?: unknown }) => boolean): boolean {
  let current: unknown = error;
  for (let depth = 0; depth < MAX_CAUSE_DEPTH; depth++) {
    if (current === null || typeof current !== "object") return false;
    if (test(current as { code?: unknown; name?: unknown })) return true;
    current = (current as { cause?: unknown }).cause;
  }
  return false;
}

/** 超时：沿 cause 链有一层带超时码，或是中止信号的 TimeoutError。 */
export function isTimeout(error: unknown): boolean {
  return someLayer(error, (l) => (typeof l.code === "string" && TIMEOUT_ERROR_CODES.has(l.code)) || l.name === "TimeoutError");
}

/** 沿 cause 链有一层带连接层错误码。 */
export function hasConnectionCode(error: unknown): boolean {
  return someLayer(error, (l) => typeof l.code === "string" && CONNECTION_ERROR_CODES.has(l.code));
}

function isGatewayStatus(error: unknown): boolean {
  const status = httpStatusOf(error);
  return status !== null && GATEWAY_STATUS_CODES.has(status);
}

/** 只读命令可重试：连接层错误码或 502 / 503 / 504，且不是超时。 */
export function isRetryable(error: unknown): boolean {
  return !isTimeout(error) && (hasConnectionCode(error) || isGatewayStatus(error));
}

/** 只读原语的一次重试（ADR 0052 决策 6 的只读白名单「由设备模块重试 1 次」）：第一次失败可重试（isRetryable）且 mayRetry() 仍为真
 *  时再发一次，否则抛出第一次的失败；重试之后的失败原样抛出。守卫的只读白名单与生命周期通道上的只读原语共用这一条规则，调用方用
 *  mayRetry 表达「此时已不该再向设备发命令」（窗口已关闭、截止信号已中止）。只用于没有副作用的命令。 */
export async function retryReadOnce<T>(send: () => T | Promise<T>, mayRetry: () => boolean = () => true): Promise<T> {
  try {
    return await send();
  } catch (e) {
    if (!isRetryable(e) || !mayRetry()) throw e;
  }
  return await send();
}

/** 传输层故障：超时、连接层错误码、502 / 503 / 504。有副作用的命令遇到它即结果未知。 */
function isTransportFault(error: unknown): boolean {
  return isTimeout(error) || hasConnectionCode(error) || isGatewayStatus(error);
}

// ---- 只读白名单 ----

/** 只读 mobile 命令集合在驱动适配器上的形状（ADR 0052 决策 4）：元素是 execute 的完整脚本串，与适配器自己发出的写法相同。
 *  适配器没有给出时集合为空，mobile 命令一律按有副作用处理。 */
export interface ReadOnlyMobileCommands {
  readonly readOnlyMobileCommands: ReadonlySet<string>;
}

const READ_ONLY_COMMANDS: ReadonlySet<string> = new Set([
  "takeScreenshot", "getContexts", "getAppiumContexts", "getPageSource", "getCurrentPackage", "status",
]);
const ADDRESS_COMMAND = "getUrl";
const SCRIPT_COMMANDS: ReadonlySet<string> = new Set(["execute", "executeScript"]);
const CONTEXT_SWITCH_COMMANDS: ReadonlySet<string> = new Set(["switchContext", "switchAppiumContext"]);
const NATIVE_CONTEXT = "NATIVE_APP";
// Device Farm 远程访问会话的运行中状态（GetRemoteAccessSession 的状态值）。
const RUNNING = "RUNNING";

// 不算命令的成员：取用与调用都不检查令牌（日志、序列化与类型判断会碰到它们），返回值照样留在膜内。遍历另有处理，见 membrane。
const INSPECT = Symbol.for("nodejs.util.inspect.custom");
const NON_COMMAND_MEMBERS: ReadonlySet<PropertyKey> = new Set<PropertyKey>([
  "toString", "toJSON", "valueOf", "toLocaleString", "constructor", Symbol.toPrimitive, Symbol.toStringTag, INSPECT,
]);

// ---- 值的分类 ----

function isObjectLike(value: unknown): value is object {
  return value !== null && (typeof value === "object" || typeof value === "function");
}

function isThenable(value: unknown): value is PromiseLike<unknown> {
  return isObjectLike(value) && typeof (value as { then?: unknown }).then === "function";
}

/** 不可能藏着命令的内建数据类型。 */
function isDataLeaf(value: object): boolean {
  return ArrayBuffer.isView(value) || value instanceof ArrayBuffer || value instanceof Date || value instanceof RegExp
    || value instanceof Error;
}

/** 纯数据：原型为 Object / null 的对象或普通数组，逐层只含原始值与数据叶子。任何代理、访问器、函数或类实例都不算。 */
function isPlainData(value: object, seen: Set<object>): boolean {
  if (seen.has(value)) return true;
  if (types.isProxy(value)) return false;
  const proto = Object.getPrototypeOf(value);
  if (Array.isArray(value) ? proto !== Array.prototype : proto !== Object.prototype && proto !== null) return false;
  seen.add(value);
  for (const key of Reflect.ownKeys(value)) {
    const desc = Reflect.getOwnPropertyDescriptor(value, key);
    if (desc === undefined) continue;
    if (!("value" in desc)) return false;
    const item: unknown = desc.value;
    if (!isObjectLike(item)) continue;
    if (typeof item === "function") return false;
    if (!isDataLeaf(item) && !isPlainData(item, seen)) return false;
  }
  return true;
}

function isPlainContainer(value: object): boolean {
  if (types.isProxy(value)) return false;
  const proto = Object.getPrototypeOf(value);
  return Array.isArray(value) ? proto === Array.prototype : proto === Object.prototype || proto === null;
}

/** 被拒绝的调用：不发出命令。被 await（或取 then / catch / finally）时才生成被拒绝的 promise，所以没人 await 时不产生未处理的
 *  拒绝；链式调用（如 `driver.$(…).click()`）在它上面继续得到同一个被拒绝的结果。reason 可以是还在归类的 promise。 */
function rejected(reason: Error | Promise<Error>): unknown {
  let promise: Promise<never> | null = null;
  const settle = (): Promise<never> => (promise ??= Promise.resolve(reason).then((e) => Promise.reject(e)));
  const chain: unknown = new Proxy(function rejectedCommand() { /* 不发出命令 */ }, {
    get(_target, prop) {
      if (prop === "then") return (onF?: (v: never) => unknown, onR?: (e: unknown) => unknown) => settle().then(onF, onR);
      if (prop === "catch") return (onR?: (e: unknown) => unknown) => settle().catch(onR);
      if (prop === "finally") return (onFinally?: () => void) => settle().finally(onFinally);
      if (prop === "toString") return () => "[rejected device command]";
      if (typeof prop === "symbol") return undefined;
      return () => chain;
    },
    apply() { return chain; },
  });
  return chain;
}

// ---- 执行窗口 ----

/** 一个 step 的执行窗口，对象本身即执行令牌。 */
class ExecutionWindow {
  resultUnknown = false;
  outcome: WindowOutcome | null = null;
  /** 经守卫切入的当前上下文；窗口打开时会话在原生上下文（step 前核对的义务），切换失败或形态不明时为 null。 */
  context: string | null = NATIVE_CONTEXT;
  private statusQuery: Promise<string | null> | null = null;

  constructor(readonly act: AbortController) {}

  abort(message: string): void {
    if (!this.act.signal.aborted) this.act.abort(new Error(message));
  }

  /** 查一次会话状态；并发失败共享在途的那一次。查询本身失败返回 null。 */
  queryStatus(sessionStatus: () => Promise<string | null>): Promise<string | null> {
    this.statusQuery ??= sessionStatus().catch(() => null).finally(() => { this.statusQuery = null; });
    return this.statusQuery;
  }
}

/** 膜内对象记下的派生令牌：ROOT 表示 driver 代理本身，取用成员时按当时的令牌派生。 */
const ROOT = Symbol("root");
type Derivation = ExecutionWindow | null | typeof ROOT;

/** 会话丢失的归类。消息在调用时读取：循环引用下本模块可能先于 surface.mts 求值，模块顶层不能碰它的绑定。 */
function lostFailure(): StepFailure {
  return { errorType: "session_lost", message: SESSION_LOST_MESSAGE };
}

function failure(errorType: StepFailure["errorType"], message: string): StepFailure {
  return { errorType, message };
}

function copyOutcome(outcome: WindowOutcome | null): WindowOutcome | null {
  return outcome === null ? null : { failure: { ...outcome.failure }, resultUnknown: outcome.resultUnknown };
}

// ---- 守卫 ----

export interface CommandGuardArgs {
  exec: Browser;
  adapter: DriverAdapter & Partial<ReadOnlyMobileCommands>;
  sessionStatus: () => Promise<string | null>;
}

class Guard implements CommandGuard {
  readonly driver: Browser;
  private current: ExecutionWindow | null = null;
  /** shutdown 时撤销的窗口：之后的 closeWindow 仍交回它的判定。 */
  private revokedByShutdown: ExecutionWindow | null = null;
  private shut = false;
  private lost = false;
  private readonly store = new AsyncLocalStorage<ExecutionWindow>();
  private readonly exec: object;
  private readonly readOnlyScripts: ReadonlySet<string>;
  private readonly sessionStatus: () => Promise<string | null>;
  /** 膜内对象与守卫交出的函数到执行实例一侧原值的映射（传回 WebdriverIO 时解包）。 */
  private readonly toRawMap = new WeakMap<object, object>();
  /** 使用方回调到执行实例一侧包装的映射，按派生令牌分开（同一个回调在同一窗口里再传一次得到同一个包装）；没有令牌时的包装单放。 */
  private readonly callbackWrappers = new WeakMap<object, {
    none?: (...args: unknown[]) => unknown; byWindow: WeakMap<ExecutionWindow, (...args: unknown[]) => unknown>;
  }>();
  private readonly wrapperToCallback = new WeakMap<object, object>();

  constructor(args: CommandGuardArgs) {
    this.exec = args.exec as unknown as object;
    this.readOnlyScripts = args.adapter.readOnlyMobileCommands ?? new Set<string>();
    this.sessionStatus = args.sessionStatus;
    this.driver = this.membrane(this.exec, ROOT, null) as Browser;
  }

  // ---- 端口 ----

  openWindow(act: AbortController): void {
    if (this.shut) {
      act.abort(new Error(FINALIZING_COMMAND_MESSAGE));
      return;
    }
    const win = new ExecutionWindow(act);
    this.current = win;
    this.store.enterWith(win);
    if (this.lost) this.recordLost(win);
  }

  closeWindow(): WindowOutcome | null {
    const win = this.current ?? this.revokedByShutdown;
    this.current = null;
    this.revokedByShutdown = null;
    return copyOutcome(win?.outcome ?? null);
  }

  shutdown(): void {
    this.shut = true;
    const win = this.current;
    this.current = null;
    if (win !== null) {
      this.revokedByShutdown = win;
      win.abort(FINALIZING_COMMAND_MESSAGE);
    }
  }

  // ---- 调用的检查与发出 ----

  /** 当前令牌：派生令牌与异步上下文令牌都是当前窗口才放行；返回窗口，或要抛出的异常。 */
  private admit(derived: ExecutionWindow | null): ExecutionWindow | Error {
    if (this.shut) {
      return attachClassification(new Error(FINALIZING_COMMAND_MESSAGE), failure("engine_error", FINALIZING_COMMAND_MESSAGE));
    }
    const win = this.current;
    if (win === null || derived !== win || this.store.getStore() !== win) {
      return attachClassification(new Error(STALE_COMMAND_MESSAGE), failure("engine_error", STALE_COMMAND_MESSAGE));
    }
    if (this.lost) {
      this.recordLost(win);
      return attachClassification(new Error(SESSION_LOST_MESSAGE), lostFailure());
    }
    return win;
  }

  private isReadOnly(owner: unknown, command: string, args: readonly unknown[], win: ExecutionWindow): boolean {
    if (owner !== this.exec) return false;
    if (READ_ONLY_COMMANDS.has(command)) return true;
    if (command === ADDRESS_COMMAND) return win.context !== null && win.context !== NATIVE_CONTEXT;
    if (SCRIPT_COMMANDS.has(command)) return typeof args[0] === "string" && this.readOnlyScripts.has(args[0]);
    return false;
  }

  /** 膜内一次命令调用。fn 以执行实例一侧的 owner 为 this 执行。 */
  private invoke(fn: (...args: unknown[]) => unknown, owner: unknown, name: PropertyKey, args: unknown[],
    derived: ExecutionWindow | null): unknown {
    const admitted = this.admit(derived);
    if (admitted instanceof Error) return rejected(admitted);
    const win = admitted;
    const command = typeof name === "string" ? name : "";
    const readOnly = this.isReadOnly(owner, command, args, win);
    if (!readOnly && win.resultUnknown) {
      const mark = win.outcome?.failure ?? failure("engine_error", RESULT_UNKNOWN_MESSAGE);
      return rejected(attachClassification(new Error(AFTER_RESULT_UNKNOWN_MESSAGE), { ...mark }));
    }
    const rawArgs = args.map((a) => this.toRaw(a, win));
    const send = (): unknown => Reflect.apply(fn, owner, rawArgs);
    return readOnly ? this.readOnlyCall(send, win) : this.sideEffectCall(send, command, rawArgs, win);
  }

  /** 只读命令：经 retryReadOnce 对连接层错误码与 502 / 503 / 504 重试一次（第一次失败期间窗口已关闭、进入终结或会话已丢失则不
   *  重试）；最终的失败按只读命令归类。 */
  private async readOnlyCall(send: () => unknown, win: ExecutionWindow): Promise<unknown> {
    let value: unknown;
    try {
      value = await retryReadOnce(send, () => this.isLive(win) && !this.lost);
    } catch (e) {
      throw await this.classify(e, win, true);
    }
    return this.toUser(value, win);
  }

  /** 有副作用的命令：不重试。结果是 thenable 时立即挂上失败处理（结果未知要在失败的那一刻置位，不等使用方 await），交回的
   *  thenable 留在膜内、兑现值也进膜。 */
  private sideEffectCall(send: () => unknown, command: string, rawArgs: readonly unknown[], win: ExecutionWindow): unknown {
    let raw: unknown;
    try {
      raw = send();
    } catch (e) {
      this.noteContextFailure(command, win);
      return rejected(this.classify(e, win, false));
    }
    if (!isThenable(raw)) {
      this.noteContextSwitch(command, rawArgs, win);
      return this.toUser(raw, win);
    }
    const thenable = raw;
    let classified: Promise<Error> | null = null;
    const fail = (e: unknown): Promise<Error> => (classified ??= this.classify(e, win, false));
    // 先挂的回调先执行：上下文的记录与失败归类都发生在使用方的 await 恢复之前。这个回调本身不抛，不产生未处理的拒绝。
    thenable.then(
      () => { this.noteContextSwitch(command, rawArgs, win); },
      (e: unknown) => { this.noteContextFailure(command, win); void fail(e); },
    );
    let settled: Promise<unknown> | null = null;
    const settle = (): Promise<unknown> => (settled ??= new Promise<unknown>((resolve, reject) => {
      thenable.then((v) => resolve(this.toUser(v, win)), (e: unknown) => { fail(e).then(reject, reject); });
    }));
    return this.membrane(thenable as object, win, settle);
  }

  private noteContextSwitch(command: string, rawArgs: readonly unknown[], win: ExecutionWindow): void {
    if (CONTEXT_SWITCH_COMMANDS.has(command) && this.current === win) {
      win.context = typeof rawArgs[0] === "string" ? rawArgs[0] : null;
    }
  }

  private noteContextFailure(command: string, win: ExecutionWindow): void {
    if (CONTEXT_SWITCH_COMMANDS.has(command)) win.context = null;
  }

  private isLive(win: ExecutionWindow): boolean {
    return !this.shut && this.current === win;
  }

  /** 失败的归类（ADR 0052 决策 6；ADR 0051 决策 4）：先置结果未知（有副作用的命令遇到传输层故障，同步完成），再查一次会话状态，
   *  按结论挂标记；结果已知且查到仍为 RUNNING 时标记带 sessionRunningConfirmed。窗口已关闭（晚到的失败）时不查状态、不改任何
   *  窗口的判定。返回带标记的异常，本身不拒绝。 */
  private async classify(error: unknown, win: ExecutionWindow, readOnly: boolean): Promise<Error> {
    const existing = readClassification(error);
    if (existing !== null) return error instanceof Error ? error : attachClassification(error, existing);
    const unknown = !readOnly && isTransportFault(error);
    if (!this.isLive(win)) {
      return attachClassification(error, unknown ? failure("engine_error", RESULT_UNKNOWN_MESSAGE) : this.knownFailure(error, readOnly));
    }
    if (unknown) this.flagResultUnknown(win);
    const status = await win.queryStatus(this.sessionStatus);
    if (status !== null && status !== RUNNING) this.recordLost(win);
    if (this.lost) return attachClassification(error, lostFailure());
    if (unknown) return attachClassification(error, failure("engine_error", RESULT_UNKNOWN_MESSAGE));
    const known: StepClassification = this.knownFailure(error, readOnly);
    // 查到会话仍为 RUNNING 才带这项事实：驱动适配器只在它成立时按实测过的驱动错误文本再归类（ADR 0051 决策 4）
    return attachClassification(error, status === RUNNING ? { ...known, sessionRunningConfirmed: true } : known);
  }

  private knownFailure(error: unknown, readOnly: boolean): StepFailure {
    if (readOnly && isTimeout(error)) return failure("engine_error", READ_ONLY_TIMEOUT_MESSAGE);
    return failure("engine_error", commandFailedMessage(errorText(error)));
  }

  private flagResultUnknown(win: ExecutionWindow): void {
    win.resultUnknown = true;
    win.outcome ??= { failure: failure("engine_error", RESULT_UNKNOWN_MESSAGE), resultUnknown: true };
    win.abort(RESULT_UNKNOWN_MESSAGE);
  }

  /** 会话丢失：锁存；窗口仍打开时改写它的判定（会话丢失不再要求存活探测）并中止当前 act。 */
  private recordLost(win: ExecutionWindow): void {
    this.lost = true;
    if (this.current !== win) return;
    win.outcome = { failure: lostFailure(), resultUnknown: false };
    win.abort(SESSION_LOST_MESSAGE);
  }

  // ---- 膜 ----

  /** 执行实例一侧的值交给使用方：纯数据原样返回，函数换成守卫交出的函数，其余对象套上膜。 */
  private toUser(value: unknown, win: ExecutionWindow | null): unknown {
    if (!isObjectLike(value)) return value;
    if (this.toRawMap.has(value)) return value;
    const callback = this.wrapperToCallback.get(value);
    if (callback !== undefined) return callback;
    if (typeof value === "function") return this.guardedFunction(value as (...a: unknown[]) => unknown, undefined, "", win);
    if (isDataLeaf(value) || isPlainData(value, new Set())) return value;
    return this.membrane(value, win, null);
  }

  /** 使用方的值交给执行实例一侧：膜内对象与守卫交出的函数解包，使用方回调换成把参数套上膜的包装，含膜内对象的纯容器复制一份
   *  再解包，其余原样。 */
  private toRaw(value: unknown, win: ExecutionWindow | null, seen: Set<object> = new Set()): unknown {
    if (!isObjectLike(value)) return value;
    const raw = this.toRawMap.get(value);
    if (raw !== undefined) return raw;
    if (typeof value === "function") return this.rawCallback(value as (...a: unknown[]) => unknown, win);
    if (isDataLeaf(value) || !isPlainContainer(value) || seen.has(value)) return value;
    seen.add(value);
    let changed = false;
    const copy: Record<PropertyKey, unknown> = Array.isArray(value) ? [] as unknown as Record<PropertyKey, unknown>
      : Object.create(Object.getPrototypeOf(value)) as Record<PropertyKey, unknown>;
    for (const key of Reflect.ownKeys(value)) {
      const desc = Reflect.getOwnPropertyDescriptor(value, key);
      if (desc === undefined || !("value" in desc)) return value;
      const item = this.toRaw(desc.value, win, seen);
      if (item !== desc.value) changed = true;
      if (Array.isArray(value) && key === "length") continue;
      Object.defineProperty(copy, key, { ...desc, value: item });
    }
    return changed ? copy : value;
  }

  /** 使用方回调：WebdriverIO 调它时传进来的元素与列表先套上膜，它的返回值解包后再交回。 */
  private rawCallback(fn: (...args: unknown[]) => unknown, win: ExecutionWindow | null): (...args: unknown[]) => unknown {
    let slots = this.callbackWrappers.get(fn);
    if (slots === undefined) {
      slots = { byWindow: new WeakMap() };
      this.callbackWrappers.set(fn, slots);
    }
    const existing = win === null ? slots.none : slots.byWindow.get(win);
    if (existing !== undefined) return existing;
    const guard = this;
    const wrapper = function (this: unknown, ...rawArgs: unknown[]): unknown {
      const out = Reflect.apply(fn, guard.toUser(this, win), rawArgs.map((a) => guard.toUser(a, win)));
      return isThenable(out) ? Promise.resolve(out).then((v) => guard.toRaw(v, win)) : guard.toRaw(out, win);
    };
    if (win === null) slots.none = wrapper;
    else slots.byWindow.set(win, wrapper);
    this.wrapperToCallback.set(wrapper, fn);
    return wrapper;
  }

  /** 守卫交出的函数：每次调用都过 invoke。owner 未给时取调用时的 this 解包。 */
  private guardedFunction(fn: (...args: unknown[]) => unknown, owner: unknown, name: PropertyKey,
    derived: ExecutionWindow | null): (...args: unknown[]) => unknown {
    const guard = this;
    const wrapper = function (this: unknown, ...args: unknown[]): unknown {
      return guard.invoke(fn, owner === undefined ? guard.toRaw(this, derived) : owner, name, args, derived);
    };
    this.toRawMap.set(wrapper, fn);
    return wrapper;
  }

  /** 不算命令的成员：直接执行，返回值仍进膜。 */
  private passThrough(fn: (...args: unknown[]) => unknown, owner: object, win: ExecutionWindow | null): (...args: unknown[]) => unknown {
    return (...args: unknown[]) => this.toUser(Reflect.apply(fn, owner, args.map((a) => this.toRaw(a, win))), win);
  }

  /** 给 raw 套膜。代理的目标是一个空壳（数组对应空数组，让 Array.isArray 成立），所有操作转发给 raw，这样返回包装值不触犯代理
   *  对目标自身属性的约束。settle 只在命令调用的 thenable 结果上给出：then / catch / finally 经它兑现（含失败归类）。 */
  private membrane(raw: object, derivation: Derivation, settle: (() => Promise<unknown>) | null): object {
    const guard = this;
    const shell: object = Array.isArray(raw) ? [] : {};
    let generic: Promise<unknown> | null = null;
    const windowNow = (): ExecutionWindow | null => (derivation === ROOT ? guard.current : derivation);
    const handler: ProxyHandler<object> = {
      get(_shell, prop) {
        const win = windowNow();
        if ((prop === "then" || prop === "catch" || prop === "finally") && isThenable(raw)) {
          const thenable = raw;
          const settled = settle ?? ((): Promise<unknown> => (generic ??= new Promise<unknown>((resolve, reject) => {
            thenable.then((v) => resolve(guard.toUser(v, win)), reject);
          })));
          if (prop === "then") return (onF?: (v: unknown) => unknown, onR?: (e: unknown) => unknown) => settled().then(onF, onR);
          if (prop === "catch") return (onR?: (e: unknown) => unknown) => settled().catch(onR);
          return (onFinally?: () => void) => settled().finally(onFinally);
        }
        const value: unknown = Reflect.get(raw, prop, raw);
        // 遍历不检查令牌：交出的是膜外的生成器，逐个把元素套上膜，遍历出的元素上的命令仍受约束。遍历器本身不能进膜：它的 next
        // 不在 Object.prototype 上，会被当成命令检查令牌，旧令牌或结果未知时 next 返回被拒绝的结果，for…of 读到的 done 是真值，
        // 循环静默地一次也不执行，而不是报错。
        if (prop === Symbol.iterator && typeof value === "function") {
          const iterate = value as () => Iterator<unknown>;
          return function* () {
            const iterator = Reflect.apply(iterate, raw, []) as Iterator<unknown>;
            for (const item of { [Symbol.iterator]: () => iterator }) yield guard.toUser(item, win);
          };
        }
        if (prop === Symbol.asyncIterator && typeof value === "function") {
          const iterate = value as () => AsyncIterator<unknown>;
          return async function* () {
            const iterator = Reflect.apply(iterate, raw, []) as AsyncIterator<unknown>;
            for await (const item of { [Symbol.asyncIterator]: () => iterator }) yield guard.toUser(item, win);
          };
        }
        if (typeof value === "function") {
          const fn = value as (...args: unknown[]) => unknown;
          const nonCommand = NON_COMMAND_MEMBERS.has(prop)
            || (typeof prop === "string" && (Object.prototype as unknown as Record<string, unknown>)[prop] === value);
          return nonCommand ? guard.passThrough(fn, raw, win) : guard.guardedFunction(fn, raw, prop, win);
        }
        return guard.toUser(value, win);
      },
      set(_shell, prop, value) {
        return Reflect.set(raw, prop, guard.toRaw(value, windowNow()), raw);
      },
      has(_shell, prop) {
        return Reflect.has(raw, prop);
      },
      deleteProperty(_shell, prop) {
        return Reflect.deleteProperty(raw, prop);
      },
      ownKeys(target) {
        const keys = Reflect.ownKeys(raw);
        if (Array.isArray(target) && !keys.includes("length")) keys.push("length");
        return keys;
      },
      getOwnPropertyDescriptor(target, prop) {
        const desc = Reflect.getOwnPropertyDescriptor(raw, prop);
        const isLength = Array.isArray(target) && prop === "length";
        if (desc === undefined) return isLength ? Reflect.getOwnPropertyDescriptor(target, prop) : undefined;
        const value = guard.toUser("value" in desc ? desc.value : Reflect.get(raw, prop, raw), windowNow());
        // 空壳数组自带不可配置的 length：如实报告为不可配置；其余属性空壳上没有，只能报告为可配置。
        if (isLength) return { value, writable: true, enumerable: false, configurable: false };
        return { value, writable: desc.writable ?? false, enumerable: desc.enumerable ?? false, configurable: true };
      },
      getPrototypeOf() {
        return Reflect.getPrototypeOf(raw);
      },
    };
    const proxy = new Proxy(shell, handler);
    this.toRawMap.set(proxy, raw);
    return proxy;
  }
}

/** 为一个 Appium 会话建命令守卫。adapter 若带 readOnlyMobileCommands（见 ReadOnlyMobileCommands），其中的脚本进只读白名单。 */
export function createCommandGuard(args: CommandGuardArgs): CommandGuard {
  return new Guard(args);
}

/** 设备部件装配用的守卫工厂（surface.mts 的 GuardFactory 端口）。 */
export const commandGuardFactory: GuardFactory = {
  create: (args) => createCommandGuard(args),
};
