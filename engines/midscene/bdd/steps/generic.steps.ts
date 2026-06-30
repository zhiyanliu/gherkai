// 通用 step definitions（v0.x 验证核心假设："QA 只写 .feature、零 step 代码"）。
// 这组 step 一次写好、任何用例复用；QA 不碰这里，只写 .feature。
// 句式（ADR 0020）：Given 打开 "url" / When "{自然语言}"（aiAct）/ Then "{自然语言}"（默认 AI 布尔断言+投票）。
// 确定性锚点见 deterministic.steps.ts 脚手架（按需自建，不预置）。Midscene 侧 When/Then 同 pattern 靠本地 cucumber 补丁区分（ADR 0021）。
import { Before, After, Given, When, Then, setDefaultTimeout, World } from "@cucumber/cucumber";
import assert from "node:assert";
import OpenAI from "openai";
import { PlaywrightAgent } from "@midscene/web/playwright";
import { chromium, type Browser } from "playwright";
import {
  BedrockAgentCoreClient,
  StartBrowserSessionCommand,
  StopBrowserSessionCommand,
} from "@aws-sdk/client-bedrock-agentcore";
import { sigv4Fetch, signCdpUpgrade, BASE_URL, MODEL, REGION } from "../../lib/agentcore-sigv4.mjs";

setDefaultTimeout(180_000);

const BROWSER_ID = "aws.browser.v1";
const VOTES = 3; // AI 断言投票次数（治种类A抖动，ADR 0014）；取多数
const MODEL_CONFIG = {
  MIDSCENE_MODEL_NAME: MODEL,
  MIDSCENE_MODEL_BASE_URL: BASE_URL,
  MIDSCENE_MODEL_API_KEY: "unused",
  MIDSCENE_USE_QWEN3_VL: "true",
};

interface W extends World {
  cp?: BedrockAgentCoreClient;
  sessionId?: string;
  browser?: Browser;
  agent?: PlaywrightAgent;
  page?: import("playwright").Page;
}

Before(async function (this: W) {
  this.cp = new BedrockAgentCoreClient({ region: REGION });
  const started = await this.cp.send(new StartBrowserSessionCommand({ browserIdentifier: BROWSER_ID, name: "v0x-generic" }));
  this.sessionId = started.sessionId!;
  const wsUrl = started.streams?.automationStream?.streamEndpoint!;
  const headers = await signCdpUpgrade(wsUrl);
  this.browser = await chromium.connectOverCDP(wsUrl, { headers });
  const ctx = this.browser.contexts()[0] ?? (await this.browser.newContext());
  this.page = ctx.pages()[0] ?? (await ctx.newPage());
  this.agent = new PlaywrightAgent(this.page, {
    generateReport: true,
    modelConfig: MODEL_CONFIG,
    createOpenAIClient: async () => new OpenAI({ baseURL: BASE_URL, apiKey: "unused", fetch: sigv4Fetch }),
  });
});

After(async function (this: W) {
  if (this.browser) await this.browser.close().catch(() => {});
  if (this.cp && this.sessionId) await this.cp.send(new StopBrowserSessionCommand({ browserIdentifier: BROWSER_ID, sessionId: this.sessionId })).catch(() => {});
});

// === 通用 step（任何用例复用，QA 不写代码）===

Given("打开 {string}", async function (this: W, url: string) {
  await this.page!.goto(url, { waitUntil: "domcontentloaded", timeout: 60_000 });
});

// 默认 AI 动作（ADR 0020）：无关键词的 When "{自然语言}" → aiAct。QA 写自然语言，不需路由关键词。
When("{string}", async function (this: W, instruction: string) {
  await this.agent!.aiAct(instruction);
});

// 默认 AI 判断（ADR 0020）：无关键词的 Then "{自然语言}" → AI 布尔判断 + N 次投票取多数
// （ADR 0014 对称布尔路径；治种类A抖动）。QA 写自然语言——含**否定**陈述（如"页面没有出现服务器错误"），
// AI 能直接判否定，无需专门的否定 step。
Then("{string}", async function (this: W, claim: string) {
  const votes: boolean[] = [];
  for (let i = 0; i < VOTES; i++) {
    votes.push(await this.agent!.aiBoolean(claim));
  }
  const yes = votes.filter(Boolean).length;
  assert.ok(yes > VOTES / 2, `AI 断言未过多数票（${yes}/${VOTES}）：${claim}`);
});

// 注：① 确定性锚点（不走 AI 的精确 URL/DOM 查）见 deterministic.steps.ts 脚手架（ADR 0020，按需自建）。
//     ② 不设「否定断言」「取数/取文本」「AI 确认/AI 执行」等带关键词的专用 step——
//        一律走无关键词的 When/Then "{自然语言}"（ADR 0020：QA 零预设、默认走 AI）。
// 若将来确需精确数值核对，走确定性锚点（ADR 0015），而非新增 AI 取数原语。
