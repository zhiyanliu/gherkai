// 三段式自检 · 第 3 段：合体 —— Midscene(SigV4 自签) + AgentCore 云端浏览器 + 维基用例
// 即模型连接(01) 加浏览器连接/CDP(02) 加 Midscene grounding，并产出对标基准数据（ADR 0010）。
//
// 用例（与 Nova Act 引擎同一个，苹果对苹果）：
//   打开 wikipedia.org → 执行动作指令 ACTION（在搜索框输入 "OpenAI" 并提交搜索）→ 断言进入 OpenAI 词条页。
//   ACTION 与 ASSERTION 两句与 Nova 侧 engines/novaact/spikes/wikipedia_benchmark.py 逐字相同，改一侧必须同步另一侧。
// 断言：
//   A 确定性：page.url() 含 /wiki/OpenAI（Playwright，可复现）
//   B AI 断言：agent.aiBoolean(ASSERTION)，执行 N=10 次测抖动；与生产 worker 的 AI 断言投票用同一个 API（ADR 0014）。
//     Nova 侧用 act_get(ASSERTION, BOOL_SCHEMA)：两者都是问是非、取布尔值、判否不抛错，调用形式不同、断言句相同
//     （两者的对应关系见 ADR 0010 洞察 ③）。调用本身出错按判否计。
// 度量（两侧共有的度量键名与口径一致；Nova 侧另多两项计费时长，见下）：
//   actOk / actMs：动作是否成功、动作耗时。actMs 只包住 agent.aiAct 调用本身（含 SDK 在调用内部的动作后等待）。
//   loadWaitMs：动作之后等页面到 domcontentloaded 的耗时，单独一列，不并入 actMs。
//   actTokens：动作的 token 用量 {input, output}。
//   assertA_deterministic：A 的结论与当时的 url。
//   assertB_ai：B 的通过次数、抖动率、与 A 是否一致、每次平均耗时 avgMs、每次平均 token 用量 avgTokens。
//   Nova 侧另有计费时长 time_worked_s；本引擎按 token 计费，没有这个量，汇总表里标「不适用」。
// token 用量取自 SDK 公开的 agent.metrics（MidsceneUsageMetrics，自 agent 建起的累计快照）：输入取
// totalPromptTokens、输出取 totalCompletionTokens，每次调用前后各读一次，差值就是该次调用的用量
// （与 worker 按 step 取 token 的算法一致，见 src/worker/run-scope.mts 的 cumulativeTokens）。
// 两项都来自模型服务响应里的 usage；响应不带 usage 时 SDK 按 0 累计，此时汇总表里的 0 表示缺数据、不表示零用量。
// 输出：先打印 metrics 的 JSON，再打印一张汇总表；表的行名两侧一致，可以直接并排填进 ADR 0010 的对标表。
//
// 运行：cd engines/midscene && AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/03-midscene-grounding.ts
import OpenAI from "openai";
import { PlaywrightAgent } from "@midscene/web/playwright";
import { chromium, type Browser } from "playwright";
import {
  BedrockAgentCoreClient,
  StartBrowserSessionCommand,
  StopBrowserSessionCommand,
} from "@aws-sdk/client-bedrock-agentcore";
import { sigv4Fetch, signCdpUpgrade, getBaseUrl, MODEL, modelFamily, getRegion } from "../src/lib/agentcore-sigv4.mjs";
// region 改惰性 getter（ADR 0033/0016 决策 C）；spike 直接运行时带 AWS_REGION=... 前缀，顶层求值 OK。
const REGION = getRegion(), BASE_URL = getBaseUrl();

const BROWSER_ID = "aws.browser.v1";
const N_FLAKE = 10; // B(AI 断言) 抖动探测次数
// 动作指令与断言句：与 Nova 侧 wikipedia_benchmark.py 的 ACTION / ASSERTION 逐字相同（ADR 0010「同一用例」）。
const ACTION = 'type "OpenAI" into the search input and submit the search';
const ASSERTION = "the page is the Wikipedia article about OpenAI";
const LOAD_WAIT_TIMEOUT_MS = 60000;

type TokenUsage = { input: number; output: number };

// agent.metrics 的累计 token 快照（只读、可重复读，读一次不改变任何状态）。
function tokenTotals(agent: PlaywrightAgent): TokenUsage {
  const m = agent.metrics;
  return { input: m.totalPromptTokens, output: m.totalCompletionTokens };
}

function tokenDelta(before: TokenUsage, after: TokenUsage): TokenUsage {
  return { input: after.input - before.input, output: after.output - before.output };
}

function mean(xs: number[]): number {
  return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0;
}

// 关键（源码 agent.js:852-853）：一旦给 Agent 传 createOpenAIClient，它就切到「隔离 ModelConfigManager」，
// 只读 opts.modelConfig，完全无视 overrideAIConfig/全局 env。
// 所以模型配置必须随 opts.modelConfig 一起给（见下方 new PlaywrightAgent）。
const MODEL_CONFIG = {
  MIDSCENE_MODEL_NAME: MODEL,
  MIDSCENE_MODEL_BASE_URL: BASE_URL,
  MIDSCENE_MODEL_API_KEY: "unused", // 占位；真正鉴权由 sigv4Fetch 接管
  MIDSCENE_MODEL_FAMILY: modelFamily(),  // 模型家族：按模型 id 推断，与 worker 同一张表（ADR 0044 决策 2）
};

