// Midscene 薄 worker（ADR 0022/0024）：读 stdin 的 job JSON → 跑一个 scope → 吐 ADR 0024 事件到事件通道。
//
// 不含 BDD runner 装饰器：会话/aiAct/aiBoolean 投票/派发逻辑直接在本进程跑（ADR 0022 薄 worker）。
// core 经子进程 adapter 起本 worker（ADR 0026 机制层），讲 ADR 0024 协议——与 Nova Act 引擎对称。
//
// 三通道分离（ADR 0024）：协议事件吐到 EVENTS_FD 指定的 fd（无则回落 stdout，便于手动直跑调试）；
// Midscene/SDK 的 stdout 噪声留 stdout；worker 自身诊断走 stderr。
//
// cost（ADR 0024）：从 agent._unstableLogContent() 的 executions[].tasks[].usage.total_tokens 取原生
// token 数，worker 只报 {tokens}；core 合计、美元折算交消费者（不追 Qwen 单价）。两个引擎对称：都只报原生量。
//
// **本模块不是进程入口**（ADR 0037 决策 3）：入口是 `bin.mts`（npm bin `gherkai-worker-midscene` /
// 容器 CMD），它装 tsx loader + 注册裸 specifier 的 resolve hook 后调本模块的 `main`。故这里只导出
// `main`、不自带 `if 入口` 守卫——「装 loader」与「跑 worker」分层，且 import 本模块做单测时不触发 main。
//
// 跑（一般由 core adapter 按 ADR 0037 的定位链 spawn；也可手动）：
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
import { sigv4Fetch, signCdpUpgrade, getBaseUrl, MODEL, getRegion } from "../lib/agentcore-sigv4.mjs";
import { ArtifactUploader } from "../lib/artifact-upload.mjs";  // 产物 S3 上传（ADR 0029；无落点 env 时 no-op 报 file://）
import { EventSink } from "../lib/event-sink.mjs";  // 事件出口（ADR 0024「I/O 边缘可注入接口」，两态见该模块头）
import { JobSource } from "../lib/job-source.mjs";  // job 入口（同上）
// 确定性 step 注册表（ADR 0022）+ 测试开发的锚点脚手架。
// import 脚手架即触发其顶层 deterministic(...) 注册副作用（对称 Nova 引擎 import deterministic_steps）。
import { match as matchDeterministic, DeterministicAssertion, listRegistry, matchBatch } from "./deterministic.mjs";
import { buildInstruction } from "./argument.mjs";
import "./deterministic.steps.mjs";  // 内建脚手架（ADR 0022 退役 bdd 层后迁入 worker/）——**先于**使用方 steps 注册
import { loadUserSteps } from "./user-steps.mjs";  // 使用方 steps/ 目录的加载（ADR 0037 决策 4）

