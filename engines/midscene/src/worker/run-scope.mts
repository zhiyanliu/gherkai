// Midscene 薄 worker（ADR 0022/0024）：读 stdin 的 job JSON → 运行一个 scope → 发出 ADR 0024 事件到事件通道。
//
// 不含 BDD runner 装饰器：会话/aiAct/aiBoolean 投票/派发逻辑直接在本进程运行（ADR 0022 薄 worker）。
// core 经子进程 adapter 起本 worker（ADR 0026 机制层），讲 ADR 0024 协议——与 Nova Act 引擎对称。
//
// 三通道分离（ADR 0024）：协议事件吐到 EVENTS_FD 指定的 fd（无则回落 stdout，便于手动直接运行调试）；
// Midscene/SDK 的 stdout 噪声留 stdout；worker 自身诊断走 stderr。
//
// cost（ADR 0024）：从 agent.metrics（SDK 公开的累计用量快照）的 totalTokens 取原生 token 数，按 step 取前后
// 差值，worker 只报 {tokens}；core 合计、美元折算交消费者（不追模型单价——单价随 region / 协商 / 版本变）。
// 两个引擎对称：都只报原生量。
//
// **本模块不是进程入口**（ADR 0037 决策 3）：入口是 `bin.mts`（npm bin `gherkai-worker-midscene` /
// 容器 CMD），它装 tsx loader + 注册裸 specifier 的 resolve hook 后调本模块的 `main`。故这里只导出
// `main`、不自带 `if 入口` 守卫——「装 loader」与「运行 worker」分层，且 import 本模块做单测时不触发 main。
//
// 运行（一般由 core adapter 按 ADR 0037 的 worker 定位链 spawn；也可手动）：
//   echo '<job json>' | AWS_REGION=us-east-1 RUN_ID=<本次运行的编号> node dist/bin.mjs
//
// 被测对象经界面接缝操作（ADR 0052 决策 2，契约见 worker/surface.mts）：scope 开头按 job.target.device 选一次实现——桌面浏览器
// 是 worker/surface-desktop.mts（静态加载），设备是 device/surface.mts（动态加载：桌面路径与能力自述不加载设备依赖，ADR 0052
// 决策 3）。本文件的 step 循环、短路、evidence 时序与收尾只有一份，不按设备写条件分支；两套被测对象的差异全部落在实现里，
// 或由实现返回的数据表达（快照里 step_kind 的有无、异常上的归类标记、release 返回的产物链接）。
import OpenAI from "openai";
import type { Agent, AgentOpt } from "@midscene/core";
import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";
import { sigv4Fetch, getBaseUrl, MODEL, modelFamily } from "../lib/agentcore-sigv4.mjs";
// 产物 S3 上传（ADR 0029；无落点 env 时 no-op 报 file://）；UPLOAD_TIMEOUT_MS 是自报 grace 下限的加数之一
// （中断兜底提前上传那一段的预算，见下 minGraceSeconds），单一真值住上传器、此处只引用。
import { ArtifactUploader, UPLOAD_TIMEOUT_MS } from "../lib/artifact-upload.mjs";
import { EventSink } from "../lib/event-sink.mjs";  // 事件出口（ADR 0024「I/O 边缘可注入接口」，两态见该模块头）
import { JobSource, PROTOCOL_SCHEMA_VERSION, type Job as WireJob } from "../lib/job-source.mjs";  // job 入口（同上）；Job 类型是 core 发来的 job 行形状
import { precheckJob } from "../lib/precheck.mjs";  // 建会话前的结构版本、目标与预算自检（ADR 0049 决策 7、0024）
// 设备目标的会话上限与设备收尾之和（ADR 0049 决策 4、5），以及重规划上限覆盖键的启动期校验（ADR 0044 决策 2）：设备模块里
// 唯一允许值 import 的文件，它不 import 任何 SDK（ADR 0052 决策 3）
import { MAX_SESSION_S, deviceGraceSeconds, replanningCycleLimit } from "../device/limits.mjs";
// 确定性 step 注册表（ADR 0022）。内建导航由下方 import 的脚手架 deterministic.steps.mts 在模块顶层经 registerBuiltin(...) 登记、
// 带内建标记（ADR 0050 决策 1）——import 即注册，对称 Nova 引擎 import deterministic_steps；使用方 steps 在 main 里随后加载。
import {
  match as matchDeterministic, selectHandler, DeterministicAssertion, DeterministicConflict, DeterministicKeywordMismatch,
  listRegistry, matchBatch, type Match, type MatchItem, type SelectedHandler, type StepTargetKey,
} from "./deterministic.mjs";
import { buildInstruction } from "./argument.mjs";
// step 级机读证据（ADR 0042）：SDK 结构 → gherkai 自有 schema 的映射与落盘全住那个模块；此处只挂钩子。
import { stepEvidenceRef, executionsLength, EVIDENCE_KIND, ENGINE, type EvidenceHook } from "./evidence.mjs";
import { errorText, oneLineError } from "./error-text.mjs";  // 失败原因压成一行有界文本（ADR 0042；与 evidence 侧同一规则）
import { redactSecrets } from "../lib/redact.mjs";  // stderr 诊断行的脱敏出口（见下 log）
import "./deterministic.steps.mjs";  // 内建脚手架（ADR 0022 退役 bdd 层后迁入 worker/）——**先于**使用方 steps 注册
import { EXTRA_HTTP_HEADERS_ENV, INCOMPLETE_DEFINITION_MESSAGE, SESSION_WARMUP_KEY, SESSION_WARMUP_URL_ENV } from "../lib/tunnel-warmup.mjs";
import { loadUserSteps } from "./user-steps.mjs";  // 使用方 steps/ 目录的加载（ADR 0037 决策 4）
// 界面接缝的契约（只有类型与归类标记的读写）与桌面实现；桌面收尾各段的预算常量随桌面实现住在那里，此处引用来算 grace 下限。
import {
  readClassification,
  type DeviceSurfaceModule, type ReleaseMode, type ReleaseOutcome, type ReportRef, type ScopeTermination, type Snapshot,
  type StepFailure, type StepKind, type StepStatus, type SurfaceDeps, type TargetSurface,
} from "./surface.mjs";
import {
  BROWSER_CLOSE_BUDGET_MS, INFLIGHT_SETTLE_MS, STOP_SESSION_BUDGET_MS, createDesktopSurface, isConnectRetriesExhausted, isTransientNetwork,
} from "./surface-desktop.mjs";

// 网络专用退出码（ADR 0028）：与 core/gherkai_core/wire.py 的 EX_WORKER_NETWORK 同值（协议层单一事实源，两 Engine adapter 共用翻译）。
// 桌面建连失败、重试耗尽且会话已全部确认停止时以这个退出码退出，作 out-of-band 信号（scope_started 之前）。设备路径不使用它：
// 只有桌面实现会产生「建连重试耗尽」的异常（ADR 0051 决策 5）。
const EX_WORKER_NETWORK = 80;
// scenario 边界 log 提前上传的总墙钟预算（ADR 0029 上传时机第四级）：单个 log 上传已被
// uploadOne 的 AbortSignal.timeout(10s) 封顶，但一个 scenario 边界要传多个 log，退化网络下串行累加会拖住
// 下一 scenario、并叠进 grace。给整次快照套此总预算：超预算即放弃剩余（best-effort，scope 末 flush 兜底）。
// 提前上传在主流程执行（scenario 之间、非 SIGTERM handler），此预算限的是「延迟下一 scenario 的墙钟」，非 grace。
const SCENARIO_LOG_SNAPSHOT_BUDGET_MS = 8000;
// 截图后台队列的排空预算（ADR 0042 决策一「有界排空」）：
//   · scope 末（正常路径：判定已全部 emit、会话已释放）给宽预算——此刻只剩字节要落地，等一等换来的是
//     evidence 里的截图 URI 不悬空；真排不完的还有整目录 flush 兜。
//   · 提前退出路径（停止信号 / 建连重试耗尽 / 异常）给紧预算——**这段计入 grace**，与会话释放、中断兜底
//     提前上传共用同一个宽限（本段是自报下限 minGraceSeconds 的加数之一，见下）。这些路径不 flush、
//     排不完的字节就此丢，故也不能给 0。
const QUEUE_DRAIN_SCOPE_END_MS = 30_000;
export const QUEUE_DRAIN_EXIT_MS = 6_000;

// 自报 grace 下限的余量（ADR 0024 grace 硬约束的 margin）：收尾各段预算之和之外再多留一份，吸收段间调度、
// SDK 抖动与不被上述预算覆盖的零碎（诊断写出、事件 flush、进程退出本身）。
// **取值来路**：使下限落在已标定的 31 s 上（各段之和 23.5 + 本余量 7.5）——31 不是新数，是 ADR 0032 真容器校准
// 判「25 够用」（实测约 2x 余量）后、又被 ADR 0042 决策一的 6 s 截图队列排空顶上来的今值。改本常量就是改一个
// 已标定的下限，要有意识地改。与 Nova 侧不对称的一点：Nova 的 margin 可 env 覆盖（再标定免改代码），本常量是
// 编译期值、再标定要改这里重编。
export const MIN_GRACE_MARGIN_MS = 7500;
/** 本 worker 支持的测试目标（ADR 0049 决策 1）：桌面网页，加 Android 与 iOS 的网页与应用（Appium 经 Device Farm 远程访问
 *  会话）。设备条目带 max_session_s，取自设备常量模块（会话硬上限减停止宽限的硬上限，ADR 0049 决策 4）；桌面条目不带
 *  （ADR 0049 决策 2）。**单一来源**：能力自述报它，建会话前的自检（ADR 0049 决策 7）也核它。键是协议面的 snake_case
 *  （ui_kinds / max_session_s），不是注册面的驼峰（uiKinds），与 Nova 侧 WORKER_TARGETS 形状相同（Nova 只有桌面网页一条）。 */
