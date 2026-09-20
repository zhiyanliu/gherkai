// Midscene 薄 worker（ADR 0022/0024）：读 stdin 的 job JSON → 运行一个 scope → 吐 ADR 0024 事件到事件通道。
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
//   echo '<job json>' | AWS_REGION=us-east-1 node dist/bin.mjs
import OpenAI from "openai";
import { PlaywrightAgent } from "@midscene/web/playwright";
import { chromium, type Browser } from "playwright";
import {
  BedrockAgentCoreClient,
  StartBrowserSessionCommand,
  StopBrowserSessionCommand,
} from "@aws-sdk/client-bedrock-agentcore";
import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";
import { sigv4Fetch, signCdpUpgrade, getBaseUrl, MODEL, modelFamily, getRegion } from "../lib/agentcore-sigv4.mjs";
// 产物 S3 上传（ADR 0029；无落点 env 时 no-op 报 file://）；UPLOAD_TIMEOUT_MS 是自报 grace 下限的加数之一
// （中断兜底提前上传那一段的预算，见下 minGraceSeconds），单一真值住上传器、此处只引用。
import { ArtifactUploader, UPLOAD_TIMEOUT_MS } from "../lib/artifact-upload.mjs";
import { EventSink } from "../lib/event-sink.mjs";  // 事件出口（ADR 0024「I/O 边缘可注入接口」，两态见该模块头）
import { JobSource } from "../lib/job-source.mjs";  // job 入口（同上）
// 确定性 step 注册表（ADR 0022）+ 测试开发写 step 用的脚手架。
// import 脚手架即触发其顶层 deterministic(...) 注册副作用（对称 Nova 引擎 import deterministic_steps）。
import { match as matchDeterministic, DeterministicAssertion, listRegistry, matchBatch } from "./deterministic.mjs";
import { buildInstruction } from "./argument.mjs";
// step 级机读证据（ADR 0042）：SDK 结构 → gherkai 自有 schema 的映射与落盘全住那个模块；此处只挂钩子。
import { stepEvidenceRef, executionsLength, EVIDENCE_KIND, ENGINE, type EvidenceHook } from "./evidence.mjs";
import { errorText } from "./error-text.mjs";  // 失败原因压成一行有界文本（ADR 0042；与 evidence 侧同一规则）
import "./deterministic.steps.mjs";  // 内建脚手架（ADR 0022 退役 bdd 层后迁入 worker/）——**先于**使用方 steps 注册
import { loadUserSteps } from "./user-steps.mjs";  // 使用方 steps/ 目录的加载（ADR 0037 决策 4）

const BROWSER_ID = "aws.browser.v1";
// 网络专用退出码（ADR 0028）：与 core/gherkai_core/wire.py 的 EX_WORKER_NETWORK 同值（协议层单一事实源，两 Engine adapter 共用翻译）。
// worker 建连失败、重试耗尽时以此码退出，作 out-of-band 信号（建连失败先于任何事件 emit）。
const EX_WORKER_NETWORK = 80;
// 建连重试上限（ADR 0028）；退避 [0.5,1,2]s，总 ~3.5s，远小于本 worker 自报的 grace 下限（见下 minGraceSeconds）。
const CONNECT_ATTEMPTS = 4;
const CONNECT_BACKOFF_MS = [500, 1000, 2000];
// SIGTERM cleanup 里单个 StopBrowserSession 的超时预算（ADR 0028）：退化网络下 Stop 可能挂很久
// （共享 client maxAttempts=3、无显式超时），超过 schedule grace 会被 SIGKILL 打断到一半 → 会话泄漏。
// 套这个预算：挂死时及时放弃，至少让 worker 干净退出、不被强杀。须 < grace——本段是自报下限
// minGraceSeconds 的加数之一（见下），故「够运行完」由那个下限保证、不靠人对数字。
export const STOP_SESSION_BUDGET_MS = 3000;
// StartBrowserSession 已发出 RPC 但 sessionId 未返回的在途窗口兜底（ADR 0028）：SIGTERM 落在这一瞬时
// 服务端可能已建会话但客户端没拿到 id。给一小段时间让 Start 的 await 返回、id 落进待清理集，再 cleanup。
export const INFLIGHT_SETTLE_MS = 1500;
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

// SIGTERM cleanup 末尾关本地 browser 的超时预算（会话已 Stop 之后才执行，见下 cleanup）：close 易挂起，
// 套预算别让它吃掉 grace 里留给后面几段的份额。本段同样是自报下限 minGraceSeconds 的加数之一。
export const BROWSER_CLOSE_BUDGET_MS = 3000;
// 自报 grace 下限的余量（ADR 0024 grace 硬约束的 margin）：收尾各段预算之和之外再多留一份，吸收段间调度、
// SDK 抖动与不被上述预算覆盖的零碎（诊断写出、事件 flush、进程退出本身）。
// **取值来路**：使下限落在已标定的 31 s 上（各段之和 23.5 + 本余量 7.5）——31 不是新数，是 ADR 0032 真容器校准
// 判「25 够用」（实测约 2x 余量）后、又被 ADR 0042 决策一的 6 s 截图队列排空顶上来的今值。改本常量 = 改一个
// 已标定的下限，要有意识地改。与 Nova 侧不对称的一点：Nova 的 margin 可 env 覆盖（再标定免改码），本常量是
// 编译期值、再标定要改这里重编。
export const MIN_GRACE_MARGIN_MS = 7500;
// 自述对象的 schema 版本（ADR 0036「5.」：只在既有键语义变化时递增；加键不递增）。
const CAPABILITIES_SCHEMA_VERSION = 1;

