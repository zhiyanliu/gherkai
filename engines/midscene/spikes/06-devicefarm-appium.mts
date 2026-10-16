// 移动设备方向的 spike A / B：Device Farm 远程访问会话 + 托管 Appium 端点 + Midscene 自定义界面适配器（AbstractInterface），
// 在一台真机上执行设备网页（Android Chrome / iOS Safari）或原生应用（Android，经 Device Farm 上传并安装 APK）。
// 测量四样：会话建立与停止耗时、WebDriver 命令往返、AI 步耗时与 token、evidence 原料（dump.executions 与截图落盘）是否照旧。
//
// 运行（跳板机，实例角色即凭证；Bedrock 走 AWS_REGION，Device Farm 固定 us-west-2）：
//   cd engines/midscene && AWS_REGION=us-east-1 MIDSCENE_RUN_DIR=/tmp/spike06 node --import tsx spikes/06-devicefarm-appium.mts
// 可选 env：
//   DF_PLATFORM=android|ios（缺省 android）      DF_DEVICE_ARN（缺省按平台各一台默认机）
//   SPIKE_SCENARIO=web|app|egress|faults（缺省 web） DF_PROJECT_ARN（缺省按名 gherkai-spike 查）
//     egress：设备侧出网事实（源 IP、国内外站点导航耗时）与 Appium 主机侧 appium:app 公网 / S3 预签名地址下载对照
//            （DF_EGRESS_URL_A 公网 APK 地址、DF_EGRESS_URL_B S3 预签名地址、DF_EGRESS_PKG 该 APK 的包名）
//     faults：失败形态——模型名错误、应用被外部杀掉、会话被外部 Stop 时适配器与 Agent 各报什么、多久报出来
//     cap：150 分钟会话上限——每分钟发一条命令并查会话状态，记录命令开始失败的时刻与最终状态（SPIKE_CAP_MAX_MIN 缺省 165）
//     deeplink：应用目标上 mobile: deepLink 能否把被测应用带到某一页（Android 维基百科客户端需 DF_APP_ARN；iOS 用系统「地图」）
//   DF_APP_URL（app 场景：APK 的 https 地址）      DF_APP_ARN（已上传过的 Device Farm 应用 ARN，给了就不再上传）
//   DF_APP_PACKAGE（缺省 org.wikipedia）          DF_APP_INSTALL=devicefarm|appium（缺省 devicefarm：上传后 InstallToRemoteAccessSession；
//                                                 appium：用 appium:app 让 Appium 主机自己下载安装——公网 https 与 S3 预签名地址实测都能装；
//                                                 不带 appPackage / appActivity 时会卡在启动，要配 appium:autoLaunch false 或给齐包名与活动名）
//   SPIKE_SKIP_AI=1（只量会话与命令往返，不调模型）
// 结果落 $MIDSCENE_RUN_DIR/spike06-results.json；无论成败最后都停会话（设备按分钟计费）。
import * as fs from "node:fs";
import * as path from "node:path";
import OpenAI from "openai";
import { remote, attach } from "webdriverio";
import {
  DeviceFarmClient,
  ListProjectsCommand,
  CreateRemoteAccessSessionCommand,
  GetRemoteAccessSessionCommand,
  StopRemoteAccessSessionCommand,
  ListRemoteAccessSessionsCommand,
  ListArtifactsCommand,
  CreateUploadCommand,
  GetUploadCommand,
  ListUploadsCommand,
  InstallToRemoteAccessSessionCommand,
} from "@aws-sdk/client-device-farm";
import { AbstractInterface, defineActionsFromInputPrimitives, type DeviceAction } from "@midscene/core/device";
import { Agent } from "@midscene/core/agent";
import { getBaseUrl, MODEL, modelFamily, sigv4Fetch } from "../src/lib/agentcore-sigv4.mjs";
import { buildEvidence, executionsLength } from "../src/worker/evidence.mjs";

const DF_REGION = "us-west-2";
const PLATFORM = (process.env.DF_PLATFORM ?? "android") as "android" | "ios";
const SCENARIO = (process.env.SPIKE_SCENARIO ?? "web") as "web" | "app" | "egress" | "faults" | "cap" | "warmup" | "timeouts" | "release" | "deeplink";
// 隧道「令牌换 cookie」预热、超时分层与会话释放三类探针的输入（见各 probe 函数头注释）
const TUNNEL_BASE = (process.env.DF_TUNNEL_BASE ?? "").replace(/\/$/, "");
const TUNNEL_TOKEN = process.env.DF_TUNNEL_TOKEN ?? "";
const XSITE_ORIGIN = process.env.DF_XSITE_ORIGIN ?? "https://example.com";
const WARMUP_ROUTE = (process.env.DF_WARMUP_ROUTE ?? (process.env.DF_PLATFORM === "ios" ? "deeplink" : "url")) as "url" | "deeplink";
const NCT_S = process.env.DF_NCT ? Number(process.env.DF_NCT) : 900;
const DEFAULT_DEVICE = {
  android: "arn:aws:devicefarm:us-west-2::device:653D5AB0CD6B4EA88DFAE9AD4386F608", // Xiaomi Redmi Note 13, Android 15
  ios: "arn:aws:devicefarm:us-west-2::device:BDC0E688BC0F4CE7BEE056028DB32001",     // Apple iPhone 7, iOS 15.8.4
}[PLATFORM];
const DEVICE_ARN = process.env.DF_DEVICE_ARN || DEFAULT_DEVICE;
const RUN_DIR = process.env.MIDSCENE_RUN_DIR || "/tmp/spike06";
const SKIP_AI = process.env.SPIKE_SKIP_AI === "1";
const APP_URL = process.env.DF_APP_URL;
const APP_ARN = process.env.DF_APP_ARN;
const APP_PACKAGE = process.env.DF_APP_PACKAGE ?? "org.wikipedia";
const APP_INSTALL = process.env.DF_APP_INSTALL ?? "devicefarm";
const START_URL = "https://en.m.wikipedia.org/wiki/OpenAI";

type Driver = Awaited<ReturnType<typeof remote>>;
const results: Record<string, unknown> = {
  platform: PLATFORM, scenario: SCENARIO, device_arn: DEVICE_ARN, model: MODEL, started_at: new Date().toISOString(),
};
const log = (m: string) => console.log(`[06 ${new Date().toISOString().slice(11, 19)}] ${m}`);
// webdriver 10.0.2 的 newSession 在客户端超时后会留下一个未处理的 rejected promise（实测：进程因 unhandledRejection 直接退出、
// finally 没有机会执行、设备会话泄漏）。探针记录它并继续运行；worker 实现同样需要这一层兜底。
process.on("unhandledRejection", (reason) => {
  ((results.unhandled_rejections ??= []) as string[]).push(errText(reason).slice(0, 300));
  log(`unhandledRejection（已记录、继续）：${errText(reason).slice(0, 200)}`);
});
const ms = (t0: number) => Math.round(performance.now() - t0);
async function timed<T>(name: string, fn: () => Promise<T>): Promise<T> {
  const t0 = performance.now();
  try { return await fn(); } finally { const d = ms(t0); (results.timings ??= {} as Record<string, number[]>); const tm = results.timings as Record<string, number[]>; (tm[name] ??= []).push(d); log(`${name}: ${d} ms`); }
}
const sleep = (t: number) => new Promise((r) => setTimeout(r, t));
// WebdriverIO 把服务端错误体塞进 message，有时是对象，直接拼字符串只剩 [object Object]；把能拿到的字段都展开
const errText = (e: unknown): string => {
  const o = e as Record<string, unknown>;
  const parts = [o?.name, typeof o?.message === "string" ? o.message : JSON.stringify(o?.message), o?.stacktrace, o?.data ? JSON.stringify(o.data) : undefined];
  return parts.filter(Boolean).join(" | ").slice(0, ERR_MAX);
};
const ERR_MAX = process.env.SPIKE_ERR_MAX ? Number(process.env.SPIKE_ERR_MAX) : 600;

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
    projectArn: project, deviceArn: DEVICE_ARN, name: `spike06-${PLATFORM}-${SCENARIO}-${Date.now()}`,
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

// ---- 应用上传与安装（Device Farm 路径）----
// 上传是项目级资源，处理成功后可跨会话复用；安装是会话级动作。
async function ensureAppUpload(project: string): Promise<string> {
  if (APP_ARN) return APP_ARN;
  if (!APP_URL) throw new Error("app 场景需要 DF_APP_URL 或 DF_APP_ARN");
  const name = path.basename(new URL(APP_URL).pathname);
  const existing = await df.send(new ListUploadsCommand({ arn: project, type: PLATFORM === "ios" ? "IOS_APP" : "ANDROID_APP" }));
  const hit = existing.uploads?.find((u) => u.name === name && u.status === "SUCCEEDED");
  if (hit?.arn) { log(`复用已上传的应用 ${name}`); results.app_upload_reused = true; return hit.arn; }
  const local = path.join(RUN_DIR, name);
  if (!fs.existsSync(local)) {
    await timed("app_download", async () => { const r = await fetch(APP_URL); if (!r.ok) throw new Error(`下载 APK 失败：${r.status}`); fs.writeFileSync(local, Buffer.from(await r.arrayBuffer())); });
  }
  const bytes = fs.readFileSync(local);
  results.app_bytes = bytes.length;
  const created = await df.send(new CreateUploadCommand({ projectArn: project, name, type: PLATFORM === "ios" ? "IOS_APP" : "ANDROID_APP", contentType: "application/octet-stream" }));
  const upload = created.upload!;
  await timed("app_upload_put", async () => {
    const r = await fetch(upload.url!, { method: "PUT", body: bytes, headers: { "Content-Type": "application/octet-stream" } });
    if (!r.ok) throw new Error(`PUT 到 Device Farm 预签名地址失败：${r.status}`);
  });
  await timed("app_upload_processing", async () => {
    for (;;) {
      const g = await df.send(new GetUploadCommand({ arn: upload.arn! }));
      const st = g.upload!.status;
      if (st === "SUCCEEDED") { results.app_upload_metadata = g.upload!.metadata?.slice(0, 600); return; }
      if (st === "FAILED") throw new Error(`Device Farm 处理上传失败：${g.upload!.message ?? ""} ${g.upload!.metadata ?? ""}`.slice(0, 500));
      await sleep(5_000);
    }
  });
  return upload.arn!;
}
async function installApp(driver: Driver, sessionArn: string, appArn: string): Promise<void> {
  await timed("app_install_call", async () => {
    const r = await df.send(new InstallToRemoteAccessSessionCommand({ remoteAccessSessionArn: sessionArn, appArn }));
    results.app_install_response = { status: r.appUpload?.status, message: r.appUpload?.message };
  });
  await timed("app_install_until_present", async () => {
    const t0 = performance.now();
    for (;;) {
      if (await driver.isAppInstalled(APP_PACKAGE)) return;
      if (ms(t0) > 5 * 60_000) throw new Error(`安装 5 分钟后 ${APP_PACKAGE} 仍未出现在设备上`);
      await sleep(5_000);
    }
  });
}

// ---- WebDriver 连接与命令往返 ----
function caps(): Record<string, unknown> {
  const common = { "appium:newCommandTimeout": NCT_S };   // 模型思考几十秒，别让 Appium 把会话当闲置回收；timeouts 场景按 DF_NCT 调小以测它的计时语义
  // 预热与超时探针都在系统浏览器里做
  if (SCENARIO === "warmup" || SCENARIO === "timeouts" || SCENARIO === "release") {
    return PLATFORM === "ios"
      ? { platformName: "iOS", "appium:automationName": "XCUITest", browserName: "Safari", ...common }
      : { platformName: "Android", "appium:automationName": "UiAutomator2", browserName: "Chrome", ...common };
  }
  // egress：要导航站点时带 Safari（否则 iOS 没有网页上下文、url 命令会挂住）；只做主机侧安装试验时不带浏览器
  if (PLATFORM === "ios" && SCENARIO === "egress") return { platformName: "iOS", "appium:automationName": "XCUITest", ...(process.env.DF_EGRESS_SKIP_NAV === "1" ? { "appium:noReset": true } : { browserName: "Safari" }), ...common };
  if (PLATFORM === "ios") {
    // app 场景不带 bundleId：先连（XCUITest 落在主屏）、经 Device Farm 装、再 activateApp；DF_APP_PACKAGE 在 iOS 上就是 bundle id
    return { platformName: "iOS", "appium:automationName": "XCUITest", ...(SCENARIO === "web" ? { browserName: "Safari" } : { "appium:noReset": true }), ...common };
  }
  if (SCENARIO === "web" || SCENARIO === "egress" || SCENARIO === "cap") return { platformName: "Android", "appium:automationName": "UiAutomator2", browserName: "Chrome", ...common };
  if (SCENARIO === "faults") return { platformName: "Android", "appium:automationName": "UiAutomator2", "appium:noReset": true, ...common };
  // app 场景：Device Farm 路径先连会话（不带应用能力）、再装再启；appium 路径由 Appium 主机按 appium:app 下载安装
  return {
    platformName: "Android", "appium:automationName": "UiAutomator2", "appium:noReset": true,
    ...(APP_INSTALL === "appium" && APP_URL ? { "appium:app": APP_URL, "appium:appPackage": APP_PACKAGE } : {}),
    ...common,
  };
}
async function connect(endpoint: string): Promise<Driver> {
  const u = new URL(endpoint);
  return remote({
    protocol: u.protocol.replace(":", ""), hostname: u.hostname,
    port: u.port ? Number(u.port) : 443, path: u.pathname + u.search,
    logLevel: "warn",
    capabilities: caps(),
  });
}
function pngSize(b64: string): { width: number; height: number } {
  const buf = Buffer.from(b64.slice(0, 64), "base64"); // IHDR 在前 24 字节内
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
}
const elementId = (ref: unknown): string => Object.values(ref as Record<string, string>)[0];
// WebdriverIO 把非标准错误体压成 [object Object]；对失败的路由再发一次原始 HTTP 请求，记下状态码与响应体
async function rawProbe(endpoint: string, driver: Driver, route: string): Promise<unknown> {
  try {
    const base = endpoint.replace(/\/$/, "");
    const r = await fetch(`${base}/session/${driver.sessionId}/${route}`);
    const body = (await r.text()).slice(0, 800);
    (results.raw_probes ??= {} as Record<string, unknown>);
    (results.raw_probes as Record<string, unknown>)[route] = { status: r.status, body };
    log(`原始探针 ${route}: HTTP ${r.status} ${body.slice(0, 300)}`);
    return body;
  } catch (e) { log(`原始探针 ${route} 本身失败：${errText(e)}`); return undefined; }
}