export const WORKER_TARGETS: ReadonlyArray<{ device: string; ui_kinds: string[]; max_session_s?: number }> = [
  { device: "desktop", ui_kinds: ["web"] },
  { device: "android", ui_kinds: ["web", "app"], max_session_s: MAX_SESSION_S },
  { device: "ios", ui_kinds: ["web", "app"], max_session_s: MAX_SESSION_S },
];

/** 本引擎自报给组合根的 grace 下限，单位秒（ADR 0024「引擎自报下限」，经 `--capabilities` 出口，
 *  契约见 ADR 0036「5. worker 自述：--capabilities」）。
 *
 *  Midscene worker 没有「可控的单 act 超时」概念（不像 Nova 的 act 时间上界），但它的 **SIGTERM 收尾路径
 *  本身有确定的超时预算**，grace 必须够这条路径运行完：不够则收尾被 SIGKILL 截断——会话释放本身有
 *  「先释放会话、再提前上传」的排序 + Stop 预算保底不泄漏，但 worker 退不干净、中断兜底的引擎报告提前上传与
 *  截图队列排空会被拦腰砍掉。故下限是收尾最坏串行路径各段预算之和加余量，**由那些预算常量算出、
 *  不另写字面量**：谁改某段预算，下限自动跟着走（曾把这个下限当常量放在组合根，收尾里加进截图队列排空后
 *  只能靠人记得把它改大；漏一次就是 grace 默默不够、收尾被硬杀截断）。
 *
 *  两条收尾路径（ADR 0049 决策 5、ADR 0051 决策 5），**取较大者、不相加**——一个 job 的目标是确定的，worker 进程只会走
 *  其中一条，相加会把永远不在同一进程里执行的段算进宽限：
 *  - 桌面：shutdownSequence 的逐段串行（见该函数与桌面实现的 interrupt 释放）——在途窗口兜底 INFLIGHT_SETTLE_MS
 *    + 会话 Stop STOP_SESSION_BUDGET_MS + 关 browser BROWSER_CLOSE_BUDGET_MS（三者随桌面实现住在 worker/surface-desktop.mts）
 *    + 中断兜底报告提前上传的单次上传超时 UPLOAD_TIMEOUT_MS + 截图队列退出段排空 QUEUE_DRAIN_EXIT_MS（ADR 0042 决策一：排在
 *    会话释放之后、与兜底提前上传并列）+ MIN_GRACE_MARGIN_MS，按当前常量为 31 秒；
 *  - 设备：终结四阶段的前三段（等在途 Create、终结核对、释放，常量在 device/limits.mts）加同一组尾段（上传超时、退出段排空、
 *    余量），按当前常量为 63.5 秒。尾段的三个常量只有一份，由这里传给 deviceGraceSeconds。
 *  结果不取整（文档写「约 64 秒」时以算出的 63.5 为准）。scenario 边界提前上传的 SCENARIO_LOG_SNAPSHOT_BUDGET_MS
 *  **不在其中**——它在主流程执行、不在收尾路径上（见该常量注释）。 */
export function minGraceSeconds(): number {
  const desktopMs = INFLIGHT_SETTLE_MS + STOP_SESSION_BUDGET_MS + BROWSER_CLOSE_BUDGET_MS
    + UPLOAD_TIMEOUT_MS + QUEUE_DRAIN_EXIT_MS + MIN_GRACE_MARGIN_MS;
  const device = deviceGraceSeconds({ uploadMs: UPLOAD_TIMEOUT_MS, queueDrainExitMs: QUEUE_DRAIN_EXIT_MS, marginMs: MIN_GRACE_MARGIN_MS });
  return Math.max(desktopMs / 1000, device);
}

// 惰性（用 getBaseUrl→getRegion，fail-loud 下沉到 main 用时，非 import 时——见 agentcore-sigv4 注释）。
function modelConfig() {
  return {
    MIDSCENE_MODEL_NAME: MODEL,
    MIDSCENE_MODEL_BASE_URL: getBaseUrl(),
    MIDSCENE_MODEL_API_KEY: "unused",
    // 模型家族（ADR 0044 决策 2）：决定 Midscene 用哪套提示词与请求参数。由 modelFamily() 按模型 id 推断、
    // 可经 env 显式指定，**取代旧的单一家族硬开关 `MIDSCENE_USE_QWEN3_VL: "true"`**（模型不再只有一个）。
    // 已核 SDK 1.12.8 侧这两者语义等价：node_modules/@midscene/shared/dist/lib/env/ 下 constants.js 的
    // DEFAULT_MODEL_CONFIG_KEYS 把 modelFamily 槽绑到 MIDSCENE_MODEL_FAMILY，parse-model-config.js 的
    // parseOpenaiSdkConfig 取 `provider[keys.modelFamily] || legacyConfigToModelFamily(provider)`，而后者对
    // MIDSCENE_USE_QWEN3_VL 的映射结果正是 "qwen3-vl"——两条路汇进同一个 modelFamily 字段、下游适配同一条，
    // 且显式键优先于 legacy 推导。取值合法性由 SDK 自己校验（它按版本有一张 family 可取值表）。
    MIDSCENE_MODEL_FAMILY: modelFamily(),
  };
}

// 事件出口抽进 ../lib/event-sink.mts（ADR 0024「I/O 边缘可注入接口」）：可注入、可测；subprocess 态写
// EVENTS_FD fd（无则回落 stdout 调试）。emit 为 async（合理不对称：为 Fargate 化的 DDB PutItem（aws-sdk-js）
// 预留；Nova 那个引擎 emit 同步）+ 作参数注入 runStep/runScenario（两个引擎统一打桩机制），不再是模块级函数。
// log（stderr 诊断）**不属那三条 I/O 边、不进 sink**（协议传输面 vs 诊断面物理隔离，ADR 0024），保模块级。
function log(msg: string): void {
  // 诊断行常拼着异常文本，可能带设备端点、预签名地址或隧道令牌：写出前经 redactSecrets（ADR 0051 决策 11、0035 决策 5）
  process.stderr.write(redactSecrets(msg) + "\n");
}

// 中断兜底的安全点提前上传（ADR 0029 上传时机第三级的 handler 兜底，为 Fargate 预演）——从 onSignal 提出为可测纯函数
// （对称 Nova 把 _on_signal 提到模块级、供 test_interrupt_model/process 测；否则 main() 内闭包无法单测，是
// 「该对称却漏」的测试缺口）。**调用点在 onSignal 里必须排在 cleanup 之后**（会话释放优先铁律，ADR 0024）——
// 本函数只管「提前上传那一步」的决策，不含 cleanup/退出，顺序由调用方保证。
// 决策：① reportFile 空窗（首个 AI task 前未置）→ 跳过（无 report 可传）；② 有 → best-effort 提前上传（读盘上那份
// 增量 report）、**失败吞+log、绝不抛**（提前上传是保险、不该影响退出码/退出流程；no-op local 下 snapshotReport 自返回）。
// 救的是「首个/当前 act 中途、无 prior step_done」这格：主流程卡在 await aiAct、step_done 提前上传从未触发、S3 一无
// 所有，而盘上已有截至最后一个已返回 AI 调用的一致 report。Node handler 是事件循环回调、能安全 await 读盘上传
// （Nova 因 greenlet 做不到、Midscene 能——关键不对称）。
async function interruptSnapshot(
  uploader: { snapshotReport: (p: string) => Promise<void> },
  reportFile: string | null | undefined,
  logFn: (m: string) => void = log,
): Promise<void> {
  if (!reportFile) return;  // 空窗：无 report 可传
  try {
    await uploader.snapshotReport(reportFile);
  } catch (e) {
    // 产品面一行：发生了什么 + 不影响什么（best-effort、失败吞不抛的判据见上函数头）。
    logFn(`worker: 引擎原生报告未能在中断退出前上传（不影响判定与退出；这次中断的引擎报告可能看不到）：${(e as Error).message}`);
  }
}

// 截图后台队列的有界排空（ADR 0042 决策一）——与 interruptSnapshot 结构相同的可测小函数：只管「排空那一步」的
// 决策（排不完记一行、放弃），**位置**（必须排在会话释放之后）由调用方保证。
// best-effort、**绝不抛**：收尾路径上抛会跳过后面的 exit / flush；排不完不是错，正常路径还有整目录 flush 兜。
// flushFollows 由调用点声明「我后面还跟着整目录 flush 吗」（不在这里猜调用栈）。分句按调用点是否真跟着整目录
// flush：只在会 flush 的路径上说「改由收尾上传」（ADR 0039 面一的文案不变量例外条，两引擎措辞一致）；不跟 flush 的
// 提前退出路径说这些截图已放弃。必传、无默认——默认值会让新调用点静默拿到一句可能为假的承诺。
async function drainArtifactQueue(
  uploader: { drain: (timeoutMs: number) => Promise<boolean> },
  budgetMs: number,
  flushFollows: boolean,
  logFn: (m: string) => void = log,
): Promise<void> {
  try {
    if (!(await uploader.drain(budgetMs))) {
      // 产品面一行：发生了什么 + 剩下的谁传 / 还能看什么 + 不影响什么。
      logFn(flushFollows
        ? "worker: 部分证据截图未能在收尾预算内传完（剩余的改由收尾统一上传；判定与报告不受影响）"
        : "worker: 部分证据截图未能在收尾预算内传完（已放弃，不影响判定结果；仍可看引擎原生报告）");
    }
  } catch (e) {
    // 产品面一行，与上面「排不完」那行措辞一致（best-effort、绝不抛的判据见上函数头）。
    logFn(`worker: 证据截图收尾上传失败（不影响判定结果；仍可看引擎原生报告）：${(e as Error).message}`);
  }
}

