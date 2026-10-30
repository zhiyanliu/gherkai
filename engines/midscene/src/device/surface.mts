// 设备侧的界面接缝实现（ADR 0052 决策 2；ADR 0051 决策 4、5；ADR 0050 决策 2）：实现 worker/surface.mts 的 TargetSurface，
// run-scope 经 `await import("../device/surface.mjs")` 动态加载本模块（桌面路径与能力自述不加载，ADR 0052 决策 3）。
//
// 本模块只做编排：按固定次序调用设备模块的各块（ADR 0052 决策 3 的模块划分），把它们的结论变成接缝的返回值。各块对本模块的
// 依赖面写成下方的端口类型（DeviceParts 的各字段），由部件工厂每个 scope 装配一次（缺省装配在 device/parts.mts，测试经
// DeviceSurfaceOptions.parts 注入假部件）：
//   - Device Farm 会话块（DeviceFarmSessions）：设备解析、Create、等到 RUNNING、查状态、换台时停掉被替换的会话；本模块不碰
//     Device Farm SDK；
//   - 终结块（DeviceFinalizer）：释放的两种模式与终结四阶段（ADR 0051 决策 5），每个会话恰一条 session_closed；
//   - Appium 块（AppiumConnector、AppiumSession）：三个客户端实例、生命周期通道上的上下文读取与切换、网页上下文的重新定位；
//   - 能力探测块（CapabilityProbe）、驱动适配器（AdapterRegistry、DriverAdapter）、命令守卫（GuardFactory、CommandGuard）、
//     界面实现与 Agent（AgentFactory）、会话预热块（DeviceWarmup）；
//   - 应用启停直接用 device/app.mts 的原语，安装包存储经端口注入。
// 会话事件的线上形状只在 device/device-session.mts 组装一次，部件经传给它们的 SessionEventSink 发出（Create 返回之后、按名找回
// 孤儿时、终结时）；本模块自己不发任何事件，所以 acquire 与 warmup 期间出现的只会是 session_opened / session_closed，scope_started
// 由 run-scope 在 acquire 返回就绪（且预热通过）之后发（ADR 0051 决策 4）。
//
// 三条通道的分工（ADR 0052 决策 2「生命周期通道」、决策 6「命令守卫」）：
//   - 经命令守卫：handler 的 ctx.driver、内建导航（navigate）、Midscene 界面实现发出的命令，受执行令牌与结果未知标志约束；
//   - 生命周期通道：step 前核对、复原并核对、界面快照、scenario 前核对、获取期的应用启动、预热与终结，经 AppiumSession 的
//     生命周期成员或执行实例直接执行，不经令牌与标志；
//   - Device Farm：只经 DeviceFarmSessions 与 DeviceFinalizer。
// 命令失败的会话丢失判定一律先查会话状态（ADR 0051 决策 4「会话丢失的判定靠查状态」）：状态不是 RUNNING 即会话丢失，并锁存，
// 之后各项义务与快照不再向设备发命令。
//
// 获取预算（ADR 0052 决策 6 超时分层表 ③）：从 acquire 开始计，覆盖到 warmup 返回为止，跨换台重建不重置；预算只读
// job.deviceRequest.acquireTimeoutS（ADR 0051 决策 2）。各块经 AcquireBudget 的 signal 感知到期与进入终结，本模块在每一步之后
// 核对一次（预热返回之后也核对，预热成功也不例外）：到期的失败归 acquire_timeout（判据型的 precheck_failed 保持原归因），进入
// 终结即停、不再向设备发命令。Appium 会话建成之后抛出的未归类异常先查一次会话状态：不是 RUNNING 归 session_lost（准备阶段的
// 消息），RUNNING 或查不到归 engine_error。
//
// 执行窗口的出口（ADR 0052 决策 6「执行异常的归类由守卫带给 runStep」）：设备路径没有 network_error 出口，handler 与 AI 自己抛出、
// 没有带归类的异常在 execute 出口挂 engine_error；断言异常不挂，交 run-scope 判 failed。
//
// 释放只进入一次（ADR 0051 决策 5「终结只执行一次」）：正常释放进行中又收到中断，同一次终结升级为中断——尚未开始的 deleteSession
// 不再发出，尚未开始的正常模式诊断上传不再进行、诊断文件交给后台队列，使停止信号到退出仍落在中断路径的宽限推导之内；已在途的
// deleteSession 不打断，它的上限由终结块封顶；已在途的诊断上传同样不打断（上传器的单次超时封顶），落定之后上传失败才把诊断文件
// 交给后台队列，由停止路径的排空带上。
//
// 设备产物（原始控件树、device-session.json）落在 `<产物根>/device/<scope 键>/` 下：产物根按 run 共享，各 scope 分目录才不互相覆盖。
//
// 本模块静态 import 缺省装配，WebdriverIO 与 Device Farm SDK 因此在本模块的静态加载闭包里：镜像的设备依赖冒烟只 import 本模块
// （engines/midscene/Dockerfile），这条闭包断了冒烟就照不出依赖缺失（护栏见 surface.test.mts）。各块与本模块互相 import，
// 各块只在函数体内读本模块导出的消息常量，本模块也只在函数体内读 Appium 块导出的准备阶段会话丢失消息，两侧模块顶层都不读。
import path from "node:path";
import fs from "node:fs";
import type { Agent, AgentOpt } from "@midscene/core";
import type { Browser } from "webdriverio";
import { injectDeviceNavigate } from "../worker/deterministic.steps.mjs";
import {
  DEVICES, DeterministicAssertion, UI_KINDS, type Device, type SelectedHandler, type UiKind, type WebdriverCtx,
} from "../worker/deterministic.mjs";
import { errorText, oneLineError } from "../worker/error-text.mjs";
import { scenarioKey } from "../worker/evidence.mjs";
import { redactSecrets } from "../lib/redact.mjs";
import {
  attachClassification, readClassification,
  type AcquireResult, type AddressReading, type Controls, type HandlerCall, type ReleaseMode, type ReleaseOutcome,
  type ReportRef, type ScopeTermination, type Snapshot, type SnapshotResult, type StepFacts, type StepFailure,
  type SurfaceDeps, type TargetSurface, type TentativeVerdict,
} from "../worker/surface.mjs";
import {
  appHandle, checkAppObject, launchApp, presignAppObject,
  type AppObjectLocation, type AppObjectStore, type AppTimingDeps,
} from "./app.mjs";
import {
  CONTROLS_MAX_ITEMS, MAX_SESSION_S, PAGE_SOURCE_MAX_BYTES, REPLACE_DEVICE_MIN_REMAINING_MS, SNAPSHOT_CAPTURE_BUDGET_MS,
  replanningCycleLimit,
} from "./limits.mjs";
import {
  DEVICE_SESSION_REPORT_KIND, sessionEventSink, writeDeviceSessionFile,
  type DeviceSessionRecord, type ScaleSource, type SessionDeviceInfo, type SessionEventSink,
} from "./device-session.mjs";
import { defaultDeviceParts } from "./parts.mjs";

// ---- 给使用方看的消息（ADR 0039；ADR 给了原文整句的照原文）----

/** 获取预算耗尽（ADR 0051 决策 4 的原文）。 */
export const ACQUIRE_TIMEOUT_MESSAGE = "在等待时间内没有拿到可用设备，请稍后重试或调大获取设备的等待时间";
/** 会话丢失与会话到期（ADR 0051 决策 4 的原文）。 */
export const SESSION_LOST_MESSAGE =
  "远程访问会话在执行中途结束，本 scope 余下的 step 未执行；可缩短 scope 或检查是否有人手动停止了会话";
/** 执行前发现会话丢失（获取期的准备、能力探测、会话预热，scope_started 之前）：此时一个 step 都还没有开始，不用执行中途的那句
 *  （ADR 0051 决策 4 的消息要求：发生了什么、为什么、怎么办）。 */
export const SESSION_LOST_BEFORE_START_MESSAGE =
  "远程访问会话在准备设备时已结束，本 scope 的 step 都没有执行；请确认是否有人手动停止了会话，然后重新运行";
/** 能力探测出错时需要网页上下文的 step（ADR 0052 决策 5 的原文）。 */
export const WEB_CONTEXT_PROBE_ERROR_MESSAGE = "未能确认设备是否提供网页上下文";
/** 能力探测确认不提供网页上下文时需要它的 step（处置按 ADR 0051 决策 4 的类别表：改写为 AI 断言或换设备）。 */
export const WEB_CONTEXT_UNAVAILABLE_MESSAGE =
  "这台设备不提供网页上下文，这一步需要网页上下文才能执行；请改写为 AI 断言，或换一台设备";
