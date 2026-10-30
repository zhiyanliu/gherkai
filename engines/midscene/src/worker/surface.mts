// 界面接缝（ADR 0052 决策 2）：run-scope 对被测对象的全部操作都经 TargetSurface 这一个接口，桌面浏览器（worker/surface-desktop.mts）
// 与设备（device/surface.mts）各一个实现，scope 开头按 job.target.device 选一次。本文件是 run-scope 与两个实现之间的契约：只放类型、
// 常量与执行异常归类标记的读写函数，不放实现，也只有 `import type`——桌面路径与能力自述加载它不会带进任何设备依赖（ADR 0052 决策 3
// 「设备模块动态加载」）。
//
// 成员与 ADR 0052 决策 2 的对应：
//   五个操作：取 agent（acquire）、取确定性句柄（bindHandler）、导航或启动应用（navigate）、释放（release）、预热（warmup）；
//   四项边界义务：scenario 前核对（preScenarioCheck）、step 前核对（preStep）、step 后复原并核对（restore）、
//     采集界面快照（分两半：第 4 步的 readAddress 与第 6 步的 snapshot，原先单列的「读当前地址」即前一半）。
//   另有两个成员把 ADR 已定的约束落到接口上：execute 是 step 第 3 步的执行窗口——执行令牌在 step 执行结束的那一刻撤销、
//   结果未知与进入终结时要中止当前 act 的 abortSignal（ADR 0052 决策 6；ADR 0051 决策 5），实现必须知道这段窗口的起止并持有
//   这个 signal；sessionId 是会话血缘，scope_done 在每条出口上都要带它。
//
// 单个 step 的固定顺序（ADR 0052 决策 2，契约的一部分）落在本接口上：
//   1. 发 step_started；
//   2. preStep：返回失败即本 step 记 error，不执行 handler 或 AI；
//   3. 在 execute 窗口内执行确定性 handler（bindHandler 绑好的调用；内建导航也是一条注册表条目）或 AI，得到暂定判定；
//   4. readAddress：读不读由实现按目标、能力探测结论与暂定判定决定；
//   5. restore：返回失败即最终判定改为 error，类别与消息取返回值；
//   6. snapshot：只在最终判定为 failed / error 时采控件摘要与原始控件树（设备），唯一可能改判的是发现会话丢失；
//   7. 产 evidence、发 step_done，然后把截图与原始控件树入队。
//   第 4、6 步只在本 run 产 evidence 时调用（有 evidence 落点）；没有落点时快照无人消费，设备上省下切换上下文与采集的时间。
//
// 主流程不写按设备的条件分支（ADR 0052 决策 2「不做」）：两套被测对象的差异全部落在实现里，或由实现返回的数据表达——
// 例如快照里 step_kind 的有无决定 evidence 是否加设备键，requires 是否满足由 bindHandler 判定。
//
// 失败的两种传递方式按调用方是谁来分：生命周期通道上的成员（四项义务、预热、acquire 的执行前失败）由 run-scope 直接调用，
// 失败作为返回值交回、不抛出，run-scope 据返回值决定判定与出口；经使用方 handler 或 Midscene 抛出的执行异常（execute、
// bindHandler 绑好的调用、navigate）由命令守卫与实现把 step 级归类挂到异常对象上（attachClassification），runStep 的通用异常
// 分类先读这个标记（readClassification）、读到即按它归类，读不到的（桌面路径的全部异常）沿用瞬时网络判定（ADR 0052 决策 6）。
import type { Agent, AgentOpt } from "@midscene/core";
import type { ArtifactUploader } from "../lib/artifact-upload.mjs";
import type { Job } from "../lib/job-source.mjs";
import type { WarmupFailure } from "../lib/tunnel-warmup.mjs";
import type { SelectedHandler } from "./deterministic.mjs";

// ---- step 的种类、判定与 step 级归类 ----

