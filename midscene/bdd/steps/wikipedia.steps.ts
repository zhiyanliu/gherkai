// Midscene 侧 step definitions（cucumber-js + TS）。
// 加载根级共享 features/wikipedia_search.feature（ADR 0005）。
// 接线复用 spike 第 3 段验证过的：SigV4 自签模型连接 + AgentCore 浏览器连接（CDP）。
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
// 共享 SigV4 模块（模型连接 + 浏览器连接/CDP），与 spike 同源，消除重复（.mjs 指向 .mts，ESM 解析）
import { sigv4Fetch, signCdpUpgrade, BASE_URL, MODEL, REGION } from "../../lib/agentcore-sigv4.mjs";

setDefaultTimeout(180_000); // act + 断言较慢

const BROWSER_ID = "aws.browser.v1";
const MODEL_CONFIG = {
  MIDSCENE_MODEL_NAME: MODEL,
  MIDSCENE_MODEL_BASE_URL: BASE_URL,
  MIDSCENE_MODEL_API_KEY: "unused",
  MIDSCENE_USE_QWEN3_VL: "true",
};

// 每个 scenario 一套云端会话 + agent（挂在 cucumber World 上）
interface MidsceneWorld extends World {
  cp?: BedrockAgentCoreClient;
  sessionId?: string;
  browser?: Browser;
  agent?: PlaywrightAgent;
  page?: import("playwright").Page;
}

Before(async function (this: MidsceneWorld) {
  this.cp = new BedrockAgentCoreClient({ region: REGION });
  const started = await this.cp.send(new StartBrowserSessionCommand({ browserIdentifier: BROWSER_ID, name: "bdd-midscene" }));
  this.sessionId = started.sessionId!;
  const wsUrl = started.streams?.automationStream?.streamEndpoint!;
  const headers = await signCdpUpgrade(wsUrl);
  this.browser = await chromium.connectOverCDP(wsUrl, { headers });
  const ctx = this.browser.contexts()[0] ?? (await this.browser.newContext());
  const page = ctx.pages()[0] ?? (await ctx.newPage());
  this.page = page; // 存原始 Playwright Page 供确定性断言/导航用
  this.agent = new PlaywrightAgent(page, {
    generateReport: true,
    modelConfig: MODEL_CONFIG,
    createOpenAIClient: async () => new OpenAI({ baseURL: BASE_URL, apiKey: "unused", fetch: sigv4Fetch }),
  });
});

After(async function (this: MidsceneWorld) {
  if (this.browser) await this.browser.close().catch(() => {});
  if (this.cp && this.sessionId) await this.cp.send(new StopBrowserSessionCommand({ browserIdentifier: BROWSER_ID, sessionId: this.sessionId })).catch(() => {});
});

Given("the Wikipedia home page is open", async function (this: MidsceneWorld) {
  await this.page!.goto("https://www.wikipedia.org/", { waitUntil: "domcontentloaded", timeout: 60_000 });
});

When("I search for {string} and open its article", async function (this: MidsceneWorld, term: string) {
  await this.agent!.aiAct(`type "${term}" into the search input and submit the search`);
});

Then("the page is the Wikipedia article about {string}", async function (this: MidsceneWorld, term: string) {
  // A 确定性断言（Playwright）+ B AI 断言，双重，与 spike 对齐
  assert.match(this.page!.url(), new RegExp(`/wiki/${term}`, "i"), `url should contain /wiki/${term}, got ${this.page!.url()}`);
  await this.agent!.aiAssert(`the page is the Wikipedia article about ${term}`);
});