/** 应用目标上调用了网页上下文（应用目标固定在原生界面执行，ADR 0052 决策 5）。 */
export const WEB_CONTEXT_ON_APP_MESSAGE = "应用目标在原生界面上执行，没有网页上下文；请改用原生界面上的操作，或改写为 AI 步";
/** step 后复原失败的后半句（ADR 0052 决策 2 第 5 步的原文）；前半句是原判定或结果未知的整句。 */
export const RESTORE_FAILED_TAIL = "之后未能切回原生界面，后续 step 的截图坐标会错位";
/** step 前核对切回原生界面失败。 */
export const PRE_STEP_FAILED_MESSAGE = "这一步开始前未能切回原生界面，没有执行这一步";
/** 结果未知之后，下一条 scenario 前的存活探测失败而会话仍在运行。 */
export const LIVENESS_FAILED_MESSAGE =
  "上一个 scenario 里有设备命令没有回应，之后设备也没有响应截图请求，本 scope 余下的 scenario 未执行；请稍后重试";
/** 换过一台设备后，新设备仍拒绝安装驱动辅助程序。 */
export const HELPER_REJECTED_AGAIN_MESSAGE =
  "设备拒绝安装执行测试所需的驱动辅助程序，换了一台设备后仍被拒绝；请换一个机型后重试";
/** 设备拒绝安装驱动辅助程序，剩余的等待时间不够再换一台。 */
export const HELPER_REJECTED_NO_TIME_MESSAGE =
  "设备拒绝安装执行测试所需的驱动辅助程序，剩余的等待时间不够再换一台设备；请调大获取设备的等待时间后重试，或换一个机型";
/** 应用目标的 job 没有带安装包的存储位置。 */
export const APP_LOCATION_MISSING_MESSAGE =
  "这个 job 没有带安装包的存储位置，无法安装被测应用；请用与 worker 同版本的命令行工具重新提交";
/** 句柄种类与目标不符（selectHandler 不会给出，防御用）。 */
export const HANDLER_KIND_MISMATCH_MESSAGE = "这一步的确定性实现只能在桌面浏览器上执行，不能在设备上执行";

/** 设备回报了没有对应驱动适配器的自动化驱动。 */
export function unsupportedDriverMessage(automationName: string): string {
  return `设备回报的自动化驱动 ${JSON.stringify(automationName)} 不受支持，无法在这台设备上执行测试；请换一台设备后重试`;
}

/** 获取期未归类的失败。 */
export function acquireErrorMessage(reason: string): string {
  return reason === "" ? "准备设备时出错" : `准备设备时出错：${reason}`;
}

/** 预热期未归类的失败（导航本身失败的归因由会话预热块给出，这里只兜住它没有归类就抛出的异常）。 */
export function warmupErrorMessage(reason: string): string {
  return reason === "" ? "会话预热时出错" : `会话预热时出错：${reason}`;
}

/** 内建导航在设备上失败、且失败方没有给出归类。 */
export function navigateErrorMessage(reason: string): string {
  return reason === "" ? "未能打开地址" : `未能打开地址：${reason}`;
}

/** step 后复原失败时的整句：原判定为 passed / failed 时以「原判定为 …」开头；原判定已是 error（如结果未知）时以它的消息开头。 */
export function restoreFailedMessage(tentative: TentativeVerdict): string {
  if (tentative.status === "error" && tentative.message) return `${tentative.message}；${RESTORE_FAILED_TAIL}`;
  return `原判定为 ${tentative.status}；${RESTORE_FAILED_TAIL}`;
}

// ---- 设备 Agent 的构造项（ADR 0044 决策 2；ADR 0052 决策 6）----

/** 设备 Agent 的构造项：在两种 Agent 共用的构造项上加重规划上限。取值只经 limits 的 replanningCycleLimit（缺省值、覆盖键
 *  MIDSCENE_REPLANNING_CYCLE_LIMIT 的读法与非法值的报错都在那里，与 worker 启动期的校验同一份）；设备路径必须自己读这个键并经
 *  构造项传入，因为 SDK 的取值顺序是构造项优先于 env。桌面不经这里，SDK 按同名 env 自行处理。 */
export function deviceAgentOpts(base: AgentOpt, env: NodeJS.ProcessEnv = process.env): AgentOpt {
  return { ...base, replanningCycleLimit: replanningCycleLimit(env) };
}

// ---- 端口：各设备模块对本模块提供的面 ----

/** 获取预算：signal 在预算到期或进入终结时中止，各块把它传给每次调用，停止信号由此穿透；remainingMs 供 newSession 封顶与
 *  换台条件判断。 */
export interface AcquireBudget {
  readonly signal: AbortSignal;
  remainingMs(): number;
}

/** 部件给出的结论：继续，或执行前失败的 scope 级终止。 */
export type Outcome<T> = { ok: true; value: T } | { ok: false; termination: ScopeTermination };

/** 设备解析的结果。model 与系统版本取自 Device Farm 的设备描述（设备选择输入），只用于诊断与 session_opened.device。 */
export interface DeviceChoice {
  deviceArn: string;
  model: string | null;
  osVersion: string | null;
}

/** 建好的远程访问会话。 */
export interface RemoteSession {
  arn: string;
  /** 这次 Create 请求携带的会话名（session-name 模块编码）。 */
  name: string;
  /** 发出 Create 的时刻（与 now() 同一时钟，毫秒）：会话年龄的起点（ADR 0051 决策 2）。 */
  createRequestedAt: number;
  /** 与 session_opened.device 相同的设备描述。 */
  device: SessionDeviceInfo;
}

/** 到达 RUNNING 的会话。 */
export interface RunningSession {
  /** Appium 端点。它是凭证：只交给建连，不进事件、日志与诊断（ADR 0051 决策 11）。 */
  endpoint: string;
  /** RUNNING 之后才可能有的设备单元（instanceArn）；有值时覆盖建会话时的取值记入诊断。 */
  unit: string | null;
}

/** Device Farm 会话块对本模块的面。 */
export interface DeviceFarmSessions {
  /** 设备解析（ADR 0051 决策 3）：零候选重列一次仍为零、指定 ARN 被同步拒绝时返回 precheck_failed；全部繁忙时在预算内等待。
   *  replacing 非 null 表示为换台重新解析，传被替换的会话。 */
  resolve(budget: AcquireBudget, replacing: RemoteSession | null): Promise<Outcome<DeviceChoice>>;
  /** Create：限流与机型繁忙在预算内重试，每次请求一个新尝试序号，结果未知的请求登记为待核；重试前按名找回的会话逐会话、与剩余
   *  分页并行按 Stop 规则停止（接预算的信号），这次核对返回、这些处理都结束才发下一次 Create；Create 返回 ARN 后、本调用返回之前
   *  经会话事件出口发 session_opened(created)。 */
  create(choice: DeviceChoice, budget: AcquireBudget): Promise<Outcome<RemoteSession>>;
  /** 等到状态为 RUNNING 且端点可用；就绪之前已是 STOPPING / COMPLETED 即返回 session_lost 的终止（准备阶段那句消息），状态细节只进日志。 */
  waitRunning(session: RemoteSession, budget: AcquireBudget): Promise<Outcome<RunningSession>>;
  /** 查一次会话状态（GetRemoteAccessSession 的状态值）；查询本身失败返回 null，调用方此时不据此判会话丢失。 */
  status(arn: string): Promise<string | null>;
  /** 换台：被替换的会话按终结释放阶段的 Stop 规则处理（ADR 0051 决策 5）：先 Get，STOPPING / COMPLETED 即确认；其余状态或 Get
   *  失败时发一次 Stop，Stop 报错或返回体不是这两个状态时补查一次 Get。不重试、不等到确认：仍未确认的由终结再处理，它的
   *  session_closed 也归终结，每个会话恰一条。 */
  retire(arn: string): Promise<void>;
}

/** newSession 的请求：端点、目标与应用信息。能力集由 Appium 块单点组装（ADR 0052 决策 3）。 */
export interface ConnectRequest {
  endpoint: string;
  device: Device;
  uiKind: UiKind;
  /** 包名或 bundle id，只在应用目标上有值。 */
  appId: string | null;
  /** 安装包的预签名地址（应用目标），网页目标为 null。凭证，不进日志与诊断。 */
  appUrl: string | null;
}

