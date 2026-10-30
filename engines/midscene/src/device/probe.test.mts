// 能力探测的单测（ADR 0052 决策 5；决策 2 的失败归级）。运行：npx tsx --test src/device/probe.test.mts。
//
// 假客户端按脚本回结果，覆盖：网页上下文三类结论的归类真值表（重试后零候选、有候选而只读命令失败、列上下文失败、传输层错误、
// 原生只读命令也失败时先查会话状态）、只认属于被测对象的候选、应用目标不探测网页上下文、探测命令只经探测实例发出且不自设放弃式
// 计时、坐标比例的两级来源与都失败时的执行前失败、/status 的 Appium 版本，以及获取预算中止即停。WebdriverIO 与真机的真实行为
// （客户端超时是否真的生效、iOS 26 的挂起形态）不在这里证明：前者由 appium.test.mts 的真实运行层负责，后者列入真机验收。
import { test } from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Browser } from "webdriverio";
import { SCALE_UNKNOWN_MESSAGE, createCapabilityProbe, type ProbeDeps } from "./probe.mjs";
import { ACQUIRE_TIMEOUT_MESSAGE, SESSION_LOST_MESSAGE, type AcquireBudget, type AppiumSession } from "./surface.mjs";
import { PROBE_TIMEOUT_MS, WEB_CONTEXT_RELIST_DELAY_MS } from "./limits.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));

// ---- 失败形态（与 webdriver 10.0.2 抛出的错误形态相同，状态码按 appium.mts 的约定挂在 statusCode 上）----

const clientTimeout = (): Error => Object.assign(
  new Error('WebDriverError: Request timed out! Consider increasing the "connectionRetryTimeout" option. when running "url" with method "GET"'),
  { code: "ETIMEDOUT" },
);
const runtimeDomainMissing = (): Error => Object.assign(
  new Error("WebDriverError: 'Runtime' domain was not found when running \"url\" with method \"GET\""),
  { name: "unknown error", statusCode: 500 },
);
const connectionReset = (): Error => Object.assign(
  new Error('WebDriverError: Request failed with error code ECONNRESET when running "url" with method "GET"'),
  { code: "ECONNRESET" },
);
const gateway = (): Error => Object.assign(new Error("WebDriverError: Bad Gateway"), { statusCode: 503 });

function pngBase64(width: number, height: number): string {
  const b = Buffer.alloc(33);
  Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]).copy(b, 0);
  b.writeUInt32BE(13, 8);
  b.write("IHDR", 12, "ascii");
  b.writeUInt32BE(width, 16);
  b.writeUInt32BE(height, 20);
  return b.toString("base64");
}

const IOS_SOURCE = (w: number, h: number): string =>
  `<?xml version="1.0" encoding="UTF-8"?><AppiumAUT><XCUIElementTypeApplication type="XCUIElementTypeApplication" name="Safari" ` +
  `enabled="true" visible="true" x="0" y="0" width="${w}" height="${h}"><XCUIElementTypeWindow width="${w}" height="${h}"/>` +
  `</XCUIElementTypeApplication></AppiumAUT>`;

// ---- 假会话 ----

type Step = "ok" | Error;

interface Script {
  device: "android" | "ios";
  uiKind: "web" | "app";
  /** 探测实例上 getContexts 依次的结果。 */
  contexts?: Array<unknown[] | Error>;
  /** 探测实例上只读命令（getUrl）依次的结果。 */
  reads?: Step[];
  /** 会话建好时的当前上下文。 */
  initialContext?: string;
  currentContextFails?: boolean;
  switchToNativeFails?: boolean;
  /** 执行实例的截图（原生只读命令与比例回退用）。 */
  screenshot?: string | Error;
  pageSource?: string | Error;
  screenInfo?: unknown | Error;
  status?: unknown | Error;
  /** probe 实例的只读命令挂起到外部放行（测「不自设放弃式计时」）。 */
  readGate?: Promise<void>;
}

