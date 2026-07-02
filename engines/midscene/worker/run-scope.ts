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
// 跑（一般由 core adapter spawn；也可手动）：
//   echo '<job json>' | AWS_REGION=us-east-1 node --import tsx worker/run-scope.ts
//   （用 `--import tsx`，非 `tsx/esm`：本子工程是 commonjs，tsx/esm loader 会冲突——与 cli compose 一致）
import OpenAI from "openai";
import { PlaywrightAgent } from "@midscene/web/playwright";
import { chromium, type Browser } from "playwright";
import {
  BedrockAgentCoreClient,
  StartBrowserSessionCommand,
  StopBrowserSessionCommand,
} from "@aws-sdk/client-bedrock-agentcore";
import * as fs from "node:fs";
import { pathToFileURL } from "node:url";
import { sigv4Fetch, signCdpUpgrade, BASE_URL, MODEL, REGION } from "../lib/agentcore-sigv4.mjs";
// 确定性 step 注册表（ADR 0022）+ test engineer 的锚点脚手架。
// import 脚手架即触发其顶层 deterministic(...) 注册副作用（对称 Nova 引擎 import deterministic_steps）。
import { match as matchDeterministic, DeterministicAssertion } from "./deterministic.js";
import { buildInstruction } from "./argument.js";
import "../bdd/steps/deterministic.steps.js";

const BROWSER_ID = "aws.browser.v1";
// AI 断言投票次数由 job.assertionVotes 决定（ADR 0014/0024，组合根经 --assertion-votes 设）。
// 默认 1（不抖动检测，结果直观）；调高才跑 N 次取多数票。
// 网络专用退出码（ADR 0028）：与 core/adapters/subprocess_engine.py 的 EX_WORKER_NETWORK 同值。
// worker 建连失败、重试耗尽时以此码退出，作 out-of-band 信号（建连失败先于任何事件 emit）。
const EX_WORKER_NETWORK = 80;
const CONNECT_ATTEMPTS = 4; // 建连重试上限（ADR 0028）；退避 [0.5,1,2]s，总 ~3.5s < grace 5s
const CONNECT_BACKOFF_MS = [500, 1000, 2000];
// SIGTERM cleanup 里单个 StopBrowserSession 的超时预算（ADR 0028）：退化网络下 Stop 可能挂很久
// （共享 client maxAttempts=3、无显式超时），超过 schedule grace 会被 SIGKILL 打断到一半 → 会话泄漏。
// 套这个预算：挂死时及时放弃，至少让 worker 干净退出、不被强杀。须 < grace（schedule 默认 5s，cli 10s）。
const STOP_SESSION_BUDGET_MS = 3000;
// StartBrowserSession 已发出 RPC 但 sessionId 未返回的在途窗口兜底（ADR 0028）：SIGTERM 落在这一瞬时
// 服务端可能已建会话但客户端没拿到 id。给一小段时间让 Start 的 await 返回、id 落进待清理集，再 cleanup。
const INFLIGHT_SETTLE_MS = 1500;

// AWS SDK v3 服务端瞬时故障的节流错误 name 集（ADR 0028）——对齐 botocore 节流码集（保两腿对称）。
// AgentCore 起会话（StartBrowserSessionCommand）是 AWS SDK v3 调用，服务端瞬时不可用/限流时抛的 error
// 带 name（如 ThrottlingException）+ $metadata.httpStatusCode + 可选 $retryable。
const AWS_THROTTLE_NAMES = new Set([
  "ThrottlingException", "Throttling", "ThrottledException", "RequestThrottledException",
  "TooManyRequestsException", "ProvisionedThroughputExceededException", "RequestLimitExceeded",
  "SlowDown", "LimitExceededException", "ServiceUnavailable", "ServiceUnavailableException",
]);
const AWS_TRANSIENT_STATUS = new Set([500, 502, 503, 504]);

// 是否网络/SSL 瞬时故障（可重试，ADR 0028）。Node 侧按 error code / TLS 错 / AWS SDK v3 服务端瞬时识别。
// 遍历 error.cause 链：SDK 常把底层 socket/TLS 错、或 AWS 服务端错包成自有 Error，只看最外层会漏判（防环：限 8 层）。
function isTransientNetwork(e: unknown): boolean {
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
    if (cur.name && AWS_THROTTLE_NAMES.has(cur.name)) return true;
    if (cur.$metadata?.httpStatusCode != null && AWS_TRANSIENT_STATUS.has(cur.$metadata.httpStatusCode)) return true;
    if (cur.$retryable?.throttling === true) return true;
    const msg = cur.message ?? "";
    if (/\b(socket hang up|ssl|tls|econnreset|epipe|timeout|handshake|UNEXPECTED_EOF)\b/i.test(msg)) return true;
    cur = cur.cause as typeof cur;
  }
  return false;
}
const MODEL_CONFIG = {
  MIDSCENE_MODEL_NAME: MODEL,
  MIDSCENE_MODEL_BASE_URL: BASE_URL,
  MIDSCENE_MODEL_API_KEY: "unused",
  MIDSCENE_USE_QWEN3_VL: "true",
};
const URL_IN_QUOTES = /"(https?:\/\/[^"]+)"/;