// SIGTERM/SIGINT 收尾序列（ADR 0024 终止契约 + 0029 中断兜底提前上传 + 0042 截图队列排空）——从 onSignal 提出为可测函数（依赖注入），
// 对称 Nova 把 _on_signal 提到模块级供 test_interrupt_model/process 测。**锁住关键顺序不变量**：
//   会话释放（cleanup）**必须先于**中断兜底提前上传（interruptSnapshot）与截图队列排空（drainArtifactQueue）
//   ——ADR 0024「会话释放优先」铁律，那两件都是 best-effort、绝不延迟会话释放（退化网络下各自挂满自己的
//   预算，也不该让会话多泄漏那么久）。
// 返回该退出的退出码（cleanupFailed→1 让泄漏可观测、否则 0）；不自己 process.exit（交调用方，便于测试不真退进程）。
// deps 全注入（cleanup/getCleanupFailed/uploader/reportFile...）→ 单测可传 spy 断言调用序列，无需真信号/真进程。
// cleanup 即界面接缝的 interrupt 释放（ADR 0052 决策 2）：等在途的建会话请求（桌面 INFLIGHT_SETTLE_MS，设备终结阶段 1）、为
// 结果未知的请求发 attempted 事件、为每个会话发 session_closed 都在它里面，桌面与设备共用这一条序列；它对应 ADR 0051 决策 5
// 终结四阶段的前三段，本函数的提前上传与排空是阶段 4。
interface ShutdownDeps {
  cleanup: () => Promise<void>;        // 释放会话（**先执行**）
  uploader: {
    snapshotReport: (p: string) => Promise<void>;
    drain: (timeoutMs: number) => Promise<boolean>;  // 截图后台队列的有界排空（ADR 0042 决策一）
  };
  reportFile: () => string | null | undefined;  // 惰性读（agentRef 可能收尾时才有值）
  getCleanupFailed: () => boolean;     // cleanup 内部副作用写的泄漏标记
  logFn?: (m: string) => void;
}
async function shutdownSequence(deps: ShutdownDeps): Promise<number> {
  const logFn = deps.logFn ?? log;
  logFn("worker: signal received, releasing session(s)");
  await deps.cleanup();                                          // ① 会话释放优先（ADR 0024 铁律）
  await interruptSnapshot(deps.uploader, deps.reportFile(), logFn);  // ② 提前上传排其后（best-effort、不延迟①）
  // ③ 截图后台队列的有界排空（ADR 0042 决策一）：同样排在①之后、与②并列。本路径**不 flush**，队列里
  //    没传完的截图就此丢，故给一小段计入 grace 的预算把在途的落地。
  await drainArtifactQueue(deps.uploader, QUEUE_DRAIN_EXIT_MS, false, logFn);
  const failed = deps.getCleanupFailed();
  logFn(`worker: session shutdown complete after signal${failed ? " (WITH FAILURE)" : ""}`);
  return failed ? 1 : 0;
}

interface Step { index: number; keyword: string; text: string; argument?: unknown }
interface Scenario { id: string; name: string; steps: Step[] }
// 与 lib/job-source.mts 导出的 Job 同一形状（键集固定：schemaVersion / timeoutS / target / deviceRequest，ADR 0024 / 0048 决策 3），只把 scenarios 收窄成本文件的 Scenario
interface Job extends Omit<WireJob, "scenarios"> { scenarios: Scenario[] }


// Midscene/Bedrock 原生量 token 累计（ADR 0024：engine 只报原生量，core 不算美元）。
// 取 SDK 公开的 `agent.metrics.totalTokens`（MidsceneUsageMetrics）——**自 agent 建起的累计快照**，SDK 随 task
// 推进把每次模型调用的 usage 折进去（含 searchAreaUsage、按 request_id 去重，比旧的手工求和更全）。
// **在 metrics 与构造项 onLLMUsage 回调之间选 metrics，二选一不两套**：metrics 是快照、幂等可重复读，正好配
// 下面「step 前后各读一次、差即本 step」的算法；onLLMUsage 是每次调用推一次的回调，worker 得自己攒计数器、
// 管清零与归属，多一份可变状态却换不到更多信息。
// 累计快照是**整个 agent 会话**的——故按 step 取 token 必须用"增量"：step 运行前记一次累计、运行后再记一次、差值
// 才是本 step 的 token。否则：取末次 usage 会少报（多票断言只算最后一票，欠计 (N-1)/N）；或求和全部会双计
// （把前面 step 的也算进来）。返回 token 累计和。
// `?? 0` + try/catch 守「拿不到就不报」：本函数在 runStep 的 try **之外**被调（记起点），冒泡会连 step_done 都发不出。
function cumulativeTokens(agent: Agent): number {
  try {
    return agent.metrics?.totalTokens ?? 0;
  } catch {
    return 0;
  }
}

// 本 step 的 token 成本是运行后累计减运行前累计的增量。增量 0（无新 usage）→ undefined（不假装 0）。
function stepCost(beforeTokens: number, agent: Agent): Record<string, unknown> | undefined {
  const after = cumulativeTokens(agent);
  const delta = after - beforeTokens;
  return delta > 0 ? { tokens: delta } : undefined;
}

// 两个非 job 入口（--capabilities 自述 / --match-steps 查询）的 stdout payload 写出（ADR 0036「stdout 一行 JSON 即退」）：
// **必须等真 flush 完才能退**，否则 pipe 下大 payload 在 64KB 处静默截断且 rc 仍是 0——组合根只能报「输出非
// JSON」、真因不可见（ADR 0036 的 best-effort 降级把它吞成 plan 无标注）。两种直觉写法都不够：
//   - `process.stdout.write(s)` 后紧跟 process.exit：pipe 上 stdout 是异步写，exit 不 flush 未写完的尾部；
//   - `fs.writeSync(1, s)`：worker 进程里装着 tsx 的 ESM loader（`bin.mts` 进程内 `registerTsx()`；`npm test`
//     经 `node --import tsx` 同样如此），tsx 把 fd 1 置成非阻塞，writeSync 对 pipe 只写满内核缓冲就返回
//     **部分写字节数、且不重试**（实际运行中实测 1MB 只出 65536）。
// 故走 write 回调等 libuv 真写完（背压/EAGAIN 交事件循环），再由统一出口 process.exit。
async function writeStdoutFlushed(s: string): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    process.stdout.write(s, (e) => (e ? reject(e) : resolve()));
  });
}

// `--no-report` 方式（组合根经 env GHERKAI_NO_ARTIFACTS=1 告知，ADR 0037 决策 3）：**不生成、不上报**引擎原生产物——
// 关 agent 的 generateReport、不提前上传 log、不带 report ref。Midscene SDK 即便不出 report 也可能往 run 目录写 log/dump
// （相对 cwd 的 ./midscene_run），故这一方式下若无 MIDSCENE_RUN_DIR 就把它导到一次性临时目录、不进使用方 CWD（SDK 内部行为，不上报）。
const NO_ARTIFACTS = process.env.GHERKAI_NO_ARTIFACTS === "1";

/** scope 末整目录 flush 的根：`--no-report` 方式返回 undefined（不上报任何原生产物，ADR 0037 决策 3——这一方式下
 *  MIDSCENE_RUN_DIR 只是给 SDK 内部 log/dump 的一次性落点，flush 会把它们传上 S3、违背「不上报」）。导出供单测。 */
export function artifactFlushRoot(): string | undefined {
  if (NO_ARTIFACTS) return undefined;
  const runRoot = process.env.MIDSCENE_RUN_DIR;
  return runRoot ? path.resolve(runRoot) : undefined;
}

/** 两种 Agent 共用的构造项（ADR 0052 决策 7：设备 Agent 与桌面 PlaywrightAgent 同用这几项），经 SurfaceDeps.agentOpts 交给
 *  选中的实现，实现在其上只加自己的项：桌面加 forceChromeSelectRendering（见桌面实现），设备加重规划上限（缺省 12、同名 env
 *  覆盖、非法值在 main 读 job 之后即报错，ADR 0044 决策 2；桌面不传，由 SDK 按同名 env 自行处理）。提成模块级函数（不碰
 *  page/browser）好让单测锁住这几个开关；**不纯、别随处调**——`modelConfig()` 里的 getBaseUrl 读 AWS_REGION（缺则
 *  fail-loud 抛），故只在构造界面接缝时调（与 AgentCore 客户端的构造同一时刻，都在建会话之前）。 */
function sharedAgentOpts(): AgentOpt {
  return {
    generateReport: !NO_ARTIFACTS,  // --no-report：不出 report.html（ADR 0037 决策 3）
    // 让 SDK 把每张截图另落成独立文件 `report/screenshots/<id>.<扩展名>`（ADR 0042 决策一）：evidence 只
    // 引用这些文件、零解码零复制，从而不必读 ScreenshotItem.base64（SDK 每个 task 后即 flush 报告并置空它，
    // 之后读会对多 MB 的 report.html 做同步全文扫描且找不到即抛）。副作用是 report 目录多出
    // `<n>.execution.json`，随 scope 末整目录 flush 一并上传，接受。
    // **必须与 generateReport 同真同假**：SDK 在 generateReport=false 且此项为 true 时直接抛
    // （`--no-report` 方式不产 evidence，正好同为 false）。两种 Agent 都受这条约束，故放在共用项里。
    persistExecutionDump: !NO_ARTIFACTS,
    modelConfig: modelConfig(),
    createOpenAIClient: async () => new OpenAI({ baseURL: getBaseUrl(), apiKey: "unused", fetch: sigv4Fetch }) as any,
  };
}