function fakeSession(s: Script) {
  const calls: string[] = [];
  const contexts = [...(s.contexts ?? [])];
  const reads = [...(s.reads ?? [])];
  let current = s.initialContext ?? "NATIVE_APP";
  const exec = {
    async takeScreenshot() {
      calls.push("exec.takeScreenshot");
      if (s.screenshot instanceof Error) throw s.screenshot;
      return s.screenshot ?? pngBase64(1080, 2400);
    },
    async getUrl() { calls.push("exec.getUrl"); return "https://wrong.example/"; },
    async url() { calls.push("exec.url"); },
    async getWindowRect() { calls.push("exec.getWindowRect"); return { width: 1, height: 1 }; },
    async getContexts() { calls.push("exec.getContexts"); return ["NATIVE_APP"]; },
  } as unknown as Browser;
  const probe = {
    async getContexts() {
      calls.push("probe.getContexts");
      const next = contexts.shift() ?? ["NATIVE_APP"];
      if (next instanceof Error) throw next;
      return next;
    },
    async switchContext(name: string) { calls.push(`probe.switchContext:${name}`); current = name; },
    async getUrl() {
      calls.push("probe.getUrl");
      if (s.readGate) await s.readGate;
      const next = reads.shift() ?? "ok";
      if (next instanceof Error) throw next;
      return "https://shop.example/";
    },
    async url() { calls.push("probe.url"); },
    async status() {
      calls.push("probe.status");
      if (s.status instanceof Error) throw s.status;
      return s.status ?? { ready: true, build: { version: "2.11.5" } };
    },
    async getWindowRect() { calls.push("probe.getWindowRect"); return { width: 1, height: 1 }; },
  } as unknown as Browser;
  const session = {
    exec, probe,
    automationName: s.device === "ios" ? "XCUITest" : "UiAutomator2",
    platformVersion: "18.6",
    async currentContext() {
      calls.push("session.currentContext");
      if (s.currentContextFails) throw connectionReset();
      return current;
    },
    async switchToNative() {
      calls.push("session.switchToNative");
      if (s.switchToNativeFails) throw connectionReset();
      current = "NATIVE_APP";
    },
    async probeScreenshot() { calls.push("session.probeScreenshot"); },
    async pageSource(signal: AbortSignal) {
      calls.push("session.pageSource");
      if (signal.aborted) throw new Error("aborted");
      if (s.pageSource instanceof Error) throw s.pageSource;
      return s.pageSource ?? IOS_SOURCE(390, 844);
    },
    async readWebAddress() { calls.push("session.readWebAddress"); return { missing: "error" as const }; },
    async withWebContext<T>(_d: Browser, fn: () => Promise<T> | T) { calls.push("session.withWebContext"); return fn(); },
    async openUrl() { calls.push("session.openUrl"); },
    async deleteSession() { calls.push("session.deleteSession"); },
  };
  return { session: session as unknown as AppiumSession, calls, probe, exec, current: () => current };
}

function budget(): AcquireBudget & { controller: AbortController } {
  const controller = new AbortController();
  return { controller, signal: controller.signal, remainingMs: () => 600_000 };
}

function probeWith(s: Script, extra: Partial<ProbeDeps> = {}) {
  const fake = fakeSession(s);
  const sleeps: number[] = [];
  const logs: string[] = [];
  const screenInfoCalls: Browser[] = [];
  const probe = createCapabilityProbe({
    async deviceScreenInfo(driver) {
      screenInfoCalls.push(driver);
      fake.calls.push(driver === fake.probe ? "screenInfo:probe" : "screenInfo:exec");
      if (s.screenInfo instanceof Error) throw s.screenInfo;
      return s.screenInfo ?? { scale: 3, screenSize: { width: 390, height: 844 } };
    },
    sleep: async (ms) => { sleeps.push(ms); },
    log: (line) => { logs.push(line); },
    ...extra,
  });
  return { ...fake, capability: probe, sleeps, logs, screenInfoCalls };
}

const target = (s: Script) => ({ device: s.device, uiKind: s.uiKind });

// ---- 网页上下文：三类结论 ----