/** step 的执行方式，即 evidence 的 step_kind（ADR 0051 决策 8）。由命中的注册表条目上的标记判别：内建导航条目记 navigation；
 *  使用方 handler 在内部自己调导航仍记 deterministic；未命中确定性条目、交给 AI 的记 ai（ADR 0052 决策 2 第 7 步）。 */
export type StepKind = "ai" | "deterministic" | "navigation";

/** step_done 的三种判定。 */
export type StepStatus = "passed" | "failed" | "error";

/** 接缝与命令守卫能给出的 step 级错误类别（ADR 0051 决策 4 的类别表）：会话丢失、执行出错、设备不提供所需能力。封闭集合，
 *  readClassification 只认这三类。其余 step 级类别不由接缝给出：assertion_failed 来自 handler 抛出的断言异常或 AI 断言的票数，
 *  network_error 只在桌面路径由瞬时网络判定得出（设备路径没有这个出口，ADR 0052 决策 6）。 */
export const STEP_ERROR_TYPES = ["session_lost", "engine_error", "capability_unavailable"] as const;
export type StepErrorType = (typeof STEP_ERROR_TYPES)[number];

/** 一次 step 级失败的归类：类别与给使用方看的消息。消息是产品语言（ADR 0039），ADR 给了原文整句的照原文，例如结果未知的
 *  「设备在等待时间内没有回应，这一步可能已执行也可能未执行」（ADR 0052 决策 6）。run-scope 收到后发
 *  step_done{status: "error", errorType, message}。既是生命周期成员返回的失败，也是挂在执行异常上的标记内容。 */
export interface StepFailure {
  errorType: StepErrorType;
  message: string;
}

/** 第 3 步结束时的暂定判定（交给 restore，见该成员）。message 是 run-scope 已经算好的、准备写进 step_done 的那句（passed 时为 null）。 */
export interface TentativeVerdict {
  status: StepStatus;
  message: string | null;
}

/** 交给 readAddress 与 snapshot 的 step 事实：执行方式与判定。readAddress 收到的是暂定判定，snapshot 收到的是复原之后的最终判定。 */
export interface StepFacts {
  kind: StepKind;
  status: StepStatus;
}

// ---- scope 级终止 ----

/** scope 级终止可用的错误类别：ADR 0051 决策 4 类别表里归 scope 级的那些行。capability_unavailable 只在 step 级出现；
 *  release_failed 由 core 从会话事件的配对推出，worker 不直接报。 */
export type ScopeErrorType = "precheck_failed" | "acquire_timeout" | "session_lost" | "engine_error";

/** scope 级终止：执行前失败（acquire、warmup 返回）与 scenario 前核对返回的终止。run-scope 收到后经通用的「scope 终止」出口
 *  发 scope_done{status: "error", errorType, message}，本条与后续 scenario 不再发任何事件，由 core 合成 SKIPPED（ADR 0051 决策 4；
 *  ADR 0052 决策 2）。出口里释放、session_closed、scope_done 与排空的次序归 ADR 0051 决策 5。
 *  lib/tunnel-warmup.mts 的 WarmupFailure 与它形状相同、可直接当它用（下方的类型断言守住这一点）。 */
export interface ScopeTermination {
  errorType: ScopeErrorType;
  message: string;
}

/** acquire 的结果：被测对象就绪（带 agent 与执行所用的会话血缘），或执行前失败的 scope 级终止。 */
export type AcquireResult =
  | { ready: true; agent: Agent; sessionId: string }
  | { ready: false; termination: ScopeTermination };

// ---- 界面快照（evidence 的输入，ADR 0051 决策 8；ADR 0042 决策一的设备例外）----

/** 顶层 url 为 null 时的原因（ADR 0051 决策 8 的封闭集合）：设备不提供网页上下文、应用目标（没有地址可言）、读取超时、读取出错。 */
export type UrlMissing = "no_web_context" | "not_applicable" | "timeout" | "error";

/** 控件摘要采集失败的原因：超出采集预算、采集出错。 */
export type ControlsMissing = "timeout" | "error";