/** 按 job 目标选一次界面接缝实现（ADR 0052 决策 2、3）：主流程里唯一看目标的地方，之后的 step 循环与收尾只经接缝。
 *  桌面实现静态加载；设备实现在这里动态加载，桌面路径与能力自述因此不加载 WebdriverIO 与 Device Farm SDK。 */
async function createSurface(device: string, deps: Omit<SurfaceDeps, "agentOpts">): Promise<TargetSurface> {
  const full: SurfaceDeps = { ...deps, agentOpts: sharedAgentOpts() };
  if (device === "desktop") return createDesktopSurface(full);
  const mod: DeviceSurfaceModule = await import("../device/surface.mjs");
  return mod.createDeviceSurface(full);
}

/** scope 级的执行前失败与终止都发这一形状的 scope_done（ADR 0051 决策 4：status / errorType / message 同进同出，status 只取
 *  error）。sessionId 为 undefined 时不带这个键（建会话前的自检与完整性判据）；reportRefs 给了才带（scope 级产物链接）。 */
function scopeErrorEvent(scopeId: string, sessionId: string | null | undefined, t: ScopeTermination,
                         reportRefs?: ReportRef[]): Record<string, unknown> {
  return {
    type: "scope_done", scopeId,
    ...(sessionId !== undefined ? { sessionId } : {}),
    status: "error", errorType: t.errorType, message: t.message,
    ...(reportRefs !== undefined ? { reportRefs } : {}),
  };
}

/** 会话预热失败（执行前失败的一种，ADR 0051 决策 13）：在主流程 try 里抛出，由 exitAfterFailure 先释放会话、再排空队列、再发
 *  scope_done{status: error}，不发 scope_started、不经网络专用退出码（ADR 0051 决策 4）。走 exitAfterFailure 而不是 scope 终止
 *  出口，是为了桌面这条出口的次序不变（ADR 0051 决策 5「桌面执行前失败出口次序不改」）；设备的预热失败同走这里，见该函数。 */
export class ScopeTerminationError extends Error {
  constructor(readonly termination: ScopeTermination) {
    super(termination.message);
    this.name = "ScopeTerminationError";
  }
}

export async function main(): Promise<number> {
  if (NO_ARTIFACTS && !process.env.MIDSCENE_RUN_DIR) {
    process.env.MIDSCENE_RUN_DIR = fs.mkdtempSync(path.join(os.tmpdir(), "gherkai-midscene-"));
  }
  // 使用方 steps/ 目录的注册（ADR 0037 决策 4）：**内建脚手架之后**（模块顶 import 已注册完）、
  // **两个非 job 入口与 job 循环之前**——故 --capabilities / --match-steps / plan 标注都反映使用方定制
  // （ADR 0036「真值单一」不变：注册表是内建加使用方）。加载失败 fail-loud（抛 → bin 一行 stderr + 非零退出）。
  await loadUserSteps();

  // 模型家族的启动期校验（ADR 0044 决策 2）：推不出即抛 → bin 一行 stderr + 非零退出。**位置 load-bearing**：
  // 在任何入口分派之前，故 `--capabilities` 这条 run 前置检查也会把坏配置挡下——不然要等到 job 模式里已经建好
  // 云端浏览器会话、第一次调模型时才炸。返回值不用（真正取值在构造界面接缝时的 modelConfig()）；这一步只为早失败。
  modelFamily();

  // 批量 match 查询（ADR 0036 决策 4，plan 命中标注）：stdin 一行 JSON 数组（step 文本）→ stdout 一行
  // 逐条命中结果。匹配语义留在 worker（CLI 零复刻）；同样不建会话、零 AWS。
  if (process.argv.includes("--match-steps")) {
    const chunks: Buffer[] = [];
    for await (const c of process.stdin) chunks.push(c as Buffer);
    const items: MatchItem[] = JSON.parse(Buffer.concat(chunks).toString("utf-8"));  // {keyword, text}[]；旧版 CLI 给裸字符串
    await writeStdoutFlushed(JSON.stringify(matchBatch(items)) + "\n");
    return 0;
  }
  // 引擎能力自述（ADR 0036「5.」）：一个 JSON 对象即退，同样不建会话、不读 stdin、零费用。
  // min_grace_s 是本引擎收尾路径要的 grace 下限（ADR 0024「引擎自报下限」：真值住算它的这一侧，
  // 组合根只查询后聚合、不持引擎特定常量）。deterministic_steps 是注册表清单（ADR 0036「2.」：内建脚手架
  // 在模块顶 import 时注册、使用方 steps 上面刚加载完，此刻注册表即真值）。model_id 是起 job 时真交给
  // Midscene SDK 的模型名，即 modelConfig() 的 MIDSCENE_MODEL_NAME，与它同源引用 lib/agentcore-sigv4 的 MODEL
  // 常量、此处不另写字面量（否则自述会与实际用的模型漂移，而 doctor 正是拿这个键显示「当前用哪个模型」）。
  // **加键不加入口**（ADR 0036「5.」）：新增自述项都是本对象的新键、不再开第二个 flag——组合根一次 spawn
  // 就同时拿到「steps 加载成功 / 清单 / grace 下限 / 目标 / 模型」；targets 见 WORKER_TARGETS（ADR 0049 决策 1）。
  if (process.argv.includes("--capabilities")) {
    await writeStdoutFlushed(JSON.stringify({
      schema_version: PROTOCOL_SCHEMA_VERSION,  // 协议版本一个数、两个方向各带（ADR 0024）
      engine: ENGINE,  // 与 evidence 报的引擎名同源，不另写字面量
      min_grace_s: minGraceSeconds(),
      targets: WORKER_TARGETS.map((t) => ({ ...t, ui_kinds: [...t.ui_kinds] })),  // ADR 0049 决策 1
      deterministic_steps: listRegistry(),
      model_id: MODEL,
      [SESSION_WARMUP_KEY]: true,  // 支持隧道会话预热（ADR 0051 决策 13；0049 决策 1）：本机 --expose-local 的预检据此放行
    }) + "\n");
    return 0;
  }

  // 早期信号护栏（对称 Nova：handler 先于 JobSource.read 装载，ADR 0024）——S3 态下 read 含一次网络往返，
  // 窗口内 SIGTERM 若走 Node 默认处置会以信号终止（非 0）→ adapter 误归 engine_error。此阶段无会话、无产物，
  // 直接以退出码 0 干净退出（零事件 + exit 0，core 判 error 不误归因）；真正的 onSignal（提前上传+释放会话）建好后替换本 handler。
  const earlySignal = () => process.exit(0);
  process.on("SIGTERM", earlySignal);
  process.on("SIGINT", earlySignal);

  // I/O 边缘可注入接口（ADR 0024）：job 入口 / 事件出口从内联收进 lib 组件，subprocess 态即读 stdin、写 EVENTS_FD。
  const raw = await JobSource.fromEnv().read();
  // 重规划上限覆盖键的启动期校验（ADR 0044 决策 2）：非法值即抛 → bin 一行 stderr + 非零退出、点名该键。位置在读 job 之后、
  // 建界面接缝之前，任何会话都还没建；桌面与设备都校验，只有设备实现把取值经构造项传给 SDK。返回值不用，这一步只为早失败。
  replanningCycleLimit();
  const eventSink = EventSink.fromEnv();  // main 级单例（对称 uploader）；作参数注入 runScenario/runStep

  // 建会话前的自检（ADR 0049 决策 7；ADR 0024 协议版本）**先于读 job 行的任何别的键**：先核 schemaVersion（不等于本 worker 认的即版本
  // 不一致），再用与能力自述同一份 WORKER_TARGETS 核对 Job 的目标与墙钟预算（timeoutS 只在这里被读，不计时、不自停）。别的版本写出的
  // job 行连 scope 的形状都不保证，先取它会把「版本不一致」变成一个 TypeError。不满足即按执行前失败的统一规则（ADR 0051 决策 4）发
  // scope_done{status: error, errorType: precheck_failed}、不发 scope_started、不建会话、以 0 退出——零会话费用；core 据此合成 SKIPPED
  // 明细并按 scope 级 error 判定。scopeId 尽力取（形状未知时记 unknown）。
  const rejected = precheckJob(raw as Partial<Pick<Job, "schemaVersion" | "target" | "timeoutS">>, WORKER_TARGETS);
  if (rejected !== null) {
    log(`worker: precheck failed — ${rejected}`);
    const rawScope = (raw as { scope?: { id?: unknown } } | null)?.scope;
    const scopeId = rawScope && typeof rawScope === "object" && typeof rawScope.id === "string" && rawScope.id ? rawScope.id : "unknown";
    await eventSink.emit(scopeErrorEvent(scopeId, undefined, { errorType: "precheck_failed", message: rejected }));
    return 0;
  }
  const job = raw as Job;
  // definition 完整性判据（ADR 0035「边界与不变量」；ADR 0051 决策 13）：隧道模式下额外请求头与会话预热地址成对下发——收到请求头却没有
  // 预热地址，是旧后端丢字段的部署残缺（开发版本混搭），按执行前失败发 scope_done{precheck_failed}、不建会话、零会话费用。
  const warmupUrl = process.env[SESSION_WARMUP_URL_ENV] || null;
  if (process.env[EXTRA_HTTP_HEADERS_ENV] && !warmupUrl) {
    log(`worker: precheck failed — ${INCOMPLETE_DEFINITION_MESSAGE}`);
    await eventSink.emit(scopeErrorEvent(job.scope.id, undefined, { errorType: "precheck_failed", message: INCOMPLETE_DEFINITION_MESSAGE }));
    return 0;
  }

  return await runScope(job, {
    emit: (ev) => eventSink.emit(ev),
    // 产物 S3 上传器（ADR 0029，对称 Nova 的模块级 _uploader）：cloud 上传+删本地报 s3://，local no-op 报 file://。
    uploader: ArtifactUploader.fromEnv(),
    warmupUrl,
    createSurface: (deps) => createSurface(job.target.device, deps),
    installSignalHandler: (onSignal) => {
      // 交接：先挂真 handler 再摘早期护栏（顺序不能反——Node 在某信号最后一个 listener 被移除时恢复
      // 默认处置，先摘会开出「SIGTERM 走内核默认动作→非0退出→误归 engine_error」的窗口；重叠期两个
      // handler 并存无害：此刻尚未建会话、earlySignal 的 exit(0) 与 onSignal 语义一致）。
      process.on("SIGTERM", onSignal);
      process.on("SIGINT", onSignal);  // Ctrl-C 也走同一路径（提前上传+释放会话），对称 Nova 已纳入 SIGINT
      process.removeListener("SIGTERM", earlySignal);
      process.removeListener("SIGINT", earlySignal);
    },
    exit: (code) => process.exit(code),
  });
}