/** 本引擎自报给组合根的 grace 下限，单位秒（ADR 0024「引擎自报下限」，经 `--capabilities` 出口，
 *  契约见 ADR 0036「5. worker 自述：--capabilities」）。
 *
 *  Midscene worker 没有「可控的单 act 超时」概念（不像 Nova 的 act 时间上界），但它的 **SIGTERM 收尾路径
 *  本身有确定的超时预算**，grace 必须够这条路径运行完：不够则收尾被 SIGKILL 截断——会话释放本身有
 *  「先释放会话、再提前上传」的排序 + Stop 预算保底不泄漏，但 worker 退不干净、中断兜底的引擎报告提前上传与
 *  截图队列排空会被拦腰砍掉。故下限 = 收尾最坏串行路径各段预算之和 + 余量，**由那些预算常量算出、
 *  不另写字面量**：谁改某段预算，下限自动跟着走（曾把这个下限当常量放在组合根，收尾里加进截图队列排空后
 *  只能靠人记得把它改大；漏一次就是 grace 默默不够、收尾被硬杀截断）。
 *
 *  加数与顺序即 shutdownSequence 的逐段串行（见该函数）：在途窗口兜底 INFLIGHT_SETTLE_MS
 *  + 会话 Stop STOP_SESSION_BUDGET_MS + 关 browser BROWSER_CLOSE_BUDGET_MS + 中断兜底报告提前上传的单次
 *  上传超时 UPLOAD_TIMEOUT_MS + 截图队列退出段排空 QUEUE_DRAIN_EXIT_MS（ADR 0042 决策一：排在会话释放
 *  之后、与兜底提前上传并列）+ MIN_GRACE_MARGIN_MS。scenario 边界提前上传的 SCENARIO_LOG_SNAPSHOT_BUDGET_MS
 *  **不在其中**——它在主流程执行、不在收尾路径上（见该常量注释）。 */
export function minGraceSeconds(): number {
  const totalMs = INFLIGHT_SETTLE_MS + STOP_SESSION_BUDGET_MS + BROWSER_CLOSE_BUDGET_MS
    + UPLOAD_TIMEOUT_MS + QUEUE_DRAIN_EXIT_MS + MIN_GRACE_MARGIN_MS;
  return totalMs / 1000;
}

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

// 是否网络/SSL 瞬时故障（可重试，ADR 0028）。Node 侧按 error code / TLS 错 / AWS SDK v3 服务端瞬时识别。
// 遍历 error.cause 链：SDK 常把底层 socket/TLS 错、或 AWS 服务端错包成自有 Error，只看最外层会漏判（防环：限 8 层）。
//
// connecting=true（仅建连阶段传，ADR 0028）：额外认 Playwright TargetClosedError 的 message
// "...has been closed"——CDP 连接被网络断掉后的下游症状（Playwright 把底层 socket 故障吞掉、只留这句）。
// 与 Nova 侧对称（Nova SDK 建连时主动 CDPSession.send 会撞出它；Midscene connectOverCDP 通常招 websocket
// TLS 错、已被下面正则命中，故此路径 Midscene 实际少见——防御性对称）。因语义模糊（网络断/会话正常关/浏览器真崩
// 同报一句），**只建连阶段认**（此阶段 act 无副作用、重试安全）；act 中途（connecting=false）不认，守铁律。
function isTransientNetwork(e: unknown, connecting = false): boolean {
  let cur = e as {
    code?: string; name?: string; message?: string; cause?: unknown;
    $metadata?: { httpStatusCode?: number }; $retryable?: { throttling?: boolean };
  } | undefined;
  for (let depth = 0; cur && depth < 8; depth++) {
    const code = cur.code ?? "";
    if (code === "ENOTFOUND") return false; // DNS 未找到（永久），此层直接否决
    if (["ECONNRESET", "ECONNREFUSED", "ETIMEDOUT", "EPIPE", "EAI_AGAIN", "ECONNABORTED"].includes(code)) {
      return true; // EAI_AGAIN = DNS 临时失败，当瞬时
    }
    // AWS SDK v3 服务端瞬时（AgentCore 起会话节流/5xx，ADR 0028）：name 节流集 / 5xx 状态 / $retryable.throttling
    if (cur.name && AWS_TRANSIENT_NAMES.has(cur.name)) return true;
    if (cur.$metadata?.httpStatusCode != null && AWS_TRANSIENT_STATUS.has(cur.$metadata.httpStatusCode)) return true;
    if (cur.$retryable?.throttling === true) return true;
    const msg = cur.message ?? "";
    if (/\b(socket hang up|ssl|tls|econnreset|epipe|timeout|handshake|UNEXPECTED_EOF)\b/i.test(msg)) return true;
    // 建连阶段额外认 Playwright 连接被关（下游症状）——精确匹配 "has been closed"（TargetClosedError），
    // 不用宽 "closed"（正常关闭也含）。TS Playwright 无稳定异常类可 instanceof，故按 message。
    if (connecting && /has been closed/i.test(msg)) return true;
    cur = cur.cause as typeof cur;
  }
  return false;
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
const URL_IN_QUOTES = /"(https?:\/\/[^"]+)"/;