/** 控件摘要的一项（ADR 0051 决策 8）：类型、id、文本、无障碍标识；控件树里没有的属性为 null。抽取归驱动适配器（ADR 0052 决策 4）。 */
export interface ControlItem {
  type: string | null;
  id: string | null;
  text: string | null;
  a11y_id: string | null;
}

/** 控件摘要：items 截断到上限（200 条，常量在 device/limits.mts），total 是截断前采到的总数，truncated 表示 items 是否被截断。
 *  items 为空数组表示采集成功但这一屏没有可识别的控件。 */
export interface Controls {
  items: ControlItem[];
  total: number;
  truncated: boolean;
}

/** 第 4 步的读地址结果。url 取到时 url_missing 为 null；url 为 null 时设备实现给出原因，桌面实现恒为 null（桌面 evidence 不写这个键）。 */
export interface AddressReading {
  url: string | null;
  url_missing: UrlMissing | null;
}

/** 一个 step 的界面快照，由 snapshot 产出、交给 evidence 模块（evidence 保持纯映射、不发 WebDriver 命令，ADR 0052 决策 7）。
 *  键名与 evidence 文档的键一致（snake_case），可选键「出现与否」本身就是契约：evidence 只写快照里出现了的设备键，
 *  桌面快照只有 url 与 url_missing 两键，桌面 evidence 因此逐字节不变。 */
export interface Snapshot {
  /** 桌面：AI step 末的 page.url()，取不到为 null，evidence 把它写进每个 act 的 url；设备：第 4 步在网页上下文读到的地址，
   *  应用目标恒为 null。 */
  url: string | null;
  /** url 为 null 时的原因（设备）；url 有值或桌面目标时为 null。 */
  url_missing: UrlMissing | null;
  /** 只有设备实现填写。它的有无即 evidence 是否按设备目标处理：加 step_kind 与顶层 url / url_missing，并且确定性与导航 step
   *  在 failed / error 时也产 evidence（acts 为空数组），passed 的不产（ADR 0051 决策 8、ADR 0042 决策一的设备例外）。 */
  step_kind?: StepKind;
  /** 只在设备目标、最终判定为 failed / error 时出现，与 controls_missing 同进同出：采集成功为控件摘要、controls_missing 为 null；
   *  采集失败为 null、controls_missing 记原因。其余情形两键都不出现，evidence 也不写。 */
  controls?: Controls | null;
  controls_missing?: ControlsMissing | null;
  /** 出现条件同 controls：原始控件树的本地文件路径，写盘前已经过脱敏出口（ADR 0051 决策 11）、超过上限（1 MiB，常量在
   *  device/limits.mts）时已截断；采集失败为 null。evidence 用上传器的 refFor 算出 URI 写进 page_source，并把这个文件与截图一起
   *  交后台上传队列（ADR 0042 决策一）。 */
  page_source_path?: string | null;
  /** 与 page_source_path 同进同出：原始控件树是否因超过上限被截断。 */
  page_source_truncated?: boolean;
}

/** snapshot 的结果：快照本身，以及采集中发现会话丢失时的改判（只会是 session_lost，其余采集失败都不改判定）。 */
export interface SnapshotResult {
  snapshot: Snapshot;
  failure: StepFailure | null;
}

// ---- 确定性句柄、释放与构造 ----

/** bindHandler 绑好句柄上下文的调用：传入正则的具名组，执行命中的 handler。 */
export type HandlerCall = (groups: Record<string, string>) => Promise<void>;

/** 释放的两种模式（ADR 0051 决策 5）：
 *  - normal：主流程掌控的出口，即正常收尾、执行前失败与 scope 级终止（会话丢失、scenario 前核对终止）；
 *  - interrupt：停止信号与进程级异常，调用即进入终结。 */
export type ReleaseMode = "normal" | "interrupt";