const BROWSER_ID = "aws.browser.v1";
// AI 断言投票次数由 job.assertionVotes 决定（ADR 0014/0024，组合根经 --assertion-votes 设）。
// 默认 1（不抖动检测，结果直观）；调高才跑 N 次取多数票。
// 网络专用退出码（ADR 0028）：与 core/gherkai_core/wire.py 的 EX_WORKER_NETWORK 同值（协议层单一事实源，两 Engine adapter 共用翻译）。
// worker 建连失败、重试耗尽时以此码退出，作 out-of-band 信号（建连失败先于任何事件 emit）。
const EX_WORKER_NETWORK = 80;
// 建连重试上限（ADR 0028）；退避 [0.5,1,2]s，总 ~3.5s，远小于组合根按引擎推导的 grace 下限
// （midscene 见 runtime/gherkai_runtime/compose.py `MIDSCENE_GRACE_MIN_S`；此处不复述会变的数字）。
const CONNECT_ATTEMPTS = 4;
const CONNECT_BACKOFF_MS = [500, 1000, 2000];
// SIGTERM cleanup 里单个 StopBrowserSession 的超时预算（ADR 0028）：退化网络下 Stop 可能挂很久
// （共享 client maxAttempts=3、无显式超时），超过 schedule grace 会被 SIGKILL 打断到一半 → 会话泄漏。
// 套这个预算：挂死时及时放弃，至少让 worker 干净退出、不被强杀。须 < grace（组合根按引擎推导的下限，midscene-only ≈ MIDSCENE_GRACE_MIN_S=25s）。
const STOP_SESSION_BUDGET_MS = 3000;
// StartBrowserSession 已发出 RPC 但 sessionId 未返回的在途窗口兜底（ADR 0028）：SIGTERM 落在这一瞬时
// 服务端可能已建会话但客户端没拿到 id。给一小段时间让 Start 的 await 返回、id 落进待清理集，再 cleanup。
const INFLIGHT_SETTLE_MS = 1500;
// scenario 边界 log 抢传的总墙钟预算（ADR 0029「第四级：scenario 边界抢传」）：单个 log 上传已被
// uploadOne 的 AbortSignal.timeout(10s) 封顶，但一个 scenario 边界要传多个 log，退化网络下串行累加会拖住
// 下一 scenario、并叠进 grace。给整次快照套此总预算：超预算即放弃剩余（best-effort，scope 末 flush 兜底）。
// 抢传跑在主流程（scenario 之间、非 SIGTERM handler），此预算限的是「延迟下一 scenario 的墙钟」，非 grace。
const SCENARIO_LOG_SNAPSHOT_BUDGET_MS = 8000;

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
    MIDSCENE_USE_QWEN3_VL: "true",
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

// 中断兜底抢传（ADR 0029「act 边界抢传」的 handler 兜底，为 Fargate 预演）——从 onSignal 提出为可测纯函数
// （对称 Nova 把 _on_signal 提到模块级、供 test_interrupt_model/process 测；否则 main() 内闭包无法单测，是
// 「该对称却漏」的测试缺口）。**调用点在 onSignal 里必须排在 cleanup 之后**（会话释放优先铁律，ADR 0024）——
// 本函数只管「抢传那一步」的决策，不含 cleanup/退出，顺序由调用方保证。
// 决策：① reportFile 空窗（首个 AI task 前未置）→ 跳过（无 report 可抢）；② 有 → best-effort 抢传（读盘上那份
// 增量 report）、**失败吞+log、绝不抛**（抢传是保险、不该影响退出码/退出流程；no-op local 下 snapshotReport 自返回）。
// 救的是「首个/当前 act 中途、无 prior step_done」这格：主流程卡在 await aiAct、step_done 抢传从未触发、S3 一无
// 所有，而盘上已有截至最后一个已返回 AI 调用的一致 report。Node handler 是事件循环回调、能安全 await 读盘上传
// （Nova 因 greenlet 做不到、Midscene 能——关键不对称）。
async function interruptSnapshot(
  uploader: { snapshotReport: (p: string) => Promise<void> },
  reportFile: string | null | undefined,
  logFn: (m: string) => void = log,
): Promise<void> {
  if (!reportFile) return;  // 空窗：无 report 可抢
  try {
    await uploader.snapshotReport(reportFile);
  } catch (e) {
    logFn(`worker: 中断兜底抢传 report 失败（best-effort、忽略）：${(e as Error).message}`);
  }
}

