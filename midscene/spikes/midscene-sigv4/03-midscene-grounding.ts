// 三段式自检 · 第 3 段：合体 —— Midscene(SigV4 自签) + AgentCore 云端浏览器 + 维基用例
// = 模型连接(01) + 浏览器连接/CDP(02) + Midscene grounding，并产出对标基准数据（ADR 0010）。
//
// 用例（与 Nova Act 腿同一个，苹果对苹果）：
//   打开 wikipedia.org → 搜 "OpenAI" → 断言进入 OpenAI 词条页。
// 断言：
//   A 确定性：page.url() 含 /wiki/OpenAI（Playwright，可复现）
//   B AI 断言：agent.aiAssert("当前在 OpenAI 的维基词条页")，跑 N=10 次测抖动
// 度量：动作成功率、A/B 是否一致、B 的 10 次抖动率、各步耗时。
//
// 跑：cd midscene && AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/midscene-sigv4/03-midscene-grounding.ts
import OpenAI from "openai";
import { PlaywrightAgent } from "@midscene/web/playwright";
import { chromium, type Browser } from "playwright";
import {
  BedrockAgentCoreClient,
  StartBrowserSessionCommand,
  StopBrowserSessionCommand,
} from "@aws-sdk/client-bedrock-agentcore";
import { sigv4Fetch, signCdpUpgrade, BASE_URL, MODEL, REGION } from "../../lib/agentcore-sigv4.mjs";

const BROWSER_ID = "aws.browser.v1";
const N_FLAKE = 10; // B(AI 断言) 抖动探测次数

// 关键（源码 agent.js:852-853）：一旦给 Agent 传 createOpenAIClient，它就切到「隔离 ModelConfigManager」，
// 只读 opts.modelConfig，完全无视 overrideAIConfig/全局 env。
// 所以模型配置必须随 opts.modelConfig 一起给（见下方 new PlaywrightAgent）。
const MODEL_CONFIG = {
  MIDSCENE_MODEL_NAME: MODEL,
  MIDSCENE_MODEL_BASE_URL: BASE_URL,
  MIDSCENE_MODEL_API_KEY: "unused", // 占位；真正鉴权由 sigv4Fetch 接管
  MIDSCENE_USE_QWEN3_VL: "true",    // qwen3-vl 的 grounding 适配开关
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

    // === 动作：搜 OpenAI 并进入词条 ===
    let actOk = false;
    const tAct = Date.now();
    try {
      await agent.aiAct('type "OpenAI" into the search input and submit the search');
      await page.waitForLoadState("domcontentloaded", { timeout: 60000 }).catch(() => {});
      actOk = true;
    } catch (e: any) { metrics.actError = e?.message; }
    metrics.actMs = Date.now() - tAct;
    metrics.actOk = actOk;
    metrics.urlAfterAct = page.url();

    // === A：确定性断言（Playwright，可复现）===
    const urlNow = page.url();
    const aPass = /\/wiki\/OpenAI/i.test(urlNow);
    metrics.assertA_deterministic = { pass: aPass, url: urlNow };

    // === B：AI 断言，N 次抖动 ===
    const bResults: boolean[] = [];
    const bMs: number[] = [];
    for (let i = 0; i < N_FLAKE; i++) {
      const t = Date.now();
      try {
        await agent.aiAssert("the page is the Wikipedia article about OpenAI");
        bResults.push(true);
      } catch { bResults.push(false); }
      bMs.push(Date.now() - t);
      process.stdout.write(`  B[${i + 1}/${N_FLAKE}]=${bResults[i] ? "pass" : "FAIL"} `);
    }
    const bPassCount = bResults.filter(Boolean).length;
    metrics.assertB_ai = {
      runs: N_FLAKE, passCount: bPassCount,
      flakeRate: (N_FLAKE - bPassCount) / N_FLAKE,
      consistentWithA: bResults.every((r) => r === aPass),
      avgMs: Math.round(bMs.reduce((a, b) => a + b, 0) / bMs.length),
    };

    console.log("\n\n[03] ===== 对标基准（Midscene 腿）=====");
    console.log(JSON.stringify(metrics, null, 2));
    console.log("\n[03] report.html 见 midscene_run/ 目录");
    console.log(actOk && aPass ? "[03] PASS — 合体全通" : "[03] PARTIAL — 见上方 metrics");
  } finally {
    if (browser) await browser.close().catch(() => {});
    await cp.send(new StopBrowserSessionCommand({ browserIdentifier: BROWSER_ID, sessionId }));
    console.log("[03] session stopped.");
  }
}

main().catch((e) => { console.error("[03] FAIL:", e?.message ?? e); process.exit(1); });