async function main() {
  const metrics: Record<string, unknown> = { region: REGION, model: MODEL, case: "wikipedia/OpenAI" };
  const cp = new BedrockAgentCoreClient({ region: REGION });
  console.log("[03] StartBrowserSession ...");
  const started = await cp.send(new StartBrowserSessionCommand({ browserIdentifier: BROWSER_ID, name: "spike-grounding" }));
  const sessionId = started.sessionId!;
  const wsUrl = started.streams?.automationStream?.streamEndpoint!;
  let browser: Browser | undefined;

  try {
    const headers = await signCdpUpgrade(wsUrl);
    browser = await chromium.connectOverCDP(wsUrl, { headers });
    const ctx = browser.contexts()[0] ?? (await browser.newContext());
    const page = ctx.pages()[0] ?? (await ctx.newPage());
    await page.goto("https://www.wikipedia.org/", { waitUntil: "domcontentloaded", timeout: 60000 });

    // Midscene agent：注入 SigV4 client + 出报告
    const agent = new PlaywrightAgent(page, {
      generateReport: true,
      modelConfig: MODEL_CONFIG, // 隔离模式下唯一被读的模型配置
      createOpenAIClient: async (_openai: any) => new OpenAI({ baseURL: BASE_URL, apiKey: "unused", fetch: sigv4Fetch }),
    });

    // === 动作：执行 ACTION。计时只包住 aiAct 本身，token 快照在计时窗口之外读 ===
    let actOk = false;
    const tokBeforeAct = tokenTotals(agent);
    const tAct = Date.now();
    try {
      await agent.aiAct(ACTION);
      actOk = true;
    } catch (e: any) { metrics.actError = e?.message; }
    const actMs = Date.now() - tAct;
    const actTokens = tokenDelta(tokBeforeAct, tokenTotals(agent));
    metrics.actOk = actOk;
    metrics.actMs = actMs;
    metrics.actTokens = actTokens;

    // === 页面加载等待：单独计时，不并入 actMs ===
    const tLoad = Date.now();
    await page.waitForLoadState("domcontentloaded", { timeout: LOAD_WAIT_TIMEOUT_MS }).catch(() => {});
    const loadWaitMs = Date.now() - tLoad;
    metrics.loadWaitMs = loadWaitMs;
    metrics.urlAfterAct = page.url();

    // === A：确定性断言（Playwright，可复现）===
    const urlNow = page.url();
    const aPass = /\/wiki\/OpenAI/i.test(urlNow);
    metrics.assertA_deterministic = { pass: aPass, url: urlNow };

    // === B：AI 断言，N 次抖动 ===
    const bResults: boolean[] = [];
    const bMs: number[] = [];
    const bTokens: TokenUsage[] = [];
    for (let i = 0; i < N_FLAKE; i++) {
      const tok0 = tokenTotals(agent);
      const t = Date.now();
      let vote = false;
      try {
        vote = await agent.aiBoolean(ASSERTION);
      } catch { /* 调用出错按判否计 */ }
      bResults.push(vote);
      bMs.push(Date.now() - t);
      bTokens.push(tokenDelta(tok0, tokenTotals(agent)));
      process.stdout.write(`  B[${i + 1}/${N_FLAKE}]=${bResults[i] ? "pass" : "FAIL"} `);
    }
    const bPassCount = bResults.filter(Boolean).length;
    const flakeRate = (N_FLAKE - bPassCount) / N_FLAKE;
    const consistentWithA = bResults.every((r) => r === aPass);
    const bAvgMs = Math.round(mean(bMs));
    const bAvgTokens: TokenUsage = {
      input: Math.round(mean(bTokens.map((u) => u.input))),
      output: Math.round(mean(bTokens.map((u) => u.output))),
    };
    metrics.assertB_ai = {
      runs: N_FLAKE, passCount: bPassCount, flakeRate, consistentWithA,
      avgMs: bAvgMs, avgTokens: bAvgTokens,
    };

    console.log("\n\n[03] ===== 对标基准（Midscene 引擎）=====");
    console.log(JSON.stringify(metrics, null, 2));

    // 汇总表：行名与 Nova 侧 wikipedia_benchmark.py 的汇总表逐行一致
    const NOT_APPLICABLE = "不适用（本引擎按 token 计费）";
    const rows: [string, string][] = [
      ["动作成功", actOk ? "是" : "否"],
      ["动作耗时（只计引擎 act 调用）", `${actMs} ms`],
      ["页面加载等待（动作之后，单独计时）", `${loadWaitMs} ms`],
      ["动作 token（输入 / 输出）", `${actTokens.input} / ${actTokens.output}`],
      ["动作计费时长 time_worked_s", NOT_APPLICABLE],
      ["A 确定性断言（url 含 /wiki/OpenAI）", aPass ? "pass" : "FAIL"],
      [`B AI 断言 ×${N_FLAKE}`, `${bPassCount}/${N_FLAKE}，抖动 ${Math.round(flakeRate * 100)}%`],
      ["A/B 一致", consistentWithA ? "是" : "否"],
      ["B 平均耗时/次", `${bAvgMs} ms`],
      ["B 平均 token/次（输入 / 输出）", `${bAvgTokens.input} / ${bAvgTokens.output}`],
      ["B 平均计费时长/次 time_worked_s", NOT_APPLICABLE],
    ];
    console.log(`\n[03] ===== 汇总表（Midscene ${MODEL}）=====`);
    console.log("| 度量 | Midscene |\n|---|---|");
    for (const [k, v] of rows) console.log(`| ${k} | ${v} |`);

    console.log("\n[03] report.html 见 midscene_run/ 目录");
    console.log(actOk && aPass ? "[03] PASS — 合体全通" : "[03] PARTIAL — 见上方 metrics");
  } finally {
    if (browser) await browser.close().catch(() => {});
    await cp.send(new StopBrowserSessionCommand({ browserIdentifier: BROWSER_ID, sessionId }));
    console.log("[03] session stopped.");
  }
}

main().catch((e) => { console.error("[03] FAIL:", e?.message ?? e); process.exit(1); });