/** 建连结果：建好、设备单元拒装驱动辅助包（换不换台由本模块按剩余预算决定）、或执行前失败。 */
export type ConnectOutcome =
  | { kind: "connected"; session: AppiumSession }
  | { kind: "replace_device"; reason: string }
  | { kind: "terminated"; termination: ScopeTermination };

/** Appium 块的建连面：newSession 的单请求超时取下限与剩余预算的较小者（封顶优先）；未封顶的瞬时失败在
 *  预算允许时只重试 newSession 一次；被封顶的客户端超时与预算不够重试时归 acquire_timeout（ADR 0051 决策 3）。 */
export interface AppiumConnector {
  connect(req: ConnectRequest, budget: AcquireBudget): Promise<ConnectOutcome>;
}

/** 为 evidence 读网页地址的结果：读到的地址，或读不到的原因（多候选、零候选与出错为 error，超时为 timeout）。 */
export type AddressAttempt = { url: string } | { missing: "timeout" | "error" };

/** 建好的 Appium 会话。生命周期成员不经命令守卫；带 driver 参数的成员把命令经传入的守卫代理发出。 */
export interface AppiumSession {
  /** 执行实例：只交给命令守卫、获取期的应用启动与生命周期通道，不交给 handler。 */
  readonly exec: Browser;
  /** 会话回报的 automationName（选驱动适配器用）。 */
  readonly automationName: string;
  /** 会话能力对象回报的系统版本（唯一读取点在 Appium 块）；没有时为 null。 */
  readonly platformVersion: string | null;
  /** 生命周期通道：读一次当前上下文。 */
  currentContext(): Promise<string>;
  /** 生命周期通道：切回原生上下文。 */
  switchToNative(): Promise<void>;
  /** 生命周期通道：经探测实例在原生上下文截图，受探测客户端的短超时约束（scenario 前的存活探测）；连接层错误与 502 / 503 / 504
   *  重试一次，超时与 500 不重试。 */
  probeScreenshot(): Promise<void>;
  /** 生命周期通道：原生上下文的 page source，受传入的截止信号约束；连接层错误与 502 / 503 / 504 在信号未中止时重试一次。 */
  pageSource(signal: AbortSignal): Promise<string>;
  /** 生命周期通道：重新定位网页上下文（只有一个候选才采用）、读地址、切回原生上下文；只在能力结论为「提供」时调用。列上下文与
   *  读地址各按只读原语重试一次，切入不重试。 */
  readWebAddress(signal: AbortSignal): Promise<AddressAttempt>;
  /** ctx.withWebContext：重新定位、切入执行 fn、结束后切回原生；多候选或零候选抛出带 engine_error 标记的异常。 */
  withWebContext<T>(driver: Browser, fn: () => Promise<T> | T): Promise<T>;
  /** 网页目标且能力结论为「提供」时的导航：重新定位后在网页上下文打开地址。 */
  openUrl(driver: Browser, address: string): Promise<void>;
  /** 正常收尾的 deleteSession（5 秒，不重试，ADR 0051 决策 5）。 */
  deleteSession(): Promise<void>;
}

/** 网页上下文的探测结论（ADR 0052 决策 5）。 */
export type WebContextVerdict = "available" | "unavailable" | "probe_error";

/** 能力探测的结论：只缓存结论，不缓存句柄。 */
export interface ProbeConclusion {
  /** 网页目标的网页上下文结论；应用目标不探测，为 null。 */
  webContext: WebContextVerdict | null;
  /** 最后一次列出的网页上下文候选数（诊断用）；没有列过为 null。 */
  webContextCandidates: number | null;
  /** iOS 取活动元素的上下文；Android 固定 mobile 输入命令，为 null。 */
  inputContext: "web" | "native" | null;
  /** 坐标比例：iOS 为点与像素之比，Android 恒为 1。 */
  scale: number;
  scaleSource: ScaleSource;
  /** /status 回报的 Appium 版本，只记诊断。 */
  appiumVersion: string | null;
}

/** 能力探测块：建连后、预热前执行一次。单项失败记为结论「探测出错」，比例回退后仍无法确定是执行前失败
 *  （engine_error「无法确定坐标比例」），探测中发现会话丢失归 session_lost：命令失败时经 sessionStatus 查一次当前远程访问会话的
 *  状态（绑定到当前会话 ARN；查询失败返回 null 或抛出，此时不据此判会话丢失，ADR 0051 决策 4）。 */
export interface CapabilityProbe {
  run(
    session: AppiumSession, target: { device: Device; uiKind: UiKind }, budget: AcquireBudget,
    sessionStatus: () => Promise<string | null>,
  ): Promise<Outcome<ProbeConclusion>>;
}

/** 驱动适配器对本模块的面；按会话回报的 automationName 选一次。界面实现要用的完整面（原语、系统键、只读命令集合）是它的子类型，
 *  经下面几个端口的类型参数 A 从适配器清单原样交到界面实现块，本模块只用这两个成员。 */
export interface DriverAdapter {
  /** 经 DeepLink 打开地址：网页目标交给系统浏览器（appId 为 null），应用目标交给被测应用（带包名或 bundle id）。失败抛出带归类
   *  标记的异常（地址字符校验不过、无法解析 Intent、设备不支持打开地址归 capability_unavailable；前台不是被测应用归
   *  engine_error）。设备不支持打开地址的结论由适配器缓存到本会话。 */
  deepLink(driver: Browser, address: string, appId: string | null): Promise<void>;
  /** 从原始控件树抽取控件摘要，只在 failed / error step 上调用。 */
  extractControls(pageSource: string): Controls;
}

export interface AdapterRegistry<A extends DriverAdapter = DriverAdapter> {
  /** 按 automationName 选适配器；没有对应的返回 null。 */
  select(automationName: string): A | null;
}

/** 执行窗口结束时守卫交回的判定：窗口内发生过的结果未知或会话丢失。 */
export interface WindowOutcome {
  failure: StepFailure;
  /** true 表示结果未知且会话仍在运行（下一条 scenario 前要做存活探测）。 */
  resultUnknown: boolean;
}

/** 命令守卫：会话级的 driver 代理与执行令牌。 */
export interface CommandGuard {
  /** 交给 handler、内建导航与界面实现的唯一 driver。 */
  readonly driver: Browser;
  /** 发出本 step 的执行令牌，并绑定本次 act 的中止控制（结果未知时守卫中止它）。 */
  openWindow(act: AbortController): void;
  /** 撤销令牌，返回窗口内的判定；没有发生结果未知或会话丢失时为 null。 */
  closeWindow(): WindowOutcome | null;
  /** 进入终结：立即撤销令牌、中止当前 act，此后经代理的命令一律被拒。 */
  shutdown(): void;
}

export interface GuardFactory {
  create(args: { exec: Browser; adapter: DriverAdapter; sessionStatus: () => Promise<string | null> }): CommandGuard;
}

/** 界面实现块：AppiumInterface 与设备 Agent 的构造，原语经适配器与守卫代理下发。adapter 是适配器清单选出的同一个实例；scale 与
 *  inputContext 取能力探测的结论（iOS 取活动元素的上下文，Android 为 null，ADR 0052 决策 5）。create 写成函数类型的属性而不是
 *  方法：参数按逆变规则严格核对，实现要的参数端口没给（如输入上下文）在编译期即报错，方法写法的双变核对会放过它。 */
export interface AgentFactory<A extends DriverAdapter = DriverAdapter> {
  create: (args: {
    driver: Browser; adapter: A; session: AppiumSession; device: Device; scale: number;
    inputContext: ProbeConclusion["inputContext"]; opts: AgentOpt;
  }) => Agent;
}

/** 会话预热块：按路线导航预热地址一次并在原生控件树里确认标记（ADR 0051 决策 13）。命令失败时经 sessionStatus 查一次当前远程
 *  访问会话的状态，不是 RUNNING 即 session_lost（与能力探测的同名参数同义）。url 路线就绪后离开到 about:blank：离开导航返回之后
 *  先核 budget.signal，已中止（预算到期或进入终结）即不再切换上下文。返回 null 之后本模块仍核一次获取预算：预热期间预算用尽的，
 *  即使标记已就绪也归 acquire_timeout。 */
export interface DeviceWarmup {
  run(args: {
    session: AppiumSession; adapter: DriverAdapter; route: "url" | "deep_link"; url: string; budget: AcquireBudget;
    sessionStatus: () => Promise<string | null>;
  }): Promise<ScopeTermination | null>;
}

