// 移动设备方向的 spike A：Device Farm 远程访问会话 + 托管 Appium 端点 + Midscene 自定义界面适配器（AbstractInterface），
// 在一台 Android 真机的 Chrome 上执行设备网页。测量四样：会话建立与停止耗时、WebDriver 命令往返、
// AI 步耗时与 token、evidence 原料（dump.executions 与截图落盘）是否照旧。
//
// 运行（跳板机，实例角色即凭证；Bedrock 走 AWS_REGION，Device Farm 固定 us-west-2）：
//   cd engines/midscene && AWS_REGION=us-east-1 MIDSCENE_RUN_DIR=/tmp/spike06 node --import tsx spikes/06-devicefarm-appium.mts
// 可选 env：DF_PROJECT_ARN（缺省按名 gherkai-spike 查）、DF_DEVICE_ARN（缺省 Redmi Note 13 / Android 15）、
//   SPIKE_SKIP_AI=1（只量会话与命令往返，不调模型）。
// 结果落 $MIDSCENE_RUN_DIR/spike06-results.json；无论成败最后都停会话（设备按分钟计费）。
import * as fs from "node:fs";
import * as path from "node:path";
import OpenAI from "openai";
import { remote } from "webdriverio";
import {
  DeviceFarmClient,
  ListProjectsCommand,
  CreateRemoteAccessSessionCommand,
  GetRemoteAccessSessionCommand,
  StopRemoteAccessSessionCommand,
} from "@aws-sdk/client-device-farm";
import { AbstractInterface, defineActionsFromInputPrimitives, type DeviceAction } from "@midscene/core/device";
import { Agent } from "@midscene/core/agent";
import { getBaseUrl, MODEL, modelFamily, sigv4Fetch } from "../src/lib/agentcore-sigv4.mjs";

const DF_REGION = "us-west-2";
const DEVICE_ARN = process.env.DF_DEVICE_ARN
  || "arn:aws:devicefarm:us-west-2::device:653D5AB0CD6B4EA88DFAE9AD4386F608"; // Xiaomi Redmi Note 13, Android 15
const RUN_DIR = process.env.MIDSCENE_RUN_DIR || "/tmp/spike06";
const SKIP_AI = process.env.SPIKE_SKIP_AI === "1";
const START_URL = "https://en.m.wikipedia.org/wiki/OpenAI";

type Driver = Awaited<ReturnType<typeof remote>>;
const results: Record<string, unknown> = { device_arn: DEVICE_ARN, model: MODEL, started_at: new Date().toISOString() };
const log = (m: string) => console.log(`[06 ${new Date().toISOString().slice(11, 19)}] ${m}`);
const ms = (t0: number) => Math.round(performance.now() - t0);
async function timed<T>(name: string, fn: () => Promise<T>): Promise<T> {
  const t0 = performance.now();
  try { return await fn(); } finally { const d = ms(t0); (results.timings ??= {} as Record<string, number[]>); const tm = results.timings as Record<string, number[]>; (tm[name] ??= []).push(d); log(`${name}: ${d} ms`); }
}
const sleep = (t: number) => new Promise((r) => setTimeout(r, t));