/** 产物链接，与 scope_done / step_done 的 reportRefs 项形状相同（ADR 0027）。 */
export interface ReportRef {
  kind: string;
  ref: string;
  label?: string;
}

/** release 的结果。releaseFailed 为真表示有会话没能确认停止、或发过 attempted 事件（结果未知的建会话请求），即退出码 1 的依据
 *  （ADR 0051 决策 5）；reportRefs 是要并进 scope_done 的 scope 级产物链接（设备的 device-session.json，kind 为 device_session，
 *  ADR 0051 决策 8），桌面为空。 */
export interface ReleaseOutcome {
  releaseFailed: boolean;
  reportRefs: ReportRef[];
}

/** 两个实现的构造参数（run-scope 在 scope 开头组装一次）。各项都是两条路径共用的形状；某个实现用不到的项它直接忽略。 */
export interface SurfaceDeps {
  /** 本 scope 的 job（线上字段为驼峰，见 lib/job-source.mts）；实现读 scope.id、target 与 deviceRequest。 */
  job: Omit<Job, "scenarios">;
  /** 事件出口（run-scope 的 EventSink.emit，整行经脱敏）。两种实现都用它发 session_opened / session_closed（ADR 0051 决策 4）。 */
  emit: (event: Record<string, unknown>) => Promise<void>;
  /** worker 日志（run-scope 的 log，经脱敏出口，ADR 0051 决策 11）。 */
  log: (line: string) => void;
  /** 两种 Agent 共用的构造项（报告与执行记录的开关、模型配置等，generateReport 与 persistExecutionDump 同真同假，ADR 0052 决策 7）。
   *  各实现在其上只加自己的项：桌面加 forceChromeSelectRendering，设备加重规划上限（ADR 0044 决策 2）。 */
  agentOpts: AgentOpt;
  /** 产物上传器：设备实现经 toReportRef 上传 device-session.json 并得到链接。 */
  uploader: Pick<ArtifactUploader, "toReportRef" | "refFor">;
  /** 产物落点根（与 evidence 落点同一判据）；undefined 表示本 run 不产产物（`--no-report` 方式），实现不写诊断文件与原始控件树。 */
  artifactRoot: string | undefined;
  /** 请求进入终结，与收到停止信号走同一条路径（run-scope 的信号处理：释放、兜底上传、排空、退出）。设备实现在会话建立后注册的
   *  进程级兜底（unhandledRejection / uncaughtException，ADR 0051 决策 5）记录后调用它；桌面实现不注册进程级处理器、不调用它。 */
  requestFinalization: () => void;
}

/** 实现的构造函数：只组装、不做 I/O（I/O 从 acquire 开始），可以同步抛出构造期错误（如设备侧的 env 覆盖值非法）。实现可另带
 *  仅供测试注入的可选参数。导出名固定：worker/surface-desktop.mts 导出 createDesktopSurface，device/surface.mts 导出
 *  createDeviceSurface。 */
export type SurfaceFactory = (deps: SurfaceDeps) => TargetSurface;

/** device/surface.mts 的模块形状：run-scope 经 `await import("../device/surface.mjs")` 动态加载它（桌面路径与能力自述不加载，
 *  ADR 0052 决策 3），可用本类型标注加载结果，让设备模块的导出名与签名在编译期对上。 */
export interface DeviceSurfaceModule {
  createDeviceSurface: SurfaceFactory;
}

// ---- 界面接缝 ----

/** run-scope 操作被测对象的唯一接口（ADR 0052 决策 2）。所有成员都由 run-scope 在固定时机调用（navigate 例外，见该成员）；
 *  会话一旦判定丢失，实现的各项义务与快照不再向被测对象发命令，直接返回（不再改判定）。 */