// --- 事件通道：写 EVENTS_FD（adapter 经环境变量告知 fd 号，pass_fds 继承）；无则回落 stdout ---
const EVENTS_FD = process.env.EVENTS_FD ? Number(process.env.EVENTS_FD) : 1;
function emit(obj: unknown): void {
  fs.writeSync(EVENTS_FD, JSON.stringify(obj) + "\n"); // 同步写：保证事件按序到达（ADR 0024 顺序不变量）
}
function log(msg: string): void {
  process.stderr.write(msg + "\n");
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

async function readStdin(): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const c of process.stdin) chunks.push(c as Buffer);
  return Buffer.concat(chunks).toString("utf-8");
}

async function main(): Promise<number> {
  const job: Job = JSON.parse((await readStdin()).split("\n")[0]);
  const scope = job.scope;

  const cp = new BedrockAgentCoreClient({ region: REGION });
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
  //   不让易挂起的 browser.close 挟持会话释放（审计窗口 5）。close 套超时预算，避免耗尽 grace。
  //   幂等：cleanedUp 守卫，防 SIGTERM handler 与 finally 双调。
  //   **并行** Stop pendingSessions（每个套超时预算）；任一未确认释放 → cleanupFailed（除非 discardAttempt）。
  //   并行（Promise.all）而非串行：N 个会话累积时墙钟 ≈ 单个预算（3s）而非 N×3s——串行会让重试积累的
  //   多个泄漏会话把 cleanup 拖过 grace 被 SIGKILL 截断（正是本修复要防的泄漏，ADR 0028）。
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

  // SIGTERM：清理会话再退（防 AgentCore 会话泄漏继续烧钱）。
  let terminated = false;
  let onTerminate: (() => void) | undefined;  // 重试退避用：SIGTERM 到达即 resolve、打断退避（对称 Nova 的 sleep 被信号打断）
  process.on("SIGTERM", async () => {
    if (terminated) return;
    terminated = true;
    onTerminate?.();  // 立即唤醒正在退避的重试循环，使其尽快停（不再 reconnect/跑 act）
    log("worker: SIGTERM received, releasing AgentCore session(s)");
    // 在途窗口兜底（ADR 0028）：SIGTERM 落在 StartBrowserSession 已发 RPC 但 id 未返回的一瞬（startInFlight）时，
    // 待清理集还空但服务端可能已建会话。给一小段时间让 Start 的 await 返回、id 落进 pendingSessions，再 cleanup。
    // 重试循环每 attempt 的 id 一返回即入集（见 connect），故此处只需覆盖「Start 在途未返回」这一瞬。
    if (startInFlight && pendingSessions.size === 0) {
      await new Promise<void>((r) => setTimeout(r, INFLIGHT_SETTLE_MS));
    }
    await cleanup();
    log(`worker: session shutdown complete after SIGTERM${cleanupFailed ? " (WITH FAILURE)" : ""}`);
    process.exit(cleanupFailed ? 1 : 0);
  });

  const reportRefs: Array<{ kind: string; ref: string; label?: string }> = [];
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
    const page = ctx.pages()[0] ?? (await ctx.newPage());
    const agent = new PlaywrightAgent(page, {
      generateReport: true,
      modelConfig: MODEL_CONFIG,
      createOpenAIClient: async () => new OpenAI({ baseURL: BASE_URL, apiKey: "unused", fetch: sigv4Fetch }) as any,
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
        if (!isTransientNetwork(e) || attempt >= CONNECT_ATTEMPTS - 1) {
          if (isTransientNetwork(e)) { networkExhausted = true; log(`worker: 建连重试耗尽（${attempt + 1} 次）：${(e as Error).message}`); }
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

    // sessionId 随 scope_started 即回传（不只等 scope_done）——超时/SIGTERM 中途打断时 scope_done 不会 emit，
    // 但血缘已先随首事件落到 core（ADR 0028 观测缺口修复，对称 Nova）。
    emit({ type: "scope_started", scopeId: scope.id, sessionId });  // 三级时长起点（越过此点不再重试建连）
    // scope 内串行跑 scenarios，共享同一会话（ADR 0019/0024）
    const votesN = job.assertionVotes ?? 1;  // AI 断言投票次数（ADR 0014/0024）；缺省 1
    for (const sc of job.scenarios) {
      emit({ type: "scenario_started", scenarioId: sc.id });
      // scope 内 step 短路在 runScenario 内（上游 error 跳过后续、发 step_skipped，ADR 0031 决定六）。
      const statuses = await runScenario(agent, page, sc.id, sc.steps, votesN);
      emit({ type: "scenario_done", scenarioId: sc.id, status: aggregate(statuses) });
    }

    // 归集原生报告（ADR 0027 reportRefs）：destroy 后 reportFile finalize，Midscene 出 1 个 html/worker（scope 级）
    // kind=report（产物类型；粒度由挂在 scope_done 表达，ADR 0027）；ref 用 file:// URI；agent.reportFile 是绝对路径。
    await agent.destroy().catch(() => {});
    if (agent.reportFile) {
      reportRefs.push({ kind: "report", ref: `file://${agent.reportFile}`, label: "Midscene report" });
    }
  } catch (e) {
    await cleanup();
    // 建连重试耗尽（网络瞬时故障）→ 退网络专用码（ADR 0028）；但 cleanupFailed（会话泄漏）优先级更高。
    if (networkExhausted && !cleanupFailed) {
      log("worker: connect retries exhausted, exiting with network code");
      return EX_WORKER_NETWORK;
    }
    throw e; // 非网络耗尽 → 原样冒泡到 main().catch（记 engine_error）
  } finally {
    await cleanup();
  }

  emit({ type: "scope_done", scopeId: scope.id, sessionId: sessionId ?? null, reportRefs });
  // 正常路径若会话释放失败 → 非 0 退出，让 schedule 记 error、泄漏可观测（审计窗口 C，对照 Nova）
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
): Promise<string[]> {
  const statuses: string[] = [];
  let shortcircuit = false;
  for (const step of steps) {
    if (shortcircuit) {
      emit({ type: "step_skipped", scenarioId, stepIndex: step.index });
      continue;
    }
    const status = await runStep(agent, page, scenarioId, step, votesN);
    statuses.push(status);
    if (status === "error") shortcircuit = true;  // 本 scenario 后续 step 短路
  }
  return statuses;
}

async function runStep(
  agent: PlaywrightAgent, page: import("playwright").Page, scenarioId: string, step: Step, votesN: number,
): Promise<string> {
  const { index, keyword, text } = step;
  emit({ type: "step_started", scenarioId, stepIndex: index });  // step 时长起点
  try {
    // ① 确定性注册表（ADR 0022）：命中走精确 handler、不投票；AssertionError→failed，其它→error
    const hit = matchDeterministic(text);
    if (hit) {
      try {
        await hit.handler({ page }, hit.groups);
      } catch (e) {
        if (e instanceof DeterministicAssertion || (e as Error).name === "AssertionError") {
          emit({
            type: "step_done", scenarioId, stepIndex: index,
            status: "failed", errorType: "assertion_failed",
            message: (e as Error).message || `确定性断言未过：${text}`,
          });
          return "failed";
        }
        throw e; // 其它异常 → 落到下面 catch，记 error
      }
      emit({ type: "step_done", scenarioId, stepIndex: index, status: "passed" });
      return "passed";
    }
    const urlMatch = URL_IN_QUOTES.exec(text);
    if (urlMatch) {
      // ② 内建确定性导航（ADR 0020）：抽 URL 直接 goto，不浪费 AI
      await page.goto(urlMatch[1], { waitUntil: "domcontentloaded", timeout: 60_000 });
      emit({ type: "step_done", scenarioId, stepIndex: index, status: "passed" });
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
      emit(ev);
      return passed ? "passed" : "failed";
    }
    // When / Given（非 URL）→ AI 动作（无 votes）
    const tokBefore = cumulativeTokens(agent);  // 动作前累计 → 增量算本 step 成本
    await agent.aiAct(buildInstruction(step.text, step.argument as any));
    const ev: Record<string, unknown> = { type: "step_done", scenarioId, stepIndex: index, status: "passed" };
    const cost = stepCost(tokBefore, agent);
    if (cost) ev.cost = cost;
    emit(ev);
    return "passed";
  } catch (e) {
    // 诊断分类细化（ADR 0028，对称 Nova）：act 中途网络瞬时故障（CDP 闪断等）标 network_error 比笼统
    // engine_error 更准。**仅分类、不触发重试/恢复**：act 不幂等，schedule job 级重试要求「会话未起（零
    // step_done）」，此处 step_started 早已 emit、saw_step=True，双条件 AND 天然不满足；本失败走 step_done
    // 事件流（非退出码 80），core 侧 is_network=False。"act 中途恢复"仍 defer，这里只把失败原因记准。
    const errorType = isTransientNetwork(e) ? "network_error" : "engine_error";
    emit({
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
export { runStep, runScenario, isTransientNetwork, aggregate };

// 仅作为入口被直接运行时才跑 main（对称 Nova 的 `if __name__ == "__main__"`）——
// 被测试 import 时不触发 main，使 runStep/isTransientNetwork 可注 fake agent 单测。
// tsx 下 import.meta.url 是本模块 URL；process.argv[1] 是入口脚本路径，二者指同一文件即"作入口运行"。
const _entry = process.argv[1] ? pathToFileURL(process.argv[1]).href : "";
if (import.meta.url === _entry) {
  main().then((code) => process.exit(code)).catch((e) => { log(`worker fatal: ${e}`); process.exit(1); });
}