// 事件出口抽进 ../lib/event-sink.mts（ADR 0024「I/O 边缘可注入接口」）：可注入、可测；subprocess 态写
// EVENTS_FD fd（无则回落 stdout 调试）。emit 为 async（合理不对称：为 Fargate 化的 DDB PutItem（aws-sdk-js）
// 预留；Nova 那个引擎 emit 同步）+ 作参数注入 runStep/runScenario（两个引擎统一打桩机制），不再是模块级函数。
// log（stderr 诊断）**不属那三条 I/O 边、不进 sink**（协议传输面 vs 诊断面物理隔离，ADR 0024），保模块级。
function log(msg: string): void {
  process.stderr.write(msg + "\n");
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

// 截图后台队列的有界排空（ADR 0042 决策一）——与 interruptSnapshot 同形的可测小函数：只管「排空那一步」的
// 决策（排不完记一行、放弃），**位置**（必须排在会话释放之后）由调用方保证。
// best-effort、**绝不抛**：收尾路径上抛会跳过后面的 exit / flush；排不完不是错，正常路径还有整目录 flush 兜。
// flushFollows 由调用点声明「我后面还跟着整目录 flush 吗」（不在这里猜调用栈）。分句按调用点是否真跟着整目录
// flush：只在会 flush 的路径上说「改由收尾上传」（ADR 0039 面一的文案不变量例外条，两引擎同形）；不跟 flush 的
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
    // 产品面一行，与上面「排不完」那行同形（best-effort、绝不抛的判据见上函数头）。
    logFn(`worker: 证据截图收尾上传失败（不影响判定结果；仍可看引擎原生报告）：${(e as Error).message}`);
  }
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

