// Midscene 薄 worker（ADR 0022/0024）：读 stdin 的 job JSON → 跑一个 scope → 吐 0024 事件到事件通道。
//
// 从 bdd/steps/generic.steps.ts 改造而来：脱掉 cucumber 装饰器，逻辑（开会话/aiAct/aiBoolean 投票/派发）原样复用。
// core 经子进程 adapter 起本 worker（ADR 0026 机制层），讲 0024 协议——与 Nova Act 腿对称。
//
// 三通道分离（ADR 0024）：0024 事件吐到 EVENTS_FD 指定的 fd（无则回落 stdout，便于手动直跑调试）；
// Midscene/SDK 的 stdout 噪声留 stdout；worker 自身诊断走 stderr。
//
// cost（ADR 0024）：从 agent._unstableLogContent() 的 executions[].tasks[].usage.total_tokens 取原生
// token 数，worker 只报 {tokens}；core 合计、美元折算交消费者（不追 Qwen 单价）。两腿对称：都只报原生量。
//
// 跑（一般由 core adapter spawn；也可手动）：
//   echo '<job json>' | AWS_REGION=us-east-1 node --import tsx/esm worker/run-scope.ts
import OpenAI from "openai";
import { PlaywrightAgent } from "@midscene/web/playwright";
import { chromium, type Browser } from "playwright";
import {
  BedrockAgentCoreClient,
  StartBrowserSessionCommand,
  StopBrowserSessionCommand,
} from "@aws-sdk/client-bedrock-agentcore";
import * as fs from "node:fs";
import { sigv4Fetch, signCdpUpgrade, BASE_URL, MODEL, REGION } from "../lib/agentcore-sigv4.mjs";

const BROWSER_ID = "aws.browser.v1";
const VOTES = 3; // AI 断言投票次数（治种类A抖动，ADR 0014）
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
interface Job { scope: { id: string; name: string }; engine: string; scenarios: Scenario[] }

function unquote(text: string): string {
  const t = text.trim();
  return t.length >= 2 && t.startsWith('"') && t.endsWith('"') ? t.slice(1, -1) : t;
}