// ---- Device Farm 会话 ----
const df = new DeviceFarmClient({ region: DF_REGION });
async function projectArn(): Promise<string> {
  if (process.env.DF_PROJECT_ARN) return process.env.DF_PROJECT_ARN;
  const r = await df.send(new ListProjectsCommand({}));
  const p = r.projects?.find((x) => x.name === "gherkai-spike");
  if (!p?.arn) throw new Error("没有名为 gherkai-spike 的 Device Farm 项目，先建或给 DF_PROJECT_ARN");
  return p.arn;
}
async function startSession(project: string): Promise<{ arn: string; endpoint: string }> {
  const created = await df.send(new CreateRemoteAccessSessionCommand({
    projectArn: project, deviceArn: DEVICE_ARN, name: `spike06-${Date.now()}`,
    configuration: { billingMethod: "METERED" },
  }));
  const arn = created.remoteAccessSession!.arn!;
  log(`会话已请求：${arn.slice(-24)}，状态 ${created.remoteAccessSession!.status}`);
  const t0 = performance.now();
  const seen = new Set<string>();
  for (;;) {
    const g = await df.send(new GetRemoteAccessSessionCommand({ arn }));
    const s = g.remoteAccessSession!;
    if (!seen.has(s.status!)) { seen.add(s.status!); log(`状态 ${s.status} @${ms(t0)} ms`); }
    if (s.status === "RUNNING" && s.endpoints?.remoteDriverEndpoint) {
      results.session_ready_ms = ms(t0); results.session_statuses = [...seen];
      results.device = { name: s.device?.name, os: s.device?.os, resolution: s.device?.resolution };
      return { arn, endpoint: s.endpoints.remoteDriverEndpoint };
    }
    if (["COMPLETED", "STOPPING", "ERRORED", "FAILED"].includes(s.status!)) throw new Error(`会话未到 RUNNING 即终止：${s.status} ${s.message ?? ""}`);
    if (ms(t0) > 15 * 60_000) throw new Error("等会话 15 分钟未 RUNNING");
    await sleep(10_000);
  }
}
async function stopSession(arn: string): Promise<void> {
  const t0 = performance.now();
  await df.send(new StopRemoteAccessSessionCommand({ arn }));
  for (;;) {
    const g = await df.send(new GetRemoteAccessSessionCommand({ arn }));
    const st = g.remoteAccessSession!.status;
    if (st === "COMPLETED" || st === "STOPPING" && ms(t0) > 120_000) { results.session_stop_ms = ms(t0); results.session_final_status = st; results.device_minutes = g.remoteAccessSession!.deviceMinutes; log(`会话 ${st}，停止用时 ${ms(t0)} ms，deviceMinutes=${JSON.stringify(g.remoteAccessSession!.deviceMinutes)}`); return; }
    if (ms(t0) > 5 * 60_000) { results.session_stop_ms = ms(t0); results.session_final_status = st; log(`停止等待超 5 分钟，状态 ${st}`); return; }
    await sleep(5_000);
  }
}

// ---- WebDriver 连接与命令往返 ----
async function connect(endpoint: string): Promise<Driver> {
  const u = new URL(endpoint);
  return remote({
    protocol: u.protocol.replace(":", ""), hostname: u.hostname,
    port: u.port ? Number(u.port) : 443, path: u.pathname + u.search,
    logLevel: "warn",
    capabilities: {
      platformName: "Android",
      "appium:automationName": "UiAutomator2",
      browserName: "Chrome",
      "appium:newCommandTimeout": 900,   // 模型思考几十秒，别让 Appium 把会话当闲置回收
    },
  });
}
function pngSize(b64: string): { width: number; height: number } {
  const buf = Buffer.from(b64.slice(0, 64), "base64"); // IHDR 在前 24 字节内
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
}