// ---- Midscene 适配器：截图、尺寸、动作三件 ----
// 截图与手势都在 NATIVE_APP 上下文：整屏像素坐标系（Android 的 mobile: 手势直接用像素；iOS 的 XCUITest 手势用点，
// 按截图像素宽 / 窗口点宽的比例换算）。网页上下文（Android 的 CHROMIUM、iOS 的 WEBVIEW_*）只在读地址、历史后退时临时切入。
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
  describe = () => `Device Farm Appium 端点上的 ${PLATFORM} ${SCENARIO}（${DEVICE_ARN.slice(-12)}）`;
  private scale = 1;                 // 截图像素 / 手势坐标单位；Android 为 1，iOS 首次用到时按窗口点宽算出
  private webCtx: string | undefined; // 网页上下文名，首次用到时查
  private async native<T>(fn: () => Promise<T>): Promise<T> {
    const cur = await this.d.getContext();
    if (cur !== "NATIVE_APP") await this.d.switchContext("NATIVE_APP");
    return fn();
  }
  private async inWeb<T>(fn: () => Promise<T>): Promise<T> {
    const cur = (await this.d.getContext()) as string;
    if (cur === "NATIVE_APP" || !this.webCtx) {
      const cs = (await this.d.getContexts()) as string[];
      this.webCtx = cs.find((c) => c !== "NATIVE_APP");
      if (!this.webCtx) throw new Error(`没有网页上下文：${JSON.stringify(cs)}`);
    }
    if (cur !== this.webCtx) await this.d.switchContext(this.webCtx);
    try { return await fn(); } finally { if (cur !== this.webCtx) await this.d.switchContext(cur); }
  }
  async screenshotBase64(): Promise<string> { return "data:image/png;base64," + await this.native(() => this.d.takeScreenshot()); }
  async size() {
    const shot = await this.native(() => this.d.takeScreenshot());
    const px = pngSize(shot);
    if (PLATFORM === "ios" && this.scale === 1) {
      const info = await this.native(() => this.d.execute("mobile: deviceScreenInfo")).catch(() => undefined) as { scale?: number } | undefined;
      if (info?.scale) { this.scale = info.scale; results.ios_scale = { px, device_screen_info: info, scale: this.scale }; }
      else { const rect = await this.native(() => this.d.getWindowRect()); this.scale = px.width / rect.width; results.ios_scale = { px, window_points: rect, scale: this.scale }; }
    }
    return px;
  }
  private pt(v: number): number { return Math.round((v / this.scale) * 100) / 100; }
  // iOS 没有键码。两台 iPhone（iOS 15.8 / 26.3）在 Safari 与原生应用上逐条实测后的结论：W3C 标准路线就够——
  // 网页上下文可用时对网页活动元素 sendKeys，否则对原生活动元素 sendKeys；旧版 /keys 与 W3C 键盘动作只留作对照。候选：
  //   web-active-element：网页上下文里的活动元素加 sendKeys（Safari 远程检查器的 type 原子，合成事件）；
  //   legacy-keys-raw：Appium 旧版 POST /keys（XCUITest 在原生上下文转给 WDA 的 /wda/keys，打到第一响应者）；
  //   w3c-key-actions-native：W3C 键盘动作（WebdriverIO 的 keys；iPhone 7 / iOS 15.8 上不报错但不落字、每次 52 秒）；
  //   native-active-element：NATIVE_APP 的活动元素加 sendKeys（iPhone 7 / iOS 15.8 上报无此元素）。
  // mobile: keys 只在 iOS 17+ 的 iPad 上有效，不列入。
  // 两台 iPhone 实测后的定稿顺序：标准路线在前（网页上下文可用则网页活动元素，否则原生活动元素），旧版 /keys 只留作对照
  static typeRouteOrder: string[] = ["web-active-element", "native-active-element", "legacy-keys-raw"];
  private typeRoute: string | undefined;
  /** 探针或确定性步骤已知的目标输入框元素 id；有它时「direct-element-sendkeys」路线可用 */
  knownFieldId: string | undefined;
  constructor(private readonly d: Driver, private readonly endpoint: string) { super(); }
  typingRoutes(text: string): Array<[string, () => Promise<void>]> {
    const all: Record<string, () => Promise<void>> = {
      // 标准路线一：按「持有键盘焦点」谓词找到元素，再对元素 sendKeys（W3C 的 element/value）
      "predicate-focus-sendkeys": () => this.native(async () => {
        const els = await this.d.$$("-ios predicate string:hasKeyboardFocus == 1");
        if (!els.length) throw new Error("没有持有键盘焦点的元素");
        await this.d.elementSendKeys(els[0].elementId, text);
      }),
      // 标准路线二：对已知元素直接 sendKeys（确定性步骤或探针自己找到的输入框）
      "direct-element-sendkeys": () => this.native(async () => {
        if (!this.knownFieldId) throw new Error("没有已知的输入框元素");
        await this.d.elementSendKeys(this.knownFieldId, text);
      }),
      "web-active-element": () => this.inWeb(async () => { const ref = await this.d.getActiveElement(); await this.d.elementSendKeys(elementId(ref), text); }),
      "legacy-keys-raw": () => this.native(async () => {
        const r = await fetch(`${this.endpoint.replace(/\/$/, "")}/session/${this.d.sessionId}/keys`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ value: [...text] }) });
        if (!r.ok) throw new Error(`POST /keys HTTP ${r.status} ${(await r.text()).slice(0, 300)}`);
      }),
      "w3c-key-actions-native": () => this.native(async () => { await this.d.keys(text); }),
      "native-active-element": () => this.native(async () => { const ref = await this.d.getActiveElement(); await this.d.elementSendKeys(elementId(ref), text); }),
      "mobile-type": () => this.native(async () => { await this.d.execute("mobile: type", { text }); }),   // Android UiAutomator2 专有
    };
    const base = PLATFORM === "android" ? ["web-active-element", "native-active-element", "mobile-type"] : AppiumInterface.typeRouteOrder;
    const order = this.knownFieldId ? ["direct-element-sendkeys", ...base] : base;
    return order.map((n) => [n, all[n]] as [string, () => Promise<void>]);
  }
  private async iosSendKeys(text: string): Promise<void> {
    const routes = this.typingRoutes(text);
    const ordered = this.typeRoute ? [...routes.filter((r) => r[0] === this.typeRoute), ...routes.filter((r) => r[0] !== this.typeRoute)] : routes;
    const errors: string[] = [];
    for (const [name, fn] of ordered) {
      try {
        await fn();
        this.typeRoute = name;
        ((results.ios_type_routes ??= []) as string[]).push(name);
        return;
      } catch (e) { errors.push(`${name}: ${errText(e)}`); }
    }
    ((results.ios_type_errors ??= []) as string[]).push(errors.join(" || "));
    throw new Error(`iOS 输入全部路线失败：${errors.join(" || ")}`);
  }
  private async swipe(from: { x: number; y: number }, to: { x: number; y: number }, durationMs = 400): Promise<void> {
    await this.d.performActions([{
      type: "pointer", id: "finger1", parameters: { pointerType: "touch" },
      actions: [
        { type: "pointerMove", duration: 0, x: this.pt(from.x), y: this.pt(from.y) },
        { type: "pointerDown", button: 0 },
        { type: "pause", duration: 100 },
        { type: "pointerMove", duration: durationMs, x: this.pt(to.x), y: this.pt(to.y) },
        { type: "pointerUp", button: 0 },
      ],
    }]);
    await this.d.releaseActions().catch(() => {});
  }
  actionSpace(): DeviceAction[] {
    const d = this.d;
    const ios = PLATFORM === "ios";
    const androidKey = (name: string) => ({ Enter: 66, Return: 66, Backspace: 67, Tab: 61, Back: 4, Home: 3, Escape: 111 } as Record<string, number>)[name];
    return defineActionsFromInputPrimitives({
      pointer: {
        tap: async (p) => {
          if (ios) await d.execute("mobile: tap", { x: this.pt(p.x), y: this.pt(p.y) });
          else await d.execute("mobile: clickGesture", { x: Math.round(p.x), y: Math.round(p.y) });
        },
        longPress: async (p, o) => {
          const dur = o?.duration ?? 800;
          if (ios) await d.execute("mobile: touchAndHold", { x: this.pt(p.x), y: this.pt(p.y), duration: dur / 1000 });
          else await d.execute("mobile: longClickGesture", { x: Math.round(p.x), y: Math.round(p.y), duration: dur });
        },
      },
      keyboard: {
        typeText: async (value) => { if (ios) await this.iosSendKeys(value); else await d.execute("mobile: type", { text: value }); },
        keyboardPress: async (name) => {
          if (ios) {
            const ch = ({ Enter: "\n", Return: "\n", Backspace: "\b" } as Record<string, string>)[name];
            if (ch === undefined) throw new Error(`iOS 上未映射的键：${name}`);
            await this.iosSendKeys(ch);
          } else {
            const k = androidKey(name); if (k === undefined) throw new Error(`未映射的键：${name}`);
            await d.execute("mobile: pressKey", { keycode: k });
          }
        },
        clearInput: async () => {
          if (ios) await this.iosSendKeys("\b".repeat(40));
          else for (let i = 0; i < 40; i++) await d.execute("mobile: pressKey", { keycode: 67 });
        },
      },
      scroll: {
        scroll: async (param) => {
          const s = await this.size();
          const dir = (param as { direction?: string }).direction ?? "down";
          const dist = (param as { distance?: number }).distance ?? Math.round(s.height * 0.5);
          if (ios) {
            // 手指方向与内容方向相反：向下看内容时手指上滑。首选 XCUITest 的 mobile: swipe（整个应用窗口上的真实轻扫手势），
            // W3C 指针拖动在 iOS 26 的分页视图（UIPageViewController）上实测不翻页，只作回落。
            const finger = ({ down: "up", up: "down", right: "left", left: "right" } as Record<string, string>)[dir] ?? "up";
            try { await d.execute("mobile: swipe", { direction: finger }); }
            catch (e) {
              ((results.ios_swipe_fallbacks ??= []) as string[]).push(errText(e).slice(0, 160));
              const cx = s.width / 2, cy = s.height / 2, dy = Math.min(dist, s.height * 0.6) / 2, dx = Math.min(dist, s.width * 0.6) / 2;
              const vec = { down: [0, -dy], up: [0, dy], right: [-dx, 0], left: [dx, 0] }[dir] ?? [0, -dy];
              await this.swipe({ x: cx - vec[0], y: cy - vec[1] }, { x: cx + vec[0], y: cy + vec[1] });
            }
          } else {
            await d.execute("mobile: scrollGesture", { left: 0, top: Math.round(s.height * 0.2), width: s.width, height: Math.round(s.height * 0.6), direction: dir, percent: Math.min(1, dist / s.height) });
          }
        },
      },
      system: {
        backButton: async () => {
          if (ios) await this.inWeb(() => d.back());               // Safari 没有系统返回键，用历史后退
          else await d.execute("mobile: pressKey", { keycode: 4 });
        },
        homeButton: async () => {
          if (ios) await d.execute("mobile: pressButton", { name: "home" });
          else await d.execute("mobile: pressKey", { keycode: 3 });
        },
      },
    }, { size: () => this.size(), includeSwipe: false });
  }
  url = async () => (SCENARIO === "web" ? this.inWeb(() => this.d.getUrl()).catch((e) => { results.url_error = errText(e); return ""; }) : "");
  async destroy() { /* 会话由 main 统一收 */ }
}