/** 终结块的钩子：Appium 会话已建成时给出 deleteSession，正常模式下远程访问会话不是 STOPPING /
 *  COMPLETED 时先调它；中断模式不给。正常模式的终结进行中升级为中断时，钩子在被调用的那一刻核对，已升级即直接返回、不发命令。 */
export interface FinalizeHooks {
  deleteAppiumSession: (() => Promise<void>) | null;
}

/** 终结块：normal 为正常收尾、执行前失败与 scope 级终止的出口（deleteSession、终结核对、释放），interrupt 为停止信号与进程级
 *  异常（等在途 Create、终结核对、释放）。为每个会话经会话事件出口发恰一条 session_closed，待核尝试发一对 attempted；
 *  releaseFailed 为真表示有会话未能确认停止或有 attempted 尝试（ADR 0051 决策 5）。只进入一次：正常模式进行中收到中断时不重新进入，
 *  由钩子跳过尚未开始的 deleteSession（见 FinalizeHooks）。 */
export interface DeviceFinalizer {
  finalize(mode: ReleaseMode, hooks: FinalizeHooks): Promise<{ releaseFailed: boolean }>;
}

/** 一次装配得到的全部部件。sessions 与 finalizer 共享同一份会话登记（待清理集与待核尝试）。A 是适配器清单给出的适配器类型，
 *  适配器清单与界面实现块对它取同一个类型。 */
export interface DeviceParts<A extends DriverAdapter = DriverAdapter> {
  sessions: DeviceFarmSessions;
  finalizer: DeviceFinalizer;
  appium: AppiumConnector;
  probe: CapabilityProbe;
  adapters: AdapterRegistry<A>;
  guards: GuardFactory;
  agents: AgentFactory<A>;
  warmup: DeviceWarmup;
  appStore: AppObjectStore;
}

/** 部件工厂收到的环境。 */
export interface DevicePartsEnv {
  job: SurfaceDeps["job"];
  log: (line: string) => void;
  /** 会话事件的唯一出口（形状与去重见 device/device-session.mts）。 */
  events: SessionEventSink;
  now: () => number;
  /** 部件读 worker 自定的 env 键（本次运行编号 RUN_ID 等）时的来源：接缝构造项的 env，缺省为进程 env；这类键部件不另读 process.env。AWS SDK 的区域与凭证解析仍按 SDK 惯例读进程 env（如安装包存储的 AWS_REGION）。 */
  processEnv: NodeJS.ProcessEnv;
}

export type DevicePartsFactory<A extends DriverAdapter = DriverAdapter> = (env: DevicePartsEnv) => DeviceParts<A>;

/** 进程级兜底要挂的两个事件（缺省为 process，测试注入）。 */
export interface ProcessEvents {
  on(event: "unhandledRejection" | "uncaughtException", listener: (reason: unknown) => void): unknown;
  off(event: "unhandledRejection" | "uncaughtException", listener: (reason: unknown) => void): unknown;
}

/** createDeviceSurface 的可选参数，只供测试注入（接缝契约允许实现另带这类参数）。 */
export interface DeviceSurfaceOptions {
  /** 缺省为 device/parts.mts 的 defaultDeviceParts。 */
  parts?: DevicePartsFactory;
  now?: () => number;
  /** 重规划上限的覆盖键与部件读的 env（DevicePartsEnv.processEnv）都取这里，缺省为进程 env。 */
  env?: NodeJS.ProcessEnv;
  processEvents?: ProcessEvents;
  /** 应用启动采样的等待（device/app.mts 的 AppTimingDeps）。 */
  appTiming?: AppTimingDeps;
}

// ---- 构造 ----

/** 设备侧接缝的构造函数（导出名由 worker/surface.mts 的 DeviceSurfaceModule 固定）。只组装、不做 I/O；目标不是设备、缺设备
 *  请求、重规划上限的覆盖值非法或缺本次运行编号时同步抛出。 */
export function createDeviceSurface(deps: SurfaceDeps, options: DeviceSurfaceOptions = {}): TargetSurface {
  const { job } = deps;
  const device = job.target.device;
  const uiKind = job.target.uiKind;
  if (!(DEVICES as readonly string[]).includes(device) || !(UI_KINDS as readonly string[]).includes(uiKind)) {
    throw new Error(`这个 job 的测试目标不是移动设备（设备 ${JSON.stringify(device)}，界面类型 ${JSON.stringify(uiKind)}）`);
  }
  if (job.deviceRequest === null) throw new Error("这个 job 是移动设备目标，却没有带获取设备的请求");
  const processEnv = options.env ?? process.env;
  const agentOpts = deviceAgentOpts(deps.agentOpts, processEnv);
  const now = options.now ?? Date.now;
  const events = sessionEventSink(job.scope.id, deps.emit);
  const env: DevicePartsEnv = { job, log: deps.log, events, now, processEnv };
  const cfg: SurfaceConfig = {
    device: device as Device, uiKind: uiKind as UiKind, agentOpts, now,
    processEvents: options.processEvents ?? process, appTiming: options.appTiming ?? {},
  };
  // 两个分支各自推出适配器类型：缺省装配的适配器是界面实现要的完整面，注入的假部件是端口的最小面。
  return options.parts ? new DeviceSurface(deps, options.parts(env), cfg) : new DeviceSurface(deps, defaultDeviceParts(env), cfg);
}

// ---- 实现 ----

const NATIVE_CONTEXT = "NATIVE_APP";
// setTimeout 的延时上限（约 24.8 天），会话年龄还很远时计时器取它；8880 秒的会话上限远在其内，只防无会话时的无穷大。
const MAX_TIMER_MS = 2 ** 31 - 1;
const RUNNING = "RUNNING";
const PAGE_SOURCE_DIR = "page-source";

interface SurfaceConfig {
  device: Device;
  uiKind: UiKind;
  agentOpts: AgentOpt;
  now: () => number;
  processEvents: ProcessEvents;
  appTiming: AppTimingDeps;
}

/** 就绪之后才有的状态，一次定下。 */
interface ReadyState<A extends DriverAdapter> {
  appium: AppiumSession;
  conclusion: ProbeConclusion;
  adapter: A;
  guard: CommandGuard;
  ctx: WebdriverCtx;
}

/** 获取预算的实现：到期或 abort() 时中止 signal；stop() 只清计时器、不中止。 */
class Budget implements AcquireBudget {
  private readonly controller = new AbortController();
  private readonly deadline: number;
  private timer: ReturnType<typeof setTimeout> | null;

  constructor(totalMs: number, private readonly now: () => number) {
    this.deadline = now() + totalMs;
    // 不 unref：获取期内这是一条真实的截止线，进程不能在它之前因事件循环清空而退出。就绪、执行前失败或进入终结时清掉。
    this.timer = setTimeout(() => this.controller.abort(new Error(ACQUIRE_TIMEOUT_MESSAGE)), Math.max(0, totalMs));
  }

  get signal(): AbortSignal { return this.controller.signal; }

  remainingMs(): number { return Math.max(0, this.deadline - this.now()); }

  /** 预算是否已用尽（按截止时刻判，不受进入终结时的中止影响）。 */
  expired(): boolean { return this.remainingMs() <= 0; }

  abort(): void { this.stop(); this.controller.abort(new Error("finalizing")); }

  stop(): void {
    if (this.timer !== null) { clearTimeout(this.timer); this.timer = null; }
  }
}

function emptyRecord(target: { device: string; uiKind: string; appId: string | null }): DeviceSessionRecord {
  return {
    target: { device: target.device, ui_kind: target.uiKind, app_id: target.appId },
    session: null,
    replaced_sessions: [],
    automation_name: null,
    probe: null,
    timings: {
      acquire_started_at: null, session_created_at: null, session_running_at: null, appium_connected_at: null,
      probe_done_at: null, ready_at: null, warmup_done_at: null, released_at: null,
    },
    acquire_failure: null,
    release_failed: null,
  };
}

function reasonOf(e: unknown): string {
  return oneLineError(e instanceof Error ? e.message : e);
}

/** 断言异常：与 run-scope 判 failed 的条件逐项相同（DeterministicAssertion，或 name 为 AssertionError 的抛出物，ADR 0022）。 */
function isAssertion(e: unknown): boolean {
  if (e instanceof DeterministicAssertion) return true;
  return typeof e === "object" && e !== null && (e as { name?: unknown }).name === "AssertionError";
}