/** runScope 的进程 I/O：main 给真实的（env 里的事件出口与上传器、进程信号、process.exit），回归测试注入假的。
 *  createSurface 是选好目标实现的工厂（main 里即 createSurface 按 job.target.device 选一次）；它收到的构造参数缺 agentOpts，
 *  由选择处按目标补上。 */
export interface ScopeIo {
  emit: (event: Record<string, unknown>) => Promise<void>;
  uploader: ArtifactUploader;
  /** 会话预热地址（env GHERKAI_SESSION_WARMUP_URL，ADR 0051 决策 13）；没有即 null。 */
  warmupUrl: string | null;
  createSurface: (deps: Omit<SurfaceDeps, "agentOpts">) => Promise<TargetSurface>;
  /** 换上收尾用的信号处理（main：SIGTERM / SIGINT 交接，见 main）。 */
  installSignalHandler: (onSignal: () => void) => void;
  /** 收尾序列结束后的进程退出（main：process.exit）。 */
  exit: (code: number) => void;
}

/** 一个 scope 的执行：构造界面接缝、建立被测对象、预热、逐个 scenario 执行、收尾。返回退出码（ADR 0051 决策 5：0 表示内容完整且
 *  全部会话已确认停止；1 表示有会话没能确认停止或发过 attempted 事件；网络专用退出码只出现在桌面建连重试耗尽且会话已全部
 *  确认停止时）。主流程不写按设备的条件分支：差异都在接缝实现里（ADR 0052 决策 2）。
 *
 *  四条出口，各自的次序：
 *  - 正常收尾：最后一个 scenario_done → agent.destroy 与 scope 级报告上传 → 释放（每会话 session_closed）→ scope_done →
 *    排空截图队列 → 整目录 flush（ADR 0051 决策 5；桌面原有次序）；
 *  - scope 终止出口（acquire 返回的执行前失败、会话丢失、scenario 前核对终止）：同正常收尾，scope_done 带 status / errorType /
 *    message；执行前失败时还没有 agent，从释放开始。三者在实践中只来自设备实现（ADR 0051 决策 4、5；ADR 0052 决策 2）；
 *  - 会话预热失败与其余异常：exitAfterFailure（释放 → 排空 → scope_done 或退出码），不 flush（见该函数）；
 *  - 停止信号与设备接缝的进程级兜底：shutdownSequence（interrupt 释放 → 中断兜底提前上传 → 排空 → 退出），之后本函数不再发任何
 *    step、scenario 或 scope 事件（ADR 0051 决策 5 阶段 1）；会话事件由接缝经未门控的 io.emit 照发。 */