test("Android Chrome：单个 CHROMIUM 候选、经探测实例只读命令成功即「提供」，探测结束切回原生上下文；结论只有数据、不带句柄", async () => {
  const s: Script = { device: "android", uiKind: "web", contexts: [["NATIVE_APP", "CHROMIUM"]], initialContext: "CHROMIUM" };
  const h = probeWith(s);
  const r = await h.capability.run(h.session, target(s), budget(), async () => "RUNNING");
  assert.ok(r.ok);
  assert.deepEqual(r.value, {
    webContext: "available", webContextCandidates: 1, inputContext: null, scale: 1, scaleSource: "fixed", appiumVersion: "2.11.5",
  });
  // 会话建好时在网页上下文：先切回原生，再经探测实例列上下文、切入、读一次地址，最后经生命周期通道切回原生
  assert.deepEqual(h.calls.filter((c) => !c.startsWith("probe.status")), [
    "session.currentContext", "session.switchToNative",
    "probe.getContexts", "probe.switchContext:CHROMIUM", "probe.getUrl",
    "session.currentContext", "session.switchToNative",
  ]);
  assert.equal(h.current(), "NATIVE_APP");
  assert.deepEqual(h.screenInfoCalls, [], "Android 的坐标比例恒为 1，不读屏幕信息");
});

test("重试后候选仍为零即「不提供」：零候选等 WEB_CONTEXT_RELIST_DELAY_MS 再列一次，不切入、不发只读命令", async () => {
  const s: Script = { device: "ios", uiKind: "web", contexts: [["NATIVE_APP"], ["NATIVE_APP"]] };
  const h = probeWith(s);
  const r = await h.capability.run(h.session, target(s), budget(), async () => "RUNNING");
  assert.ok(r.ok);
  assert.equal(r.value.webContext, "unavailable");
  assert.equal(r.value.webContextCandidates, 0);
  assert.equal(r.value.inputContext, "native", "iOS 网页上下文不可用时在原生上下文取活动元素");
  assert.deepEqual(h.sleeps, [WEB_CONTEXT_RELIST_DELAY_MS]);
  assert.equal(h.calls.filter((c) => c === "probe.getContexts").length, 2);
  assert.ok(!h.calls.some((c) => c.startsWith("probe.switchContext") || c.endsWith("getUrl") || c.endsWith(".url")));
});

test("只认属于被测对象的候选：WEBVIEW_chrome 与应用自己的 WEBVIEW_<包名> 不算，iOS 只认 WEBVIEW_<数字>", async () => {
  for (const [device, names] of [
    ["android", ["NATIVE_APP", "WEBVIEW_chrome", "WEBVIEW_com.example.shop"]],
    ["ios", ["NATIVE_APP", "WEBVIEW_chrome", "WEBVIEW_com.apple.mobilesafari"]],
  ] as const) {
    const s: Script = { device, uiKind: "web", contexts: [[...names], [...names]] };
    const h = probeWith(s);
    const r = await h.capability.run(h.session, target(s), budget(), async () => "RUNNING");
    assert.ok(r.ok);
    assert.equal(r.value.webContext, "unavailable", device);
    assert.equal(r.value.webContextCandidates, 0, device);
    assert.ok(!h.calls.some((c) => c.startsWith("probe.switchContext")), device);
  }
});

test("有候选、切得进，只读命令有界重试后仍超时或报错、而原生只读命令正常：「不提供」（iOS 26.3 的两种形态）", async () => {
  for (const failure of [clientTimeout, runtimeDomainMissing]) {
    const s: Script = {
      device: "ios", uiKind: "web",
      contexts: [["NATIVE_APP", "WEBVIEW_8152"], ["NATIVE_APP", "WEBVIEW_8152.1"]],
      reads: [failure(), failure()],
    };
    const h = probeWith(s);
    const r = await h.capability.run(h.session, target(s), budget(), async () => "RUNNING");
    assert.ok(r.ok, failure.name);
    assert.equal(r.value.webContext, "unavailable", failure.name);
    assert.equal(r.value.webContextCandidates, 1);
    assert.equal(r.value.inputContext, "native");
    // 只读命令只经探测实例、恰两次（有界重试一次）；之后经生命周期通道回到原生上下文、在原生上下文截图核对
    assert.equal(h.calls.filter((c) => c === "probe.getUrl").length, 2);
    assert.ok(!h.calls.includes("exec.getUrl"));
    const afterReads = h.calls.slice(h.calls.lastIndexOf("probe.getUrl") + 1);
    assert.deepEqual(afterReads, ["session.currentContext", "session.switchToNative", "exec.takeScreenshot"]);
    assert.equal(h.current(), "NATIVE_APP");
  }
});