/** 执行窗口出口上 handler 与 AI 自己抛出的异常：已带归类的与断言异常原样返回，其余挂 engine_error，消息即异常文本（与不带标记时
 *  run-scope 写进 step_done 的那句相同）。设备路径没有 network_error 出口：连接层错误在设备上意味着结果未知或会话丢失，那两种归类
 *  由守卫给出，这里不交给瞬时网络判定（ADR 0052 决策 6）。 */
function executionFailure(e: unknown): unknown {
  if (readClassification(e) !== null || isAssertion(e)) return e;
  return attachClassification(e, { errorType: "engine_error", message: errorText(e) });
}

/** 原始控件树按 UTF-8 字节截断，不切断多字节字符。 */
function truncateUtf8(text: string, maxBytes: number): { bytes: Buffer; truncated: boolean } {
  const all = Buffer.from(text, "utf-8");
  if (all.length <= maxBytes) return { bytes: all, truncated: false };
  let end = maxBytes;
  while (end > 0 && (all[end] & 0xc0) === 0x80) end--;  // 退到字符起始字节
  return { bytes: all.subarray(0, end), truncated: true };
}

/** 原始控件树的写盘出口（ADR 0051 决策 8、11）：先经 redactSecrets 脱敏，再按 PAGE_SOURCE_MAX_BYTES 截断、不切断多字节字符；
 *  父目录不存在即创建，写盘失败原样抛出。次序不能反：先截断会把截断点上的凭据切成脱敏规则认不出的片段（如没有 `@` 的半截
 *  userinfo）写进文件。 */
export function writePageSourceFile(file: string, source: string): { truncated: boolean } {
  const { bytes, truncated } = truncateUtf8(redactSecrets(source), PAGE_SOURCE_MAX_BYTES);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, bytes);
  return { truncated };
}

class DeviceSurface<A extends DriverAdapter> implements TargetSurface {
  private readonly appId: string | null;
  private readonly record: DeviceSessionRecord;
  private budget: Budget | null = null;
  private acquireStarted = false;
  private remote: RemoteSession | null = null;
  private ready: ReadyState<A> | null = null;
  /** 锁存的会话丢失：一旦判定，各项义务与快照不再向设备发命令。 */
  private lost: StepFailure | null = null;
  /** Appium 会话一建成即记下：就绪之前的执行前失败（含未归类的异常）由正常收尾先 deleteSession（ADR 0051 决策 5）。 */
  private connectedAppium: AppiumSession | null = null;
  /** 本 scenario 发生过结果未知（守卫的标志只在 step 内有效，这里另记一份 scenario 级的，ADR 0052 决策 2）。 */
  private resultUnknownInScenario = false;
  private currentAct: AbortController | null = null;
  /** 本 step evidence 采集的截止时刻：读地址、控件摘要与原始控件树共用一段独立短预算（ADR 0051 决策 8）。 */
  private captureDeadline: number | null = null;
  private pageSourceSeq = 0;
  private releasing: Promise<ReleaseOutcome> | null = null;
  private finalizing = false;
  /** 收到过中断模式的释放（含正常释放进行中到达的那次）：已升级即跳过尚未开始的 deleteSession 与正常模式的诊断上传。 */
  private interruptRequested = false;
  private undoNavigate: (() => void) | null = null;
  private processHooked = false;
  private readonly onProcessFault = (reason: unknown): void => {
    this.deps.log(`worker: 出现未处理的异常，开始释放远程访问会话：${errorText(reason)}`);
    this.deps.requestFinalization();
  };

  constructor(private readonly deps: SurfaceDeps, private readonly parts: DeviceParts<A>, private readonly cfg: SurfaceConfig) {
    this.appId = cfg.uiKind === "app" ? (deps.job.target.app?.appId ?? null) : null;
    this.record = emptyRecord({ device: cfg.device, uiKind: cfg.uiKind, appId: this.appId });
  }

  sessionId(): string | null {
    return this.remote?.arn ?? null;
  }

  // ---- 取 agent ----

  async acquire(): Promise<AcquireResult> {
    if (this.acquireStarted) throw new Error("acquire 在一个 scope 里只调用一次");
    this.acquireStarted = true;
    this.hookProcessFaults();
    const request = this.deps.job.deviceRequest!;
    const budget = new Budget(request.acquireTimeoutS * 1000, this.cfg.now);
    this.budget = budget;
    this.record.timings.acquire_started_at = this.isoNow();
    let result: Outcome<Agent>;
    try {
      result = await this.acquireSteps(budget);
    } catch (e) {
      result = { ok: false, termination: await this.unclassifiedPreparationFailure(e, budget, acquireErrorMessage) };
    }
    if (!result.ok) {
      budget.stop();
      const termination = this.budgetAware(result.termination, budget);
      this.record.acquire_failure = { error_type: termination.errorType, message: termination.message };
      return { ready: false, termination };
    }
    return { ready: true, agent: result.value, sessionId: this.remote!.arn };
  }

  private async acquireSteps(budget: Budget): Promise<Outcome<Agent>> {
    const { sessions } = this.parts;
    const target = { device: this.cfg.device, uiKind: this.cfg.uiKind };
    // 1. 应用目标：建会话之前做安装包的存在性检查，缺包或无权时 Create 零调用（ADR 0051 决策 9）。
    let appLocation: AppObjectLocation | null = null;
    if (this.cfg.uiKind === "app") {
      const app = this.deps.job.target.app;
      if (!app || !app.bucket || !app.key || !app.appId) {
        return { ok: false, termination: { errorType: "precheck_failed", message: APP_LOCATION_MISSING_MESSAGE } };
      }
      appLocation = { bucket: app.bucket, key: app.key };
      const missing = await checkAppObject(this.parts.appStore, appLocation, budget.signal);
      if (missing) return { ok: false, termination: missing };
    }
    // 2. 解析、Create、等到 RUNNING、newSession；设备单元拒装驱动辅助包时至多换台一次（ADR 0051 决策 3）。
    let replacing: RemoteSession | null = null;
    let appium: AppiumSession;
    for (;;) {
      const expired = this.expiredOutcome(budget);
      if (expired) return expired;
      const choice = await sessions.resolve(budget, replacing);
      if (!choice.ok) return choice;
      const created = await sessions.create(choice.value, budget);
      if (!created.ok) return created;
      this.remote = created.value;
      this.record.session = { arn: created.value.arn, name: created.value.name, device: { ...created.value.device } };
      this.record.timings.session_created_at = this.isoNow();
      const afterCreate = this.expiredOutcome(budget);
      if (afterCreate) return afterCreate;
      const running = await sessions.waitRunning(created.value, budget);
      if (!running.ok) return running;
      this.record.timings.session_running_at = this.isoNow();
      if (running.value.unit !== null && this.record.session) this.record.session.device.unit = running.value.unit;
      const afterRunning = this.expiredOutcome(budget);
      if (afterRunning) return afterRunning;
      const appUrl = appLocation ? await presignAppObject(this.parts.appStore, appLocation) : null;
      const connected = await this.parts.appium.connect(
        { endpoint: running.value.endpoint, device: this.cfg.device, uiKind: this.cfg.uiKind, appId: this.appId, appUrl },
        budget,
      );
      if (connected.kind === "terminated") return { ok: false, termination: connected.termination };
      if (connected.kind === "replace_device") {
        if (replacing !== null) {
          return { ok: false, termination: { errorType: "precheck_failed", message: HELPER_REJECTED_AGAIN_MESSAGE } };
        }
        if (budget.remainingMs() < REPLACE_DEVICE_MIN_REMAINING_MS) {
          return { ok: false, termination: { errorType: "precheck_failed", message: HELPER_REJECTED_NO_TIME_MESSAGE } };
        }
        this.deps.log(`worker: 设备拒绝安装驱动辅助程序，换一台设备重新建立会话：${oneLineError(connected.reason)}`);
        this.record.replaced_sessions.push({ arn: created.value.arn, name: created.value.name, reason: connected.reason });
        await sessions.retire(created.value.arn);
        replacing = created.value;
        continue;
      }
      appium = connected.session;
      this.connectedAppium = appium;
      break;
    }
    this.record.timings.appium_connected_at = this.isoNow();
    this.record.automation_name = appium.automationName;
    // 3. 应用目标：显式启动并采样，回到「未运行」即启动即自退（ADR 0051 决策 9、14）。获取期还没有执行令牌，经执行实例；
    //    启动原语收到预算信号，到期或进入终结之后不再发命令。命令失败抛出，由 acquire 的兜底先查会话状态再归类；因信号中止而抛出的
    //    （预算到期或进入终结）不查会话状态，分别归 acquire_timeout 与不被使用的 engine_error。
    if (this.appId !== null) {
      const beforeLaunch = this.expiredOutcome(budget);
      if (beforeLaunch) return this.connectedFailure(appium, beforeLaunch.termination);
      const selfExit = await launchApp(appium.exec, this.appId, this.cfg.appTiming, budget.signal);
      if (selfExit) return this.connectedFailure(appium, selfExit);
    }
    const afterLaunch = this.expiredOutcome(budget);
    if (afterLaunch) return this.connectedFailure(appium, afterLaunch.termination);
    // 4. 能力探测（ADR 0052 决策 5）。会话状态的查询绑定到当前会话 ARN（换台后是新的那个）。
    const arn = this.remote!.arn;
    const sessionStatus = (): Promise<string | null> => this.parts.sessions.status(arn);
    const probed = await this.parts.probe.run(appium, target, budget, sessionStatus);
    if (!probed.ok) return this.connectedFailure(appium, probed.termination);
    const conclusion = probed.value;
    this.record.probe = {
      web_context: conclusion.webContext ?? "not_applicable",
      web_context_candidates: conclusion.webContextCandidates,
      input_context: conclusion.inputContext,
      scale: conclusion.scale,
      scale_source: conclusion.scaleSource,
      appium_version: conclusion.appiumVersion,
    };
    this.record.timings.probe_done_at = this.isoNow();
    // 5. 适配器、守卫、界面实现与 Agent。进入终结之后再建的守卫不会被撤销、注入的导航也不会被撤回，所以这里先核对一次。
    const beforeReady = this.expiredOutcome(budget);
    if (beforeReady) return this.connectedFailure(appium, beforeReady.termination);
    const adapter = this.parts.adapters.select(appium.automationName);
    if (adapter === null) {
      return this.connectedFailure(appium, { errorType: "engine_error", message: unsupportedDriverMessage(appium.automationName) });
    }
    const guard = this.parts.guards.create({ exec: appium.exec, adapter, sessionStatus });
    const agent = this.parts.agents.create({
      driver: guard.driver, adapter, session: appium, device: this.cfg.device, scale: conclusion.scale,
      inputContext: conclusion.inputContext, opts: this.cfg.agentOpts,
    });
    this.ready = { appium, conclusion, adapter, guard, ctx: this.handlerCtx(guard, conclusion, appium) };
    this.undoNavigate = injectDeviceNavigate((address) => this.navigate(address));
    this.record.timings.ready_at = this.isoNow();
    this.deps.log(this.readyLogLine(appium, conclusion));
    return { ok: true, value: agent };
  }