export interface TargetSurface {
  /** 取 agent：建立被测对象并构造 Midscene Agent。
   *  - 桌面：StartBrowserSession、CDP 建连与 PlaywrightAgent，含建连重试（ADR 0028）；
   *  - 设备：设备解析、Create、等到 RUNNING、应用存在性检查与预签名、newSession、activateApp 与启动采样、能力探测
   *    （ADR 0051 决策 2、3、9；ADR 0052 决策 3、5）。获取预算（job.deviceRequest.acquireTimeoutS）从这里开始计，覆盖到 warmup
   *    返回为止（ADR 0052 决策 6 超时分层表的 ③）。
   *  两种实现都在会话建立后、一切长耗时动作之前发 session_opened（ADR 0051 决策 4）。
   *  返回 ready 时带 agent 与 sessionId（scope_started 用）；执行前失败返回 scope 级终止（设备的 precheck_failed、acquire_timeout、
   *  engine_error 等，ADR 0051 决策 4；桌面不产生这种返回）。未归类的失败照常抛出——桌面建连失败即此，非瞬时或重试耗尽的
   *  归因与退出码 80 仍由 run-scope 与桌面实现按 ADR 0028 处理（设备路径不使用 80）。
   *  调用：run-scope 在建会话前自检之后调用一次。 */
  acquire(): Promise<AcquireResult>;

  /** 预热：导航会话预热地址一次并确认页面标记（ADR 0051 决策 13；ADR 0052 决策 6）。返回 null 表示就绪；否则返回 scope 级终止：
   *  DENIED 或 AUTH REQUIRED 归 precheck_failed，ERROR、预算内没有标记或导航失败在有界重试耗尽后归 engine_error，永不归
   *  network_error，也不用退出码 80。
   *  - 桌面：lib/tunnel-warmup.mts 的 warmupSession，原样搬移；
   *  - 设备：按探测结论选 url 或 mobile: deepLink 路线，在原生控件树里找标记；url 路线就绪后离开到 about:blank，deepLink 路线
   *    不离开；应用目标不预热，直接返回 null。经生命周期通道执行、不经命令守卫，计入获取预算。
   *  调用：run-scope 在 acquire 返回 ready 之后、发 scope_started 之前，只在有预热地址时调用一次。 */
  warmup(url: string): Promise<ScopeTermination | null>;

  /** 会话血缘：执行所用会话的 id，桌面为 AgentCore 会话 id，设备为远程访问会话 ARN（换台后是新的那个，ADR 0051 决策 4）；
   *  还没有成功建立的会话时为 null（被丢弃的建连尝试不算）。run-scope 在每条出口的 scope_done 上带它。 */
  sessionId(): string | null;

  /** scenario 前核对（ADR 0052 决策 2）：从第二条 scenario 起，每条发 scenario_started 之前无条件调用一次；第一条之前不调用。
   *  返回 null 表示继续；返回 scope 级终止时 run-scope 经「scope 终止」出口收尾，这条与后续 scenario 不再发事件。
   *  - 桌面：恒返回 null；
   *  - 设备：上一条 scenario 里发生过结果未知（命令守卫置过结果未知标志，实现另记一个 scenario 级的记录）时，经生命周期通道
   *    在原生上下文截图一次作存活探测（受探测客户端的短超时约束），失败先查一次会话状态：非 RUNNING 归 session_lost，RUNNING 归
   *    engine_error；会话年龄已达 max_session_s 时直接返回 session_lost，不为让第一个 step 报错而开一条 scenario。 */
  preScenarioCheck(): Promise<ScopeTermination | null>;

  /** step 前核对（ADR 0052 决策 2 第 2 步）：在 step_started 之后、执行之前调用。返回 null 表示可以执行；返回失败时 run-scope
   *  记本 step 为 error（类别与消息取返回值），不调 handler、不调 AI，继续第 4 步之后的流程。
   *  - 桌面：空操作，恒返回 null；
   *  - 设备：确认会话处在原生上下文（一次读取），不在就切回；切回失败归 engine_error；命令失败先查会话状态，丢失归 session_lost
   *    （ADR 0051 决策 4「会话丢失靠查状态」）。经生命周期通道执行，不经执行令牌与结果未知标志。 */
  preStep(): Promise<StepFailure | null>;