test("只读命令第一次失败、重试成功：「提供」，重试时重新定位", async () => {
  const s: Script = {
    device: "ios", uiKind: "web",
    contexts: [["NATIVE_APP", "WEBVIEW_8152"], ["NATIVE_APP", "WEBVIEW_9001"]],
    reads: [clientTimeout(), "ok"],
  };
  const h = probeWith(s);
  const r = await h.capability.run(h.session, target(s), budget(), async () => "RUNNING");
  assert.ok(r.ok);
  assert.equal(r.value.webContext, "available");
  assert.equal(r.value.inputContext, "web");
  assert.ok(h.calls.includes("probe.switchContext:WEBVIEW_9001"), "第二次重新列出并采用当时唯一的候选");
});

test("列上下文的调用本身失败（有界重试后仍失败）：「探测出错」", async () => {
  const s: Script = { device: "android", uiKind: "web", contexts: [runtimeDomainMissing(), runtimeDomainMissing()] };
  const h = probeWith(s);
  const r = await h.capability.run(h.session, target(s), budget(), async () => "RUNNING");
  assert.ok(r.ok);
  assert.equal(r.value.webContext, "probe_error");
  assert.equal(r.value.webContextCandidates, null, "没有列出过候选");
  assert.equal(h.calls.filter((c) => c === "probe.getContexts").length, 2);
});

test("传输层错误（连接层错误码、HTTP 502 / 503 / 504）：「探测出错」，不当作设备不提供", async () => {
  for (const failure of [connectionReset, gateway]) {
    const s: Script = {
      device: "android", uiKind: "web",
      contexts: [["NATIVE_APP", "CHROMIUM"], ["NATIVE_APP", "CHROMIUM"]],
      reads: [failure(), failure()],
    };
    const h = probeWith(s);
    const r = await h.capability.run(h.session, target(s), budget(), async () => "RUNNING");
    assert.ok(r.ok);
    assert.equal(r.value.webContext, "probe_error", failure.name);
  }
});

test("原生只读命令也失败：先查会话状态，不是 RUNNING 归 session_lost，仍在运行为「探测出错」", async () => {
  const script = (): Script => ({
    device: "android", uiKind: "web",
    contexts: [["NATIVE_APP", "CHROMIUM"], ["NATIVE_APP", "CHROMIUM"]],
    reads: [clientTimeout(), clientTimeout()],
    screenshot: connectionReset(),
  });
  const lost = probeWith(script());
  const r1 = await lost.capability.run(lost.session, { device: "android", uiKind: "web" }, budget(), async () => "STOPPING");
  assert.deepEqual(r1, { ok: false, termination: { errorType: "session_lost", message: SESSION_LOST_MESSAGE } });

  const running = probeWith(script());
  const r2 = await running.capability.run(running.session, { device: "android", uiKind: "web" }, budget(), async () => "RUNNING");
  assert.ok(r2.ok);
  assert.equal(r2.value.webContext, "probe_error");

  // 状态查询本身失败或没有给查询函数：不据此判会话丢失
  const unknown = probeWith(script());
  const r3 = await unknown.capability.run(unknown.session, { device: "android", uiKind: "web" }, budget(), async () => null);
  assert.ok(r3.ok);
  assert.equal(r3.value.webContext, "probe_error");
  const noQuery = probeWith(script());
  const r4 = await noQuery.capability.run(noQuery.session, { device: "android", uiKind: "web" }, budget());
  assert.ok(r4.ok);
  assert.equal(r4.value.webContext, "probe_error");
});

test("会话建好后连原生上下文都切不回：先查会话状态，丢失即 session_lost", async () => {
  const s: Script = { device: "android", uiKind: "web", initialContext: "CHROMIUM", switchToNativeFails: true };
  const h = probeWith(s);
  const r = await h.capability.run(h.session, target(s), budget(), async () => "COMPLETED");
  assert.deepEqual(r, { ok: false, termination: { errorType: "session_lost", message: SESSION_LOST_MESSAGE } });
  assert.ok(!h.calls.includes("probe.getContexts"), "会话已丢失，不再探测网页上下文");
});

test("多个候选：无法确定被测页面，记「探测出错」，不按列出的第一个去猜", async () => {
  const s: Script = { device: "ios", uiKind: "web", contexts: [["NATIVE_APP", "WEBVIEW_1", "WEBVIEW_2"]] };
  const h = probeWith(s);
  const r = await h.capability.run(h.session, target(s), budget(), async () => "RUNNING");
  assert.ok(r.ok);
  assert.equal(r.value.webContext, "probe_error");
  assert.equal(r.value.webContextCandidates, 2);
  assert.ok(!h.calls.some((c) => c.startsWith("probe.switchContext")));
});