export async function runScope(job: Job, io: ScopeIo): Promise<number> {
  const scope = job.scope;
  const uploader = io.uploader;
  // 进入终结（停止信号或设备接缝的进程级兜底）之后，在途的 step 不再发 step_done、也不发 scope_done（ADR 0051 决策 5 阶段 1）：
  // 主流程与 runScenario / runStep 经这个门控的出口发事件；接缝的会话事件走 io.emit 本身，终结期间照发。
  let finalizing = false;
  const sink = { emit: async (e: unknown): Promise<void> => { if (!finalizing) await io.emit(e as Record<string, unknown>); } };
  let surface: TargetSurface | undefined;
  // agent 引用上提到 handler 可见（ADR 0029 中断兜底提前上传：handler 里读 agent.reportFile 传那份增量 report）。
  let agentRef: Agent | undefined;
  // 最近一次释放的结果：exitAfterFailure、正常收尾与信号收尾都读它定退出码（释放失败的判据由接缝实现保持为累积状态）。
  let released: ReleaseOutcome = { releaseFailed: false, reportRefs: [] };
  const release = async (mode: ReleaseMode): Promise<ReleaseOutcome> => {
    if (surface === undefined) return released;
    released = await surface.release(mode);
    return released;
  };

  // SIGTERM/SIGINT 与设备接缝的进程级兜底：清理会话再退（防会话泄漏后持续计费）。收尾序列提出为可测的 shutdownSequence
  // （cleanup 先于提前上传的顺序不变量在那里被单测锁住）；此处只做「守卫去重 + 门控事件 + 退出」这层外壳。
  const onSignal = async (): Promise<void> => {
    if (finalizing) return;
    finalizing = true;
    const code = await shutdownSequence({
      cleanup: async () => { await release("interrupt"); },
      uploader,
      reportFile: () => agentRef?.reportFile,
      getCleanupFailed: () => released.releaseFailed,
    });
    io.exit(code);
  };

  // 构造在建会话之前：只组装、不做 I/O；构造期错误（缺本次运行的编号、AWS_REGION 未设、设备侧的覆盖值非法）直接抛出，
  // 由 bin 写一行 fatal、以 1 退出，不发任何事件。
  surface = await io.createSurface({
    job, emit: io.emit, log, uploader, artifactRoot: artifactFlushRoot(),
    requestFinalization: () => { void onSignal(); },
  });
  io.installSignalHandler(() => { void onSignal(); });

  const reportRefs: ReportRef[] = [];
  let termination: ScopeTermination | null = null;
  // 被测对象就绪之后的部分：预热、scope_started、逐个 scenario、agent.destroy 与 scope 级报告上传。抛出的异常落到下面的 catch。
  const runAcquired = async (agent: Agent, sessionId: string): Promise<void> => {
    agentRef = agent;

    // 会话预热（ADR 0051 决策 13）：第一个 scenario 之前导航预热地址一次换会话 cookie，不按 scenario 重做。失败不发 scope_started、
    // 以 ScopeTerminationError 穿出本 try（释放会话照常），catch 里按归因发 scope_done；预热自己吞掉导航异常、不进建连重试域、
    // 不退网络专用退出码（ADR 0028 分类红线）。
    if (io.warmupUrl) {
      const failure = await surface!.warmup(io.warmupUrl);
      if (failure !== null) {
        log(`worker: tunnel warmup failed — ${failure.errorType}: ${failure.message}`);
        throw new ScopeTerminationError(failure);
      }
      log("worker: tunnel warmup ready");  // 就绪也留一行：真实执行的核对与排障都要看得见预热发生过（离开预热页在接缝的预热内）
    }

    // sessionId 随 scope_started 即回传（不只等 scope_done）——超时/SIGTERM 中途打断时 scope_done 不会 emit，
    // 但血缘已先随首事件落到 core（ADR 0028 观测缺口修复，对称 Nova）；会话事件更早一步（ADR 0051 决策 4）。
    await sink.emit({ type: "scope_started", scopeId: scope.id, sessionId });  // 三级时长起点（越过此点不再重试建连）
    // scope 内串行执行 scenarios，共享同一会话（ADR 0019/0024）
    const votesN = job.assertionVotes ?? 1;  // AI 断言投票次数（ADR 0014/0024，组合根经 --assertion-votes 设）；缺省 1 表示单次判定、不做抖动检测
    // report 提前上传的 mtime 去重状态：**scope 级共享**（单份 report.html 跨 scenario 累积增长，共享才准）。
    const snapState = { mtime: -1 };
    // scenario 边界 log 提前上传的 per-file mtime 去重表（ADR 0029 上传时机第四级）：**scope 级共享**（log append-only
    // 单调增长、跨 scenario 累积，只传真变过的 topic 文件、不重发未变 log）。log 落 `<MIDSCENE_RUN_DIR>/log/`。
    const logSeen = new Map<string, number>();
    const logDir = (!NO_ARTIFACTS && process.env.MIDSCENE_RUN_DIR) ? path.join(path.resolve(process.env.MIDSCENE_RUN_DIR), "log") : undefined;
    // step 级机读证据的注入（ADR 0042 决策一）：落点与 flush 根同一判据——`--no-report` 方式（这一方式也没开
    // persistExecutionDump、无截图文件可引）或没给产物落点 → undefined，即本 run 不产 evidence。
    const evidenceRoot = artifactFlushRoot();
    const evidence: EvidenceHook | undefined = evidenceRoot
      ? { runDir: evidenceRoot, scopeId: scope.id, uploader, logFn: log }
      : undefined;
    const seam: ScopeSeam = { surface: surface!, agent, target: job.target, sessionLost: null };
    for (const [i, sc] of job.scenarios.entries()) {
      // scenario 前核对（ADR 0052 决策 2）：从第二条起、在 scenario_started 之前无条件调用；返回终止即经 scope 终止出口收尾，
      // 这条与后续 scenario 不发任何事件（core 合成 SKIPPED；在途 scenario 不合成，所以必须排在 scenario_started 之前）。
      if (i > 0) {
        const stop = await surface!.preScenarioCheck();
        if (stop !== null) { termination = stop; break; }
      }
      await sink.emit({ type: "scenario_started", scenarioId: sc.id });
      // scope 内 step 短路在 runScenario 内（上游 error 跳过后续、发 step_skipped，ADR 0031 决定六）；
      // act 边界提前上传（report snapshot）也在 runScenario 内 step_done 安全点（ADR 0029，为 Fargate 预演）。
      const statuses = await runScenario(seam, sc.id, sc.steps, votesN, uploader, snapState, sink, evidence);
      await sink.emit({ type: "scenario_done", scenarioId: sc.id, status: aggregate(statuses) });
      // scenario 边界提前上传诊断 log（ADR 0029 上传时机第四级，Midscene 单引擎、为 Fargate 预演）：把该 scenario 期间已在盘、
      // 未传的 log/*.log 提前传进 S3，收窄 log 丢失窗口从「整个 run」到「当前正在执行的 scenario」。best-effort：失败吞、
      // 不阻塞下一 scenario（对齐 report 提前上传）。per-file mtime 去重 + 总墙钟预算在 snapshotLogs 内（退化网络护栏）。
      // no-op（local）下 snapshotLogs 直接返回。report 已由 runScenario 内 step_done 提前上传覆盖，此处只补 log。
      if (logDir) {
        try {
          await uploader.snapshotLogs(logDir, logSeen, SCENARIO_LOG_SNAPSHOT_BUDGET_MS);
        } catch (e) {
          // 产品面一行：**不承诺「收尾再试」**——正常完成路径的 scope 末整目录 flush 会兜一次，但停止信号 /
          // 网络耗尽 / 异常三条提前退出路径只排空队列、不 flush，那句在这些路径上是假的（与 Nova 上传器同一判据）。
          log(`worker: 引擎诊断日志未能提前上传（不影响判定与报告；这些日志可能最终没能上传）：${(e as Error).message}`);
        }
      }
      // 会话丢失序列（ADR 0051 决策 5）：当前 step 已记 error、本 scenario 余下 step 已短路、scenario_done 已发；后续 scenario
      // 不发事件，经 scope 终止出口发 scope_done{status: error, errorType: session_lost}。
      if (seam.sessionLost !== null) { termination = { errorType: "session_lost", message: seam.sessionLost.message }; break; }
    }
    if (termination !== null) log(`worker: scope terminated — ${termination.errorType}: ${termination.message}`);

    // 归集原生报告（ADR 0027 reportRefs）：destroy 后 reportFile finalize，Midscene 出 1 个 html/worker（scope 级）
    // kind=report（产物类型；粒度由挂在 scope_done 表达，ADR 0027）；agent.reportFile 是绝对路径。
    // ref 经 uploader：cloud 上传 S3+删本地报 s3://，local no-op 报 file://（ADR 0029，对称 Nova）。
    await agent.destroy().catch(() => {});
    if (agent.reportFile && !NO_ARTIFACTS) {
      // **scope 级 report 上传 best-effort：失败吞+log、不带 report ref、不 throw**（ADR 0032，对称 Nova summary）——
      // 此刻 scope 判定已 emit 完，report 上传失败（多为 S3 网络瞬时）不该 throw→冒泡到 bin.mts 的统一 catch→worker fatal + exit(1)、
      // 把已执行完的 scope 毁成 worker fatal。对齐同文件 interruptSnapshot/snapshotLogs 提前上传的 best-effort。
      try {
        const ref = await uploader.toReportRef(agent.reportFile);  // 实时上传（不删，留到 flush 整目录删）
        reportRefs.push({ kind: "report", ref, label: "Midscene report" });
      } catch (e) {
        // 产品面一行：判定已 emit 完，这里只丢一个报告链接（不带 report ref、失败吞不抛的判据见上）。
        log(`worker: 引擎原生报告未能上传（不影响判定与报告，报告里少一个引擎报告链接）：${(e as Error).message}`);
      }
    }
  };

  try {
    // 建立被测对象（桌面：建连段含 ADR 0028 的重试，越过 scope_started 即跳出重试域；设备：获取预算内的全部准备）。
    const acquired = await surface.acquire();
    if (!acquired.ready) {
      // 执行前失败（只有设备实现会返回，ADR 0051 决策 4）：不发 scope_started、不发任何 scenario 或 step 事件，经 scope 终止出口按
      // 正常收尾的次序收尾——释放（每会话 session_closed）→ scope_done{status: error} → 排空（ADR 0051 决策 5）。
      termination = acquired.termination;
      log(`worker: target not ready — ${termination.errorType}: ${termination.message}`);
    } else {
      await runAcquired(acquired.agent, acquired.sessionId);
    }
  } catch (e) {
    // 统一出口（exitAfterFailure，deps 注入、单测锁次序）：先释放会话、再排空截图队列，然后按异常种类定事件与退出码。
    return await exitAfterFailure(e, {
      cleanup: async () => { await release("normal"); },
      drain: () => drainArtifactQueue(uploader, QUEUE_DRAIN_EXIT_MS, false),
      cleanupFailed: () => released.releaseFailed,
      networkExhausted: isConnectRetriesExhausted(e),
      scopeId: scope.id,
      sessionId: surface.sessionId(),
      reportRefs: () => released.reportRefs,
      emit: (ev) => sink.emit(ev),
    });
  } finally {
    await release("normal");
  }

  // 释放之后发 scope_done（ADR 0051 决策 5：释放结果经 session_closed 写进判定，scope_done 排在释放之后）；scope 级产物链接
  // 是引擎报告加接缝给的（设备的 device-session.json，桌面为空）。
  const refs = [...reportRefs, ...released.reportRefs];
  await sink.emit(termination === null
    ? { type: "scope_done", scopeId: scope.id, sessionId: surface.sessionId(), reportRefs: refs }
    : scopeErrorEvent(scope.id, surface.sessionId(), termination, refs));
  // scope 末：整目录 flush 剩余产物（report.html 已实时传、跳过；log/ 等一并传）+ 全成功删整目录（ADR 0029）。
  // no-op（local/未注入落点）时直接返回、不碰本地。仅正常完成与 scope 级终止的路径走到此；异常/网络耗尽的 catch 内 return 不 flush
  // ——中断产物保留本地（对称 Nova）。
  const flushRoot = artifactFlushRoot();  // --no-report 方式 → undefined，不 flush（对称 Nova 的 no-artifacts 分支）
  // 先排空后台截图队列、再整目录 flush（ADR 0042 决策一）：flush 只兜漏网的那几张——若反过来，队列里
  // 在途的那张会被 flush 按「还没记 uploaded」重传一次（同 key 冗余）。
  // flushFollows=true：本路径的排空后面就跟着整目录 flush。flushRoot 为 undefined（`--no-report` 方式）时
  // 不 flush，但那一方式与 evidence 落点同一判据（见上 evidenceRoot）、队列必空，这句提示不会发出。
  await drainArtifactQueue(uploader, QUEUE_DRAIN_SCOPE_END_MS, true);
  if (flushRoot) await uploader.flushAndCleanup(flushRoot);
  // 会话释放失败（含发过 attempted 事件）→ 非 0 退出，让 schedule 记 error、泄漏可观测
  // （ADR 0024「会话释放失败可观测」，对照 Nova；ADR 0051 决策 5 的退出码）
  return released.releaseFailed ? 1 : 0;
}

export interface FailureExitDeps {
  cleanup: () => Promise<void>;
  drain: () => Promise<void>;
  cleanupFailed: () => boolean;  // 取值要在 cleanup 之后，故给访问器而不是布尔
  networkExhausted: boolean;
  scopeId: string;
  sessionId: string | null;
  emit: (ev: Record<string, unknown>) => Promise<void>;
  /** 释放之后的 scope 级产物链接（设备的 device-session.json，ADR 0051 决策 8），挂进执行前失败的 scope_done；同样要在 cleanup 之后
   *  取。没给或为空即不带 reportRefs 键（桌面的这条事件与改动前逐字节一致）。 */
  reportRefs?: () => ReportRef[];
  logFn?: (line: string) => void;
}

/** 主流程 try 块抛出后的统一出口（deps 全注入，对称 shutdownSequence；单测据此锁住次序与四种组合）：
 *  ① 释放会话优先（ADR 0024）；② 再排空截图后台队列——网络耗尽与异常这两条提前退出路径都不 flush（中断产物留本地），队列里没传完的
 *  字节就此丢，故给有界预算兜一把；③ 会话预热失败（ScopeTerminationError，ADR 0051 决策 13、决策 4）：归因与 sessionId 恒经
 *  scope_done 传递、释放失败只让退出码为 1（不是 worker fatal、不是退出码 80）；
 *  ④ 建连重试耗尽且会话已释放 → EX_WORKER_NETWORK（ADR 0028），释放失败（会话泄漏）优先级更高；
 *  ⑤ 其余原样重抛到 bin.mts 的统一 catch（打 `worker fatal:` + exit 1，core 记 engine_error）。
 *  ③ 的次序是桌面原有的「释放 → 排空 → scope_done」（ADR 0051 决策 5 桌面执行前失败出口）。设备的预热失败走同一出口：ADR 给设备
 *  执行前失败的次序是「释放 → scope_done → 排空」，两者只差排空的位置，而 scope_started 之前截图队列必为空（还没有 step 入队），
 *  排空即刻返回，两种次序在事件与产物上没有差别；设备 acquire 返回的执行前失败走 runScope 的 scope 终止出口，次序与 ADR 逐字相同。 */