// ---- iOS 输入探针（确定性，不调模型）----
// 在 AI 点开搜索框之后对已聚焦的输入框逐条路线输入一段文本，经网页上下文读回活动元素的 value 判断是否落字，记录耗时与错误，
// 再按实测结果把可用路线排到前面。网页上下文不可用的系统（iOS 26.3 实测）读不回 value，只能记错误、靠后续 AI 步判断。
// 直接用 CSS 找搜索框并原子点击的做法在 iPhone 7 上拿到的是隐藏的输入框（元素不可见），所以借 AI 的点击来聚焦。
async function iosTypingProbe(iface: AppiumInterface, driver: Driver): Promise<void> {
  const report: Array<Record<string, unknown>> = [];
  const web = (results.contexts as string[]).find((c) => c !== "NATIVE_APP") ?? "NATIVE_APP";
  const readBack = async (): Promise<string | undefined> => {
    const cur = (await driver.getContext()) as string;
    try {
      await driver.switchContext(web);
      const ref = await driver.getActiveElement();
      return (await driver.getElementAttribute(elementId(ref), "value")) ?? undefined;
    } catch {
      // 网页上下文不可用（iOS 26）：从原生树读持有焦点元素的 value
      await driver.switchContext("NATIVE_APP").catch(() => {});
      const els = await driver.$$("-ios predicate string:hasKeyboardFocus == 1");
      return els.length ? ((await driver.getElementAttribute(els[0].elementId, "value")) ?? undefined) : undefined;
    } finally { await driver.switchContext(cur).catch(() => {}); }
  };
  const clear = async (): Promise<void> => {
    const cur = (await driver.getContext()) as string;
    try { await driver.switchContext(web); const ref = await driver.getActiveElement(); await driver.elementClear(elementId(ref)); }
    catch { await driver.switchContext("NATIVE_APP").catch(() => {}); const ref = await driver.getActiveElement(); await driver.elementClear(elementId(ref)); }
    finally { await driver.switchContext(cur).catch(() => {}); }
  };
  for (const [name, fn] of iface.typingRoutes("Playwright")) {
    const rec: Record<string, unknown> = { route: name };
    const t0 = performance.now();
    try {
      await fn();                               // 路线内部自行切上下文
      rec.type_ms = ms(t0);
      const value = await readBack().catch((e) => { rec.readback_error = errText(e); return undefined; });
      rec.value = value; rec.ok = typeof value === "string" && value.includes("Playwright");
      await clear().catch(() => {});
    } catch (e) { rec.error = errText(e); }
    rec.total_ms = ms(t0);
    report.push(rec);
    log(`输入探针 ${name}: ${JSON.stringify(rec)}`);
  }
  results.ios_typing_probe = report;
  const good = report.filter((r) => r.ok).sort((a, b) => (a.type_ms as number) - (b.type_ms as number)).map((r) => r.route as string);
  const rest = AppiumInterface.typeRouteOrder.filter((n) => !good.includes(n));
  AppiumInterface.typeRouteOrder = [...good, ...rest];
  results.ios_type_route_order = AppiumInterface.typeRouteOrder;
}

// ---- 出网探针（清单第 10 项的网络部分，兼核 Appium 主机侧能否自行下载 appium:app）----
async function egressProbe(driver: Driver, endpoint: string): Promise<void> {
  const web = (results.contexts as string[]).find((c) => c !== "NATIVE_APP");
  if (web) await driver.switchContext(web);
  else if (process.env.DF_EGRESS_SITES) { results.device_navigation = "没有网页上下文，跳过导航"; }
  const nav: Record<string, unknown> = {};
  const sites = process.env.DF_EGRESS_SITES ? process.env.DF_EGRESS_SITES.split(",").map((x) => x.trim()).filter(Boolean)
    : process.env.DF_EGRESS_SKIP_NAV === "1" ? [] : ["https://checkip.amazonaws.com/", "https://www.wikipedia.org/", "https://www.baidu.com/", "https://m.amap.com/", "https://www.weather.com.cn/", "https://m.weibo.cn/"];
  const mask = (u: string) => u.replace(/\/\/[^@/]+@/, "//<凭证已略>@");   // 隧道地址带 userinfo，日志里不落明文
  for (const u of web ? sites : []) {
    const t0 = performance.now();
    try {
      await driver.url(u);
      const title = await driver.getTitle();
      const body = String(await driver.execute("return document.body ? document.body.innerText : ''")).trim().slice(0, 80);
      const landed = mask(String(await driver.getUrl().catch(() => "?"))).slice(0, 90);   // 实际落在哪个地址：导航被拒时页面不变
      nav[mask(u)] = { ms: ms(t0), title: String(title).slice(0, 60), body, landed };
      // iOS Safari 对地址里内嵌的凭据不予采用、弹原生「Sign in to <host>」表单（实测）；在原生上下文把凭据填进去并提交，验证这条处置可行
      if (PLATFORM === "ios" && process.env.DF_EGRESS_BASICAUTH === "1" && /\/\/[^@/]+@/.test(u)) {
        const t1 = performance.now();
        const [user, pass] = new URL(u).username ? [new URL(u).username, new URL(u).password] : ["", ""];
        const cur = (await driver.getContext()) as string;
        await driver.switchContext("NATIVE_APP");
        const sheet = await driver.$$("-ios predicate string:label BEGINSWITH 'Sign in to'");
        const rec: Record<string, unknown> = { sheet_found: sheet.length > 0 };
        if (sheet.length) {
          // 每一步前重新查找：填完用户名后表单会重排，先前拿到的元素引用会失效（首轮实测 stale element）
          const find = (sel: string) => driver.$$(sel);
          const fields = await find("-ios class chain:**/XCUIElementTypeTextField");
          if (fields.length) {
            // 用 W3C 标准的 element/value 填：WebdriverIO 的 keys 在 iOS 上生成的键盘动作缺 keyUp 配对、WDA 直接拒绝
            await fields[0].click(); await driver.elementSendKeys((await find("-ios class chain:**/XCUIElementTypeTextField"))[0].elementId, user);
            const secure = await find("-ios class chain:**/XCUIElementTypeSecureTextField");
            if (secure.length) { await secure[0].click(); await driver.elementSendKeys((await find("-ios class chain:**/XCUIElementTypeSecureTextField"))[0].elementId, pass); }
            const btn = await find("-ios predicate string:label == 'Sign In' AND type == 'XCUIElementTypeButton'");
            if (btn.length) await btn[0].click();
            await sleep(3000);
            await driver.switchContext(cur);
            rec.title_after = String(await driver.getTitle()).slice(0, 60); rec.landed_after = mask(String(await driver.getUrl())).slice(0, 90); rec.ms = ms(t1);
          } else { rec.fields = fields.length; await driver.switchContext(cur); }
        } else { await driver.switchContext(cur); }
        results.ios_basic_auth_sheet = rec; log(`iOS 鉴权表单处置: ${JSON.stringify(rec)}`);
      }
      if (process.env.DF_EGRESS_SHOTS === "1") {   // 原生整屏截图：看导航被拒时屏幕上是什么（如系统鉴权弹窗）
        const cur = (await driver.getContext()) as string;
        await driver.switchContext("NATIVE_APP"); const shot = await driver.takeScreenshot(); await driver.switchContext(cur);
        fs.mkdirSync(path.join(RUN_DIR, "nav-shots"), { recursive: true });
        fs.writeFileSync(path.join(RUN_DIR, "nav-shots", `${Object.keys(nav).length}.png`), Buffer.from(shot, "base64"));
      }
    } catch (e) { nav[mask(u)] = { ms: ms(t0), error: errText(e).replace(/\/\/[^@/]+@/g, "//<凭证已略>@") }; }
    log(`导航 ${mask(u)}: ${JSON.stringify(nav[mask(u)])}`);
  }
  results.device_navigation = nav;
  await driver.deleteSession().catch(() => {});
  // Appium 主机侧：appium:app 公网地址 vs S3 预签名地址（各开一个 WebDriver 会话；Device Farm 会话不变）
  const host: Record<string, unknown> = {};
  // autoLaunch 关掉：只看「主机能否下载并安装」，不让启动失败掩盖下载结果（首轮两条地址都卡在启动上；关掉后两条都装上了）
  const trials: Array<[string, string | undefined, string | undefined]> = [["public_url", process.env.DF_EGRESS_URL_A, process.env.DF_EGRESS_PKG_A], ["s3_presigned", process.env.DF_EGRESS_URL_B, process.env.DF_EGRESS_PKG_B]];
  for (const [name, url, pkg] of trials) {
    if (!url) { host[name] = "未提供地址"; continue; }
    const t0 = performance.now();
    let d: Driver | undefined;
    try {
      const u = new URL(endpoint);
      d = await remote({ protocol: u.protocol.replace(":", ""), hostname: u.hostname, port: u.port ? Number(u.port) : 443, path: u.pathname + u.search, logLevel: "warn",
        capabilities: PLATFORM === "ios"
          ? { platformName: "iOS", "appium:automationName": "XCUITest", "appium:app": url, "appium:autoLaunch": false, "appium:noReset": true, "appium:newCommandTimeout": 900 }
          : { platformName: "Android", "appium:automationName": "UiAutomator2", "appium:app": url, "appium:autoLaunch": false, "appium:noReset": true, "appium:newCommandTimeout": 900 } });
      const session_ms = ms(t0);
      const installed = pkg ? await d.isAppInstalled(pkg) : undefined;
      // 装上还要能启动：签名不被设备接受的包 isAppInstalled 可能为真却启动即死
      let launch: unknown;
      if (pkg && installed) {
        try { await d.activateApp(pkg); await sleep(3000); launch = { state: await d.queryAppState(pkg) }; }   // 4 为前台
        catch (e) { launch = { error: errText(e).slice(0, 300) }; }
      }
      host[name] = { ok: true, session_ms, installed, pkg, launch };
      if (pkg && installed) { await d.removeApp(pkg).catch(() => {}); }   // 下一条地址装的是另一个包，不互相干扰；维基百科包留给后续运行也无妨
    } catch (e) { host[name] = { ok: false, ms: ms(t0), error: errText(e).replace(/\?X-Amz[^ ]*/g, "?<签名已略>").slice(0, 1400) }; }
    finally { if (d) await d.deleteSession().catch(() => {}); }
    log(`主机下载 ${name}: ${JSON.stringify(host[name])}`);
  }
  results.host_app_download = host;
}

// ---- 150 分钟上限探针（清单第 1 项）----
// 每 60 秒：一条轻命令（读标题）加一次 GetRemoteAccessSession；记录每分钟的状态，命令连续失败三次或会话离开 RUNNING 即收尾。
async function capProbe(driver: Driver, sessionArn: string): Promise<void> {
  const maxMin = Number(process.env.SPIKE_CAP_MAX_MIN ?? "165");
  const timeline: Array<Record<string, unknown>> = [];
  const t0 = performance.now();
  let fails = 0;
  // 心跳用 window/rect：两种上下文都实现（title 在 NATIVE_APP 下报资源不存在，首轮因此两分钟就收尾了）
  for (let minute = 0; minute <= maxMin; minute++) {
    const rec: Record<string, unknown> = { minute, at: new Date().toISOString() };
    try { const t1 = performance.now(); rec.rect = await driver.getWindowRect(); rec.cmd_ms = ms(t1); fails = 0; }
    catch (e) { rec.cmd_error = errText(e).slice(0, 200); fails++; }
    try { const g = await df.send(new GetRemoteAccessSessionCommand({ arn: sessionArn })); rec.status = g.remoteAccessSession?.status; rec.message = g.remoteAccessSession?.message?.slice(0, 160); rec.device_minutes = g.remoteAccessSession?.deviceMinutes?.metered; }
    catch (e) { rec.status_error = errText(e).slice(0, 160); }
    timeline.push(rec);
    log(`cap ${minute} min: ${JSON.stringify(rec)}`);
    fs.writeFileSync(path.join(RUN_DIR, "cap-timeline.json"), JSON.stringify(timeline, null, 1));
    if (fails >= 3 || (rec.status && rec.status !== "RUNNING")) break;
    await sleep(60_000);
  }
  results.cap_timeline_minutes = timeline.length;
  results.cap_last = timeline[timeline.length - 1];
  results.cap_elapsed_ms = ms(t0);
}

// ---- 失败形态（清单第 8 项）----
// 三种人为制造的失败：模型名错误（模型侧 4xx）、应用在 AI 步中途被杀、Device Farm 会话在 AI 步中途被外部 Stop。
async function faultSteps(step: Stepper, driver: Driver, sessionArn: string): Promise<void> {
  // F3：应用被外部杀掉——AI 步开始 4 秒后 terminateApp
  const killer = sleep(4000).then(() => driver.terminateApp(APP_PACKAGE)).then(() => log("已在 AI 步中途杀掉应用")).catch((e) => log(`杀应用失败：${errText(e)}`));
  await step("act", "跳过引导：底部有 Skip 就点 Skip；没有就点右下角的蓝色箭头翻到下一页，直到出现 Skip 或 Get started 并点它，进入应用首页");
  await killer;
  await step("bool", "这是维基百科应用的界面（引导页或首页）");
  // F4：模型名错误——另起一个 Agent，只改模型名
  {
    const bogus = new Agent(new AppiumInterface(driver, ""), {
      generateReport: false, persistExecutionDump: false, replanningCycleLimit: 2,
      modelConfig: { MIDSCENE_MODEL_NAME: "us.openai.gpt-does-not-exist", MIDSCENE_MODEL_BASE_URL: getBaseUrl(), MIDSCENE_MODEL_API_KEY: "unused", MIDSCENE_MODEL_FAMILY: modelFamily() },
      createOpenAIClient: async () => new OpenAI({ baseURL: getBaseUrl(), apiKey: "unused", fetch: sigv4Fetch }) as never,
    } as never);
    const t0 = performance.now();
    try { await bogus.aiBoolean("屏幕上有任何内容"); results.fault_bad_model = { ok: true, ms: ms(t0) }; }
    catch (e) { results.fault_bad_model = { ok: false, ms: ms(t0), error: errText(e) }; }
    await bogus.destroy().catch(() => {});
    log(`模型名错误：${JSON.stringify(results.fault_bad_model)}`);
  }
  // F2：会话被外部 Stop——AI 步开始 5 秒后调 StopRemoteAccessSession
  const stopper = sleep(5000).then(() => df.send(new StopRemoteAccessSessionCommand({ arn: sessionArn }))).then(() => { results.fault_external_stop_sent_at = new Date().toISOString(); log("已在 AI 步中途发出 StopRemoteAccessSession"); }).catch((e) => log(`外部 Stop 失败：${errText(e)}`));
  const t0 = performance.now();
  await step("act", "打开应用的 Search 标签并在搜索框输入 OpenAI");
  results.fault_external_stop = { step_ms: ms(t0) };
  await stopper;
  // 会话已死，后续每个 WebDriver 命令各报什么
  const after: Record<string, unknown> = {};
  for (const [name, fn] of [["screenshot", () => driver.takeScreenshot()], ["contexts", () => driver.getContexts()], ["pageSource", () => driver.getPageSource()]] as Array<[string, () => Promise<unknown>]>) {
    const t1 = performance.now();
    try { await fn(); after[name] = { ok: true, ms: ms(t1) }; } catch (e) { after[name] = { ok: false, ms: ms(t1), error: errText(e).slice(0, 300) }; }
  }
  results.fault_after_stop_commands = after;
  log(`外部 Stop 之后：${JSON.stringify(after)}`);
}