test("应用目标固定原生上下文，不探测网页上下文；iOS 应用目标在原生上下文取活动元素", async () => {
  const android: Script = { device: "android", uiKind: "app" };
  const a = probeWith(android);
  const ra = await a.capability.run(a.session, target(android), budget(), async () => "RUNNING");
  assert.ok(ra.ok);
  assert.deepEqual(ra.value, {
    webContext: null, webContextCandidates: null, inputContext: null, scale: 1, scaleSource: "fixed", appiumVersion: "2.11.5",
  });
  assert.ok(!a.calls.some((c) => c.includes("getContexts") || c.includes("switchContext") || c.endsWith("getUrl")));

  const ios: Script = { device: "ios", uiKind: "app" };
  const i = probeWith(ios);
  const ri = await i.capability.run(i.session, target(ios), budget(), async () => "RUNNING");
  assert.ok(ri.ok);
  assert.equal(ri.value.webContext, null);
  assert.equal(ri.value.inputContext, "native");
  assert.equal(ri.value.scale, 3);
  assert.ok(!i.calls.some((c) => c.includes("getContexts")));
});

// ---- 独立的短超时实例，不用 Promise.race ----

test("探测的网页命令只由探测实例发出，探测本身不设放弃式计时：只读命令挂得再久也等它由客户端超时结束", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  let release!: () => void;
  const gate = new Promise<void>((r) => { release = r; });
  const s: Script = { device: "android", uiKind: "web", contexts: [["NATIVE_APP", "CHROMIUM"]], readGate: gate };
  const h = probeWith(s);
  const pending = h.capability.run(h.session, target(s), budget(), async () => "RUNNING");
  for (let i = 0; i < 20 && !h.calls.includes("probe.getUrl"); i++) await new Promise((r) => setImmediate(r));
  assert.ok(h.calls.includes("probe.getUrl"));
  // 远超短预算：若探测自己用计时器放弃这条命令，结论此时就已定下（不提供或探测出错）
  t.mock.timers.tick(PROBE_TIMEOUT_MS * 10);
  for (let i = 0; i < 5; i++) await new Promise((r) => setImmediate(r));
  release();
  const r = await pending;
  assert.ok(r.ok);
  assert.equal(r.value.webContext, "available");
});