export async function exitAfterFailure(e: unknown, deps: FailureExitDeps): Promise<number> {
  await deps.cleanup();
  await deps.drain();
  const termination = e instanceof ScopeTerminationError ? e.termination : null;
  if (termination !== null) {
    const refs = deps.reportRefs?.() ?? [];
    await deps.emit(scopeErrorEvent(deps.scopeId, deps.sessionId, termination, refs.length > 0 ? refs : undefined));
    return deps.cleanupFailed() ? 1 : 0;
  }
  if (deps.networkExhausted && !deps.cleanupFailed()) {
    (deps.logFn ?? log)("worker: connect retries exhausted, exiting with network code");
    return EX_WORKER_NETWORK;
  }
  throw e;
}

/** runScenario / runStep 的 scope 级上下文：界面接缝、执行所用的 agent、job 的目标（selectHandler 按它取句柄），以及 scope 级终止
 *  状态。sessionLost 由 runStep 在某个 step 的最终判定归会话丢失时置位（首个为准）：本 scenario 余下 step 照常短路，runScope 在
 *  scenario_done 之后不再开始后续 scenario、经 scope 终止出口收尾（ADR 0051 决策 5「会话丢失序列」）。 */
export interface ScopeSeam {
  surface: TargetSurface;
  agent: Agent;
  target: StepTargetKey;
  sessionLost: StepFailure | null;
}

// scope 内串行运行一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028，对称 Nova）。
// 短路：本 scenario 内一旦某 step status==error（导航 SSL 失败等），后续 step 不再调 AI——① 省钱；
// ② 不在损坏环境（SSL 错误页）上产生误导性假失败。被跳过的 step 发独立 step_skipped 事件（非 step_done；
// core 据此本地赋 StepResult(SKIPPED, shortcircuited=True)）。判据锁 status==error（不看 errorType）；
// **只短路本 scenario**（下一 scenario 可能导航新页恢复，独立用例不牵连；跨 job 是 fail-fast 职责，正交）。
// 返回各步 status——被跳过步**不进** statuses，故不参与 aggregate（scenario 判定由那个 error step 决定）。
async function runScenario(
  seam: ScopeSeam, scenarioId: string, steps: Step[], votesN: number,
  uploader: ArtifactUploader, snapState: { mtime: number },
  sink: { emit: (e: unknown) => Promise<void> },
  evidence?: EvidenceHook,  // step 级机读证据（ADR 0042）；不注入即不产（`--no-report` 方式 / 无产物落点）
): Promise<string[]> {
  const { agent } = seam;
  const statuses: string[] = [];
  let shortcircuit = false;
  for (const step of steps) {
    if (shortcircuit) {
      await sink.emit({ type: "step_skipped", scenarioId, stepIndex: step.index });
      continue;
    }
    const status = await runStep(seam, scenarioId, step, votesN, sink, evidence);
    statuses.push(status);
    // act 边界提前上传（ADR 0029，为 Fargate 预演）：step_done 安全点（act 已返回、SDK onTaskUpdate 已 await flush，
    // 盘上 report 一致无半写），把增量增长的单份 report.html 用 snapshotReport overwrite 同 key 提前上传。
    // 在 error 短路判定**之前**——损坏那步的 report 最该留。mtime 去重（仅 report 变了才传，确定性/导航步不写
    // report → mtime 不变 → 跳过）；空窗跳过（首个 AI task 前 agent.reportFile 未置）；失败吞（best-effort、不打断）。
    if (agent.reportFile) {
      try {
        const mt = fs.statSync(agent.reportFile).mtimeMs;
        if (mt !== snapState.mtime) {
          await uploader.snapshotReport(agent.reportFile);
          snapState.mtime = mt;
        }
      } catch (e) {
        // 本行不作再传承诺（ADR 0039 产品面文案不变量，两引擎措辞一致）：正常路径上 snapState.mtime 未更新，
        // 后续 step_done 安全点与 scope 末的报告上传还会再传；停止信号路径有中断兜底提前上传
        // （interruptSnapshot）再传一次；但网络耗尽与异常两条提前退出路径只排空截图队列、既不 snapshotReport
        // 也不 flush，那份增量 report 就此丢。
        log(`worker: 引擎原生报告未能提前上传（不影响判定；这份报告可能最终没能上传）：${(e as Error).message}`);
      }
    }
    if (status === "error") shortcircuit = true;  // 本 scenario 后续 step 短路
  }
  return statuses;
}

// evidence ref **追加**进 step_done 的 reportRefs（ADR 0042 决策一）：追加而非整体赋值——将来若 Midscene
// 也有第二类 step 级产物，两者不能各自赋值互相覆盖（Nova 侧已有 trajectory 挂载，正是这么被约束的）。
// Midscene 此前 step 级 reportRefs 恒空，evidence 是首条，故事件对象上此键可能还不存在。
function appendReportRef(
  ev: Record<string, unknown>, ref: { kind: string; ref: string; label?: string },
): void {
  const refs = (ev.reportRefs as Array<{ kind: string; ref: string; label?: string }> | undefined) ?? [];
  refs.push(ref);
  ev.reportRefs = refs;
}

/** 一条 step 的派发结论（纯计算，不发命令）：命中的注册表条目、按目标取到的句柄与 step_kind（ADR 0052 决策 2 第 7 步）。
 *  命中出错（关键字不符、命中多条）记在 matchError 里，等 step 前核对通过之后作为本 step 的判定报出；它们的 step_kind 记
 *  deterministic（文本落在了确定性模式上）。navigation 只来自命中条目的内建标记：使用方 handler 自己调导航仍是 deterministic。 */
interface Dispatch {
  hit: Match | null;
  selected: SelectedHandler | null;
  matchError: Error | null;
  kind: StepKind;
}

function dispatchOf(text: string, keyword: string, target: StepTargetKey): Dispatch {
  let hit: Match | null;
  try {
    hit = matchDeterministic(text, keyword);
  } catch (e) {
    if (e instanceof DeterministicKeywordMismatch || e instanceof DeterministicConflict) {
      return { hit: null, selected: null, matchError: e, kind: "deterministic" };
    }
    throw e;
  }
  // 命中之后按当前目标取句柄（ADR 0050 决策 1）：命中的 pattern 在这个目标上没有句柄（如桌面上只写了 webdriver 条目的 step）
  // → 走 AI、不调用任何 handler、不记 error、不顺延到别的 pattern。
  const selected = hit ? selectHandler(hit, target) : null;
  const kind: StepKind = selected === null ? "ai" : hit?.builtin === "navigation" ? "navigation" : "deterministic";
  return { hit, selected, matchError: null, kind };
}

/** 一条 step 的固定七步（ADR 0052 决策 2，接缝契约的一部分）：
 *  ① 发 step_started；② 接缝的 step 前核对，失败即本 step 记 error、不调 handler 也不调 AI；③ 在接缝的执行窗口内执行确定性
 *  handler（内建导航也是其中一条）或 AI，得暂定判定；④ 本 run 产 evidence 时按暂定判定读地址；⑤ 接缝复原并核对，失败即最终
 *  判定改 error（类别与消息取返回值）；⑥ 本 run 产 evidence 时采界面快照（只在 failed / error 采控件），唯一可能改判的是会话丢失；
 *  ⑦ 产 evidence、发 step_done，然后把截图与原始控件树入队。桌面接缝上 ②⑤ 是空操作、④⑥ 只在 AI step 取一次 page.url()，
 *  事件流与 evidence 与改动前逐字节一致。
 *  执行异常的归类先认接缝或命令守卫挂在异常上的标记（session_lost / engine_error / capability_unavailable），没有标记的
 *  （桌面路径的全部异常）沿用瞬时网络判定（ADR 0052 决策 6）。 */