// 报 Midscene/Bedrock 原生量 token（ADR 0024：engine 只报原生量，core 不算美元）。
// 从 agent._unstableLogContent 取最近一次 AI 调用的 usage.total_tokens；取不到则返回 undefined。
function lastCost(agent: PlaywrightAgent): Record<string, unknown> | undefined {
  try {
    const content = (agent as any)._unstableLogContent?.();
    const execs = content?.executions ?? [];
    let usage: any = undefined;
    for (const ex of execs) for (const task of ex.tasks ?? []) if (task.usage) usage = task.usage;
    if (!usage || usage.total_tokens == null) return undefined;
    return { tokens: usage.total_tokens };
  } catch {
    return undefined;
  }
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
  let sessionId: string | undefined;
  let browser: Browser | undefined;
  let cleanedUp = false;
  let cleanupFailed = false; // StopBrowserSession 失败 → worker 非 0 退出，让泄漏可观测（对照 Nova）

  // 会话清理（ADR 0024 终止契约，对照 Nova 的 with __exit__）：
  //   顺序——**先发 StopBrowserSession 释放会话（最重要、优先）**，再关 browser；
  //   不让易挂起的 browser.close 挟持会话释放（审计窗口 5）。close 套超时预算，避免耗尽 grace。
  //   幂等：cleanedUp 守卫，防 SIGTERM handler 与 finally 双调。
  //   StopBrowserSession 失败不静默吞：记日志 + 置 cleanupFailed → 非 0 退出（审计窗口 C）。
  async function cleanup(): Promise<void> {
    if (cleanedUp) return;
    cleanedUp = true;
    const sid = sessionId;
    if (sid) {
      try {
        await cp.send(new StopBrowserSessionCommand({ browserIdentifier: BROWSER_ID, sessionId: sid }));
      } catch (e) {
        cleanupFailed = true;
        log(`worker: StopBrowserSession FAILED (会话可能泄漏，需排查): ${(e as Error).message}`);
      }
    }
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
  process.on("SIGTERM", async () => {
    if (terminated) return;
    terminated = true;
    log("worker: SIGTERM received, releasing AgentCore session");
    // 窗口(1) 兜底：若 SIGTERM 在 StartBrowserSession 返回前到达，sessionId 还没赋值，
    // 但服务端可能已建会话。给一小段时间让 Start 的 await 返回、sessionId 落地，再 cleanup。
    if (!sessionId) {
      await new Promise<void>((r) => setTimeout(r, 1500));
    }
    await cleanup();
    log(`worker: session shutdown complete after SIGTERM${cleanupFailed ? " (WITH FAILURE)" : ""}`);
    process.exit(cleanupFailed ? 1 : 0);
  });

  const reportRefs: Array<{ granularity: string; path: string }> = [];

  try {
    const started = await cp.send(new StartBrowserSessionCommand({ browserIdentifier: BROWSER_ID, name: "worker" }));
    sessionId = started.sessionId!;
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

    emit({ type: "scope_started", scopeId: scope.id });  // 三级时长起点
    // scope 内串行跑 scenarios，共享同一会话（ADR 0019/0024）
    for (const sc of job.scenarios) {
      emit({ type: "scenario_started", scenarioId: sc.id });
      const statuses: string[] = [];
      for (const step of sc.steps) {
        statuses.push(await runStep(agent, page, sc.id, step));
      }
      emit({ type: "scenario_done", scenarioId: sc.id, status: aggregate(statuses) });
    }

    // 归集原生报告（ADR 0024 reportRefs）：destroy 后 reportFile finalize，Midscene 出 1 个 html/worker（scope 级）
    await agent.destroy().catch(() => {});
    if (agent.reportFile) reportRefs.push({ granularity: "scope", path: agent.reportFile });
  } finally {
    await cleanup();
  }

  emit({ type: "scope_done", scopeId: scope.id, sessionId: sessionId ?? null, reportRefs });
  // 正常路径若会话释放失败 → 非 0 退出，让 schedule 记 error、泄漏可观测（审计窗口 C，对照 Nova）
  return cleanupFailed ? 1 : 0;
}

async function runStep(
  agent: PlaywrightAgent, page: import("playwright").Page, scenarioId: string, step: Step,
): Promise<string> {
  const { index, keyword, text } = step;
  emit({ type: "step_started", scenarioId, stepIndex: index });  // step 时长起点
  try {
    const urlMatch = URL_IN_QUOTES.exec(text);
    if (urlMatch) {
      // 内建确定性导航（ADR 0020）：抽 URL 直接 goto，不浪费 AI
      await page.goto(urlMatch[1], { waitUntil: "domcontentloaded", timeout: 60_000 });
      emit({ type: "step_done", scenarioId, stepIndex: index, status: "passed" });
      return "passed";
    }
    if (keyword === "Then") {
      // AI 断言 + N 次投票（ADR 0014/0024）
      let yes = 0;
      for (let i = 0; i < VOTES; i++) if (await agent.aiBoolean(unquote(text))) yes++;
      const passed = yes > VOTES / 2;
      const ev: Record<string, unknown> = {
        type: "step_done", scenarioId, stepIndex: index,
        status: passed ? "passed" : "failed",
        votes: { yes, total: VOTES },
      };
      const cost = lastCost(agent);
      if (cost) ev.cost = cost;
      if (!passed) { ev.errorType = "assertion_failed"; ev.message = `AI 断言未过多数票（${yes}/${VOTES}）：${text}`; }
      emit(ev);
      return passed ? "passed" : "failed";
    }
    // When / Given（非 URL）→ AI 动作（无 votes）
    await agent.aiAct(unquote(text));
    const ev: Record<string, unknown> = { type: "step_done", scenarioId, stepIndex: index, status: "passed" };
    const cost = lastCost(agent);
    if (cost) ev.cost = cost;
    emit(ev);
    return "passed";
  } catch (e) {
    emit({
      type: "step_done", scenarioId, stepIndex: index,
      status: "error", errorType: "engine_error", message: `${(e as Error).name}: ${(e as Error).message}`,
    });
    return "error";
  }
}

function aggregate(statuses: string[]): string {
  if (statuses.includes("error")) return "error";
  if (statuses.includes("failed")) return "failed";
  return "passed";
}

main().then((code) => process.exit(code)).catch((e) => { log(`worker fatal: ${e}`); process.exit(1); });
