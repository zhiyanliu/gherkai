// 三段式自检 · 第 2 段：独立验「浏览器连接（CDP）」
// 目标：TS 侧拿到 AgentCore 云端浏览器并用 Playwright 连上、导航维基、取标题、收尾停会话。
//   流程：StartBrowserSession → 拿 automationStream.streamEndpoint(ws) → SigV4 签 CDP upgrade 头
//        → Playwright connectOverCDP(ws, { headers }) → newPage → goto wikipedia → title → StopBrowserSession
// 跑：cd midscene && AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/midscene-sigv4/02-agentcore-cdp.ts
import { chromium } from "playwright";
import {
  BedrockAgentCoreClient,
  StartBrowserSessionCommand,
  StopBrowserSessionCommand,
} from "@aws-sdk/client-bedrock-agentcore";
import { signCdpUpgrade, REGION } from "../../lib/agentcore-sigv4.mjs";

const BROWSER_ID = "aws.browser.v1"; // 系统默认 browser（ADR 0011）

async function main() {
  console.log(`[02] region=${REGION} browser=${BROWSER_ID}`);
  const cp = new BedrockAgentCoreClient({ region: REGION });

  console.log("[02] StartBrowserSession ...");
  const started = await cp.send(
    new StartBrowserSessionCommand({ browserIdentifier: BROWSER_ID, name: "spike-cdp" }),
  );
  const sessionId = started.sessionId!;
  const wsUrl = started.streams?.automationStream?.streamEndpoint!;
  console.log("[02] sessionId=", sessionId);
  console.log("[02] ws=", wsUrl);

  try {
    if (!wsUrl) throw new Error("no automationStream.streamEndpoint in response");

    console.log("[02] sign CDP upgrade (SigV4, service=bedrock-agentcore) ...");
    const headers = await signCdpUpgrade(wsUrl);
    console.log("[02] signed header keys:", Object.keys(headers).join(", "));

    console.log("[02] playwright connectOverCDP ...");
    const browser = await chromium.connectOverCDP(wsUrl, { headers });
    const ctx = browser.contexts()[0] ?? (await browser.newContext());
    const page = ctx.pages()[0] ?? (await ctx.newPage());

    console.log("[02] goto wikipedia ...");
    await page.goto("https://www.wikipedia.org/", { waitUntil: "domcontentloaded", timeout: 60000 });
    const title = await page.title();
    console.log("[02] page title=", JSON.stringify(title));

    await browser.close();
    console.log("\n[02] PASS — 浏览器连接（CDP）：StartBrowserSession + SigV4 upgrade + connectOverCDP + 导航 全通");
  } finally {
    console.log("[02] StopBrowserSession (cleanup) ...");
    await cp.send(new StopBrowserSessionCommand({ browserIdentifier: BROWSER_ID, sessionId }));
    console.log("[02] session stopped.");
  }
}

main().catch((e) => {
  console.error("[02] FAIL:", e?.name ?? "", e?.message ?? e);
  process.exit(1);
});