  /** 取确定性句柄：返回一个已绑好本实现句柄上下文的调用，run-scope 在 execute 窗口内以正则具名组调用它。
   *  - 桌面：playwright 句柄得到 {page, navigate}，其中 navigate 即本接口的 navigate；
   *  - 设备：webdriver 句柄得到 ADR 0050 决策 2 的七字段 ctx（driver 为命令守卫代理、device、uiKind、appId、app、log、
   *    withWebContext），不多不少；内建导航条目所需的导航原语经模块私有通道取得，不进 ctx（ADR 0050 决策 1）。
   *  前提不满足时同步抛出带归类标记的异常，不调 handler、也不转 AI：requires 含 web_context 而能力探测确认不提供，归
   *  capability_unavailable；探测出错，归 engine_error、消息「未能确认设备是否提供网页上下文」（ADR 0052 决策 5；ADR 0050 决策 2）。
   *  句柄种类与本实现不符（不会经 selectHandler 出现）时同样同步抛出，归 engine_error。
   *  调用返回的 promise 原样传出 handler 的异常：断言异常由 run-scope 判 failed，其余按通用异常分类。 */
  bindHandler(selected: SelectedHandler): HandlerCall;

  /** step 第 3 步的执行窗口：每个 step 至多调用一次，覆盖这一步的全部执行（确定性 handler，或 AI 的一次 act、多票断言的每一票）。
   *  run 收到本次 act 的 abortSignal，AI 的 act 应把它作为 aiAct 的 abortSignal 传入（aiBoolean 不接受这一项，只截图、不发动作）。
   *  - 桌面：直接调用 run(undefined)，原样返回或抛出，没有令牌；
   *  - 设备：进入时发出执行令牌并新建本次 act 的中止控制；run 结束（返回或抛出）的那一刻撤销令牌；结果未知时命令守卫中止这个
   *    signal；进入终结（release 的 interrupt 模式）时立即撤销令牌并中止它（ADR 0052 决策 6；ADR 0051 决策 5 阶段 1）。
   *    窗口内命令守卫判定过结果未知或会话丢失时，execute 以带该归类标记的异常拒绝——即便 run 正常返回（handler 吞掉了守卫的
   *    异常），或 run 抛出的是 Midscene 包装后的另一个异常；其余异常原样抛出，是否带标记取决于抛出方。 */
  execute<T>(run: (abortSignal: AbortSignal | undefined) => Promise<T>): Promise<T>;

  /** 导航或启动应用：内建导航 step 的执行面，打开 address（ADR 0020 第 3 条；ADR 0048 决策 7）。
   *  - 桌面：page.goto，等到 domcontentloaded，超时 60 秒；
   *  - 设备：网页目标按探测结论择路——提供时在网页上下文调 url，不提供与探测出错时经 mobile: deepLink 交给系统浏览器；应用目标经
   *    mobile: deepLink 交给被测应用（Android 带 package，发命令前按 RFC 3986 校验地址字符；iOS 带 bundleId）（ADR 0052 决策 4、6）。
   *  失败即抛出；设备上的异常带归类标记：网页上下文多候选或零候选、命令成功但前台不是被测应用归 engine_error；地址字符校验不过、
   *  Android 无法解析 Intent、iOS 不支持打开地址归 capability_unavailable（最后一种缓存到会话，ADR 0052 决策 5）。
   *  调用：不由 run-scope 主流程直接调用，而由内建导航条目的句柄调用——桌面经 ctx.navigate，设备经设备模块建立接缝时注入内建条目的
   *  模块私有通道（ADR 0050 决策 1）；因此只在 execute 窗口内执行，设备上的命令经命令守卫、靠窗口内的执行令牌放行。 */
  navigate(address: string): Promise<void>;