async function runStep(
  seam: ScopeSeam, scenarioId: string, step: Step, votesN: number,
  sink: { emit: (e: unknown) => Promise<void> },
  evidence?: EvidenceHook,  // step 级机读证据（ADR 0042）；不注入即不产
): Promise<string> {
  const { surface, agent } = seam;
  const { index, keyword, text } = step;
  await sink.emit({ type: "step_started", scenarioId, stepIndex: index });  // step 时长起点
  // 本 step 起点的累计 token：成功与失败路径都按增量算成本（确定性 step 含内建导航不调 AI、增量为 0 → 不带 cost）
  const tokBefore = cumulativeTokens(agent);
  // 本 step 起点的 execution 数（ADR 0042 决策一）：step 末按它从 agent.dump.executions 切出本 step 新增的。
  // **在 try 之外**：executionsLength 自己吞异常，绝不能让「记起点」这步冒泡（那会连 step_done 都发不出）。
  const execFrom = executionsLength(agent);
  const votes: boolean[] = [];        // 逐票结果（进 evidence 的 act.vote；多数票数学仍看 yes 计数）
  let instr: string | null = null;    // 交给引擎的指令（进 evidence 的 act.prompt）；null 表示本 step 没调 AI
  let thrown: string | null = null;   // 本 step 抛出的异常文本（进 evidence 的 act.error）；与 step_done 的 message 同一份
  // step_done 事件：判定字段按各条路径的原有键序逐个写入（事件逐字节不变的前提），⑤⑥ 改判时原地覆盖。
  const ev: Record<string, unknown> = { type: "step_done", scenarioId, stepIndex: index };
  const verdict = (status: StepStatus, errorType: string, message: string) => {
    ev.status = status; ev.errorType = errorType; ev.message = message;
  };
  let dispatch: Dispatch | null = null;
  let fromHandler = false;            // 异常来自确定性 handler：分类时不按消息文本启发（见下 catch）
  try {
    // ③ 之前先定派发（纯计算）：step_kind 在 ④⑥ 要用，step 前核对失败的 step 也要有
    dispatch = dispatchOf(text, keyword, seam.target);
    // ② step 前核对（ADR 0052 决策 2）：失败即本 step 记 error，不执行 handler 或 AI
    const pre = await surface.preStep();
    if (pre !== null) {
      verdict("error", pre.errorType, pre.message);
    } else if (dispatch.matchError !== null) {
      // ① 确定性注册表（ADR 0022；内建导航也是其中一条，ADR 0020 第 3 条）：命中但关键字不在条目声明里（ADR 0050 决策 1）与
      //    命中多条都是注册表层面的写法 / 配置错误：直接记 engine_error，不经消息文本的网络启发（冲突消息内联 step 原文与各条
      //    模式，其中的 ssl / timeout 字样不是网络故障；对齐 Nova 按异常类型分类）。消息走与其它失败同一条有界归一化（一行、
      //    封顶）但不带异常类型名（类型名是内部指代，ADR 0039）；与 Nova 侧一致
      verdict("error", "engine_error", oneLineError(dispatch.matchError.message));
    } else if (dispatch.selected !== null) {
      // 命中走精确 handler、不投票；AssertionError→failed，其它→error
      if (step.argument != null) {
        // 确定性 handler 不接收多行参数（ADR 0024）：带了即记 error，不静默忽略
        verdict("error", "engine_error", `确定性 step 不接受多行参数（DataTable / DocString）：${text}`);
      } else {
        // 取确定性句柄（ADR 0050 决策 2）：前提不满足（requires 含 web_context 而设备不提供，或探测出错）时接缝同步抛出带归类
        // 标记的异常，不调 handler、不转 AI，落到下面的 catch 按标记归类
        const call = surface.bindHandler(dispatch.selected);
        const groups = dispatch.hit!.groups;
        try {
          await surface.execute(() => call(groups));
        } catch (e) {
          // 断言异常记 failed；带归类标记的（守卫判过结果未知或会话丢失，即便 handler 抛的是断言）按标记归类
          if (readClassification(e) === null && (e instanceof DeterministicAssertion || (e as Error).name === "AssertionError")) {
            ev.status = "failed"; ev.errorType = "assertion_failed"; ev.message = (e as Error).message || `确定性断言未过：${text}`;
          } else {
            fromHandler = true;
            throw e; // 其它异常 → 落到下面 catch，记 error
          }
        }
        if (ev.status === undefined) ev.status = "passed";
      }
    } else if (keyword === "Then") {
      // AI 断言 + N 次投票（ADR 0014/0024）；votesN=1 即单次判定（仍发 votes 标记这是 AI 断言）
      const prompt = buildInstruction(step.text, step.argument as any);  // 自然语言 + 多行参数（DataTable/DocString，ADR 0024）
      instr = prompt;
      let yes = 0;
      // 逐票记进 votes：evidence 要「本次调用计入判定的那一票」（ADR 0042 映射表里 act.vote 取 aiBoolean 返回值），
      // 光有 yes 计数分不清是哪几票投的 no。N 票同在一个执行窗口里（aiBoolean 只截图、不发动作，不接受 abortSignal）。
      await surface.execute(async () => {
        for (let i = 0; i < votesN; i++) {
          const vote = await agent.aiBoolean(prompt);
          votes.push(vote);
          if (vote) yes++;
        }
      });
      const passed = yes > votesN / 2;
      ev.status = passed ? "passed" : "failed";
      ev.votes = { yes, total: votesN };
      const cost = stepCost(tokBefore, agent);  // N 票 token 增量合计（修：原 lastCost 只算最后一票）
      if (cost) ev.cost = cost;
      if (!passed) { ev.errorType = "assertion_failed"; ev.message = `AI 断言未过多数票（${yes}/${votesN}）：${text}`; }
    } else {
      // When / Given → AI 动作（无 votes）。设备上执行窗口给出本次 act 的 abortSignal：结果未知与进入终结时中止它（ADR 0052 决策 6）
      const prompt = buildInstruction(step.text, step.argument as any);
      instr = prompt;
      await surface.execute((abortSignal) =>
        abortSignal === undefined ? agent.aiAct(prompt) : agent.aiAct(prompt, { abortSignal }));
      ev.status = "passed";
      const cost = stepCost(tokBefore, agent);
      if (cost) ev.cost = cost;
    }
  } catch (e) {
    // 归类标记优先（ADR 0052 决策 6）：命令守卫与设备接缝把会话丢失、结果未知（engine_error，消息写明这一步可能已执行也可能
    // 未执行）与能力不提供挂在异常上，读到即按它归类——设备路径的执行异常因此不进瞬时网络判定。
    // 没有标记的（桌面路径的全部异常）沿用诊断分类细化（ADR 0028，对称 Nova）：act 中途网络瞬时故障（CDP 闪断等）标
    // network_error 比笼统 engine_error 更准。**仅分类、不触发重试/恢复**：act 不幂等，schedule job 级重试要求「会话未起（零
    // step_done）」，此处 step_started 早已 emit、saw_step=True，双条件 AND 天然不满足；本失败走 step_done
    // 事件流（非退出码 80），core 侧 is_network=False。"act 中途恢复"仍 defer，这里只把失败原因记准。
    const mark = readClassification(e);
    const errorType = mark !== null ? mark.errorType : isTransientNetwork(e, false, !fromHandler) ? "network_error" : "engine_error";
    // message 与 evidence 的 error 同一份文本（一行、有界；Playwright 异常的 message 常拖着多行 call log，规则与理由见
    // error-text.mts，Nova 侧 `_error_text` 是对称版）：evidence 冗余 step_done 的 message 以自包含（ADR 0042 决策一）。
    // 带标记时取标记里那句给使用方看的消息（ADR 给了原文整句的照原文）。
    const message = mark !== null ? oneLineError(mark.message) : errorText(e);
    ev.status = "error"; ev.errorType = errorType; ev.message = message;
    // 失败的 act 费用已经发生（ADR 0024「失败的 act 同样带 cost」）：抛异常前已发生的调用照样折进 agent.metrics，照报 token 增量
    const cost = stepCost(tokBefore, agent);
    if (cost) ev.cost = cost;
    thrown = message;
  }
  const kind: StepKind = dispatch?.kind ?? "ai";

  // ④ 按暂定判定读地址（只在本 run 产 evidence 时；读不读、怎么读由接缝按目标与能力结论定，读取失败只置空、不改判定）
  const tentativeStatus = ev.status as StepStatus;
  const address = evidence !== undefined ? await surface.readAddress({ kind, status: tentativeStatus }) : null;
  // ⑤ 复原并核对：失败即最终判定改为 error，类别与消息取返回值（消息已由接缝写全：含原判定，或以结果未知的整句开头）
  const restored = await surface.restore({ status: tentativeStatus, message: (ev.message as string | undefined) ?? null });
  if (restored !== null) verdict("error", restored.errorType, restored.message);
  // ⑥ 界面快照（只在本 run 产 evidence 时）：best-effort，唯一的改判是采集中发现会话丢失
  let snapshot: Snapshot = { url: null, url_missing: null };
  if (evidence !== undefined) {
    const snap = await surface.snapshot({ kind, status: ev.status as StepStatus }, address);
    snapshot = snap.snapshot;
    if (snap.failure !== null) verdict("error", snap.failure.errorType, snap.failure.message);
  }
  if (ev.errorType === "session_lost" && seam.sessionLost === null) {
    seam.sessionLost = { errorType: "session_lost", message: (ev.message as string | undefined) ?? "" };
  }

  // ⑦ 本 step 判定已成之后的收尾出口：产 evidence → 挂 ref → **emit** → 才把截图与原始控件树交后台队列。
  // **这个顺序是契约**（ADR 0042 决策一「上传时机分两类」）：evidence.json 的 ref 必须随 step_done 走，故它
  // 即时传；截图字节反过来——emit 之前入队就是把字节又压回判定前面，主流程该做的是发完判定立刻进下一 step。
  // **绝不抛**（决策二：对判定零影响）——落在 act 异常分类路径之外的语义由 stepEvidenceRef 内部整体 try
  // 保证，enqueue 则是同步返回、不抛（见上传器）。故此处可直接 await。产不产由快照与判定决定：桌面上只有调过 AI 的 step 产，
  // 设备上 AI step 一律产、确定性与导航 step 在 failed / error 时产（evidence 模块的跳过规则）。
  const produced = await stepEvidenceRef(evidence, {
    scenarioId, step, status: ev.status as string, message: (ev.message as string | undefined) ?? null,
    agent, execFrom, snapshot, prompt: instr, votes, error: thrown,
  });
  if (produced !== null) {
    appendReportRef(ev, { kind: EVIDENCE_KIND, ref: produced.ref, label: EVIDENCE_KIND });
  }
  await sink.emit(ev);
  if (produced !== null && produced.screenshots.length > 0) {
    evidence?.uploader.enqueue(produced.screenshots);  // emit 之后：字节在下个 step 期间顺链传上去
  }
  return ev.status as string;
}

function aggregate(statuses: string[]): string {
  if (statuses.includes("error")) return "error";
  if (statuses.includes("failed")) return "failed";
  return "passed";
}

// 测试可见（对称 Nova：Nova worker 靠 if __name__ 守卫使 _run_step/_run_scenario/_is_transient_network 可 import 测）。
// `main` 由 bin 调（见文件头「本模块不是进程入口」）；其余是单测面。isTransientNetwork 的实现随桌面实现住在
// worker/surface-desktop.mts，runStep 对没有归类标记的异常用它，故从这里一并暴露。
export {
  runStep, runScenario, isTransientNetwork, aggregate, interruptSnapshot, drainArtifactQueue, shutdownSequence,
  sharedAgentOpts,
};