// ---- 原生应用上的输入探针（确定性，不调模型；AWS 示例应用 More → Login 页有文本框）----
async function iosAppTypingProbe(driver: Driver, endpoint: string): Promise<void> {
  await driver.switchContext("NATIVE_APP").catch(() => {});
  const tap = async (sel: string) => { const els = await driver.$$(sel); if (!els.length) throw new Error(`找不到 ${sel}`); await els[0].click(); await sleep(1200); };
  await tap("~More");
  await tap("~Login");
  const fields = await driver.$$("-ios class chain:**/XCUIElementTypeTextField");
  results.app_text_fields = fields.length;
  if (!fields.length) { results.ios_typing_probe = "Login 页没有文本框"; return; }
  const field = fields[0];
  const iface = new AppiumInterface(driver, endpoint);
  iface.knownFieldId = field.elementId;
  const report: Array<Record<string, unknown>> = [];
  for (const [name, fn] of iface.typingRoutes("Playwright")) {
    if (name === "web-active-element") continue;   // 原生应用没有网页上下文
    const rec: Record<string, unknown> = { route: name };
    const t0 = performance.now();
    try {
      await field.click(); await sleep(600);        // 每条路线前重新聚焦
      await driver.elementClear(field.elementId).catch(() => {});
      const t1 = performance.now();
      await fn();
      rec.type_ms = ms(t1);
      const value = (await driver.getElementAttribute(field.elementId, "value")) ?? undefined;
      rec.value = value; rec.ok = typeof value === "string" && value.includes("Playwright");
    } catch (e) { rec.error = errText(e); }
    rec.total_ms = ms(t0);
    report.push(rec);
    log(`应用输入探针 ${name}: ${JSON.stringify(rec)}`);
  }
  results.ios_typing_probe = report;
}

