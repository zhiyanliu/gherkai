// 通用 step definitions（v0.x 验证核心假设："QA 只写 .feature、零 step 代码"）。
// 这组 step 一次写好、任何用例复用；QA 不碰这里，只写 .feature。
// 句式：Given 打开 / When AI 执行 / Then AI 确认（AI 布尔断言+投票）/ And 页面地址包含（确定性锚点）。
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

When("AI 执行 {string}", async function (this: W, instruction: string) {
  await this.agent!.aiAct(instruction);
});

// AI 布尔断言 + N 次投票取多数（ADR 0014 对称布尔路径；治种类A抖动）
Then("AI 确认 {string}", async function (this: W, claim: string) {
  const votes: boolean[] = [];
  for (let i = 0; i < VOTES; i++) {
    votes.push(await this.agent!.aiBoolean(claim));
  }
  const yes = votes.filter(Boolean).length;
  assert.ok(yes > VOTES / 2, `AI 断言未过多数票（${yes}/${VOTES}）：${claim}`);
});

// 确定性断言锚点（ADR 0015；不靠 AI，给精确检查留入口）
Then("页面地址包含 {string}", async function (this: W, fragment: string) {
  assert.ok(this.page!.url().includes(fragment), `url 应含 "${fragment}"，实际 ${this.page!.url()}`);
});

// === 第一批打磨新增：断言类能力 ===

// ⑤ 否定/不存在断言：复用 aiBoolean 问"没有 X"。验证 AI 问否定句是否靠谱。
Then("确认页面没有 {string} 的提示", async function (this: W, text: string) {
  const votes: boolean[] = [];
  for (let i = 0; i < VOTES; i++) {
    // 问肯定句"是否存在"，再取反——比直接问否定句更稳（待实测验证该假设）
    votes.push(await this.agent!.aiBoolean(`页面上存在"${text}"这样的提示或文字`));
  }
  const present = votes.filter(Boolean).length;
  assert.ok(present <= VOTES / 2, `不该出现"${text}"，但多数票认为存在（${present}/${VOTES}）`);
});

// ① 提取数字再比较：用 aiNumber 取数，确定性比较。现有 aiBoolean 干不了。
Then("页面上展示的语言版本数量应该大于 {string}", async function (this: W, n: string) {
  const count = await this.agent!.aiNumber("页面上展示了多少种语言版本？返回数字");
  assert.ok(count > Number(n), `语言版本数应 > ${n}，实际 ${count}`);
});

// ① 提取字符串断言：用 aiString 取内容，确定性判断包含。
Then("词条首段应该提到 {string}", async function (this: W, kw: string) {
  const para = await this.agent!.aiString("返回词条第一段的文字内容");
  assert.ok(para.toLowerCase().includes(kw.toLowerCase()), `首段应含"${kw}"，实际："${para.slice(0, 120)}…"`);
});