// ---- Midscene 适配器：截图、尺寸、动作三件 ----
class AppiumInterface extends AbstractInterface {
  interfaceType = "appium-webdriver";
  // AbstractInterface 把这些声明为「可选的抽象成员」，子类仍须给出声明；spike 不实现的一律显式置 undefined。
  cacheFeatureForPoint = undefined;
  rectMatchesCacheFeature = undefined;
  getUITree = undefined;
  beforeInvokeAction = undefined;
  afterInvokeAction = undefined;
  getElementsNodeTree = undefined;
  evaluateJavaScript = undefined;
  describe = () => `Device Farm Appium 端点上的 Android Chrome（${DEVICE_ARN.slice(-12)}）`;
  constructor(private readonly d: Driver) { super(); }
  // 截图与手势都在 NATIVE_APP 上下文：整屏像素坐标系，与 UiAutomator2 的 mobile: 手势同一坐标系。
  // （第一轮在 CHROMIUM 上下文截图拿到的是视口图，纵向少一个状态栏加地址栏的偏移，点击全部落空。）
  private async native<T>(fn: () => Promise<T>): Promise<T> {
    const cur = await this.d.getContext();
    if (cur !== "NATIVE_APP") await this.d.switchContext("NATIVE_APP");
    return fn();
  }
  async screenshotBase64(): Promise<string> { return "data:image/png;base64," + await this.native(() => this.d.takeScreenshot()); }
  async size() {
    const shot = await this.native(() => this.d.takeScreenshot());
    return pngSize(shot);
  }
  actionSpace(): DeviceAction[] {
    const d = this.d;
    const key = (name: string) => ({ Enter: 66, Return: 66, Backspace: 67, Tab: 61, Back: 4, Home: 3, Escape: 111 } as Record<string, number>)[name];
    return defineActionsFromInputPrimitives({
      pointer: {
        tap: async (p) => { await d.execute("mobile: clickGesture", { x: Math.round(p.x), y: Math.round(p.y) }); },
        longPress: async (p, o) => { await d.execute("mobile: longClickGesture", { x: Math.round(p.x), y: Math.round(p.y), duration: o?.duration ?? 800 }); },
      },
      keyboard: {
        typeText: async (value) => { await d.execute("mobile: type", { text: value }); },
        keyboardPress: async (name) => { const k = key(name); if (k === undefined) throw new Error(`未映射的键：${name}`); await d.execute("mobile: pressKey", { keycode: k }); },
        clearInput: async () => { for (let i = 0; i < 40; i++) await d.execute("mobile: pressKey", { keycode: 67 }); },
      },
      scroll: {
        scroll: async (param) => {
          const s = await this.size();
          const dir = (param as { direction?: string }).direction ?? "down";
          const dist = (param as { distance?: number }).distance ?? Math.round(s.height * 0.5);
          await d.execute("mobile: scrollGesture", { left: 0, top: Math.round(s.height * 0.2), width: s.width, height: Math.round(s.height * 0.6), direction: dir, percent: Math.min(1, dist / s.height) });
        },
      },
      system: {
        backButton: async () => { await d.execute("mobile: pressKey", { keycode: 4 }); },
        homeButton: async () => { await d.execute("mobile: pressKey", { keycode: 3 }); },
      },
    }, { size: () => this.size(), includeSwipe: false });
  }
  url = async () => { const cur = await this.d.getContext(); if (cur !== "CHROMIUM") await this.d.switchContext("CHROMIUM"); const u = await this.d.getUrl(); if (cur !== "CHROMIUM") await this.d.switchContext(cur as string); return u; };
  async destroy() { /* 会话由 main 统一收 */ }
}