// SIGTERM/SIGINT 收尾序列（ADR 0024 终止契约 + 0029 中断兜底抢传）——从 onSignal 提出为可测函数（依赖注入），
// 对称 Nova 把 _on_signal 提到模块级供 test_interrupt_model/process 测。**锁住关键顺序不变量**：
//   会话释放（cleanup）**必须先于**中断兜底抢传（interruptSnapshot）——ADR 0024「会话释放优先」铁律，
//   抢传是 best-effort、绝不延迟会话释放（退化网络下抢传挂 10s 也不该让会话多泄漏 10s）。
// 返回该退出的码（cleanupFailed→1 让泄漏可观测、否则 0）；不自己 process.exit（交调用方，便于测试不真退进程）。
// deps 全注入（cleanup/getCleanupFailed/uploader/reportFile...）→ 单测可传 spy 断言调用序列，无需真信号/真进程。
interface ShutdownDeps {
  inflightPending: () => boolean;      // startInFlight && pendingSessions.size===0：在途窗口兜底是否需等
  settleMs: number;                    // 在途兜底等待（INFLIGHT_SETTLE_MS）
  sleep: (ms: number) => Promise<void>;
  cleanup: () => Promise<void>;        // 释放会话（**先跑**）
  uploader: { snapshotReport: (p: string) => Promise<void> };
  reportFile: () => string | null | undefined;  // 惰性读（agentRef 可能收尾时才有值）
  getCleanupFailed: () => boolean;     // cleanup 内部副作用写的泄漏标记
  logFn?: (m: string) => void;
}
async function shutdownSequence(deps: ShutdownDeps): Promise<number> {
  const logFn = deps.logFn ?? log;
  logFn("worker: signal received, releasing AgentCore session(s)");
  if (deps.inflightPending()) await deps.sleep(deps.settleMs);  // 在途窗口兜底（ADR 0028）
  await deps.cleanup();                                          // ① 会话释放优先（ADR 0024 铁律）
  await interruptSnapshot(deps.uploader, deps.reportFile());     // ② 抢传排其后（best-effort、不延迟①）
  const failed = deps.getCleanupFailed();
  logFn(`worker: session shutdown complete after signal${failed ? " (WITH FAILURE)" : ""}`);
  return failed ? 1 : 0;
}

interface Step { index: number; keyword: string; text: string; argument?: unknown }
interface Scenario { id: string; name: string; steps: Step[] }
interface Job { scope: { id: string; name: string }; engine: string; scenarios: Scenario[]; assertionVotes?: number }


// Midscene/Bedrock 原生量 token 累计（ADR 0024：engine 只报原生量，core 不算美元）。
// _unstableLogContent().executions 是**整个 agent 会话累积**的——故按 step 取 token 必须用"增量"：
// step 跑前记一次累计、跑后再记一次、差值才是本 step 的 token。否则：取末次 usage 会少报（多票断言只
// 算最后一票，欠计 (N-1)/N）；或求和全部会双计（把前面 step 的也算进来）。返回 token 累计和。
function cumulativeTokens(agent: PlaywrightAgent): number {
  try {
    const execs = (agent as any)._unstableLogContent?.()?.executions ?? [];
    let tokens = 0;
    for (const ex of execs) for (const task of ex.tasks ?? []) {
      if (task.usage?.total_tokens != null) tokens += task.usage.total_tokens;
    }
    return tokens;
  } catch {
    return 0;
  }
}

// 本 step 的 token 成本 = 跑后累计 − 跑前累计（增量）。增量 0（无新 usage）→ undefined（不假装 0）。
function stepCost(beforeTokens: number, agent: PlaywrightAgent): Record<string, unknown> | undefined {
  const after = cumulativeTokens(agent);
  const delta = after - beforeTokens;
  return delta > 0 ? { tokens: delta } : undefined;
}

// 自述入口（--list-deterministic / --match-steps）的 stdout payload 写出（ADR 0036「stdout 一行 JSON 即退」）：
// **必须等真 flush 完才能退**，否则 pipe 下大 payload 在 64KB 处静默截断且 rc 仍是 0——组合根只能报「输出非
// JSON」、真因不可见（ADR 0036 的 best-effort 降级把它吞成 plan 无标注）。两种直觉写法都不够：
//   - `process.stdout.write(s)` 后紧跟 process.exit：pipe 上 stdout 是异步写，exit 不 flush 未写完的尾部；
//   - `fs.writeSync(1, s)`：worker 跑在 `--import tsx` 下（见文件头「跑」），tsx 把 fd 1 置成非阻塞，
//     writeSync 对 pipe 只写满内核缓冲就返回 **部分写字节数、且不重试**（真跑实测 1MB 只出 65536）。
// 故走 write 回调等 libuv 真写完（背压/EAGAIN 交事件循环），再由统一出口 process.exit。
async function writeStdoutFlushed(s: string): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    process.stdout.write(s, (e) => (e ? reject(e) : resolve()));
  });
}