  /** Appium 会话已建成之后的执行前失败。 */
  private connectedFailure(appium: AppiumSession, termination: ScopeTermination): Outcome<Agent> {
    this.connectedAppium = appium;
    return { ok: false, termination };
  }

  /** 每一步之后的核对：进入终结即停（这个结果不会被使用，终结路径不发 scope_done），预算到期归 acquire_timeout。 */
  private expiredOutcome(budget: Budget): { ok: false; termination: ScopeTermination } | null {
    if (this.finalizing) return { ok: false, termination: { errorType: "engine_error", message: acquireErrorMessage("") } };
    return budget.expired() ? { ok: false, termination: { errorType: "acquire_timeout", message: ACQUIRE_TIMEOUT_MESSAGE } } : null;
  }

  /** 预算到期时，非判据型的失败一律归 acquire_timeout（判据型的 precheck_failed 保持原归因）。 */
  private budgetAware(termination: ScopeTermination, budget: Budget): ScopeTermination {
    if (termination.errorType !== "precheck_failed" && budget.expired()) {
      return { errorType: "acquire_timeout", message: ACQUIRE_TIMEOUT_MESSAGE };
    }
    return termination;
  }

  /** 获取期（含会话预热）抛出而未归类的失败（ADR 0052 决策 6：不进 network_error）。Appium 会话建成之后的（应用启动与启动采样经
   *  执行实例发出的命令、各块没有归类就抛出的异常）先查一次会话状态：不是 RUNNING 归 session_lost，RUNNING 或查不到归 engine_error，
   *  消息由 describe 按所在阶段给出（ADR 0051 决策 4「会话丢失的判定靠查状态」）。获取期的会话丢失一律用准备阶段的消息，异常上
   *  带来的消息是执行中途的口径、不沿用。 */
  private async unclassifiedPreparationFailure(
    e: unknown, budget: Budget, describe: (reason: string) => string,
  ): Promise<ScopeTermination> {
    if (budget.expired()) return { errorType: "acquire_timeout", message: ACQUIRE_TIMEOUT_MESSAGE };
    const lostBeforeStart: ScopeTermination = { errorType: "session_lost", message: SESSION_LOST_BEFORE_START_MESSAGE };
    if (readClassification(e)?.errorType === "session_lost") return lostBeforeStart;
    // 进入终结时预算被中止、在途调用随之失败：这个结果不会被使用（终结路径不发 scope_done），不另记日志、不再查状态。
    if (this.finalizing) return { errorType: "engine_error", message: acquireErrorMessage("") };
    if (this.connectedAppium !== null && await this.sessionEnded(e)) return lostBeforeStart;
    this.deps.log(`worker: ${describe("")}：${errorText(e)}`);
    return { errorType: "engine_error", message: describe(reasonOf(e)) };
  }

  private readyLogLine(appium: AppiumSession, c: ProbeConclusion): string {
    const dev = this.remote!.device;
    const deviceText = [dev.platform, dev.model, dev.osVersion].filter((v) => v).join(" ");
    const web = c.webContext === null ? "不适用（应用目标）"
      : c.webContext === "available" ? "提供" : c.webContext === "unavailable" ? "不提供" : "探测出错";
    const candidates = c.webContextCandidates === null ? "" : `，候选 ${c.webContextCandidates} 个`;
    const scaleFrom = c.scaleSource === "device_screen_info" ? "取自设备屏幕信息"
      : c.scaleSource === "page_source" ? "由截图与原生控件树根节点的尺寸换算" : "固定值";
    return `worker: 设备已就绪：${deviceText}；自动化驱动 ${appium.automationName}；网页上下文 ${web}${candidates}；` +
      `坐标比例 ${c.scale}（${scaleFrom}）；Appium ${c.appiumVersion ?? "版本未知"}`;
  }

  // ---- 预热 ----

  async warmup(url: string): Promise<ScopeTermination | null> {
    const budget = this.budget;
    const ready = this.ready;
    if (budget === null || ready === null) throw new Error("warmup 只能在 acquire 返回就绪之后调用");
    try {
      if (this.cfg.uiKind === "app") return null;  // 应用目标不预热（ADR 0051 决策 13）
      const route = ready.conclusion.webContext === "available" ? "url" : "deep_link";
      let termination: ScopeTermination | null;
      try {
        const arn = this.remote!.arn;
        termination = await this.parts.warmup.run({
          session: ready.appium, adapter: ready.adapter, route, url, budget, sessionStatus: () => this.parts.sessions.status(arn),
        });
      } catch (e) {
        termination = await this.unclassifiedPreparationFailure(e, budget, warmupErrorMessage);
      }
      // 预热返回之后统一核获取预算：预算覆盖到预热返回为止，标记已就绪而离开预热页期间预算用尽的同样归 acquire_timeout。
      termination = termination === null ? (this.expiredOutcome(budget)?.termination ?? null) : this.budgetAware(termination, budget);
      if (termination !== null) {
        this.record.acquire_failure = { error_type: termination.errorType, message: termination.message };
      }
      return termination;
    } finally {
      budget.stop();
      this.record.timings.warmup_done_at = this.isoNow();
    }
  }

  // ---- scenario 前核对 ----

  async preScenarioCheck(): Promise<ScopeTermination | null> {
    this.budget?.stop();
    if (this.lost) return { ...this.lost, errorType: "session_lost" };
    if (this.ageReached()) return { errorType: "session_lost", message: this.markLost().message };
    if (!this.resultUnknownInScenario) return null;
    this.resultUnknownInScenario = false;
    try {
      await this.ready!.appium.probeScreenshot();
      return null;
    } catch (e) {
      if (await this.sessionEnded(e)) return { errorType: "session_lost", message: this.markLost().message };
      this.deps.log(`worker: 存活探测失败：${errorText(e)}`);
      return { errorType: "engine_error", message: LIVENESS_FAILED_MESSAGE };
    }
  }