test("探测、网页上下文与 Appium 块的源码里没有 Promise.race（被拒方案：放弃不解除同一客户端上的阻塞）", () => {
  for (const file of ["probe.mts", "web-context.mts", "appium.mts"]) {
    const src = fs.readFileSync(path.join(HERE, file), "utf-8");
    assert.ok(!/Promise\s*\.\s*race\s*\(/.test(src), `${file} 不应使用 Promise.race`);
  }
});

// ---- 坐标比例 ----

test("坐标比例：iOS 取设备屏幕信息的 scale（经探测实例）；Android 恒为 1", async () => {
  const s: Script = { device: "ios", uiKind: "web", contexts: [["NATIVE_APP", "WEBVIEW_1"]], screenInfo: { scale: 2 } };
  const h = probeWith(s);
  const r = await h.capability.run(h.session, target(s), budget(), async () => "RUNNING");
  assert.ok(r.ok);
  assert.equal(r.value.scale, 2);
  assert.equal(r.value.scaleSource, "device_screen_info");
  assert.deepEqual(h.screenInfoCalls, [h.probe]);
});

test("坐标比例回退：屏幕信息失败或不带 scale 时，截图长边除以原生控件树根节点的长边、取整；不调 getWindowRect", async () => {
  for (const [info, shot, root, expected] of [
    [new Error("unknown command"), [1170, 2532], [390, 844], 3],
    [{ screenSize: { width: 375 } }, [750, 1334], [375, 667], 2],
    [{ scale: 0 }, [2532, 1170], [844, 390], 3],   // 横屏：长边对长边
    [new Error("timeout"), [1179, 2556], [393, 852], 3], // 比值 3.0 附近取整
  ] as const) {
    const s: Script = {
      device: "ios", uiKind: "app", screenInfo: info, screenshot: pngBase64(shot[0], shot[1]), pageSource: IOS_SOURCE(root[0], root[1]),
    };
    const h = probeWith(s);
    const r = await h.capability.run(h.session, target(s), budget(), async () => "RUNNING");
    assert.ok(r.ok);
    assert.equal(r.value.scale, expected);
    assert.equal(r.value.scaleSource, "page_source");
    assert.ok(h.calls.includes("session.pageSource") && h.calls.includes("exec.takeScreenshot"));
    assert.ok(!h.calls.some((c) => c.endsWith("getWindowRect")), "回退不取窗口尺寸");
  }
});

test("坐标比例回退也失败：执行前失败 engine_error「无法确定坐标比例」；会话已丢失时归 session_lost", async () => {
  const script = (): Script => ({
    device: "ios", uiKind: "web", screenInfo: new Error("unknown command"), pageSource: "<AppiumAUT/>",
  });
  const h = probeWith(script());
  const r = await h.capability.run(h.session, { device: "ios", uiKind: "web" }, budget(), async () => "RUNNING");
  assert.deepEqual(r, { ok: false, termination: { errorType: "engine_error", message: SCALE_UNKNOWN_MESSAGE } });
  assert.equal(SCALE_UNKNOWN_MESSAGE, "无法确定坐标比例");
  assert.ok(!h.calls.includes("probe.getContexts"), "比例定不下来就不再探测网页上下文");

  const lost = probeWith(script());
  const r2 = await lost.capability.run(lost.session, { device: "ios", uiKind: "web" }, budget(), async () => "STOPPING");
  assert.deepEqual(r2, { ok: false, termination: { errorType: "session_lost", message: SESSION_LOST_MESSAGE } });

  const badShot = probeWith({ ...script(), pageSource: IOS_SOURCE(390, 844), screenshot: "bm90IGEgcG5n" });
  const r3 = await badShot.capability.run(badShot.session, { device: "ios", uiKind: "web" }, budget(), async () => "RUNNING");
  assert.equal(r3.ok, false, "截图解不出尺寸同样定不下比例");
});

// ---- 其余探测项与预算 ----

test("Appium 版本取自探测实例的 /status，只记诊断：读不到为 null、不影响结论", async () => {
  const ok: Script = { device: "android", uiKind: "app", status: { ready: true, build: { version: "2.11.5" } } };
  const a = probeWith(ok);
  const ra = await a.capability.run(a.session, target(ok), budget(), async () => "RUNNING");
  assert.ok(ra.ok);
  assert.equal(ra.value.appiumVersion, "2.11.5");
  assert.ok(a.calls.includes("probe.status"));

  const failing: Script = { device: "android", uiKind: "app", status: connectionReset() };
  const b = probeWith(failing);
  const rb = await b.capability.run(b.session, target(failing), budget(), async () => "RUNNING");
  assert.ok(rb.ok);
  assert.equal(rb.value.appiumVersion, null);
});

test("获取预算中止（到期或进入终结）即停：归 acquire_timeout，不再发命令", async () => {
  const before = probeWith({ device: "android", uiKind: "web" });
  const b0 = budget();
  b0.controller.abort(new Error("finalizing"));
  const r0 = await before.capability.run(before.session, { device: "android", uiKind: "web" }, b0, async () => "RUNNING");
  assert.deepEqual(r0, { ok: false, termination: { errorType: "acquire_timeout", message: ACQUIRE_TIMEOUT_MESSAGE } });
  assert.deepEqual(before.calls, []);

  // 只读命令失败的同时预算到期：不再做原生核对与重试
  const b1 = budget();
  const mid = probeWith({
    device: "android", uiKind: "web", contexts: [["NATIVE_APP", "CHROMIUM"], ["NATIVE_APP", "CHROMIUM"]],
    reads: [clientTimeout(), "ok"],
  });
  const probeClient = mid.probe as unknown as { getUrl: () => Promise<string> };
  const original = probeClient.getUrl.bind(probeClient);
  probeClient.getUrl = async () => { b1.controller.abort(new Error("finalizing")); return original(); };
  const r1 = await mid.capability.run(mid.session, { device: "android", uiKind: "web" }, b1, async () => "RUNNING");
  assert.deepEqual(r1, { ok: false, termination: { errorType: "acquire_timeout", message: ACQUIRE_TIMEOUT_MESSAGE } });
  assert.equal(mid.calls.filter((c) => c === "probe.getUrl").length, 1);
  assert.ok(!mid.calls.includes("exec.takeScreenshot"));
});