// SIGTERM/SIGINT 收尾序列（ADR 0024 终止契约 + 0029 中断兜底提前上传 + 0042 截图队列排空）——从 onSignal 提出为可测函数（依赖注入），
// 对称 Nova 把 _on_signal 提到模块级供 test_interrupt_model/process 测。**锁住关键顺序不变量**：
//   会话释放（cleanup）**必须先于**中断兜底提前上传（interruptSnapshot）与截图队列排空（drainArtifactQueue）
//   ——ADR 0024「会话释放优先」铁律，那两件都是 best-effort、绝不延迟会话释放（退化网络下各自挂满自己的
//   预算，也不该让会话多泄漏那么久）。
// 返回该退出的码（cleanupFailed→1 让泄漏可观测、否则 0）；不自己 process.exit（交调用方，便于测试不真退进程）。
// deps 全注入（cleanup/getCleanupFailed/uploader/reportFile...）→ 单测可传 spy 断言调用序列，无需真信号/真进程。
interface ShutdownDeps {
  inflightPending: () => boolean;      // startInFlight：Start RPC 在途则先等 settle，让 id 落进待清理集
  settleMs: number;                    // 在途兜底等待（INFLIGHT_SETTLE_MS）
  sleep: (ms: number) => Promise<void>;
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
  logFn("worker: signal received, releasing AgentCore session(s)");
  if (deps.inflightPending()) await deps.sleep(deps.settleMs);  // 在途窗口兜底（ADR 0028）
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
interface Job { scope: { id: string; name: string }; engine: string; scenarios: Scenario[]; assertionVotes?: number }


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
function cumulativeTokens(agent: PlaywrightAgent): number {
  try {
    return agent.metrics?.totalTokens ?? 0;
  } catch {
    return 0;
  }
}

// 本 step 的 token 成本 = 运行后累计 - 运行前累计（增量）。增量 0（无新 usage）→ undefined（不假装 0）。
function stepCost(beforeTokens: number, agent: PlaywrightAgent): Record<string, unknown> | undefined {
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

/** PlaywrightAgent 的构造项。提成模块级函数（不碰 page/browser）好让单测锁住这几个开关；
 *  **不纯、别随处调**——`modelConfig()` 里的 getBaseUrl 读 AWS_REGION（缺则 fail-loud 抛），故只在建连时调。 */
function agentOpts(): NonNullable<ConstructorParameters<typeof PlaywrightAgent>[1]> {
  return {
    generateReport: !NO_ARTIFACTS,  // --no-report：不出 report.html（ADR 0037 决策 3）
    // 让 SDK 把每张截图另落成独立文件 `report/screenshots/<id>.<扩展名>`（ADR 0042 决策一）：evidence 只
    // 引用这些文件、零解码零复制，从而不必读 ScreenshotItem.base64（SDK 每个 task 后即 flush 报告并置空它，
    // 之后读会对多 MB 的 report.html 做同步全文扫描且找不到即抛）。副作用是 report 目录多出
    // `<n>.execution.json`，随 scope 末整目录 flush 一并上传，接受。
    // **必须与 generateReport 同真同假**：SDK 在 generateReport=false 且此项为 true 时直接抛
    // （`--no-report` 方式不产 evidence，正好同为 false）。
    persistExecutionDump: !NO_ARTIFACTS,
    // SDK 默认开的「强制 Chrome 用 base-select 渲染原生下拉」（往页面注入一个 style 标签，让 select 在截图里
    // 可见）——**我们显式关掉**：本 worker 连的是 AgentCore 云端浏览器（CDP 远连），注入用的 page.evaluate 常
    // 撞上 "Execution context was destroyed"，SDK 每个 run 因此往 stderr 打一整段报错栈，纯噪声；而功能面这边
    // 用不到它（AI 看的是截图里的元素、不依赖原生 select 的外观兼容）。
    forceChromeSelectRendering: false,
    modelConfig: modelConfig(),
    createOpenAIClient: async () => new OpenAI({ baseURL: getBaseUrl(), apiKey: "unused", fetch: sigv4Fetch }) as any,
  };
}

export async function main(): Promise<number> {
  if (NO_ARTIFACTS && !process.env.MIDSCENE_RUN_DIR) {
    process.env.MIDSCENE_RUN_DIR = fs.mkdtempSync(path.join(os.tmpdir(), "gherkai-midscene-"));
  }
  // 使用方 steps/ 目录的注册（ADR 0037 决策 4）：**内建脚手架之后**（模块顶 import 已注册完）、
  // **两个非 job 入口与 job 循环之前**——故 --capabilities / --match-steps / plan 标注都反映使用方定制
  // （ADR 0036「真值单一」不变：注册表 = 内建 + 使用方）。加载失败 fail-loud（抛 → bin 一行 stderr + 非零退出）。
  await loadUserSteps();

  // 模型家族的启动期校验（ADR 0044 决策 2）：推不出即抛 → bin 一行 stderr + 非零退出。**位置 load-bearing**：
  // 在任何入口分派之前，故 `--capabilities` 这条 run 前置检查也会把坏配置挡下——不然要等到 job 模式里已经建好
  // 云端浏览器会话、第一次调模型时才炸。返回值不用（真正取值在建连时的 modelConfig()）；这一步只为早失败。
  modelFamily();

  // 批量 match 查询（ADR 0036 决策 4，plan 命中标注）：stdin 一行 JSON 数组（step 文本）→ stdout 一行
  // 逐条命中结果。匹配语义留在 worker（CLI 零复刻）；同样不建会话、零 AWS。
  if (process.argv.includes("--match-steps")) {
    const chunks: Buffer[] = [];
    for await (const c of process.stdin) chunks.push(c as Buffer);
    const texts: string[] = JSON.parse(Buffer.concat(chunks).toString("utf-8"));
    await writeStdoutFlushed(JSON.stringify(matchBatch(texts)) + "\n");
    return 0;
  }
  // 引擎能力自述（ADR 0036「5.」）：一个 JSON 对象即退，同样不建会话、不读 stdin、零费用。
  // min_grace_s = 本引擎收尾路径要的 grace 下限（ADR 0024「引擎自报下限」：真值住算它的这一侧，
  // 组合根只查询后聚合、不持引擎特定常量）。deterministic_steps = 注册表清单（ADR 0036「2.」：内建脚手架
  // 在模块顶 import 时注册、使用方 steps 上面刚加载完，此刻注册表即真值）。model_id = 起 job 时真交给
  // Midscene SDK 的模型名，即 modelConfig() 的 MIDSCENE_MODEL_NAME，与它同源引用 lib/agentcore-sigv4 的 MODEL
  // 常量、此处不另写字面量（否则自述会与实际用的模型漂移，而 doctor 正是拿这个键显示「当前用哪个模型」）。
  // **加键不加入口**（ADR 0036「5.」）：新增自述项都是本对象的新键、不再开第二个 flag——组合根一次 spawn
  // 就同时拿到「steps 加载成功 / 清单 / grace 下限 / 模型」。
  if (process.argv.includes("--capabilities")) {
    await writeStdoutFlushed(JSON.stringify({
      schema_version: CAPABILITIES_SCHEMA_VERSION,
      engine: ENGINE,  // 与 evidence 报的引擎名同源，不另写字面量
      min_grace_s: minGraceSeconds(),
      deterministic_steps: listRegistry(),
      model_id: MODEL,
    }) + "\n");
    return 0;
  }

  // 早期信号护栏（对称 Nova：handler 先于 JobSource.read 装载，ADR 0024）——S3 态下 read 含一次网络往返，
  // 窗口内 SIGTERM 若走 Node 默认处置会以信号终止（非 0）→ adapter 误归 engine_error。此阶段无会话、无产物，
  // 直接干净退 0（零事件 + exit 0，core 判 error 不误归因）；真正的 onSignal（提前上传+释放会话）建好后替换本 handler。
  const earlySignal = () => process.exit(0);
  process.on("SIGTERM", earlySignal);
  process.on("SIGINT", earlySignal);

  // I/O 边缘可注入接口（ADR 0024）：job 入口 / 事件出口从内联收进 lib 组件，subprocess 态=读 stdin / 写 EVENTS_FD。
  const job = (await JobSource.fromEnv().read()) as Job;
  const eventSink = EventSink.fromEnv();  // main 级单例（对称 uploader）；作参数注入 runScenario/runStep
  const scope = job.scope;

  const cp = new BedrockAgentCoreClient({ region: getRegion() });
  // 待清理会话集（ADR 0028 会话跟踪重构）：每次 StartBrowserSession 成功即把 id 加进来——含被重试丢弃的
  // 中间 attempt 会话。SIGTERM handler / cleanup 遍历它逐个 Stop，**不再靠单一 sessionId 快照**（旧实现：
  // 重试时 sessionId 被后一个 attempt 覆盖/置空，handler 只能 Stop 到当前快照 → 在途/已弃的 attempt 会话泄漏）。
  const pendingSessions = new Set<string>();
  let sessionId: string | undefined; // 最终成功会话 id（血缘，进 scope_done；非清理依据——清理看 pendingSessions）
  let startInFlight = false; // StartBrowserSession RPC 已发出、await 未返回（SIGTERM 兜底等待的精确信号，ADR 0028）
  let browser: Browser | undefined;
  let cleanupFailed = false; // StopBrowserSession 失败 → worker 非 0 退出，让泄漏可观测（对照 Nova）

  async function stopSession(sid: string): Promise<boolean> {
    // 单个会话 Stop，套超时预算（ADR 0028）：退化网络下 Stop 可能挂死、超 grace 被 SIGKILL 打断 → 泄漏。
    // 超时即放弃（返回 false=未确认释放），让 worker 能干净退出。timedOut 哨兵区分「超时」与「Stop 成功」。
    const timedOut = Symbol("timeout");
    try {
      const r = await Promise.race([
        cp.send(new StopBrowserSessionCommand({ browserIdentifier: BROWSER_ID, sessionId: sid })).then(() => true),
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

  // 会话清理（ADR 0024 终止契约，对照 Nova 的 with __exit__）：
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
  async function cleanupRun(discardAttempt: boolean): Promise<void> {
    await Promise.all([...pendingSessions].map(async (sid) => {
      const ok = await stopSession(sid);
      if (ok) pendingSessions.delete(sid);
      else if (!discardAttempt) cleanupFailed = true;
    }));
    // 会话已释放，再尽力关本地 browser；套超时，挂住也不拖垮（会话已停，close 失败无计费影响）
    if (browser) {
      await Promise.race([
        browser.close().catch(() => {}),
        new Promise<void>((r) => setTimeout(r, BROWSER_CLOSE_BUDGET_MS)),
      ]);
    }
  }
  // 重入守卫（语义见 makeGuardedCleanup）：leftovers = pendingSessions 里还有没确认释放的会话，
  // 有则 final 语义的重入者补清一次，让 Stop 失败点亮 cleanupFailed、泄漏可观测。
  const cleanupGuard = makeGuardedCleanup(cleanupRun, () => pendingSessions.size > 0);
  const cleanup = cleanupGuard.cleanup;

  // SIGTERM/SIGINT：清理会话再退（防 AgentCore 会话泄漏后持续计费）。
  let terminated = false;
  let onTerminate: (() => void) | undefined;  // 重试退避用：信号到达即 resolve、打断退避（对称 Nova 的 sleep 被信号打断）
  // agent 引用上提到 handler 可见（ADR 0029 中断兜底提前上传：handler 里读 agent.reportFile 传那份增量 report）。
  // connect 成功后赋值（见下 `agentRef = agent`）；handler/uploader 靠闭包捕获（执行时 uploader 已初始化）。
  let agentRef: PlaywrightAgent | undefined;
  const onSignal = async () => {
    if (terminated) return;
    terminated = true;
    onTerminate?.();  // 立即唤醒正在退避的重试循环，使其尽快停（不再 reconnect/执行 act）
    // 收尾序列提出为可测的 shutdownSequence（cleanup 先于提前上传的顺序不变量在那里被单测锁住）；此处只做
    // 「守卫去重 + 唤醒退避 + 真 process.exit」这层 handler 外壳（进程副作用，不进纯函数）。
    const code = await shutdownSequence({
      // 不要再加 pendingSessions.size === 0：上一 attempt Stop 失败的遗留会话会让集非空，那恰恰是重试场景下
      // 最需要兜底的时刻；1.5 s 已计入 minGraceSeconds 的加数，等它不超 grace（ADR 0028）。
      inflightPending: () => startInFlight,
      settleMs: INFLIGHT_SETTLE_MS,
      sleep: (ms) => new Promise<void>((r) => setTimeout(r, ms)),
      cleanup,
      uploader,
      reportFile: () => agentRef?.reportFile,
      getCleanupFailed: () => cleanupFailed,
    });
    process.exit(code);
  };
  // 交接：先挂真 handler 再摘早期护栏（顺序不能反——Node 在某信号最后一个 listener 被移除时恢复
  // 默认处置，先摘会开出「SIGTERM 走内核默认动作→非0退出→误归 engine_error」的窗口；重叠期两个
  // handler 并存无害：此刻尚未 connect、earlySignal 的 exit(0) 与 onSignal 语义一致）。
  process.on("SIGTERM", onSignal);
  process.on("SIGINT", onSignal);  // Ctrl-C 也走同一路径（提前上传+释放会话），对称 Nova 已纳入 SIGINT
  process.removeListener("SIGTERM", earlySignal);
  process.removeListener("SIGINT", earlySignal);

  const reportRefs: Array<{ kind: string; ref: string; label?: string }> = [];
  // 产物 S3 上传器（ADR 0029，对称 Nova 的模块级 _uploader）：cloud 上传+删本地报 s3://，local no-op 报 file://。
  const uploader = ArtifactUploader.fromEnv();
  let networkExhausted = false; // 建连重试耗尽（ADR 0028）→ 退 EX_WORKER_NETWORK

  // 建连段（ADR 0028）：StartBrowserSession → CDP 握手 → connectOverCDP → PlaywrightAgent。
  // 整段可被重试；scope_started 一 emit（会话已起、act 即将执行）即跳出重试域，绝不重试 act。
  // 每次 attempt 前若上次部分建起了会话/browser，先 cleanup 释放（防泄漏 + 不重复占用）。
  async function connect(): Promise<{ page: import("playwright").Page; agent: PlaywrightAgent }> {
    startInFlight = true;  // Start RPC 在途（SIGTERM 兜底信号）；返回/抛错后清
    let started;
    try {
      started = await cp.send(new StartBrowserSessionCommand({ browserIdentifier: BROWSER_ID, name: "worker" }));
    } finally {
      startInFlight = false;
    }
    sessionId = started.sessionId!;
    pendingSessions.add(sessionId);  // 立即入待清理集 → SIGTERM handler 能 Stop 本次（含被重试丢弃的）会话
    const wsUrl = started.streams?.automationStream?.streamEndpoint!;
    const headers = await signCdpUpgrade(wsUrl);
    browser = await chromium.connectOverCDP(wsUrl, { headers });
    const ctx = browser.contexts()[0] ?? (await browser.newContext());
    // 额外请求头（ADR 0035，如 ngrok-skip-browser-warning）：组合根经 env 注入，context 级对所有请求生效。
    // 纯 CDP Network.setExtraHTTPHeaders，无回调、不涉 route——与 AI 驱动零交互。无 env → 零行为变化。
    const extraHeaders = process.env.GHERKAI_EXTRA_HTTP_HEADERS;
    if (extraHeaders) await ctx.setExtraHTTPHeaders(JSON.parse(extraHeaders));
    const page = ctx.pages()[0] ?? (await ctx.newPage());
    const agent = new PlaywrightAgent(page, agentOpts());
    return { page, agent };
  }

  try {
    let conn: { page: import("playwright").Page; agent: PlaywrightAgent } | undefined;
    for (let attempt = 0; attempt < CONNECT_ATTEMPTS; attempt++) {
      try {
        conn = await connect();
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
          if (isTransientNetwork(e, true)) { networkExhausted = true; log(`worker: 建连重试耗尽（${attempt + 1} 次）：${(e as Error).message}`); }
          throw e; // 非瞬时 / 重试耗尽 → 冒泡
        }
        log(`worker: 建连失败（attempt ${attempt + 1}, session=${sid ?? "—"}），重试：${(e as Error).message}`);
        // 退避：与 SIGTERM 竞速——收到信号即提前结束退避，使循环顶部 terminated 检查尽快生效（对称 Nova）
        await new Promise<void>((resolve) => {
          const t = setTimeout(resolve, CONNECT_BACKOFF_MS[Math.min(attempt, CONNECT_BACKOFF_MS.length - 1)]);
          onTerminate = () => { clearTimeout(t); resolve(); };
        });
        if (terminated) throw e;  // 退避被 SIGTERM 打断 → 不再重连
      }
    }
    const { page, agent } = conn!;
    agentRef = agent;  // 上提给 SIGTERM/SIGINT handler（中断兜底提前上传 agent.reportFile，ADR 0029）

    // sessionId 随 scope_started 即回传（不只等 scope_done）——超时/SIGTERM 中途打断时 scope_done 不会 emit，
    // 但血缘已先随首事件落到 core（ADR 0028 观测缺口修复，对称 Nova）。
    await eventSink.emit({ type: "scope_started", scopeId: scope.id, sessionId });  // 三级时长起点（越过此点不再重试建连）
    // scope 内串行运行 scenarios，共享同一会话（ADR 0019/0024）
    const votesN = job.assertionVotes ?? 1;  // AI 断言投票次数（ADR 0014/0024，组合根经 --assertion-votes 设）；缺省 1 = 单次判定、不做抖动检测
    // report 提前上传的 mtime 去重状态：**scope 级共享**（单份 report.html 跨 scenario 累积增长，共享才准）。
    const snapState = { mtime: -1 };
    // scenario 边界 log 提前上传的 per-file mtime 去重表（ADR 0029 上传时机第四级）：**scope 级共享**（log append-only
    // 单调增长、跨 scenario 累积，只传真变过的 topic 文件、不重发未变 log）。log 落 `<MIDSCENE_RUN_DIR>/log/`。
    const logSeen = new Map<string, number>();
    const logDir = (!NO_ARTIFACTS && process.env.MIDSCENE_RUN_DIR) ? path.join(path.resolve(process.env.MIDSCENE_RUN_DIR), "log") : undefined;
    // step 级机读证据的注入（ADR 0042 决策一）：落点与 flush 根同一判据——`--no-report` 方式（这一方式也没开
    // persistExecutionDump、无截图文件可引）或没给产物落点 → undefined = 本 run 不产 evidence。
    const evidenceRoot = artifactFlushRoot();
    const evidence: EvidenceHook | undefined = evidenceRoot
      ? { runDir: evidenceRoot, scopeId: scope.id, uploader, logFn: log }
      : undefined;
    for (const sc of job.scenarios) {
      await eventSink.emit({ type: "scenario_started", scenarioId: sc.id });
      // scope 内 step 短路在 runScenario 内（上游 error 跳过后续、发 step_skipped，ADR 0031 决定六）；
      // act 边界提前上传（report snapshot）也在 runScenario 内 step_done 安全点（ADR 0029，为 Fargate 预演）。
      const statuses = await runScenario(agent, page, sc.id, sc.steps, votesN, uploader, snapState, eventSink, evidence);
      await eventSink.emit({ type: "scenario_done", scenarioId: sc.id, status: aggregate(statuses) });
      // scenario 边界提前上传诊断 log（ADR 0029 上传时机第四级，Midscene 单引擎、为 Fargate 预演）：把该 scenario 期间已在盘、
      // 未传的 log/*.log 提前传进 S3，收窄 log 丢失窗口从「整个 run」到「当前正在运行的 scenario」。best-effort：失败吞、
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
    }

    // 归集原生报告（ADR 0027 reportRefs）：destroy 后 reportFile finalize，Midscene 出 1 个 html/worker（scope 级）
    // kind=report（产物类型；粒度由挂在 scope_done 表达，ADR 0027）；agent.reportFile 是绝对路径。
    // ref 经 uploader：cloud 上传 S3+删本地报 s3://，local no-op 报 file://（ADR 0029，对称 Nova）。
    await agent.destroy().catch(() => {});
    if (agent.reportFile && !NO_ARTIFACTS) {
      // **scope 级 report 上传 best-effort：失败吞+log、不带 report ref、不 throw**（ADR 0032，对称 Nova summary）——
      // 此刻 scope 判定已 emit 完，report 上传失败（多为 S3 网络瞬时）不该 throw→冒泡到 bin.mts 的统一 catch→worker fatal + exit(1)、
      // 把已运行完的 scope 毁成 worker fatal。对齐同文件 interruptSnapshot/snapshotLogs 提前上传的 best-effort。
      try {
        const ref = await uploader.toReportRef(agent.reportFile);  // 实时上传（不删，留到 flush 整目录删）
        reportRefs.push({ kind: "report", ref, label: "Midscene report" });
      } catch (e) {
        // 产品面一行：判定已 emit 完，这里只丢一个报告链接（不带 report ref、失败吞不抛的判据见上）。
        log(`worker: 引擎原生报告未能上传（不影响判定与报告，报告里少一个引擎报告链接）：${(e as Error).message}`);
      }
    }
  } catch (e) {
    await cleanup();
    // 会话已释放，再排空截图后台队列（会话释放优先，ADR 0024；对齐 onSignal 里的③）——网络耗尽与异常
    // 这两条提前退出路径都**不 flush**（中断产物留本地），队列里没传完的字节就此丢，故给有界预算兜一把。
    await drainArtifactQueue(uploader, QUEUE_DRAIN_EXIT_MS, false);
    // 建连重试耗尽（网络瞬时故障）→ 退网络专用码（ADR 0028）；但 cleanupFailed（会话泄漏）优先级更高。
    if (networkExhausted && !cleanupFailed) {
      log("worker: connect retries exhausted, exiting with network code");
      return EX_WORKER_NETWORK;
    }
    throw e; // 非网络耗尽 → 原样冒泡到 bin.mts 的统一 catch（打 `worker fatal:` + exit 1，core 记 engine_error）
  } finally {
    await cleanup();
  }

  await eventSink.emit({ type: "scope_done", scopeId: scope.id, sessionId: sessionId ?? null, reportRefs });
  // scope 末：整目录 flush 剩余产物（report.html 已实时传、跳过；log/ 等一并传）+ 全成功删整目录（ADR 0029）。
  // no-op（local/未注入落点）时直接返回、不碰本地。仅正常完成路径走到此；异常/网络耗尽的 catch 内 return 不 flush
  // ——中断产物保留本地（对称 Nova）。
  const flushRoot = artifactFlushRoot();  // --no-report 方式 → undefined，不 flush（对称 Nova 的 no-artifacts 分支）
  // 先排空后台截图队列、再整目录 flush（ADR 0042 决策一）：flush 只兜漏网的那几张——若反过来，队列里
  // 在途的那张会被 flush 按「还没记 uploaded」重传一次（同 key 冗余）。
  // flushFollows=true：本路径的排空后面就跟着整目录 flush。flushRoot 为 undefined（`--no-report` 方式）时
  // 不 flush，但那一方式与 evidence 落点同一判据（见上 evidenceRoot）、队列必空，这句提示不会发出。
  await drainArtifactQueue(uploader, QUEUE_DRAIN_SCOPE_END_MS, true);
  if (flushRoot) await uploader.flushAndCleanup(flushRoot);
  // 正常路径若会话释放失败 → 非 0 退出，让 schedule 记 error、泄漏可观测
  // （ADR 0024「会话释放失败可观测」，对照 Nova）
  return cleanupFailed ? 1 : 0;
}

// scope 内串行运行一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028，对称 Nova）。
// 短路：本 scenario 内一旦某 step status==error（导航 SSL 失败等），后续 step 不再调 AI——① 省钱；
// ② 不在损坏环境（SSL 错误页）上产生误导性假失败。被跳过的 step 发独立 step_skipped 事件（非 step_done；
// core 据此本地赋 StepResult(SKIPPED, shortcircuited=True)）。判据锁 status==error（不看 errorType）；
// **只短路本 scenario**（下一 scenario 可能导航新页恢复，独立用例不牵连；跨 job 是 fail-fast 职责，正交）。
// 返回各步 status——被跳过步**不进** statuses，故不参与 aggregate（scenario 判定由那个 error step 决定）。
async function runScenario(
  agent: PlaywrightAgent, page: import("playwright").Page, scenarioId: string, steps: Step[], votesN: number,
  uploader: ArtifactUploader, snapState: { mtime: number },
  sink: { emit: (e: unknown) => Promise<void> },
  evidence?: EvidenceHook,  // step 级机读证据（ADR 0042）；不注入 = 不产（`--no-report` 方式 / 无产物落点）
): Promise<string[]> {
  const statuses: string[] = [];
  let shortcircuit = false;
  for (const step of steps) {
    if (shortcircuit) {
      await sink.emit({ type: "step_skipped", scenarioId, stepIndex: step.index });
      continue;
    }
    const status = await runStep(agent, page, scenarioId, step, votesN, sink, evidence);
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
        // 本行不作再传承诺（ADR 0039 产品面文案不变量，两引擎同形）：正常路径上 snapState.mtime 未更新，
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

async function runStep(
  agent: PlaywrightAgent, page: import("playwright").Page, scenarioId: string, step: Step, votesN: number,
  sink: { emit: (e: unknown) => Promise<void> },
  evidence?: EvidenceHook,  // step 级机读证据（ADR 0042）；不注入 = 不产
): Promise<string> {
  const { index, keyword, text } = step;
  await sink.emit({ type: "step_started", scenarioId, stepIndex: index });  // step 时长起点
  // 本 step 起点的累计 token：成功与失败路径都按增量算成本（确定性/URL 分支不调 AI、增量为 0 → 不带 cost）
  const tokBefore = cumulativeTokens(agent);
  // 本 step 起点的 execution 数（ADR 0042 决策一）：step 末按它从 agent.dump.executions 切出本 step 新增的。
  // **在 try 之外**：executionsLength 自己吞异常，绝不能让「记起点」这步冒泡（那会连 step_done 都发不出）。
  const execFrom = executionsLength(agent);
  const votes: boolean[] = [];        // 逐票结果（进 evidence 的 act.vote；多数票数学仍看 yes 计数）
  let instr: string | null = null;    // 交给引擎的指令（进 evidence 的 act.prompt）；null = 本 step 没调 AI
  // 本 step 判定已成之后的收尾出口（三条出口共用）：产 evidence → 挂 ref → **emit** → 才把截图交后台队列。
  // **这个顺序是契约**（ADR 0042 决策一「上传时机分两类」）：evidence.json 的 ref 必须随 step_done 走，故它
  // 即时传；截图字节反过来——emit 之前入队就是把字节又压回判定前面，主流程该做的是发完判定立刻进下一 step。
  // **绝不抛**（决策二：对判定零影响）——落在 act 异常分类路径之外的语义由 stepEvidenceRef 内部整体 try
  // 保证，enqueue 则是同步返回、不抛（见上传器）。故此处可直接 await。
  const emitWithEvidence = async (ev: Record<string, unknown>, status: string, error: string | null) => {
    const produced = await stepEvidenceRef(evidence, {
      scenarioId, step, status, message: (ev.message as string | undefined) ?? null,
      agent, execFrom, page, prompt: instr, votes, error,
    });
    if (produced !== null) {
      appendReportRef(ev, { kind: EVIDENCE_KIND, ref: produced.ref, label: EVIDENCE_KIND });
    }
    await sink.emit(ev);
    if (produced !== null && produced.screenshots.length > 0) {
      evidence?.uploader.enqueue(produced.screenshots);  // emit 之后：字节在下个 step 期间顺链传上去
    }
  };
  try {
    // ① 确定性注册表（ADR 0022）：命中走精确 handler、不投票；AssertionError→failed，其它→error
    const hit = matchDeterministic(text);
    if (hit) {
      try {
        await hit.handler({ page }, hit.groups);
      } catch (e) {
        if (e instanceof DeterministicAssertion || (e as Error).name === "AssertionError") {
          await sink.emit({
            type: "step_done", scenarioId, stepIndex: index,
            status: "failed", errorType: "assertion_failed",
            message: (e as Error).message || `确定性断言未过：${text}`,
          });
          return "failed";
        }
        throw e; // 其它异常 → 落到下面 catch，记 error
      }
      await sink.emit({ type: "step_done", scenarioId, stepIndex: index, status: "passed" });
      return "passed";
    }
    const urlMatch = URL_IN_QUOTES.exec(text);
    if (urlMatch) {
      // ② 内建确定性导航（ADR 0020）：抽 URL 直接 goto，不浪费 AI
      await page.goto(urlMatch[1], { waitUntil: "domcontentloaded", timeout: 60_000 });
      await sink.emit({ type: "step_done", scenarioId, stepIndex: index, status: "passed" });
      return "passed";
    }
    if (keyword === "Then") {
      // AI 断言 + N 次投票（ADR 0014/0024）；votesN=1 即单次判定（仍发 votes 标记这是 AI 断言）
      instr = buildInstruction(step.text, step.argument as any);  // 自然语言 + 多行参数（DataTable/DocString，ADR 0024）
      let yes = 0;
      // 逐票记进 votes：evidence 要「本次调用计入判定的那一票」（ADR 0042 映射表 act.vote = aiBoolean 返回值），
      // 光有 yes 计数分不清是哪几票投的 no。
      for (let i = 0; i < votesN; i++) {
        const vote = await agent.aiBoolean(instr);
        votes.push(vote);
        if (vote) yes++;
      }
      const passed = yes > votesN / 2;
      const ev: Record<string, unknown> = {
        type: "step_done", scenarioId, stepIndex: index,
        status: passed ? "passed" : "failed",
        votes: { yes, total: votesN },
      };
      const cost = stepCost(tokBefore, agent);  // N 票 token 增量合计（修：原 lastCost 只算最后一票）
      if (cost) ev.cost = cost;
      if (!passed) { ev.errorType = "assertion_failed"; ev.message = `AI 断言未过多数票（${yes}/${votesN}）：${text}`; }
      await emitWithEvidence(ev, passed ? "passed" : "failed", null);
      return passed ? "passed" : "failed";
    }
    // When / Given（非 URL）→ AI 动作（无 votes）
    instr = buildInstruction(step.text, step.argument as any);
    await agent.aiAct(instr);
    const ev: Record<string, unknown> = { type: "step_done", scenarioId, stepIndex: index, status: "passed" };
    const cost = stepCost(tokBefore, agent);
    if (cost) ev.cost = cost;
    await emitWithEvidence(ev, "passed", null);
    return "passed";
  } catch (e) {
    // 诊断分类细化（ADR 0028，对称 Nova）：act 中途网络瞬时故障（CDP 闪断等）标 network_error 比笼统
    // engine_error 更准。**仅分类、不触发重试/恢复**：act 不幂等，schedule job 级重试要求「会话未起（零
    // step_done）」，此处 step_started 早已 emit、saw_step=True，双条件 AND 天然不满足；本失败走 step_done
    // 事件流（非退出码 80），core 侧 is_network=False。"act 中途恢复"仍 defer，这里只把失败原因记准。
    const errorType = isTransientNetwork(e) ? "network_error" : "engine_error";
    // message 与 evidence 的 error 同过 errorText（一行、有界；Playwright 异常的 message 常拖着多行 call
    // log，规则与理由见 error-text.mts，Nova 侧 `_error_text` 是对称版）。两处必须同一份文本：evidence 冗余
    // step_done 的 message 以自包含（ADR 0042 决策一）。
    const message = errorText(e);
    const ev: Record<string, unknown> = {
      type: "step_done", scenarioId, stepIndex: index,
      status: "error", errorType, message,
    };
    // 失败的 act 费用已经发生（ADR 0024「失败的 act 同样带 cost」）：抛异常前已发生的调用照样折进 agent.metrics，照报 token 增量
    const cost = stepCost(tokBefore, agent);
    if (cost) ev.cost = cost;
    // error step 的 evidence 最该产（抛错的 task 仍在 executions 里、带 errorMessage）；抽取失败也只是没 ref
    await emitWithEvidence(ev, "error", message);
    return "error";
  }
}

function aggregate(statuses: string[]): string {
  if (statuses.includes("error")) return "error";
  if (statuses.includes("failed")) return "failed";
  return "passed";
}

// 测试可见（对称 Nova：Nova worker 靠 if __name__ 守卫使 _run_step/_run_scenario/_is_transient_network 可 import 测）。
// `main` 由 bin 调（见文件头「本模块不是进程入口」）；其余是单测面。
export {
  runStep, runScenario, isTransientNetwork, aggregate, interruptSnapshot, drainArtifactQueue, shutdownSequence,
  agentOpts,
};