  // ---- step 前核对、执行、复原 ----

  async preStep(): Promise<StepFailure | null> {
    this.budget?.stop();
    this.captureDeadline = null;
    if (this.lost) return { ...this.lost };
    if (this.ageReached()) return { ...this.markLost() };
    if (this.ready === null) return { errorType: "engine_error", message: PRE_STEP_FAILED_MESSAGE };
    const { appium } = this.ready;
    try {
      if (await appium.currentContext() !== NATIVE_CONTEXT) await appium.switchToNative();
      return null;
    } catch (e) {
      return this.commandFailure(e, PRE_STEP_FAILED_MESSAGE);
    }
  }

  bindHandler(selected: SelectedHandler): HandlerCall {
    if (selected.kind !== "webdriver") {
      throw attachClassification(new Error(HANDLER_KIND_MISMATCH_MESSAGE), {
        errorType: "engine_error", message: HANDLER_KIND_MISMATCH_MESSAGE,
      });
    }
    const ready = this.requireReady();
    if (selected.requires.includes("web_context")) {
      const unavailable = this.webContextFailure(ready.conclusion);
      if (unavailable) throw attachClassification(new Error(unavailable.message), unavailable);
    }
    const { ctx } = ready;
    return async (groups) => { await selected.fn(ctx, groups); };
  }

  async execute<T>(run: (abortSignal: AbortSignal | undefined) => Promise<T>): Promise<T> {
    if (this.lost) throw attachClassification(new Error(this.lost.message), this.lost);
    const ageLeftMs = this.ageLeftMs();
    if (ageLeftMs <= 0) {
      const lost = this.markLost();
      throw attachClassification(new Error(lost.message), lost);
    }
    const { guard } = this.requireReady();
    const act = new AbortController();
    this.currentAct = act;
    let ageExpired = false;
    let timerOutcome: WindowOutcome | null = null;
    guard.openWindow(act);
    // 会话年龄在执行中途到点：中止当前 act、撤销令牌，这一步归会话丢失（ADR 0051 决策 2）。
    const ageTimer = setTimeout(() => {
      ageExpired = true;
      act.abort(new Error(SESSION_LOST_MESSAGE));
      timerOutcome = guard.closeWindow();
    }, Math.min(ageLeftMs, MAX_TIMER_MS));
    ageTimer.unref?.();
    let value: T | undefined;
    let thrown: unknown = undefined;
    let threw = false;
    try {
      value = await run(act.signal);
    } catch (e) {
      threw = true;
      thrown = e;
    } finally {
      clearTimeout(ageTimer);
      if (this.currentAct === act) this.currentAct = null;
    }
    const outcome = ageExpired ? timerOutcome : guard.closeWindow();
    let failure: StepFailure | null = outcome?.failure ?? null;
    if (outcome?.resultUnknown) this.resultUnknownInScenario = true;
    if (ageExpired || failure?.errorType === "session_lost") failure = this.markLost();
    if (failure !== null) throw attachClassification(threw ? thrown : new Error(failure.message), failure);
    if (threw) throw executionFailure(thrown);
    return value as T;
  }

  async navigate(address: string): Promise<void> {
    if (this.lost) throw attachClassification(new Error(this.lost.message), this.lost);
    const { appium, adapter, guard, conclusion } = this.requireReady();
    try {
      if (this.cfg.uiKind === "app") await adapter.deepLink(guard.driver, address, this.appId);
      else if (conclusion.webContext === "available") await appium.openUrl(guard.driver, address);
      else await adapter.deepLink(guard.driver, address, null);
    } catch (e) {
      if (readClassification(e) !== null) throw e;
      throw attachClassification(e, { errorType: "engine_error", message: navigateErrorMessage(reasonOf(e)) });
    }
  }

  async restore(tentative: TentativeVerdict): Promise<StepFailure | null> {
    if (this.lost) return null;
    if (this.ready === null) return { errorType: "engine_error", message: restoreFailedMessage(tentative) };
    const { appium } = this.ready;
    try {
      if (await appium.currentContext() !== NATIVE_CONTEXT) await appium.switchToNative();
      return null;
    } catch (e) {
      return this.commandFailure(e, restoreFailedMessage(tentative));
    }
  }

  // ---- 界面快照 ----

  async readAddress(step: StepFacts): Promise<AddressReading | null> {
    if (!(step.kind === "ai" || step.status === "failed" || step.status === "error")) return null;
    const fixed = this.addressWithoutReading();
    if (fixed !== null) return fixed;
    const signal = this.captureSignal();
    if (signal.aborted) return { url: null, url_missing: "timeout" };
    try {
      const got = await this.ready!.appium.readWebAddress(signal);
      return "url" in got ? { url: got.url, url_missing: null } : { url: null, url_missing: got.missing };
    } catch {
      return { url: null, url_missing: signal.aborted ? "timeout" : "error" };
    }
  }

  async snapshot(step: StepFacts, address: AddressReading | null): Promise<SnapshotResult> {
    const reading = address ?? this.addressWithoutReading() ?? { url: null, url_missing: "error" as const };
    const snapshot: Snapshot = { url: reading.url, url_missing: reading.url_missing, step_kind: step.kind };
    if (step.status === "passed") return { snapshot, failure: null };
    snapshot.controls = null;
    snapshot.controls_missing = "error";
    snapshot.page_source_path = null;
    snapshot.page_source_truncated = false;
    const ready = this.ready;
    if (this.lost || ready === null) return { snapshot, failure: null };
    const signal = this.captureSignal();
    if (signal.aborted) {
      snapshot.controls_missing = "timeout";
      return { snapshot, failure: null };
    }
    const { appium, adapter } = ready;
    let source: string;
    try {
      source = await appium.pageSource(signal);
    } catch (e) {
      snapshot.controls_missing = signal.aborted ? "timeout" : "error";
      return { snapshot, failure: (await this.sessionEnded(e)) ? { ...this.markLost() } : null };
    }
    try {
      snapshot.controls = this.capControls(adapter.extractControls(source));
      snapshot.controls_missing = null;
    } catch (e) {
      this.deps.log(`worker: 本步控件摘要没能抽取（不影响本步判定）：${errorText(e)}`);
    }
    const written = this.writePageSource(source);
    snapshot.page_source_path = written.path;
    snapshot.page_source_truncated = written.truncated;
    return { snapshot, failure: null };
  }

  /** 不发命令就能确定的地址读数：应用目标没有地址；网页上下文不可用时不调读地址的命令（ADR 0052 决策 5）。 */
  private addressWithoutReading(): AddressReading | null {
    if (this.cfg.uiKind === "app") return { url: null, url_missing: "not_applicable" };
    if (this.lost) return { url: null, url_missing: "error" };
    const verdict = this.ready?.conclusion.webContext ?? null;
    if (verdict === "unavailable") return { url: null, url_missing: "no_web_context" };
    if (verdict !== "available") return { url: null, url_missing: "error" };
    return null;
  }

  private captureSignal(): AbortSignal {
    if (this.captureDeadline === null) this.captureDeadline = this.cfg.now() + SNAPSHOT_CAPTURE_BUDGET_MS;
    const left = this.captureDeadline - this.cfg.now();
    return left <= 0 ? AbortSignal.abort() : AbortSignal.timeout(left);
  }

  private capControls(controls: Controls): Controls {
    if (controls.items.length <= CONTROLS_MAX_ITEMS) return controls;
    return { items: controls.items.slice(0, CONTROLS_MAX_ITEMS), total: Math.max(controls.total, controls.items.length), truncated: true };
  }

  /** 原始控件树写盘，经 writePageSourceFile（先脱敏再截断）。没有产物落点或写盘失败时路径为 null。 */
  private writePageSource(source: string): { path: string | null; truncated: boolean } {
    const root = this.deps.artifactRoot;
    if (root === undefined) return { path: null, truncated: false };
    try {
      this.pageSourceSeq += 1;
      const file = path.join(this.scopeArtifactDir(root), PAGE_SOURCE_DIR, `step-${String(this.pageSourceSeq).padStart(4, "0")}.xml`);
      const { truncated } = writePageSourceFile(file, source);
      return { path: file, truncated };
    } catch (e) {
      this.deps.log(`worker: 本步原始控件树没能写盘（不影响本步判定）：${errorText(e)}`);
      return { path: null, truncated: false };
    }
  }