// ---- Android 原生应用上的输入探针（确定性，不调模型；维基百科客户端：底部 Search 标签进搜索页，搜索框是 EditText）----
async function androidAppTypingProbe(driver: Driver): Promise<void> {
  await driver.switchContext("NATIVE_APP").catch(() => {});
  const report: Array<Record<string, unknown>> = [];
  // 搜索框的类名随实现变（EditText / AutoCompleteTextView / SearchAutoComplete），按类名正则找，找不到再取当前持有焦点的控件
  let fields = await driver.$$("android=new UiSelector().classNameMatches(\".*(EditText|AutoCompleteTextView|SearchAutoComplete).*\")");
  if (!fields.length) fields = await driver.$$("android=new UiSelector().focused(true)");
  results.app_text_fields = fields.length;
  if (!fields.length) {
    const src = await driver.getPageSource();
    results.android_typing_probe = { error: "搜索页没找到输入控件", classes: [...new Set([...src.matchAll(/class="([^"]+)"/g)].map((m) => m[1]))].slice(0, 30), report };
    log(`Android 应用输入探针：没找到输入控件，页面类名 ${JSON.stringify(results.android_typing_probe)}`);
    return;
  }
  const field = fields[0];
  const routes: Array<[string, () => Promise<void>]> = [
    ["direct-element-sendkeys", async () => { await driver.elementSendKeys(field.elementId, "Playwright"); }],
    ["native-active-element", async () => { const ref = await driver.getActiveElement(); await driver.elementSendKeys(elementId(ref), "Playwright"); }],
    ["mobile-type", async () => { await driver.execute("mobile: type", { text: "Playwright" }); }],
  ];
  for (const [name, fn] of routes) {
    const rec: Record<string, unknown> = { route: name };
    const t0 = performance.now();
    try {
      await field.click(); await sleep(500); await driver.elementClear(field.elementId).catch(() => {});
      const t1 = performance.now(); await fn(); rec.type_ms = ms(t1);
      const value = await field.getText(); rec.value = value; rec.ok = typeof value === "string" && value.includes("Playwright");
    } catch (e) { rec.error = errText(e); }
    rec.total_ms = ms(t0); report.push(rec); log(`Android 应用输入探针 ${name}: ${JSON.stringify(rec)}`);
  }
  results.android_typing_probe = report;
}

// ---- 两个场景的 AI 步 ----
type Stepper = (kind: "act" | "bool", prompt: string) => Promise<unknown>;
async function webSteps(step: Stepper, probe?: () => Promise<void>): Promise<void> {
  await step("bool", "这是维基百科上 OpenAI 的词条页");
  await step("act", "点击维基百科页面上的搜索图标（放大镜）");
  await step("bool", "页面上出现了可输入的搜索框");
  if (probe) await probe().catch((e) => { results.ios_typing_probe_error = errText(e); log(`输入探针整体失败（继续）：${results.ios_typing_probe_error}`); });
  await step("act", "在搜索框输入 Playwright 并点击搜索结果里的 Playwright 条目");
  await step("bool", "当前页面是 Playwright 的维基百科词条页");
  await step("bool", "页面顶部有一条红色横幅写着本站已永久关闭");  // 刻意为假：量判否路径
}
// AWS Device Farm 的 iOS 示例应用（aws-device-farm-sample-app-for-ios 预构建 IPA）：标签栏加多种控件的演示页
async function iosSampleAppSteps(step: Stepper): Promise<void> {
  if (await step("bool", "屏幕上有系统弹窗（权限请求或提示）") === true) await step("act", "关闭系统弹窗（点 Don't Allow、OK 或 Not Now）");
  await step("bool", "这是 AWS Device Farm 示例应用的首页，底部标签栏里有 Home、HTTP、Native、Inputs、More");
  // 第一轮实测：Inputs 标签是十页横向分页（第一页是 textview），点页码圆点不翻页；按真实结构写
  await step("act", "点击底部的 Inputs 标签，然后在示例卡片上向左滑动翻页，直到出现带 Text Field 文本输入框的页面为止，点进第一个输入框并输入 Playwright");
  await step("bool", "某个文本输入框里显示着 Playwright");
  await step("act", "点击底部的 More 标签，点 Alerts，再点能弹出 alert 的按钮");
  await step("bool", "屏幕上出现了一个弹窗（alert），带标题与 OK 按钮");
  await step("bool", "屏幕顶部有一条红色横幅写着本应用已永久下线");  // 刻意为假：量判否路径
}
// 高德地图（com.autonavi.minimap）：首启有隐私协议与权限弹窗；量搜索与地图瓦片在美国机群上的表现
async function amapSteps(step: Stepper): Promise<void> {
  for (let i = 0; i < 3; i++) {
    const dlg = await step("bool", "屏幕上有隐私政策、用户协议或系统权限请求弹窗");
    if (dlg !== true) break;
    await step("act", "关闭当前弹窗：隐私协议点同意或同意并继续；系统权限点仅在使用中允许或允许；其它提示点知道了或关闭");
  }
  await step("bool", "这是高德地图首页，能看到地图画面与顶部的搜索框");
  await step("bool", "地图瓦片已经加载出来，能看到道路、地名或建筑轮廓，而不是空白或灰色格子");
  await step("act", "点击顶部搜索框，输入 北京南站，然后点击搜索结果列表里的第一条");
  await step("bool", "屏幕上显示了北京南站的位置详情卡片或地图上有北京南站的标注");
  await step("bool", "屏幕顶部有一条红色横幅写着本应用已永久下线");  // 刻意为假：量判否路径
}
// 任意未知包名的应用：关弹窗、确认到了首页、找搜索入口搜一个词；给后续换被测应用（如别的国内应用）直接用
async function genericAppSteps(step: Stepper): Promise<void> {
  for (let i = 0; i < 3; i++) {
    const dlg = await step("bool", "屏幕上有隐私政策、用户协议、系统权限请求或广告弹窗");
    if (dlg !== true) break;
    await step("act", "关闭当前弹窗：协议类点同意或同意并继续；系统权限点仅在使用中允许或允许；广告与提示点关闭、跳过或知道了");
  }
  await step("bool", "当前显示的是这个应用自己的首页，不是系统桌面、启动页或登录墙");
  await step("act", "找到应用里的搜索入口，输入 北京 并发起搜索");
  await step("bool", "屏幕上出现了与「北京」相关的搜索结果");
  await step("bool", "屏幕顶部有一条红色横幅写着本应用已永久下线");  // 刻意为假：量判否路径
}
async function appSteps(step: Stepper, probe?: () => Promise<void>): Promise<void> {
  // 首次启动有引导页（Skip / Continue）与可能的系统权限弹窗；先问再动，避免条件式动作提示
  if (await step("bool", "屏幕上有系统权限请求弹窗（如允许通知）") === true) await step("act", "点击不允许或 Don't allow 关闭系统弹窗");
  if (await step("bool", "这是维基百科应用的引导页（欢迎页或介绍页，底部有翻页箭头、Skip 或 Continue 按钮）") === true) await step("act", "跳过引导：底部有 Skip 就点 Skip；没有就点右下角的蓝色箭头翻到下一页，直到出现 Skip 或 Get started 并点它，进入应用首页");
  if (await step("bool", "屏幕上有系统权限请求弹窗（如允许通知）") === true) await step("act", "点击不允许或 Don't allow 关闭系统弹窗");
  // 第一轮实测：首页顶部没有搜索栏（搜索是底部标签），精确命中「Playwright」打开的是剧作家词条；两条断言按真实界面改写
  await step("bool", "这是维基百科应用的首页，底部导航栏里有 Search 标签");
  if (PLATFORM === "android" && process.env.DF_ANDROID_TYPING_PROBE === "1") {
    await step("act", "点击底部的 Search 标签，然后点击搜索框让它获得焦点");
    if (probe) await probe().catch((e) => { results.android_typing_probe_error = errText(e); log(`Android 应用输入探针整体失败：${results.android_typing_probe_error}`); });
  }
  await step("act", "点击底部的 Search 标签，在搜索框输入 Playwright，然后点击搜索结果中标题为 Playwright (software) 的那一条");
  await step("bool", "当前打开的词条标题是 Playwright (software)，正文提到浏览器自动化或 Microsoft");
  await step("bool", "屏幕顶部有一条红色横幅写着本站已永久关闭");  // 刻意为假：量判否路径
}

// ---- 隧道「令牌换 cookie」预热探针（SPIKE_SCENARIO=warmup）----
// 跳板机上 ngrok 以 /tmp/measure 的流量策略暴露上游：预热路径凭令牌下发 __Host- 前缀的会话 cookie 并返回带标记的页面，
// 页面脚本再向校验路径发一次只凭 cookie 放行的请求，成功后把标记改成 READY。探针不依赖网页上下文：标记从原生控件树里读。
const MARKERS = [
  "GHERKAI TUNNEL READY", "GHERKAI TUNNEL DENIED", "GHERKAI TUNNEL ERROR", "GHERKAI TUNNEL WARMUP", "GHERKAI TUNNEL AUTH REQUIRED",
  "GHERKAI UPSTREAM INDEX", "TUNNEL-COOKIE-PRESENT", "TUNNEL-COOKIE-ABSENT", "GHERKAI POST RECEIVED", "GHERKAI POST PROBE GET",
  "GHERKAI UPSTREAM 404", "GHERKAI NEWTAB", "GHERKAI TAB2", "GHERKAI SLOW DONE", "Visit Site", "ngrok",
];
async function webCtxOf(driver: Driver): Promise<string | undefined> {
  const cs = (await driver.getContexts()) as string[];
  return cs.find((c) => c !== "NATIVE_APP");
}
// 「可用」= 切进去后 5 秒内能读回标题（iOS 26.3 列得出 WEBVIEW、切换也成功，但任何网页命令都挂住）
async function usableWebCtx(driver: Driver): Promise<string | undefined> {
  const web = await webCtxOf(driver).catch(() => undefined);
  if (!web) return undefined;
  try {
    await driver.switchContext(web);
    const ok = await Promise.race([driver.getTitle().then(() => true), sleep(5000).then(() => false)]);
    return ok ? web : undefined;
  } catch { return undefined; } finally { await driver.switchContext("NATIVE_APP").catch(() => {}); }
}
async function nativeMarkers(driver: Driver): Promise<{ found: string[]; kb: number; ms: number }> {
  const cur = (await driver.getContext()) as string;
  if (cur !== "NATIVE_APP") await driver.switchContext("NATIVE_APP");
  const t0 = performance.now();
  const src = await driver.getPageSource();
  return { found: MARKERS.filter((m) => src.includes(m)), kb: Math.round(src.length / 1024), ms: ms(t0) };
}
async function waitMarkers(driver: Driver, want: string[], timeoutMs: number): Promise<Record<string, unknown>> {
  const t0 = performance.now(); let polls = 0; let last: { found: string[]; kb: number; ms: number } = { found: [], kb: 0, ms: 0 };
  while (ms(t0) < timeoutMs) {
    polls++;
    try { last = await nativeMarkers(driver); } catch (e) { return { hit: null, error: errText(e), waited: ms(t0), polls }; }
    const hit = want.find((w) => last.found.includes(w));
    if (hit) return { hit, found: last.found, waited: ms(t0), polls, source_kb: last.kb, source_ms: last.ms };
    await sleep(1000);
  }
  return { hit: null, found: last.found, waited: ms(t0), polls, source_kb: last.kb };
}
async function navigateTo(driver: Driver, target: string, route: "url" | "deeplink"): Promise<Record<string, unknown>> {
  const t0 = performance.now();
  try {
    if (route === "deeplink") {
      await driver.switchContext("NATIVE_APP").catch(() => {});
      await driver.execute("mobile: deepLink", PLATFORM === "ios" ? { url: target, bundleId: "com.apple.mobilesafari" } : { url: target, package: "com.android.chrome" });
    } else {
      const web = await webCtxOf(driver);
      if (!web) throw new Error("没有网页上下文，url 路线不可用");
      await driver.switchContext(web);
      try { await driver.url(target); } finally { await driver.switchContext("NATIVE_APP").catch(() => {}); }
    }
    return { route, ms: ms(t0) };
  } catch (e) { return { route, ms: ms(t0), error: errText(e) }; }
}
async function webTitle(driver: Driver): Promise<unknown> {
  const web = await webCtxOf(driver).catch(() => undefined);
  if (!web) return null;
  try { await driver.switchContext(web); return await driver.getTitle(); } catch (e) { return { error: errText(e).slice(0, 200) }; } finally { await driver.switchContext("NATIVE_APP").catch(() => {}); }
}
async function shot(driver: Driver, name: string): Promise<void> {
  try { fs.writeFileSync(path.join(RUN_DIR, name), Buffer.from(await driver.takeScreenshot(), "base64")); } catch { /* 截图失败不影响探针 */ }
}
const warmupUrl = (token: string) => `${TUNNEL_BASE}/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=${token}`;
// 预热核心：导航预热地址、等标记；给 warmup 与 timeouts 两个场景共用
async function warmupCore(driver: Driver, route: "url" | "deeplink"): Promise<Record<string, unknown>> {
  if (!TUNNEL_BASE || !TUNNEL_TOKEN) throw new Error("需要 DF_TUNNEL_BASE 与 DF_TUNNEL_TOKEN");
  const nav = await navigateTo(driver, warmupUrl(TUNNEL_TOKEN), route);
  const wait = await waitMarkers(driver, ["GHERKAI TUNNEL READY", "GHERKAI TUNNEL DENIED", "GHERKAI TUNNEL ERROR", "GHERKAI TUNNEL AUTH REQUIRED", "Visit Site"], 25_000);
  const title = await webTitle(driver);
  await shot(driver, "warmup.png");
  log(`预热（${route}）：导航 ${JSON.stringify(nav)} 标记 ${JSON.stringify(wait)} 标题 ${JSON.stringify(title)}`);
  return { nav, wait, title };
}
async function warmupProbe(driver: Driver): Promise<void> {
  const rec: Record<string, unknown> = { route: WARMUP_ROUTE }; results.warmup = rec;
  rec.contexts_initial = await driver.getContexts().catch((e) => errText(e));
  if (PLATFORM === "ios") rec.ios_contexts_initial = await driver.execute("mobile: getContexts").catch((e) => errText(e).slice(0, 300));
  // 1. 预热
  rec.warmup = await warmupCore(driver, WARMUP_ROUTE);
  // 2. 业务页：cookie 应放行，页面显示 cookie 是否到达上游
  rec.index_nav = await navigateTo(driver, `${TUNNEL_BASE}/`, WARMUP_ROUTE);
  rec.index_wait = await waitMarkers(driver, ["GHERKAI UPSTREAM INDEX", "GHERKAI TUNNEL AUTH REQUIRED", "Visit Site"], 25_000);
  await shot(driver, "index.png");
  log(`业务页：${JSON.stringify(rec.index_wait)}`);
  // 3. 负例：错令牌 → 401 页；之后业务页仍应放行（cookie 未被破坏）
  rec.wrong_token_nav = await navigateTo(driver, warmupUrl("wrong-token"), WARMUP_ROUTE);
  rec.wrong_token_wait = await waitMarkers(driver, ["GHERKAI TUNNEL AUTH REQUIRED", "GHERKAI TUNNEL READY", "Visit Site"], 20_000);
  rec.index_after_wrong_nav = await navigateTo(driver, `${TUNNEL_BASE}/`, WARMUP_ROUTE);
  rec.index_after_wrong_wait = await waitMarkers(driver, ["GHERKAI UPSTREAM INDEX", "GHERKAI TUNNEL AUTH REQUIRED"], 20_000);
  log(`错令牌：${JSON.stringify(rec.wrong_token_wait)}；之后业务页：${JSON.stringify(rec.index_after_wrong_wait)}`);
  // 4. 跨站 POST 回跳（SameSite=None 的收益）：从第三方站点的页面提交表单到隧道域；需要网页上下文执行脚本
  rec.usable_web_ctx = await usableWebCtx(driver);
  const web = rec.usable_web_ctx as string | undefined;
  if (web) {
    try {
      await driver.switchContext(web);
      await driver.url(XSITE_ORIGIN);
      rec.contexts_on_xsite = await driver.getContexts();
      await driver.execute(
        "var f=document.createElement('form');f.method='POST';f.action=arguments[0];var i=document.createElement('input');i.name='a';i.value='xsite';f.appendChild(i);document.body.appendChild(f);f.submit();",
        `${TUNNEL_BASE}/post-probe`,
      );
      await driver.switchContext("NATIVE_APP").catch(() => {});
      rec.xsite_post_wait = await waitMarkers(driver, ["GHERKAI POST RECEIVED", "GHERKAI TUNNEL AUTH REQUIRED", "Visit Site"], 20_000);
      await shot(driver, "xsite-post.png");
    } catch (e) { rec.xsite_post_error = errText(e); await driver.switchContext("NATIVE_APP").catch(() => {}); }
  } else rec.xsite_post_wait = "跳过：无可用网页上下文，无法从第三方页面提交表单";
  log(`跨站 POST：${JSON.stringify(rec.xsite_post_wait ?? rec.xsite_post_error)}`);
  // 6. 切到别的应用再切回，会话 cookie 是否保留
  try {
    if (PLATFORM === "ios") { await driver.execute("mobile: pressButton", { name: "home" }); await sleep(3000); await driver.activateApp("com.apple.mobilesafari"); }
    else { await driver.execute("mobile: pressKey", { keycode: 3 }); await sleep(3000); await driver.activateApp("com.android.chrome"); }
    await sleep(1500);
    rec.index_after_appswitch_nav = await navigateTo(driver, `${TUNNEL_BASE}/`, WARMUP_ROUTE);
    rec.index_after_appswitch_wait = await waitMarkers(driver, ["GHERKAI UPSTREAM INDEX", "GHERKAI TUNNEL AUTH REQUIRED"], 20_000);
  } catch (e) { rec.appswitch_error = errText(e); }
  log(`切应用后业务页：${JSON.stringify(rec.index_after_appswitch_wait ?? rec.appswitch_error)}`);
  // 5. target=_blank 后的网页上下文候选数（iOS 的 WEBVIEW 身份问题）
  rec.newtab_nav = await navigateTo(driver, `${TUNNEL_BASE}/newtab`, WARMUP_ROUTE);
  await waitMarkers(driver, ["GHERKAI NEWTAB"], 15_000);
  rec.contexts_before_newtab = await driver.getContexts().catch((e) => errText(e));
  try {
    const web2 = await usableWebCtx(driver);
    if (web2) { await driver.switchContext(web2); await driver.execute("document.getElementById('lnk').click()"); await driver.switchContext("NATIVE_APP").catch(() => {}); rec.newtab_click = "web ctx script"; }
    else { const el = await driver.$(PLATFORM === "ios" ? '-ios predicate string:label == "OPEN TAB2"' : 'android=new UiSelector().text("OPEN TAB2")'); await el.click(); rec.newtab_click = "native tap"; }
  } catch (e) { rec.newtab_click = { error: errText(e).slice(0, 200) }; }
  await sleep(3000);
  rec.contexts_after_newtab = await driver.getContexts().catch((e) => errText(e));
  if (PLATFORM === "ios") rec.ios_contexts_after_newtab = await driver.execute("mobile: getContexts").catch((e) => errText(e).slice(0, 400));
  rec.markers_after_newtab = await nativeMarkers(driver).catch((e) => errText(e));
  log(`新标签页：点击 ${JSON.stringify(rec.newtab_click)} 上下文 ${JSON.stringify(rec.contexts_after_newtab)}`);
}

// ---- 超时分层探针（SPIKE_SCENARIO=timeouts）----
// (a) 同一会话挂两个客户端实例、各设单请求超时，看哪个生效（webdriver 10 按 sessionId 共享 dispatcher）；
// (b) W3C pageLoad 是否在网页上下文生效、超时后的错误形态与会话可用性；
// (c) appium:newCommandTimeout（caps 里按 DF_NCT 调小）在长命令执行期间是否计时，到期后能否再 newSession。
async function timeoutsProbe(driver: Driver, endpoint: string, sessionArn: string): Promise<void> {
  const rec: Record<string, unknown> = { nct_s: NCT_S }; results.timeouts = rec;
  rec.warmup = await warmupCore(driver, WARMUP_ROUTE);
  const web = await webCtxOf(driver);
  if (!web) { rec.skipped = "无网页上下文：慢导航类探针读不回结果"; return; }
  await driver.switchContext(web);
  const u = new URL(endpoint);
  const slow = (s: number) => `${TUNNEL_BASE}/slow?s=${s}`;
  const run = async (label: string, fn: () => Promise<unknown>) => { const t0 = performance.now(); try { await fn(); rec[label] = { ms: ms(t0), outcome: "完成" }; } catch (e) { rec[label] = { ms: ms(t0), error: errText(e).slice(0, 300) }; } log(`${label}: ${JSON.stringify(rec[label])}`); };
  // (a)
  try {
    const b = await attach({
      sessionId: driver.sessionId, capabilities: (driver as unknown as { capabilities: Record<string, unknown> }).capabilities,
      protocol: u.protocol.replace(":", ""), hostname: u.hostname, port: u.port ? Number(u.port) : 443, path: u.pathname + u.search,
      logLevel: "warn", connectionRetryTimeout: 3000, connectionRetryCount: 0,
    } as never);
    await run("a_attached_client_3s_timeout_slow8", () => b.url(slow(8)));
  } catch (e) { rec.a_attach_error = errText(e); }
  await run("a_primary_client_default_timeout_slow8", () => driver.url(slow(8)));
  // (b)
  await driver.setTimeout({ pageLoad: 3000 }).catch((e) => { rec.b_set_pageload_error = errText(e); });
  rec.b_timeouts_read = await driver.getTimeouts().catch((e) => errText(e));
  await run("b_pageload_3s_slow10", () => driver.url(slow(10)));
  rec.b_usable_after = await driver.getTitle().then((t) => ({ title: t })).catch((e) => ({ error: errText(e).slice(0, 200) }));
  await driver.setTimeout({ pageLoad: 300_000 }).catch(() => {});
  // (c)
  await run(`c_long_command_${NCT_S + 10}s_with_nct_${NCT_S}s`, () => driver.url(slow(NCT_S + 10)));
  rec.c_after_long_command = await driver.getTitle().then((t) => ({ title: t })).catch((e) => ({ error: errText(e).slice(0, 200) }));
  await sleep((NCT_S + 5) * 1000);
  rec.c_after_idle = await driver.getTitle().then((t) => ({ title: t })).catch((e) => ({ error: errText(e).slice(0, 200) }));
  rec.c_remote_session_status = (await df.send(new GetRemoteAccessSessionCommand({ arn: sessionArn }))).remoteAccessSession?.status;
  await run("c_renew_session", async () => { const d2 = await connect(endpoint); rec.c_renew_session_id = d2.sessionId; await d2.deleteSession().catch(() => {}); });
}
// newSession 的客户端超时（2 秒）先触发时，服务端是否仍把会话建出来、随后正常 newSession 是否受影响
async function newSessionTimeoutProbe(endpoint: string): Promise<void> {
  const rec: Record<string, unknown> = {}; results.newsession_probe = rec;
  const u = new URL(endpoint); const base = endpoint.replace(/\/$/, "");
  const listSessions = async () => {
    const out: Record<string, unknown> = {};
    for (const r of ["sessions", "appium/sessions"]) { try { const res = await fetch(`${base}/${r}`); out[r] = { status: res.status, body: (await res.text()).slice(0, 400) }; } catch (e) { out[r] = errText(e).slice(0, 200); } }
    return out;
  };
  rec.sessions_before = await listSessions();
  const t0 = performance.now();
  try {
    const d = await remote({ protocol: u.protocol.replace(":", ""), hostname: u.hostname, port: u.port ? Number(u.port) : 443, path: u.pathname + u.search, logLevel: "warn", connectionRetryTimeout: 2000, connectionRetryCount: 0, capabilities: caps() });
    rec.short_timeout_newsession = { ms: ms(t0), outcome: "2 秒内居然成功", sessionId: d.sessionId }; await d.deleteSession().catch(() => {});
  } catch (e) { rec.short_timeout_newsession = { ms: ms(t0), error: errText(e).slice(0, 300) }; }
  rec.sessions_right_after = await listSessions();
  await sleep(75_000);
  rec.sessions_after_75s = await listSessions();
  log(`newSession 客户端超时探针：${JSON.stringify(rec).slice(0, 900)}`);
}

// ---- 会话释放探针（SPIKE_SCENARIO=release，不走通用主流程）----
// 会话名长度与同名、按名列举的可见时延、排队中撤回是否计费、并行 Stop 与 Get 的耗时、Stop 返回体、重复 Stop 与 Stop 后 deleteSession 的报错形态、
// 有无 deleteSession 两种收尾下的产物（录像、日志）与 deviceMinutes。
async function releaseProbe(project: string): Promise<void> {
  const rec: Record<string, unknown> = {}; results.release = rec;
  const create = (name: string) => df.send(new CreateRemoteAccessSessionCommand({ projectArn: project, deviceArn: DEVICE_ARN, name, configuration: { billingMethod: "METERED" } }));
  const listByName = async (name: string) => (await df.send(new ListRemoteAccessSessionsCommand({ arn: project }))).remoteAccessSessions?.filter((s) => s.name === name).map((s) => ({ arn: s.arn?.slice(-12), status: s.status })) ?? [];
  const stop = async (arn: string) => { const t0 = performance.now(); const r = await df.send(new StopRemoteAccessSessionCommand({ arn })); return { ms: ms(t0), returned_status: r.remoteAccessSession?.status, returned_device_minutes: r.remoteAccessSession?.deviceMinutes, returned_keys: Object.keys(r.remoteAccessSession ?? {}) }; };
  const waitRunning = async (arn: string) => {
    const t0 = performance.now();
    for (;;) {
      const s = (await df.send(new GetRemoteAccessSessionCommand({ arn }))).remoteAccessSession!;
      if (s.status === "RUNNING" && s.endpoints?.remoteDriverEndpoint) return { ms: ms(t0), endpoint: s.endpoints.remoteDriverEndpoint, created: s.created, started: s.started };
      if (["COMPLETED", "STOPPING", "ERRORED", "FAILED"].includes(s.status!)) throw new Error(`会话 ${s.status} ${s.message ?? ""}`);
      if (ms(t0) > 15 * 60_000) throw new Error("15 分钟未 RUNNING");
      await sleep(5000);
    }
  };
  const waitDone = async (arn: string) => {
    const t0 = performance.now();
    for (;;) {
      const s = (await df.send(new GetRemoteAccessSessionCommand({ arn }))).remoteAccessSession!;
      if (s.status === "COMPLETED" || ms(t0) > 6 * 60_000) {
        const arts: Record<string, unknown> = {};
        for (const type of ["FILE", "LOG", "SCREENSHOT"] as const) { try { arts[type] = ((await df.send(new ListArtifactsCommand({ arn, type }))).artifacts ?? []).map((x) => `${x.type}:${x.name}.${x.extension}`); } catch (e) { arts[type] = errText(e).slice(0, 120); } }
        return { ms_to_completed: ms(t0), status: s.status, device_minutes: s.deviceMinutes, created: s.created, started: s.started, stopped: s.stopped, artifacts: arts };
      }
      await sleep(10_000);
    }
  };
  // 1. 名字长度与排队中撤回
  const long256 = "spike06-release-" + "x".repeat(256 - 16);
  let pendingArn: string | undefined;
  try { const r = await create(long256); pendingArn = r.remoteAccessSession!.arn!; rec.name_256 = { ok: true, status: r.remoteAccessSession!.status }; } catch (e) { rec.name_256 = { error: errText(e).slice(0, 200) }; }
  try { const r = await create(long256 + "y"); rec.name_257 = { ok: true }; await df.send(new StopRemoteAccessSessionCommand({ arn: r.remoteAccessSession!.arn! })).catch(() => {}); } catch (e) { rec.name_257 = { error: errText(e).slice(0, 200) }; }
  if (pendingArn) { try { rec.pending_stop = await stop(pendingArn); } catch (e) { rec.pending_stop = { error: errText(e).slice(0, 200) }; } }
  log(`名字：256 ${JSON.stringify(rec.name_256)} 257 ${JSON.stringify(rec.name_257)} 排队中撤回 ${JSON.stringify(rec.pending_stop)}`);
  // 2. 同名并行创建与按名可见时延
  const name = `spike06-release-${Date.now()}`;
  const t0c = performance.now();
  const [a, b] = await Promise.all([create(name), create(name)]);
  rec.same_name_parallel = { ms: ms(t0c), statuses: [a.remoteAccessSession!.status, b.remoteAccessSession!.status] };
  const arns = [a.remoteAccessSession!.arn!, b.remoteAccessSession!.arn!];
  const tv = performance.now(); let seen: unknown[] = [];
  for (let i = 0; i < 30; i++) { seen = await listByName(name); if (seen.length >= 2) break; await sleep(1000); }
  rec.list_by_name = { ms: ms(tv), count: seen.length, seen };
  log(`同名并行创建 ${JSON.stringify(rec.same_name_parallel)}；按名可见 ${JSON.stringify(rec.list_by_name)}`);
  // 3. 等 RUNNING、各连一次 Appium、A 先 deleteSession，再并行 Stop
  const [ra, rb] = await Promise.all(arns.map(waitRunning));
  rec.running = { a: { ms: ra.ms, created: ra.created, started: ra.started }, b: { ms: rb.ms, created: rb.created, started: rb.started } };
  const [da, db] = await Promise.all([connect(ra.endpoint), connect(rb.endpoint)]);
  await Promise.all([da, db].map((d) => d.takeScreenshot().catch(() => "")));
  const tdel = performance.now(); await da.deleteSession().catch((e) => { rec.a_delete_error = errText(e).slice(0, 200); }); rec.a_delete_ms = ms(tdel);
  const [sa, sb] = await Promise.all([stop(arns[0]), stop(arns[1])]);
  rec.stop = { a_after_delete: sa, b_without_delete: sb };
  const tget = performance.now(); const ga = (await df.send(new GetRemoteAccessSessionCommand({ arn: arns[0] }))).remoteAccessSession!;
  rec.get_right_after_stop = { ms: ms(tget), status: ga.status, device_minutes: ga.deviceMinutes, stopped: ga.stopped };
  try { rec.duplicate_stop = await stop(arns[0]); } catch (e) { rec.duplicate_stop = { error: errText(e).slice(0, 300) }; }
  try { await db.deleteSession(); rec.b_delete_after_stop = "ok"; } catch (e) { rec.b_delete_after_stop = errText(e).slice(0, 300); }
  log(`Stop ${JSON.stringify(rec.stop)}；Get ${JSON.stringify(rec.get_right_after_stop)}；重复 Stop ${JSON.stringify(rec.duplicate_stop)}`);
  // 4. 到 COMPLETED 的时长、计量、时间戳与产物
  const [ca, cb] = await Promise.all([waitDone(arns[0]), waitDone(arns[1])]);
  rec.completed = { a_with_delete: ca, b_without_delete: cb };
  if (pendingArn) rec.pending_stop_final = await waitDone(pendingArn);
  log(`完成：${JSON.stringify(rec.completed).slice(0, 1200)}`);
}

// ---- 深层链接探针：应用目标上含网址的 step 能否用 mobile: deepLink 把被测应用带到某一页 ----
// 每个用例记录命令结果与耗时、之后的前台应用、页面上是否出现目标内容（轮询原生控件树）。只用原生上下文。
// Android：被测应用为维基百科客户端（DF_APP_ARN 给出上传），覆盖指定包名、连续两次、后台、冷启动、应用不处理的网址、
//          同域名错误路径、不指定包名的系统分发对照、自定义 scheme。
// iOS：没有注册了 scheme 的第三方安装包，用系统「地图」验证同一机制；iOS 15.8 上只记录「不支持」的确切报错形态。
async function foreground(driver: Driver): Promise<Record<string, unknown>> {
  if (PLATFORM === "ios") {
    const info = await driver.execute("mobile: activeAppInfo").catch((e) => ({ error: errText(e) })) as Record<string, unknown>;
    return { bundleId: info.bundleId, name: info.name, error: info.error };
  }
  return {
    package: await driver.getCurrentPackage().catch((e) => `ERR ${errText(e).slice(0, 120)}`),
    activity: await driver.getCurrentActivity().catch((e) => `ERR ${errText(e).slice(0, 120)}`),
  };
}
async function waitMarker(driver: Driver, marker: string | undefined, maxMs: number): Promise<{ hit: boolean; ms: number; source_kb: number; texts: string[] }> {
  const t0 = performance.now();
  let last = "";
  for (;;) {
    last = await driver.getPageSource().catch(() => "");
    if (marker && last.includes(marker)) break;
    if (ms(t0) > maxMs) break;
    await sleep(1000);
  }
  const attr = PLATFORM === "ios" ? / (?:label|name|value)="([^"]{2,60})"/g : / text="([^"]{2,60})"/g;
  return { hit: !!marker && last.includes(marker), ms: ms(t0), source_kb: Math.round(last.length / 1024), texts: [...new Set([...last.matchAll(attr)].map((m) => m[1]))].slice(0, 12) };
}
async function deeplinkCase(driver: Driver, name: string, args: Record<string, unknown>, marker?: string, prep?: () => Promise<unknown>): Promise<void> {
  const rec: Record<string, unknown> = { name, args };
  if (prep) rec.prep = await prep().then(() => "ok").catch((e) => errText(e).slice(0, 200));
  rec.fg_before = await foreground(driver);
  const t0 = performance.now();
  try { rec.result = await driver.execute("mobile: deepLink", args) ?? "ok"; rec.ok = true; } catch (e) { rec.ok = false; rec.error = errText(e); }
  rec.call_ms = ms(t0);
  rec.marker = marker ? { text: marker, ...(await waitMarker(driver, marker, 12_000)) } : await waitMarker(driver, undefined, 0);
  rec.fg_after = await foreground(driver);
  if (PLATFORM === "android") rec.app_state = await driver.queryAppState(APP_PACKAGE).catch((e) => errText(e).slice(0, 120));
  ((results.deeplink ??= []) as unknown[]).push(rec);
  log(`deepLink ${name}: ok=${rec.ok} ${rec.call_ms} ms marker=${JSON.stringify((rec.marker as { hit?: boolean }).hit)} fg=${JSON.stringify(rec.fg_after)} ${rec.error ? "ERR " + String(rec.error).slice(0, 200) : ""}`);
}
// 第二轮（DF_DL_ROUND=2）：Android 补测网址里 shell 特殊字符的处置与替代路线；iOS 用注册了自定义 scheme 的未签名示例包
// （Device Farm 安装时重签），DF_APP_PACKAGE 给 bundle id。iOS 15.8 只记第一个用例的报错形态，不带 bundleId 的调用在该版本上挂住。
async function deeplinkRound2(driver: Driver, sessionArn: string, appArn: string | undefined): Promise<void> {
  const pkg = APP_PACKAGE;
  if (appArn) await installApp(driver, sessionArn, appArn);
  await timed("app_activate", () => driver.activateApp(pkg));
  await sleep(4000);
  results.deeplink_launch = { fg: await foreground(driver), view: await waitMarker(driver, undefined, 0) };
  if (PLATFORM === "android") {
    const home = () => driver.execute("mobile: pressKey", { keycode: 3 });
    await deeplinkCase(driver, "encoded_parens", { url: "https://en.wikipedia.org/wiki/Selenium_%28software%29", package: pkg }, "Testing framework");
    await deeplinkCase(driver, "ampersand_query", { url: "https://en.wikipedia.org/wiki/Cucumber?x=1&y=2", package: pkg }, "Cucumber", async () => { await home(); await sleep(2000); });
    await deeplinkCase(driver, "single_quoted_parens", { url: "'https://en.wikipedia.org/wiki/Gherkin_(language)'", package: pkg }, "Gherkin");
    // 替代路线：mobile: startActivity 带 action / uri / package，看转义是否同样经过两层 shell
    {
      const rec: Record<string, unknown> = { name: "start_activity_parens_ampersand" };
      rec.fg_before = await foreground(driver);
      const t0 = performance.now();
      try { await driver.execute("mobile: startActivity", { intent: `${pkg}/.page.PageActivity`, action: "android.intent.action.VIEW", uri: "https://en.wikipedia.org/wiki/Selenium_(software)?a=1&b=2", wait: true }); rec.ok = true; } catch (e) { rec.ok = false; rec.error = errText(e); }
      rec.call_ms = ms(t0); rec.marker = { text: "Testing framework", ...(await waitMarker(driver, "Testing framework", 10_000)) }; rec.fg_after = await foreground(driver);
      ((results.deeplink ??= []) as unknown[]).push(rec); log(`startActivity: ok=${rec.ok} ${rec.error ? String(rec.error).slice(0, 300) : ""}`);
    }
    await deeplinkCase(driver, "cold_start", { url: "https://en.wikipedia.org/wiki/Cucumber", package: pkg }, "Cucumber", async () => { await driver.terminateApp(pkg); await sleep(2000); });
    await deeplinkCase(driver, "custom_scheme_with_package", { url: "wikipedia://en.wikipedia.org/wiki/Appium", package: pkg }, "Appium");
    await deeplinkCase(driver, "system_dispatch_handled_no_package", { url: "https://en.wikipedia.org/wiki/Appium" }, "Appium", async () => { await home(); await sleep(2000); });
    return;
  }
  const home = () => driver.execute("mobile: pressButton", { name: "home" });
  await deeplinkCase(driver, "custom_scheme_with_bundle", { url: "gherkaispike://item/42", bundleId: pkg });
  if ((results.deeplink as Array<{ ok: boolean }>)[0].ok === false) return;
  await deeplinkCase(driver, "custom_scheme_query_ampersand", { url: "gherkaispike://item/42?x=1&y=(2)", bundleId: pkg });
  await deeplinkCase(driver, "from_background", { url: "gherkaispike://item/43", bundleId: pkg }, undefined, async () => { await home(); await sleep(2500); });
  await deeplinkCase(driver, "cold_start", { url: "gherkaispike://item/44", bundleId: pkg }, undefined, async () => { await driver.terminateApp(pkg); await sleep(2000); });
  await deeplinkCase(driver, "unhandled_https_with_bundle", { url: "https://www.example.com/", bundleId: pkg });
  await deeplinkCase(driver, "unhandled_scheme_with_bundle", { url: "otherspike://x", bundleId: pkg });
  await deeplinkCase(driver, "system_dispatch_custom_no_bundle", { url: "gherkaispike://item/45" }, undefined, async () => { await home(); await sleep(2000); });
  await deeplinkCase(driver, "safari_baseline_with_bundle", { url: "https://en.m.wikipedia.org/wiki/Appium", bundleId: "com.apple.mobilesafari" }, "Appium");
}
// 第三轮（DF_DL_ROUND=3，仅 Android）：网址保真——以 Chrome 为被测应用、指定 package 打开会回显地址的页面，
// 在网页上下文读 location.href，与原网址的 WHATWG 标准化形式逐字对比；比较原样、百分号编码括号、单引号包裹、
// 预加反斜杠四种传递方式。期望值只做浏览器本来就会做的标准化，不替任何传递方式「修正」差异。
async function deeplinkRound3(driver: Driver): Promise<void> {
  const chrome = "com.android.chrome";
  const urls = [
    "https://httpbin.org/anything/p(1)?a=1&b=(2)",
    "https://httpbin.org/anything/q?x=%28already%29&y=a+b&z=1;2",
    "https://httpbin.org/anything/r?s=it's&t=!*$,~",
    "https://httpbin.org/anything/f?k=v#frag",
  ];
  const transforms: Record<string, (u: string) => string> = {
    raw: (u) => u,
    pct_parens: (u) => u.replace(/\(/g, "%28").replace(/\)/g, "%29"),
    single_quoted: (u) => `'${u.replace(/'/g, `'\\''`)}'`,
  };
  await timed("chrome_activate", () => driver.activateApp(chrome)).catch(() => {});
  await sleep(3000);
  const out: Record<string, unknown>[] = [];
  for (const orig of urls) {
    const expected = new URL(orig).href;
    for (const [tname, tf] of Object.entries(transforms)) {
      const rec: Record<string, unknown> = { orig, transform: tname, expected };
      const t0 = performance.now();
      try { await driver.execute("mobile: deepLink", { url: tf(orig), package: chrome }); rec.ok = true; } catch (e) { rec.ok = false; rec.error = errText(e).slice(0, 300); }
      rec.call_ms = ms(t0);
      if (rec.ok) {
        await sleep(3500);
        rec.fg = await foreground(driver);
        try {
          const ctxs = (await driver.getContexts()) as string[];
          const web = ctxs.find((c) => c.startsWith("CHROMIUM") || c.startsWith("WEBVIEW_chrome"));
          if (web) {
            await driver.switchContext(web);
            // Chrome 每次 deepLink 开一个新标签页：读全部标签页的地址，逐字等于期望值即算保真
            const handles = await driver.getWindowHandles();
            const hrefs: string[] = [];
            for (const h of handles) { await driver.switchToWindow(h); hrefs.push(String(await driver.execute("return location.href"))); }
            rec.tabs = hrefs.length;
            rec.equal = hrefs.includes(expected);
            rec.hrefs = hrefs;
            rec.href = hrefs.find((h) => h === expected) ?? hrefs.slice(-1)[0];
            await driver.switchContext("NATIVE_APP");
          } else rec.href_error = `无网页上下文：${JSON.stringify(ctxs)}`;
        } catch (e) { rec.href_error = errText(e).slice(0, 200); await driver.switchContext("NATIVE_APP").catch(() => {}); }
      }
      out.push(rec);
      log(`保真 ${tname} ${orig}: ok=${rec.ok} equal=${rec.equal} href=${String(rec.href ?? rec.href_error ?? rec.error).slice(0, 160)}`);
    }
  }
  results.deeplink_fidelity = out;
}
// 第四轮（DF_DL_ROUND=4）：确定原样传递的安全字符集。Android 同第三轮、只用原样传递；iOS 指定 Safari 的 bundleId 打开
// 回显页，不读网页上下文（iOS 上 deepLink 之后网页命令会挂住），而在原生控件树里找回显 JSON 的 "url" 字段。
async function deeplinkRound4(driver: Driver): Promise<void> {
  const out: Record<string, unknown>[] = [];
  if (PLATFORM === "android") {
    const chrome = "com.android.chrome";
    // DF_DL_URLS（空格分隔）可覆盖清单，用于逐字符隔离
    const urls = process.env.DF_DL_URLS ? process.env.DF_DL_URLS.split(" ") : [
      "https://httpbin.org/anything/m?a=1&b=2&c=x%20y",
      "https://httpbin.org/anything/s?t=!*$,~",
      "https://httpbin.org/anything/e?q=a%26b&r=%3B&u=%27",
      "https://httpbin.org/anything/h?k=v&w=2#frag",
    ];
    await driver.activateApp(chrome).catch(() => {});
    await sleep(3000);
    for (const orig of urls) {
      const expected = new URL(orig).href;
      const rec: Record<string, unknown> = { orig, expected };
      try { await driver.execute("mobile: deepLink", { url: orig, package: chrome }); rec.ok = true; } catch (e) { rec.ok = false; rec.error = errText(e).slice(0, 300); }
      if (rec.ok) {
        await sleep(3500);
        try {
          const web = ((await driver.getContexts()) as string[]).find((c) => c.startsWith("CHROMIUM") || c.startsWith("WEBVIEW_chrome"));
          await driver.switchContext(web!);
          const hrefs: string[] = [];
          for (const h of await driver.getWindowHandles()) { await driver.switchToWindow(h); hrefs.push(String(await driver.execute("return location.href"))); }
          rec.equal = hrefs.includes(expected); rec.href = hrefs.find((h) => h === expected) ?? hrefs.slice(-1)[0];
          await driver.switchContext("NATIVE_APP");
        } catch (e) { rec.href_error = errText(e).slice(0, 200); await driver.switchContext("NATIVE_APP").catch(() => {}); }
      }
      out.push(rec); log(`安全集 ${orig}: ok=${rec.ok} equal=${rec.equal} href=${String(rec.href ?? rec.href_error ?? rec.error).slice(0, 140)}`);
    }
  } else {
    const safari = "com.apple.mobilesafari";
    const urls = [
      "https://httpbin.org/anything/p(1)?a=1&b=(2)",
      "https://httpbin.org/anything/q?x=%28already%29&y=a+b&z=1;2",
      "https://httpbin.org/anything/r?s=it's&t=!*$,~",
      "https://httpbin.org/anything/m?a=1&b=2&c=x%20y",
    ];
    for (const orig of urls) {
      const rec: Record<string, unknown> = { orig, expected: new URL(orig).href };
      try { await driver.execute("mobile: deepLink", { url: orig, bundleId: safari }); rec.ok = true; } catch (e) { rec.ok = false; rec.error = errText(e).slice(0, 300); }
      if (rec.ok) {
        await sleep(5000);
        const src = await driver.getPageSource().catch(() => "");
        const decoded = src.replace(/&quot;/g, "\"").replace(/&amp;/g, "&").replace(/&apos;/g, "'").replace(/&#39;/g, "'");
        rec.echo_urls = [...new Set([...decoded.matchAll(/"url":\s*"([^"]+)"/g)].map((m) => m[1]))].slice(0, 4);
        rec.fg = await foreground(driver);
      }
      out.push(rec); log(`iOS 送达 ${orig}: ok=${rec.ok} echo=${JSON.stringify(rec.echo_urls ?? rec.error).slice(0, 200)}`);
    }
  }
  results.deeplink_safe_set = out;
}
async function deeplinkProbe(driver: Driver, sessionArn: string, appArn: string | undefined): Promise<void> {
  if (process.env.DF_DL_ROUND === "4") return deeplinkRound4(driver);
  if (process.env.DF_DL_ROUND === "3") return deeplinkRound3(driver);
  if (process.env.DF_DL_ROUND === "2") return deeplinkRound2(driver, sessionArn, appArn);
  if (PLATFORM === "android") {
    const pkg = APP_PACKAGE;
    if (appArn) await installApp(driver, sessionArn, appArn);
    await timed("app_activate", () => driver.activateApp(pkg));
    await sleep(4000);
    results.deeplink_launch = { fg: await foreground(driver), view: await waitMarker(driver, undefined, 0) };
    const home = () => driver.execute("mobile: pressKey", { keycode: 3 });
    await deeplinkCase(driver, "handled_with_package", { url: "https://en.wikipedia.org/wiki/Appium", package: pkg }, "Appium");
    await deeplinkCase(driver, "consecutive_second", { url: "https://en.wikipedia.org/wiki/Selenium_(software)", package: pkg }, "Selenium");
    const back = await driver.back().then(() => "ok").catch((e) => errText(e).slice(0, 160));
    await sleep(2000);
    results.deeplink_back_after_second = { back, fg: await foreground(driver), view: await waitMarker(driver, "Appium", 4000) };
    await deeplinkCase(driver, "from_background", { url: "https://en.wikipedia.org/wiki/WebDriver", package: pkg }, "WebDriver", async () => { await home(); await sleep(2500); });
    await deeplinkCase(driver, "cold_start", { url: "https://en.wikipedia.org/wiki/Android_(operating_system)", package: pkg }, "Android", async () => { await driver.terminateApp(pkg); await sleep(2000); });
    await deeplinkCase(driver, "unhandled_host_with_package", { url: "https://www.example.com/", package: pkg }, "Example Domain");
    await deeplinkCase(driver, "handled_host_odd_path_with_package", { url: "https://en.wikipedia.org/static/no-such-page", package: pkg });
    await deeplinkCase(driver, "handled_other_language_with_package", { url: "https://de.wikipedia.org/wiki/Appium", package: pkg }, "Appium");
    await deeplinkCase(driver, "custom_scheme_with_package", { url: "wikipedia://en.wikipedia.org/wiki/Kotlin_(programming_language)", package: pkg }, "Kotlin");
    await deeplinkCase(driver, "system_dispatch_handled_no_package", { url: "https://en.wikipedia.org/wiki/Gherkin_(language)" }, "Gherkin", async () => { await home(); await sleep(2000); });
    await deeplinkCase(driver, "system_dispatch_unhandled_no_package", { url: "https://www.example.com/" }, "Example Domain", async () => { await home(); await sleep(2000); });
    return;
  }
  // iOS：系统「地图」
  const maps = "com.apple.Maps";
  const home = () => driver.execute("mobile: pressButton", { name: "home" });
  await deeplinkCase(driver, "custom_scheme_with_bundle", { url: "maps://?q=Seattle", bundleId: maps }, "Seattle");
  if (results.deeplink && (results.deeplink as Array<{ ok: boolean }>)[0].ok === false) {
    // 不支持的设备：再记一次不带 bundleId 的形态就收尾
    await deeplinkCase(driver, "no_bundle_on_unsupported", { url: "maps://?q=Seattle" }, "Seattle");
    return;
  }
  await deeplinkCase(driver, "consecutive_second", { url: "maps://?q=Portland", bundleId: maps }, "Portland");
  await deeplinkCase(driver, "https_universal_with_bundle", { url: "https://maps.apple.com/?q=Boston", bundleId: maps }, "Boston");
  await deeplinkCase(driver, "unhandled_https_with_bundle", { url: "https://www.example.com/", bundleId: maps }, "Example Domain");
  await deeplinkCase(driver, "from_background", { url: "maps://?q=Denver", bundleId: maps }, "Denver", async () => { await home(); await sleep(2500); });
  await deeplinkCase(driver, "cold_start", { url: "maps://?q=Chicago", bundleId: maps }, "Chicago", async () => { await driver.terminateApp(maps); await sleep(2000); });
  await deeplinkCase(driver, "system_dispatch_universal_no_bundle", { url: "https://maps.apple.com/?q=Austin" }, "Austin", async () => { await home(); await sleep(2000); });
  await deeplinkCase(driver, "system_dispatch_unhandled_no_bundle", { url: "https://www.example.com/" }, "Example Domain", async () => { await home(); await sleep(2000); });
}

async function main(): Promise<number> {
  fs.mkdirSync(RUN_DIR, { recursive: true });
  const project = await projectArn();
  if (SCENARIO === "release") {
    let rc = 0;
    try { await releaseProbe(project); } catch (e) { rc = 1; results.error = errText(e); log(`失败：${errText(e)}`); }
    results.finished_at = new Date().toISOString();
    fs.writeFileSync(path.join(RUN_DIR, "spike06-results.json"), JSON.stringify(results, null, 2));
    log(`结果：${path.join(RUN_DIR, "spike06-results.json")}`);
    return rc;
  }
  log(`项目 ${project.slice(-20)}，平台 ${PLATFORM}，场景 ${SCENARIO}，设备 ${DEVICE_ARN.slice(-12)}，模型 ${MODEL}（${modelFamily()}），Bedrock ${getBaseUrl()}`);
  const appArn = (SCENARIO === "app" && APP_INSTALL === "devicefarm") || SCENARIO === "faults" || (SCENARIO === "deeplink" && !["3", "4"].includes(process.env.DF_DL_ROUND ?? "") && (PLATFORM === "android" || process.env.DF_DL_ROUND === "2")) ? await ensureAppUpload(project) : undefined;
  const session = await startSession(project);
  let driver: Driver | undefined;
  let rc = 0;
  try {
    if (SCENARIO === "timeouts" && process.env.DF_NEWSESSION_PROBE === "1") await newSessionTimeoutProbe(session.endpoint);
    driver = await timed("webdriver_connect", () => connect(session.endpoint));
    results.caps = (driver as unknown as { capabilities: unknown }).capabilities;
    results.server_status = await driver.status().catch((e) => ({ error: errText(e) }));
    log(`caps: ${JSON.stringify(results.caps).slice(0, 400)}`);
    for (let i = 0; i < 3; i++) {
      const shot = await timed("cmd_screenshot", () => driver!.takeScreenshot());
      if (i === 0) { results.screenshot_px = pngSize(shot); results.screenshot_b64_kb = Math.round(shot.length / 1024); }
      await timed("cmd_window_rect", () => driver!.getWindowRect()).catch(async (e) => { if (!results.window_rect_error) { results.window_rect_error = errText(e); log(`window rect 失败（继续）：${results.window_rect_error}`); await rawProbe(session.endpoint, driver!, "window/rect"); } });
    }
    results.contexts = await timed("cmd_get_contexts", () => driver!.getContexts());
    results.context_initial = await driver.getContext();
    await driver.switchContext("NATIVE_APP");
    for (let i = 0; i < 2; i++) { const shot = await timed("cmd_screenshot_native", () => driver!.takeScreenshot()); if (i === 0) results.screenshot_native_px = pngSize(shot); }
    results.window_rect_native = await driver.getWindowRect().catch((e) => ({ error: errText(e) }));
    if (PLATFORM === "ios") results.device_screen_info = await driver.execute("mobile: deviceScreenInfo").catch((e) => ({ error: errText(e) }));

    if (SCENARIO === "app") {
      if (appArn) await installApp(driver, session.arn, appArn);
      await timed("app_activate", () => driver!.activateApp(APP_PACKAGE));
      await sleep(3000);
      if (PLATFORM === "android") {
        // 高德首轮：activateApp 返回了、设备却一直停在桌面。查应用状态（4 前台 / 3 后台 / 1 未运行），不在前台就按活动名显式启动，再抓 logcat 看有没有崩溃
        const states: Array<[number, unknown]> = [];
        const poll = async (n: number) => { for (let i = 0; i < n; i++) { states.push([ms(t0), await driver!.queryAppState(APP_PACKAGE).catch((e) => errText(e))]); await sleep(2000); } };
        const t0 = performance.now();
        await poll(4);
        const fg = () => states.some(([, st]) => st === 4);
        if (!fg() && process.env.DF_APP_ACTIVITY) {
          await timed("app_start_activity", () => driver!.execute("mobile: startActivity", { intent: `${APP_PACKAGE}/${process.env.DF_APP_ACTIVITY}` })).catch((e) => { results.app_start_activity_error = errText(e); });
          await poll(5);
        }
        results.app_states = states;
        results.app_current_package = await driver.getCurrentPackage().catch((e) => errText(e));
        try {
          const lines = (await driver.getLogs("logcat")) as Array<{ message?: string }>;
          const hits = lines.map((l) => l.message ?? "").filter((m) => /autonavi|minimap|AndroidRuntime|FATAL|has died|Force-stopping|ANR/i.test(m)).slice(-40);
          results.app_logcat_hits = hits.map((m) => m.slice(0, 220));
          fs.writeFileSync(path.join(RUN_DIR, "logcat-after-launch.txt"), lines.map((l) => l.message ?? "").join("\n"));
        } catch (e) { results.app_logcat_error = errText(e); }
        log(`应用状态轨迹 ${JSON.stringify(states)} 前台包 ${results.app_current_package} logcat 命中 ${(results.app_logcat_hits as string[] | undefined)?.length ?? "无"}`);
      }
      // 控件树探针：确定性 step 在原生应用里能拿到什么
      const src = await timed("cmd_page_source", () => driver!.getPageSource());
      results.page_source_kb = Math.round(src.length / 1024);
      fs.writeFileSync(path.join(RUN_DIR, "page-source-after-launch.xml"), src);
      results.resource_ids_sample = [...new Set([...src.matchAll(/resource-id="([^"]+)"/g)].map((m) => m[1]).filter(Boolean))].slice(0, 25);
      if (PLATFORM === "ios") {
        results.ios_names_sample = [...new Set([...src.matchAll(/ name="([^"]{1,60})"/g)].map((m) => m[1]))].slice(0, 30);
        results.ios_types_sample = [...new Set([...src.matchAll(/<(XCUIElementType\w+)/g)].map((m) => m[1]))].slice(0, 30);
      }
      results.contexts_in_app = await driver.getContexts();
      // UiAutomator2 在动作与截图前默认等界面空闲（waitForIdleTimeout 10 秒），有动画的页面会把一张截图拖到几秒；量一下关掉的效果
      for (let i = 0; i < 2; i++) await timed("cmd_screenshot_app_default_idle", () => driver!.takeScreenshot());
      await driver.updateSettings({ waitForIdleTimeout: 0 }).catch((e) => { results.update_settings_error = errText(e); });
      for (let i = 0; i < 2; i++) await timed("cmd_screenshot_app_idle0", () => driver!.takeScreenshot());
      if (PLATFORM === "android") {
        try {
          const found = await timed("cmd_find_by_id", async () => await driver!.$$(`id=${APP_PACKAGE}:id/search_container`));
          results.find_search_container = found.length;
        } catch (e) { results.probe_error = errText(e); }
      }
    } else if (SCENARIO === "egress") {
      await egressProbe(driver, session.endpoint);
    } else if (SCENARIO === "cap") {
      await capProbe(driver, session.arn);
    } else if (SCENARIO === "faults") {
      if (appArn) await installApp(driver, session.arn, appArn);
      await timed("app_activate", () => driver!.activateApp(APP_PACKAGE));
      await sleep(3000);
    } else if (SCENARIO === "deeplink") {
      await deeplinkProbe(driver, session.arn, appArn);
    } else if (SCENARIO === "warmup") {
      await warmupProbe(driver);
    } else if (SCENARIO === "timeouts") {
      await timeoutsProbe(driver, session.endpoint, session.arn);
    } else {
      const webCtx = (results.contexts as string[]).find((c) => c !== "NATIVE_APP");
      if (webCtx) await driver.switchContext(webCtx);
      results.window_rect_web = await driver.getWindowRect().catch((e) => ({ error: errText(e) }));
      await timed("cmd_navigate", () => driver!.url(START_URL)).catch((e) => { results.navigate_error = errText(e); log(`导航失败（继续）：${results.navigate_error}`); });
      results.title_after_nav = await timed("cmd_get_title", () => driver!.getTitle()).catch(async (e) => { await rawProbe(session.endpoint, driver!, "title"); return { error: errText(e) }; });
      if (PLATFORM === "ios" && (results.navigate_error || typeof results.title_after_nav !== "string")) {
        // 网页上下文不可用时的替代导航：XCTest 侧的 deepLink 让 Safari 打开地址（不经远程检查器）
        await driver.switchContext("NATIVE_APP").catch(() => {});
        await timed("cmd_deeplink_navigate", () => driver!.execute("mobile: deepLink", { url: START_URL, bundleId: "com.apple.mobilesafari" }))
          .then(() => { results.deeplink_navigate = "ok"; }).catch((e) => { results.deeplink_navigate = errText(e); log(`deepLink 导航失败（继续）：${results.deeplink_navigate}`); });
        await sleep(4000);
      }
      results.url_after_nav = await timed("cmd_get_url", () => driver!.getUrl()).catch(async (e) => { await rawProbe(session.endpoint, driver!, "url"); return { error: errText(e) }; });
      try {  // 探针失败不该拖垮 AI 阶段
        const h1s = await timed("cmd_find_h1", async () => await driver!.$$("h1"));
        results.h1_count = h1s.length;
        results.h1_text = h1s.length ? await timed("cmd_get_text", async () => await h1s[0].getText()) : null;
        results.page_source_kb = Math.round((await timed("cmd_page_source", () => driver!.getPageSource())).length / 1024);
      } catch (e) { results.probe_error = errText(e); log(`探针失败（继续）：${results.probe_error}`); }
      log(`导航后标题「${results.title_after_nav}」 h1「${results.h1_text}」 contexts=${JSON.stringify(results.contexts)} rect=${JSON.stringify(results.window_rect_web)} shot=${JSON.stringify(results.screenshot_px)}`);
    }

    if (SKIP_AI && SCENARIO === "app" && PLATFORM === "ios") await iosAppTypingProbe(driver, session.endpoint).catch((e) => { results.ios_typing_probe_error = errText(e); log(`应用输入探针整体失败：${results.ios_typing_probe_error}`); });
    if (SKIP_AI && SCENARIO === "app" && PLATFORM === "android") await androidAppTypingProbe(driver).catch((e) => { results.android_typing_probe_error = errText(e); log(`Android 应用输入探针整体失败：${results.android_typing_probe_error}`); });
    if (!SKIP_AI && SCENARIO !== "egress" && SCENARIO !== "cap" && SCENARIO !== "warmup" && SCENARIO !== "timeouts" && SCENARIO !== "deeplink") {
      const iface = new AppiumInterface(driver, session.endpoint);
      const agent = new Agent(iface, {
        generateReport: true, persistExecutionDump: true, replanningCycleLimit: SCENARIO === "app" ? 12 : 4,
        modelConfig: { MIDSCENE_MODEL_NAME: MODEL, MIDSCENE_MODEL_BASE_URL: getBaseUrl(), MIDSCENE_MODEL_API_KEY: "unused", MIDSCENE_MODEL_FAMILY: modelFamily() },
        createOpenAIClient: async () => new OpenAI({ baseURL: getBaseUrl(), apiKey: "unused", fetch: sigv4Fetch }) as never,
      } as never);
      const ai: Record<string, unknown>[] = [];
      const step: Stepper = async (kind, prompt) => {
        const before = executionsLength(agent);    // worker 的做法：step 起点记长度，step 末切出本 step 新增的 execution
        const t0 = performance.now(); let out: unknown; let err: string | undefined;
        try { out = kind === "act" ? await agent.aiAct(prompt) : await agent.aiBoolean(prompt); } catch (e) { err = errText(e); }
        const m = (agent as unknown as { metrics?: { totalTokens?: number } }).metrics;
        const rec: Record<string, unknown> = { kind, prompt, ms: ms(t0), result: out, error: err, total_tokens_so_far: m?.totalTokens, executions: (agent.dump?.executions ?? []).length };
        // 清单第 6 项：现有 evidence 抽取对 Appium 界面的 dump 是否零改动可用
        try {
          const execs = (agent.dump?.executions ?? []).slice(before) as unknown[];
          const status = err ? "error" : kind === "bool" && out !== true ? "failed" : "passed";
          const doc = buildEvidence({
            scopeId: "spike06", scenarioId: `spike06-${PLATFORM}-${SCENARIO}`,
            step: { index: ai.length, keyword: kind === "act" ? "When" : "Then", text: prompt },
            status, message: null, executions: execs, prompt, votes: [kind === "bool" ? out === true : null],
            url: null, error: err ?? null, runDir: RUN_DIR, refFor: (local) => "file://" + local,
          });
          const frames = doc.acts.flatMap((a) => a.frames);
          const shots = frames.map((f) => f.screenshot).filter((u): u is string => typeof u === "string");
          const missing = shots.filter((u) => !fs.existsSync(u.replace("file://", "")));
          rec.evidence = { executions: execs.length, frames: frames.length, thoughts: frames.filter((f) => f.thought).length, actions: frames.filter((f) => f.actions.length).length, screenshots: shots.length, missing_files: missing.length, act_error: doc.acts.some((a) => a.error !== null), status };
          fs.mkdirSync(path.join(RUN_DIR, "evidence"), { recursive: true });
          fs.writeFileSync(path.join(RUN_DIR, "evidence", `step-${ai.length}.json`), JSON.stringify(doc, null, 2));
        } catch (e) { rec.evidence_error = errText(e); }
        ai.push(rec); log(`AI ${kind} ${rec.ms} ms tokens=${rec.total_tokens_so_far} result=${JSON.stringify(out)} ${err ? "ERR " + err : ""} evidence=${JSON.stringify(rec.evidence ?? rec.evidence_error)}`);
        return out;
      };
      if (SCENARIO === "web") await webSteps(step, () => iosTypingProbe(iface, driver!));   // 探针两个平台都做，名字沿用
      else if (SCENARIO === "app") await (PLATFORM === "ios" ? iosSampleAppSteps(step) : APP_PACKAGE === "com.autonavi.minimap" ? amapSteps(step) : APP_PACKAGE === "org.wikipedia" ? appSteps(step, () => androidAppTypingProbe(driver!)) : genericAppSteps(step));
      else if (SCENARIO === "faults") await faultSteps(step, driver, session.arn);
      results.ai_steps = ai;
      if (SCENARIO === "web") results.url_after_ai = await iface.url();
      if (SCENARIO === "app") {
        // 词条页的控件树：确定性 step 在原生应用里能拿到什么（第一轮只看了 Compose 引导页，树几乎为空）
        const src = await timed("cmd_page_source_after_ai", () => driver!.getPageSource()).catch(() => "");
        fs.writeFileSync(path.join(RUN_DIR, "page-source-after-ai.xml"), src);
        results.page_source_after_ai_kb = Math.round(src.length / 1024);
        results.resource_ids_after_ai = [...new Set([...src.matchAll(/resource-id="([^"]+)"/g)].map((m) => m[1]).filter(Boolean))].slice(0, 40);
        results.texts_after_ai = [...new Set([...src.matchAll(/ text="([^"]{2,60})"/g)].map((m) => m[1]))].slice(0, 20);
        if (PLATFORM === "ios") {
          results.ios_names_after_ai = [...new Set([...src.matchAll(/ name="([^"]{1,60})"/g)].map((m) => m[1]))].slice(0, 40);
          results.ios_labels_after_ai = [...new Set([...src.matchAll(/ label="([^"]{1,60})"/g)].map((m) => m[1]))].slice(0, 30);
        }
        results.contexts_after_ai = await driver.getContexts().catch(() => []);
      }
      await agent.destroy().catch(() => {});
      const shotsDir = path.join(RUN_DIR, "report", "screenshots");
      results.report_dir = fs.existsSync(path.join(RUN_DIR, "report")) ? fs.readdirSync(path.join(RUN_DIR, "report")).slice(0, 10) : null;
      results.screenshots_persisted = fs.existsSync(shotsDir) ? fs.readdirSync(shotsDir).length : 0;
      const execs = agent.dump?.executions ?? [];
      results.executions = execs.length;
      fs.writeFileSync(path.join(RUN_DIR, "spike06-executions.json"), JSON.stringify(execs, (k, v) => (k === "base64" ? undefined : v), 2));
    }
  } catch (e) {
    rc = 1; results.error = errText(e) + " | " + String((e as Error).stack ?? "").slice(0, 1200); log(`失败：${errText(e)}`);
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