async function main(): Promise<number> {
  fs.mkdirSync(RUN_DIR, { recursive: true });
  const project = await projectArn();
  log(`项目 ${project.slice(-20)}，设备 ${DEVICE_ARN.slice(-12)}，模型 ${MODEL}（${modelFamily()}），Bedrock ${getBaseUrl()}`);
  const session = await startSession(project);
  let driver: Driver | undefined;
  let rc = 0;
  try {
    driver = await timed("webdriver_connect", () => connect(session.endpoint));
    results.caps = (driver as unknown as { capabilities: unknown }).capabilities;
    log(`caps: ${JSON.stringify(results.caps).slice(0, 300)}`);
    for (let i = 0; i < 3; i++) {
      const shot = await timed("cmd_screenshot", () => driver!.takeScreenshot());
      if (i === 0) { results.screenshot_px = pngSize(shot); results.screenshot_b64_kb = Math.round(shot.length / 1024); }
      await timed("cmd_window_rect", () => driver!.getWindowRect());
    }
    results.contexts = await timed("cmd_get_contexts", () => driver!.getContexts());
    await driver.switchContext("NATIVE_APP");
    for (let i = 0; i < 2; i++) { const shot = await timed("cmd_screenshot_native", () => driver!.takeScreenshot()); if (i === 0) results.screenshot_native_px = pngSize(shot); }
    await driver.switchContext("CHROMIUM");
    results.window_rect = await driver.getWindowRect();
    await timed("cmd_navigate", () => driver!.url(START_URL));
    results.title_after_nav = await timed("cmd_get_title", () => driver!.getTitle());
    results.url_after_nav = await timed("cmd_get_url", () => driver!.getUrl());
    try {  // 探针失败不该拖垮 AI 阶段
      const h1s = await timed("cmd_find_h1", async () => await driver!.$$("h1"));
      results.h1_count = h1s.length;
      results.h1_text = h1s.length ? await timed("cmd_get_text", async () => await h1s[0].getText()) : null;
      results.page_source_kb = Math.round((await timed("cmd_page_source", () => driver!.getPageSource())).length / 1024);
    } catch (e) { results.probe_error = String((e as Error).message).slice(0, 200); log(`探针失败（继续）：${results.probe_error}`); }
    log(`导航后标题「${results.title_after_nav}」 h1「${results.h1_text}」 contexts=${JSON.stringify(results.contexts)} rect=${JSON.stringify(results.window_rect)} shot=${JSON.stringify(results.screenshot_px)}`);

    if (!SKIP_AI) {
      const iface = new AppiumInterface(driver);
      const agent = new Agent(iface, {
        generateReport: true, persistExecutionDump: true, replanningCycleLimit: 4,
        modelConfig: { MIDSCENE_MODEL_NAME: MODEL, MIDSCENE_MODEL_BASE_URL: getBaseUrl(), MIDSCENE_MODEL_API_KEY: "unused", MIDSCENE_MODEL_FAMILY: modelFamily() },
        createOpenAIClient: async () => new OpenAI({ baseURL: getBaseUrl(), apiKey: "unused", fetch: sigv4Fetch }) as never,
      } as never);
      const ai: Record<string, unknown>[] = [];
      const step = async (kind: "act" | "bool", prompt: string) => {
        const t0 = performance.now(); let out: unknown; let err: string | undefined;
        try { out = kind === "act" ? await agent.aiAct(prompt) : await agent.aiBoolean(prompt); } catch (e) { err = String((e as Error).message ?? e).slice(0, 300); }
        const m = (agent as unknown as { metrics?: { totalTokens?: number } }).metrics;
        const rec = { kind, prompt, ms: ms(t0), result: out, error: err, total_tokens_so_far: m?.totalTokens, executions: (agent.dump?.executions ?? []).length };
        ai.push(rec); log(`AI ${kind} ${rec.ms} ms tokens=${rec.total_tokens_so_far} result=${JSON.stringify(out)} ${err ? "ERR " + err : ""}`);
      };
      await step("bool", "这是维基百科上 OpenAI 的词条页");
      await step("act", "点击页面顶部的搜索图标");
      await step("bool", "页面上出现了可输入的搜索框");
      await step("act", "在搜索框输入 Playwright 并点击搜索结果里的 Playwright 条目");
      await step("bool", "当前页面是 Playwright 的维基百科词条页");
      await step("bool", "页面顶部有一条红色横幅写着本站已永久关闭");  // 刻意为假：量判否路径
      results.ai_steps = ai;
      await driver.switchContext("CHROMIUM");   // AI 阶段结束时停在 NATIVE_APP，读地址要回网页上下文（第三轮在此报 url 未实现）
      results.url_after_ai = await driver.getUrl();
      await agent.destroy().catch(() => {});
      const shotsDir = path.join(RUN_DIR, "report", "screenshots");
      results.report_dir = fs.existsSync(path.join(RUN_DIR, "report")) ? fs.readdirSync(path.join(RUN_DIR, "report")).slice(0, 10) : null;
      results.screenshots_persisted = fs.existsSync(shotsDir) ? fs.readdirSync(shotsDir).length : 0;
      const execs = agent.dump?.executions ?? [];
      results.executions = execs.length;
      fs.writeFileSync(path.join(RUN_DIR, "spike06-executions.json"), JSON.stringify(execs, (k, v) => (k === "base64" ? undefined : v), 2));
    }
  } catch (e) {
    rc = 1; results.error = String((e as Error).stack ?? e).slice(0, 2000); log(`失败：${(e as Error).message}`);
  } finally {
    if (driver) await timed("webdriver_delete_session", () => driver!.deleteSession()).catch((e) => log(`deleteSession: ${(e as Error).message}`));
    await stopSession(session.arn).catch((e) => log(`stop: ${(e as Error).message}`));
    results.finished_at = new Date().toISOString();
    fs.writeFileSync(path.join(RUN_DIR, "spike06-results.json"), JSON.stringify(results, null, 2));
    log(`结果：${path.join(RUN_DIR, "spike06-results.json")}`);
  }
  return rc;
}

process.exit(await main());