  /** 采集界面快照的前一半（ADR 0052 决策 2 第 4 步）：在 execute 之后、restore 之前调用，传入暂定判定。返回 null 表示本 step
   *  按暂定判定不产 evidence、没有读；否则返回读到的地址或缺失原因。读取失败只置 url 为 null、记原因，不改判定，不抛出。
   *  - 桌面：AI step 取 page.url()（取不到为 null），其余 step 返回 null；
   *  - 设备：AI step 一律读，确定性与导航 step 只在暂定判定为 failed / error 时读；应用目标直接给 not_applicable、能力结论为
   *    「不提供」直接给 no_web_context，都不发命令，绝不调 url；结论为「提供」时按决策 5 重新定位网页上下文后读，受 evidence
   *    采集的 10 秒独立短预算约束（ADR 0051 决策 8），多候选、零候选与读取出错记 error，超时记 timeout，能力结论不翻转。
   *    经生命周期通道执行。
   *  调用：只在本 run 产 evidence 时调用。 */
  readAddress(step: StepFacts): Promise<AddressReading | null>;

  /** step 后复原并核对（ADR 0052 决策 2 第 5 步）：在 readAddress 之后（或第 3 步之后，本 run 不产 evidence 时）调用，传入暂定判定。
   *  返回 null 表示判定不变；返回失败时 run-scope 把最终判定改为 error，类别与消息都取返回值，消息由实现写全：
   *  暂定判定为 passed / failed 时为「原判定为 passed；之后未能切回原生界面，后续 step 的截图坐标会错位」（passed 处按实际判定）；
   *  暂定判定已是 error（如结果未知）时以暂定的消息开头，复原失败的信息追加在其后；命令失败先查会话状态，丢失归 session_lost。
   *  - 桌面：空操作，恒返回 null；
   *  - 设备：确认会话回到原生上下文，不在就切回；经生命周期通道执行（结果未知之后的切换不在只读白名单里，经守卫会被自己拒绝）。 */
  restore(tentative: TentativeVerdict): Promise<StepFailure | null>;

  /** 采集界面快照的后一半（ADR 0052 决策 2 第 6 步）：在 restore 之后、产 evidence 之前调用，传入最终判定与第 4 步的结果。
   *  返回交给 evidence 的快照（字段约定见 Snapshot）；best-effort，采集失败置空并标原因、不改判定，唯一例外是采集中发现会话丢失，
   *  此时 failure 为 session_lost，run-scope 按会话丢失序列收尾（ADR 0051 决策 4、5）。不抛出。
   *  - 桌面：只把 address 的 url 放进快照，不采集、failure 恒为 null；
   *  - 设备：快照带 step_kind；最终判定为 failed / error 时在原生上下文采控件摘要与原始控件树（与读地址共用 10 秒独立短预算，
   *    控件摘要截断到 200 条、原始控件树截断到 1 MiB，写盘经脱敏出口，ADR 0051 决策 8、11）；address 为 null（第 4 步没读）而
   *    本 step 要产 evidence 时，url 为 null、url_missing 为 error，不补读（第 5 步把判定改成 error 的情形）。经生命周期通道执行。
   *  调用：只在本 run 产 evidence 时调用。 */
  snapshot(step: StepFacts, address: AddressReading | null): Promise<SnapshotResult>;