// `--no-report` 档（组合根经 env GHERKAI_NO_ARTIFACTS=1 告知，ADR 0037 决策 3）：**不生成、不上报**引擎原生产物——
// 关 agent 的 generateReport、不抢传 log、不带 report ref。Midscene SDK 即便不出 report 也可能往 run 目录写 log/dump
// （相对 cwd 的 ./midscene_run），故此档下若无 MIDSCENE_RUN_DIR 就把它导到一次性临时目录、不进用户 CWD（SDK 内部行为，不上报）。
const NO_ARTIFACTS = process.env.GHERKAI_NO_ARTIFACTS === "1";

export async function main(): Promise<number> {
  if (NO_ARTIFACTS && !process.env.MIDSCENE_RUN_DIR) {
    process.env.MIDSCENE_RUN_DIR = fs.mkdtempSync(path.join(os.tmpdir(), "gherkai-midscene-"));
  }
  // 使用方 steps/ 目录的注册（ADR 0037 决策 4）：**内建脚手架之后**（模块顶 import 已注册完）、
  // **三个自述入口与 job 循环之前**——故 --list-deterministic / --match-steps / plan 标注都反映使用方定制
  // （ADR 0036「真值单一」不变：注册表 = 内建 + 使用方）。加载失败 fail-loud（抛 → bin 一行 stderr + 非零退出）。
  await loadUserSteps();

  // 自述模式（ADR 0036）：dump 确定性注册表即退——不建会话、不读 stdin、零费用。
  // 脚手架已在模块顶 import（副作用注册），此刻注册表即真值。
  if (process.argv.includes("--list-deterministic")) {
    await writeStdoutFlushed(JSON.stringify(listRegistry()) + "\n");
    return 0;
  }
  // 批量 match 查询（ADR 0036 决策 4，plan 命中标注）：stdin 一行 JSON 数组（step 文本）→ stdout 一行
  // 逐条命中结果。匹配语义留在 worker（CLI 零复刻）；同样不建会话、零 AWS。
  if (process.argv.includes("--match-steps")) {
    const chunks: Buffer[] = [];
    for await (const c of process.stdin) chunks.push(c as Buffer);
    const texts: string[] = JSON.parse(Buffer.concat(chunks).toString("utf-8"));
    await writeStdoutFlushed(JSON.stringify(matchBatch(texts)) + "\n");
    return 0;
  }

  // 早期信号护栏（对称 Nova：handler 先于 JobSource.read 装载，ADR 0024）——S3 态下 read 含一次网络往返，
  // 窗口内 SIGTERM 若走 Node 默认处置会以信号终止（非 0）→ adapter 误归 engine_error。此阶段无会话、无产物，
  // 直接干净退 0（零事件 + exit 0，core 判 error 不误归因）；真正的 onSignal（抢传+释放会话）建好后替换本 handler。
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
  let cleanedUp = false;
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
  //   幂等：cleanedUp 守卫，防 SIGTERM handler 与 finally 双调。
  //   **并行** Stop pendingSessions（每个套超时预算）；任一未确认释放 → cleanupFailed（除非 discardAttempt）。
  //   并行（Promise.all）而非串行：N 个会话累积时墙钟 ≈ 单个预算（3s）而非 N×3s——串行会让重试积累的
  //   多个泄漏会话把 cleanup 拖过 grace 被 SIGKILL 截断（正是 ADR 0028「重试放大的 in-flight 会话窗口」条
  //   要防的泄漏）。
  //   discardAttempt=true（丢弃中间建连 attempt 的部分会话，ADR 0028）：Stop 失败只 log、**不点亮
  //   final cleanupFailed**——那个会话本就要丢、与「最终态会话是否泄漏」无关；否则一次中间失败会毒化
  //   后续成功 attempt 的退出码（误报泄漏 → core 当 engine_error）。final cleanup（默认）才管 cleanupFailed。
  async function cleanup(discardAttempt = false): Promise<void> {
    if (cleanedUp) return;
    cleanedUp = true;
    await Promise.all([...pendingSessions].map(async (sid) => {
      const ok = await stopSession(sid);
      if (ok) pendingSessions.delete(sid);
      else if (!discardAttempt) cleanupFailed = true;
    }));
    // 会话已释放，再尽力关本地 browser；套超时，挂住也不拖垮（会话已停，close 失败无计费影响）
    if (browser) {
      await Promise.race([
        browser.close().catch(() => {}),
        new Promise<void>((r) => setTimeout(r, 3000)),
      ]);
    }
  }

  // SIGTERM/SIGINT：清理会话再退（防 AgentCore 会话泄漏后持续计费）。
  let terminated = false;
  let onTerminate: (() => void) | undefined;  // 重试退避用：信号到达即 resolve、打断退避（对称 Nova 的 sleep 被信号打断）
  // agent 引用上提到 handler 可见（ADR 0029 中断抢传：handler 里读 agent.reportFile 抢传那份增量 report）。
  // connect 成功后赋值（见下 `agentRef = agent`）；handler/uploader 靠闭包捕获（执行时 uploader 已初始化）。
  let agentRef: PlaywrightAgent | undefined;
  const onSignal = async () => {
    if (terminated) return;
    terminated = true;
    onTerminate?.();  // 立即唤醒正在退避的重试循环，使其尽快停（不再 reconnect/跑 act）
    // 收尾序列提出为可测的 shutdownSequence（cleanup 先于抢传的顺序不变量在那里被单测锁住）；此处只做
    // 「守卫去重 + 唤醒退避 + 真 process.exit」这层 handler 外壳（进程副作用，不进纯函数）。
    const code = await shutdownSequence({
      inflightPending: () => startInFlight && pendingSessions.size === 0,
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
  process.on("SIGINT", onSignal);  // Ctrl-C 也走同一路径（抢传+释放会话），对称 Nova 已纳入 SIGINT
  process.removeListener("SIGTERM", earlySignal);
  process.removeListener("SIGINT", earlySignal);

  const reportRefs: Array<{ kind: string; ref: string; label?: string }> = [];
  // 产物 S3 上传器（ADR 0029，对称 Nova 的模块级 _uploader）：cloud 上传+删本地报 s3://，local no-op 报 file://。
  const uploader = ArtifactUploader.fromEnv();
  let networkExhausted = false; // 建连重试耗尽（ADR 0028）→ 退 EX_WORKER_NETWORK

  // 建连段（ADR 0028）：StartBrowserSession → CDP 握手 → connectOverCDP → PlaywrightAgent。
  // 整段可被重试；scope_started 一 emit（会话已起、act 即将跑）即跳出重试域，绝不重试 act。
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
    const agent = new PlaywrightAgent(page, {
      generateReport: !NO_ARTIFACTS,  // --no-report：不出 report.html（ADR 0037 决策 3）
      modelConfig: modelConfig(),
      createOpenAIClient: async () => new OpenAI({ baseURL: getBaseUrl(), apiKey: "unused", fetch: sigv4Fetch }) as any,
    });
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
        cleanedUp = false; // 允许对本次 attempt 的部分会话再清一次
        await cleanup(true);
        browser = undefined;
        const sid = sessionId; sessionId = undefined; // 清血缘：失败 attempt 的 id 不该进 scope_done
        cleanedUp = false; // 重置守卫：留给后续 attempt 成功后的 final cleanup（否则被本次置 true 永久跳过）
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
    agentRef = agent;  // 上提给 SIGTERM/SIGINT handler（中断兜底抢传 agent.reportFile，ADR 0029）

    // sessionId 随 scope_started 即回传（不只等 scope_done）——超时/SIGTERM 中途打断时 scope_done 不会 emit，
    // 但血缘已先随首事件落到 core（ADR 0028 观测缺口修复，对称 Nova）。
    await eventSink.emit({ type: "scope_started", scopeId: scope.id, sessionId });  // 三级时长起点（越过此点不再重试建连）
    // scope 内串行跑 scenarios，共享同一会话（ADR 0019/0024）
    const votesN = job.assertionVotes ?? 1;  // AI 断言投票次数（ADR 0014/0024）；缺省 1
    // report 抢传的 mtime 去重状态：**scope 级共享**（单份 report.html 跨 scenario 累积增长，共享才准）。
    const snapState = { mtime: -1 };
    // scenario 边界 log 抢传的 per-file mtime 去重表（ADR 0029「第四级」）：**scope 级共享**（log append-only
    // 单调增长、跨 scenario 累积，只传真变过的 topic 文件、不重发未变 log）。log 落 `<MIDSCENE_RUN_DIR>/log/`。
    const logSeen = new Map<string, number>();
    const logDir = (!NO_ARTIFACTS && process.env.MIDSCENE_RUN_DIR) ? path.join(path.resolve(process.env.MIDSCENE_RUN_DIR), "log") : undefined;
    for (const sc of job.scenarios) {
      await eventSink.emit({ type: "scenario_started", scenarioId: sc.id });
      // scope 内 step 短路在 runScenario 内（上游 error 跳过后续、发 step_skipped，ADR 0031 决定六）；
      // act 边界抢传（report snapshot）也在 runScenario 内 step_done 安全点（ADR 0029，为 Fargate 预演）。
      const statuses = await runScenario(agent, page, sc.id, sc.steps, votesN, uploader, snapState, eventSink);
      await eventSink.emit({ type: "scenario_done", scenarioId: sc.id, status: aggregate(statuses) });
      // scenario 边界抢传诊断 log（ADR 0029「第四级」，Midscene 单引擎、为 Fargate 预演）：把该 scenario 期间已在盘、
      // 未传的 log/*.log 抢进 S3，收窄 log 丢失窗口从「整个 run」到「当前正在跑的 scenario」。best-effort：失败吞、
      // 不阻塞下一 scenario（对齐 report 抢传）。per-file mtime 去重 + 总墙钟预算在 snapshotLogs 内（退化网络护栏）。
      // no-op（local）下 snapshotLogs 直接返回。report 已由 runScenario 内 step_done 抢传覆盖，此处只补 log。
      if (logDir) {
        try {
          await uploader.snapshotLogs(logDir, logSeen, SCENARIO_LOG_SNAPSHOT_BUDGET_MS);
        } catch (e) {
          log(`worker: scenario 边界 log 抢传失败（best-effort、忽略、scope 末 flush 兜底）：${(e as Error).message}`);
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
      // 把已跑完的 scope 毁成 worker fatal。对齐同文件 interruptSnapshot/snapshotLogs 抢传的 best-effort。
      try {
        const ref = await uploader.toReportRef(agent.reportFile);  // 实时上传（不删，留到 flush 整目录删）
        reportRefs.push({ kind: "report", ref, label: "Midscene report" });
      } catch (e) {
        log(`worker: scope 级 report 上传失败（best-effort、忽略、不带 report ref）：${(e as Error).message}`);
      }
    }
  } catch (e) {
    await cleanup();
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
  const runRoot = process.env.MIDSCENE_RUN_DIR;
  if (runRoot) await uploader.flushAndCleanup(path.resolve(runRoot));
  // 正常路径若会话释放失败 → 非 0 退出，让 schedule 记 error、泄漏可观测
  // （ADR 0024「会话释放失败可观测」，对照 Nova）
  return cleanupFailed ? 1 : 0;
}

// scope 内串行跑一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028，对称 Nova）。
// 短路：本 scenario 内一旦某 step status==error（导航 SSL 失败等），后续 step 不再调 AI——① 省钱；
// ② 不在损坏环境（SSL 错误页）上跑出误导性假失败。被跳过的 step 发独立 step_skipped 事件（非 step_done；
// core 据此本地赋 StepResult(SKIPPED, shortcircuited=True)）。判据锁 status==error（不看 errorType）；
// **只短路本 scenario**（下一 scenario 可能导航新页恢复，独立用例不牵连；跨 job 是 fail-fast 职责，正交）。
// 返回各步 status——被跳过步**不进** statuses，故不参与 aggregate（scenario 判定由那个 error step 决定）。
async function runScenario(
  agent: PlaywrightAgent, page: import("playwright").Page, scenarioId: string, steps: Step[], votesN: number,
  uploader: ArtifactUploader, snapState: { mtime: number },
  sink: { emit: (e: unknown) => Promise<void> },
): Promise<string[]> {
  const statuses: string[] = [];
  let shortcircuit = false;
  for (const step of steps) {
    if (shortcircuit) {
      await sink.emit({ type: "step_skipped", scenarioId, stepIndex: step.index });
      continue;
    }
    const status = await runStep(agent, page, scenarioId, step, votesN, sink);
    statuses.push(status);
    // act 边界抢传（ADR 0029，为 Fargate 预演）：step_done 安全点（act 已返回、SDK onTaskUpdate 已 await flush，
    // 盘上 report 一致无半写），把增量增长的单份 report.html 用 snapshotReport overwrite 同 key 抢传。
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
        log(`worker: report 抢传失败（best-effort、忽略、下步重试）：${(e as Error).message}`);
      }
    }
    if (status === "error") shortcircuit = true;  // 本 scenario 后续 step 短路
  }
  return statuses;
}

async function runStep(
  agent: PlaywrightAgent, page: import("playwright").Page, scenarioId: string, step: Step, votesN: number,
  sink: { emit: (e: unknown) => Promise<void> },
): Promise<string> {
  const { index, keyword, text } = step;
  await sink.emit({ type: "step_started", scenarioId, stepIndex: index });  // step 时长起点
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
      const instr = buildInstruction(step.text, step.argument as any);  // 自然语言 + 多行参数（DataTable/DocString，ADR 0024）
      const tokBefore = cumulativeTokens(agent);  // 投票前累计 → 用增量算本 step 全 N 票成本（不少报）
      let yes = 0;
      for (let i = 0; i < votesN; i++) if (await agent.aiBoolean(instr)) yes++;
      const passed = yes > votesN / 2;
      const ev: Record<string, unknown> = {
        type: "step_done", scenarioId, stepIndex: index,
        status: passed ? "passed" : "failed",
        votes: { yes, total: votesN },
      };
      const cost = stepCost(tokBefore, agent);  // N 票 token 增量合计（修：原 lastCost 只算最后一票）
      if (cost) ev.cost = cost;
      if (!passed) { ev.errorType = "assertion_failed"; ev.message = `AI 断言未过多数票（${yes}/${votesN}）：${text}`; }
      await sink.emit(ev);
      return passed ? "passed" : "failed";
    }
    // When / Given（非 URL）→ AI 动作（无 votes）
    const tokBefore = cumulativeTokens(agent);  // 动作前累计 → 增量算本 step 成本
    await agent.aiAct(buildInstruction(step.text, step.argument as any));
    const ev: Record<string, unknown> = { type: "step_done", scenarioId, stepIndex: index, status: "passed" };
    const cost = stepCost(tokBefore, agent);
    if (cost) ev.cost = cost;
    await sink.emit(ev);
    return "passed";
  } catch (e) {
    // 诊断分类细化（ADR 0028，对称 Nova）：act 中途网络瞬时故障（CDP 闪断等）标 network_error 比笼统
    // engine_error 更准。**仅分类、不触发重试/恢复**：act 不幂等，schedule job 级重试要求「会话未起（零
    // step_done）」，此处 step_started 早已 emit、saw_step=True，双条件 AND 天然不满足；本失败走 step_done
    // 事件流（非退出码 80），core 侧 is_network=False。"act 中途恢复"仍 defer，这里只把失败原因记准。
    const errorType = isTransientNetwork(e) ? "network_error" : "engine_error";
    await sink.emit({
      type: "step_done", scenarioId, stepIndex: index,
      status: "error", errorType, message: `${(e as Error).name}: ${(e as Error).message}`,
    });
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
export { runStep, runScenario, isTransientNetwork, aggregate, interruptSnapshot, shutdownSequence };