  // ---- 释放 ----

  release(mode: ReleaseMode): Promise<ReleaseOutcome> {
    // 先置位再取在途的那次：正常释放进行中到达的中断不重新进入终结，而是让同一次终结升级（见模块头「释放只进入一次」）。
    if (mode === "interrupt") this.interruptRequested = true;
    this.releasing ??= this.doRelease(mode);
    return this.releasing;
  }

  private async doRelease(mode: ReleaseMode): Promise<ReleaseOutcome> {
    this.finalizing = true;
    this.budget?.abort();
    this.ready?.guard.shutdown();
    this.currentAct?.abort(new Error("finalizing"));
    const appium = this.ready?.appium ?? this.connectedAppium;
    // 钩子在终结块调用它的那一刻核对升级：之前到达的中断让 deleteSession 不再发出（中断路径不调它，ADR 0051 决策 5）。
    const deleteAppiumSession = mode === "normal" && appium
      ? async (): Promise<void> => { if (!this.interruptRequested) await appium.deleteSession(); }
      : null;
    const hooks: FinalizeHooks = { deleteAppiumSession };
    let releaseFailed: boolean;
    try {
      ({ releaseFailed } = await this.parts.finalizer.finalize(mode, hooks));
    } catch (e) {
      this.deps.log(`worker: 释放远程访问会话时出错：${errorText(e)}`);
      releaseFailed = true;
    }
    this.undoNavigate?.();
    this.undoNavigate = null;
    this.unhookProcessFaults();
    this.record.timings.released_at = this.isoNow();
    this.record.release_failed = releaseFailed;
    return { releaseFailed, reportRefs: await this.deviceSessionRefs(this.interruptRequested ? "interrupt" : mode) };
  }

  /** 写 device-session.json；正常模式下经上传器得到链接挂到 scope_done（ADR 0051 决策 8）。best-effort：写盘或上传失败记一行
   *  日志，不影响判定。中断模式（含升级）不实时上传，只交给截图的后台队列，由停止路径阶段 4 的队列排空带上（ADR 0051 决策 5）：
   *  实时上传会在会话释放之后、阶段 4 之前再占一段上传超时，超出中断路径的宽限推导；这一模式返回的链接也不被使用（进入终结后不发
   *  scope_done）。正常模式的实时上传在途时收到中断：上传不打断，落定之后再核对一次是否已升级。上传失败且已升级即交给后台队列——
   *  停止路径的排空在本次释放返回之后才开始，此前入队的文件都会被它带上；上传成功则文件已经传到 S3，不再入队（链接照常返回，同样
   *  不被使用）。本方法每次释放只执行一次，入队因此至多一次。 */
  private async deviceSessionRefs(mode: ReleaseMode): Promise<ReportRef[]> {
    const root = this.deps.artifactRoot;
    if (root === undefined) return [];
    let file: string;
    try {
      file = writeDeviceSessionFile(this.scopeArtifactDir(root), this.record);
    } catch (e) {
      this.deps.log(`worker: 设备诊断文件没能写盘（不影响判定）：${errorText(e)}`);
      return [];
    }
    if (mode !== "normal") {
      this.deps.uploader.enqueue([file]);
      return [];
    }
    try {
      return [{ kind: DEVICE_SESSION_REPORT_KIND, ref: await this.deps.uploader.toReportRef(file) }];
    } catch (e) {
      if (this.interruptRequested) {
        this.deps.log(`worker: 设备诊断文件没能上传，退出前会再尝试上传（不影响判定）：${errorText(e)}`);
        this.deps.uploader.enqueue([file]);
      } else {
        this.deps.log(`worker: 设备诊断文件没能上传（不影响判定）：${errorText(e)}`);
      }
      return [];
    }
  }

  // ---- 内部 ----

  /** 本 scope 的设备产物目录 `<产物根>/device/<scope 键>`：产物根按 run 共享、S3 key 取它的相对路径，同一 run 的各 scope
   *  不分目录就会互相覆盖（scope 键的派生与 evidence 目录同一规则，ADR 0042 决策一）。 */
  private scopeArtifactDir(root: string): string {
    return path.join(root, "device", scenarioKey(this.deps.job.scope.id));
  }

  private requireReady(): ReadyState<A> {
    if (this.ready === null) throw new Error("设备还没有就绪");
    return this.ready;
  }

  /** 七个字段的句柄上下文（ADR 0050 决策 2），就绪时构造一次；内建导航的导航原语经模块私有通道注入，不进 ctx。系统版本取会话
   *  回报的值，不取 Device Farm 的设备描述（ADR 0052 决策 1）。 */
  private handlerCtx(guard: CommandGuard, conclusion: ProbeConclusion, appium: AppiumSession): WebdriverCtx {
    const appId = this.appId;
    return {
      driver: guard.driver,
      device: { platform: this.cfg.device, osVersion: appium.platformVersion ?? "", scale: conclusion.scale },
      uiKind: this.cfg.uiKind,
      appId,
      app: appId !== null ? appHandle(guard.driver, appId, this.cfg.appTiming) : null,
      log: (message: string) => this.deps.log(message),
      withWebContext: <T,>(fn: () => Promise<T> | T) => this.withWebContext(fn),
    };
  }

  private async withWebContext<T>(fn: () => Promise<T> | T): Promise<T> {
    if (this.lost) throw attachClassification(new Error(this.lost.message), this.lost);
    const { appium, guard, conclusion } = this.requireReady();
    const unavailable = this.webContextFailure(conclusion);
    if (unavailable) throw attachClassification(new Error(unavailable.message), unavailable);
    return appium.withWebContext(guard.driver, fn);
  }

  /** 网页上下文不可用时的 step 级归类：不提供归 capability_unavailable，探测出错归 engine_error（ADR 0052 决策 5）。 */
  private webContextFailure(conclusion: ProbeConclusion): StepFailure | null {
    if (this.cfg.uiKind === "app" || conclusion.webContext === null) {
      return { errorType: "capability_unavailable", message: WEB_CONTEXT_ON_APP_MESSAGE };
    }
    if (conclusion.webContext === "unavailable") return { errorType: "capability_unavailable", message: WEB_CONTEXT_UNAVAILABLE_MESSAGE };
    if (conclusion.webContext === "probe_error") return { errorType: "engine_error", message: WEB_CONTEXT_PROBE_ERROR_MESSAGE };
    return null;
  }

  /** 生命周期通道上的命令失败：先查会话状态，丢失归 session_lost，否则 engine_error 并用给定消息。 */
  private async commandFailure(e: unknown, engineMessage: string): Promise<StepFailure> {
    if (await this.sessionEnded(e)) return { ...this.markLost() };
    this.deps.log(`worker: ${engineMessage}：${errorText(e)}`);
    return { errorType: "engine_error", message: engineMessage };
  }

  /** 会话是否已结束：异常上已带会话丢失的归类，或查到的状态不是 RUNNING（查询失败不算）。 */
  private async sessionEnded(e: unknown): Promise<boolean> {
    if (readClassification(e)?.errorType === "session_lost") return true;
    const arn = this.remote?.arn;
    if (!arn) return false;
    let status: string | null;
    try {
      status = await this.parts.sessions.status(arn);
    } catch {
      status = null;
    }
    return status !== null && status !== RUNNING;
  }

  private markLost(): StepFailure {
    this.lost ??= { errorType: "session_lost", message: SESSION_LOST_MESSAGE };
    return this.lost;
  }

  /** 会话年龄离 max_session_s 还剩的毫秒数（年龄从发出 Create 起算）。 */
  private ageLeftMs(): number {
    if (this.remote === null) return Number.POSITIVE_INFINITY;
    return this.remote.createRequestedAt + MAX_SESSION_S * 1000 - this.cfg.now();
  }

  private ageReached(): boolean {
    return this.ageLeftMs() <= 0;
  }

  private hookProcessFaults(): void {
    if (this.processHooked) return;
    this.processHooked = true;
    this.cfg.processEvents.on("unhandledRejection", this.onProcessFault);
    this.cfg.processEvents.on("uncaughtException", this.onProcessFault);
  }

  private unhookProcessFaults(): void {
    if (!this.processHooked) return;
    this.processHooked = false;
    this.cfg.processEvents.off("unhandledRejection", this.onProcessFault);
    this.cfg.processEvents.off("uncaughtException", this.onProcessFault);
  }

  private isoNow(): string {
    return new Date(this.cfg.now()).toISOString();
  }
}