  /** 释放：停止本 scope 建立过的全部会话，为每个会话发恰一条 session_closed（ADR 0051 决策 4、5）。不抛出：释放中的失败只体现在
   *  返回的 releaseFailed 与 session_closed 的 release 字段上。
   *  - normal：桌面按现有清理次序，先 Stop 全部待清理会话、再关浏览器；设备在 Appium 会话已建成且远程访问会话不是 STOPPING /
   *    COMPLETED 时先 deleteSession（5 秒），再终结核对与释放阶段，Appium 会话没建成时从终结核对开始。run-scope 在正常收尾里
   *    把它排在 agent.destroy 与报告上传之后。
   *  - interrupt：调用的那一刻即进入终结——桌面唤醒建连重试的退避，设备中止当前 act 的 signal 并撤销执行令牌；之后等在途的
   *    建会话请求一段窗口（桌面为 INFLIGHT_SETTLE_MS，设备为终结阶段 1 的 10 秒），窗口内没有返回的发一对 attempted 事件，再
   *    执行释放（设备即终结四阶段的前三段，不调 deleteSession）。阶段 4 的兜底上传与排空归 run-scope 的收尾序列；进入终结后
   *    run-scope 不再为在途的 step 发 step_done，也不发 scope_done（ADR 0051 决策 5 阶段 1），所以这一模式返回的 reportRefs 不被使用。
   *  重入安全：信号处理与主流程的出口可能先后或同时调用。同一会话不重复释放、session_closed 不重复发；设备的终结只进入一次，
   *  后到的调用等在途那一次结束并返回同一结果；桌面保留现有清理守卫的重入语义（仍有未确认的会话时以最终语义再清一次）。 */
  release(mode: ReleaseMode): Promise<ReleaseOutcome>;
}

// ---- 执行异常的归类标记 ----

// 标记挂在异常对象的一个 symbol 键上：不进 JSON、不出现在可枚举键里，日志与 errorText 的输出不受影响；用 Symbol.for 是为了
// 模块被重复加载（同一文件的两个实例）时读写两侧仍认得同一个键。
const CLASSIFICATION_KEY = Symbol.for("gherkai.worker-midscene.step-classification");
// cause 链的查找上限，与 run-scope 瞬时网络判定遍历 cause 链的上限相同，同时防环。
const MAX_CAUSE_DEPTH = 8;

/** 把 step 级归类挂到异常上（写）。命令守卫在抛出前、execute 在重新抛出 Midscene 包装后的异常前调用（ADR 0052 决策 6）。
 *  error 是可扩展的 Error 时挂在它自己身上并返回同一个对象；否则（字符串、裸对象、冻结的异常）包成一个以 failure.message 为消息、
 *  原抛出物为 cause 的新 Error 再挂。已有标记的异常再挂一次即覆盖。用法：`throw attachClassification(e, failure)`。 */
export function attachClassification(error: unknown, failure: StepFailure): Error {
  const target = error instanceof Error && Object.isExtensible(error) ? error : new Error(failure.message, { cause: error });
  Object.defineProperty(target, CLASSIFICATION_KEY, {
    value: { errorType: failure.errorType, message: failure.message },
    enumerable: false,
    configurable: true,
    writable: true,
  });
  return target;
}

/** 读异常上的 step 级归类（读）：runStep 的通用异常分类先调它，读到即按它归类，读不到返回 null、交瞬时网络判定。
 *  从最外层沿 cause 链向内找，取第一个（最外层的）标记；只认封闭集合 STEP_ERROR_TYPES 里的类别且消息为字符串，其余视为没有标记。
 *  返回副本，改写它不影响异常上的标记。 */
export function readClassification(error: unknown): StepFailure | null {
  let current: unknown = error;
  for (let depth = 0; depth < MAX_CAUSE_DEPTH; depth++) {
    if (current === null || typeof current !== "object") return null;
    const mark = (current as { [CLASSIFICATION_KEY]?: unknown })[CLASSIFICATION_KEY];
    if (mark !== undefined) {
      const { errorType, message } = mark as Partial<StepFailure>;
      const known = (STEP_ERROR_TYPES as readonly unknown[]).includes(errorType);
      return known && typeof message === "string" ? { errorType: errorType as StepErrorType, message } : null;
    }
    current = (current as { cause?: unknown }).cause;
  }
  return null;
}

// 编译期核对：桌面预热的失败返回值可以直接当 scope 级终止用（ScopeTermination 的文档承诺了这一点）。
type _WarmupFailureIsScopeTermination = WarmupFailure extends ScopeTermination ? true : never;
const _warmupFailureIsScopeTermination: _WarmupFailureIsScopeTermination = true;
void _warmupFailureIsScopeTermination;
