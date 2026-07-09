// A · 负向用例（expect-failure 探针）：验证"该红能红"——Midscene 引擎。
// 断言信任的命门：一个"永远绿"的测试框架比没有还危险。这里故意造必假断言，
// 验证 aiBoolean/aiNumber/aiString 在"不符"时确实给出 false / 不匹配的值（→ 上层会判失败）。
// 一次性证伪探针，验完即可丢。
// 跑：cd midscene && AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/midscene-sigv4/05-negative-assertions.ts
import OpenAI from "openai";
import { PlaywrightAgent } from "@midscene/web/playwright";
import { chromium } from "playwright";
import {
  BedrockAgentCoreClient,
  StartBrowserSessionCommand,
  StopBrowserSessionCommand,
} from "@aws-sdk/client-bedrock-agentcore";
import { sigv4Fetch, signCdpUpgrade, getBaseUrl, MODEL, getRegion } from "../lib/agentcore-sigv4.mjs";
// region 改惰性 getter（ADR 0033/0016 决策 C）；spike 直跑带 AWS_REGION=... 前缀，顶层求值 OK。
const REGION = getRegion(), BASE_URL = getBaseUrl();

const BROWSER_ID = "aws.browser.v1";
const MODEL_CONFIG = {
  MIDSCENE_MODEL_NAME: MODEL,
  MIDSCENE_MODEL_BASE_URL: BASE_URL,
  MIDSCENE_MODEL_API_KEY: "unused",
  MIDSCENE_USE_QWEN3_VL: "true",
};

type Check = { name: string; expectRed: boolean; gotRed: boolean; detail: string };

async function main() {
  const cp = new BedrockAgentCoreClient({ region: REGION });
  const started = await cp.send(new StartBrowserSessionCommand({ browserIdentifier: BROWSER_ID, name: "neg-assert" }));
  const sessionId = started.sessionId!;
  const wsUrl = started.streams?.automationStream?.streamEndpoint!;
  const checks: Check[] = [];
  try {
    const headers = await signCdpUpgrade(wsUrl);
    const browser = await chromium.connectOverCDP(wsUrl, { headers });
    const ctx = browser.contexts()[0] ?? (await browser.newContext());
    const page = ctx.pages()[0] ?? (await ctx.newPage());
    const agent = new PlaywrightAgent(page, {
      generateReport: false,
      modelConfig: MODEL_CONFIG,
      createOpenAIClient: async () => new OpenAI({ baseURL: BASE_URL, apiKey: "unused", fetch: sigv4Fetch }),
    });

    // 进入一个已知页面：OpenAI 维基词条
    await page.goto("https://en.wikipedia.org/wiki/OpenAI", { waitUntil: "domcontentloaded", timeout: 60_000 });

    // (a) AI 布尔断言——必假：这页不是关于 Python 的
    {
      const v = await agent.aiBoolean("当前页面是关于 Python 编程语言的维基词条");
      checks.push({ name: "aiBoolean 必假(说成Python)", expectRed: true, gotRed: v === false, detail: `aiBoolean=${v}（期望 false）` });
    }
    // (b) 提取数比较——必假：语言版本数不可能 > 9999
    {
      const count = await agent.aiNumber("页面顶部展示了多少种语言版本？返回数字");
      checks.push({ name: "aiNumber 必假(>9999)", expectRed: true, gotRed: !(count > 9999), detail: `count=${count}，>9999=${count > 9999}（期望 false）` });
    }
    // (c) 提取串断言——必假：首段不会提到一个杜撰词
    {
      const para = await agent.aiString("返回词条第一段的文字内容");
      const has = para.toLowerCase().includes("zzqx-not-a-real-word");
      checks.push({ name: "aiString 必假(含杜撰词)", expectRed: true, gotRed: !has, detail: `包含杜撰词=${has}（期望 false）` });
    }
    // (d) 对照正向——必真：确认确实是 OpenAI 页（防"全假"——证明它不是无脑返回 false）
    {
      const v = await agent.aiBoolean("当前页面是关于 OpenAI 的维基词条");
      checks.push({ name: "aiBoolean 必真(对照)", expectRed: false, gotRed: v === false, detail: `aiBoolean=${v}（期望 true）` });
    }

    await browser.close().catch(() => {});
  } finally {
    await cp.send(new StopBrowserSessionCommand({ browserIdentifier: BROWSER_ID, sessionId })).catch(() => {});
  }

  console.log("\n[05] ===== 负向断言验证（Midscene）=====");
  let allGood = true;
  for (const c of checks) {
    const ok = c.gotRed === c.expectRed; // 期望红就该红、期望绿就该绿
    allGood = allGood && ok;
    console.log(`  ${ok ? "✅" : "❌"} ${c.name}: ${c.detail}  ${ok ? "" : "←判定与预期不符!"}`);
  }
  console.log(allGood
    ? "\n[05] PASS — 该红的都红、对照绿正常：AI 断言判定可信（此组用例上）"
    : "\n[05] FAIL — 有断言判定与预期不符，AI 断言可信度存疑");
  process.exit(allGood ? 0 : 1);
}

main().catch((e) => { console.error("[05] ERROR:", e?.message ?? e); process.exit(2); });
