// 网页上下文重新定位的单测（ADR 0052 决策 5；ADR 0050 决策 2 的 withWebContext）。运行：npx tsx --test src/device/web-context.test.mts。
//
// 两层：
//   - 定位规则与 Appium 会话的三个入口（withWebContext、设备上的导航、为 evidence 读地址）：假客户端按脚本回上下文列表，核对多候选与
//     零候选的处置（零候选等一会儿再列一次）、ADR 原文消息、fn 只执行一次、结束后切回原生上下文、命令只经传入的 driver 发出；
//   - 与设备侧接缝连起来：真的 createDeviceSurface 配本模块的会话实现，核对能力结论为「不提供」时任何读地址与导航都不调 url / getUrl，
//     以及定位失败不翻转能力结论（下一次照常重新定位）。
// 真实设备上的上下文名形态与多候选是否出现不在这里证明，列入真机验收。
import { afterEach, test } from "node:test";
import assert from "node:assert";
import type { Browser } from "webdriverio";
import {
  MULTIPLE_WEB_PAGES_MESSAGE, NATIVE_CONTEXT, NO_WEB_PAGE_MESSAGE, contextNames, locateWebContext, webContextCandidates,
} from "./web-context.mjs";
import { createAppiumSession } from "./appium.mjs";
import { WEB_CONTEXT_RELIST_DELAY_MS } from "./limits.mjs";
import { createDeviceSurface, type DeviceParts, type ProbeConclusion } from "./surface.mjs";
import { readClassification, type SurfaceDeps, type TargetSurface } from "../worker/surface.mjs";
import type { SelectedHandler, WebdriverCtx } from "../worker/deterministic.mjs";
import "../worker/deterministic.steps.mjs";

// ---- 假客户端 ----

interface DriverScript {
  /** getContexts 依次的结果；用完之后重复最后一项。 */
  contexts: Array<unknown[] | Error>;
  url?: string | Error;
  /** 切回原生上下文时失败。 */
  nativeSwitchFails?: boolean;
  /** 读地址时调用（测试在这里中止截止信号）。 */
  onGetUrl?: () => void;
}

function fakeDriver(name: string, script: DriverScript, calls: string[]) {
  const queue = [...script.contexts];
  let last: unknown[] | Error = ["NATIVE_APP"];
  let current = NATIVE_CONTEXT;
  const driver = {
    async getContexts() {
      calls.push(`${name}.getContexts`);
      if (queue.length > 0) last = queue.shift()!;
      if (last instanceof Error) throw last;
      return last;
    },
    async getContext() { calls.push(`${name}.getContext`); return current; },
    async switchContext(ctx: string) {
      calls.push(`${name}.switchContext:${ctx}`);
      if (ctx === NATIVE_CONTEXT && script.nativeSwitchFails) throw new Error("UND_ERR_CLOSED");
      current = ctx;
    },
    async getUrl() {
      calls.push(`${name}.getUrl`);
      script.onGetUrl?.();
      if (script.url instanceof Error) throw script.url;
      return script.url ?? "https://shop.example/cart";
    },
    async url(address: string) { calls.push(`${name}.url:${address}`); },
    async takeScreenshot() { calls.push(`${name}.takeScreenshot`); return ""; },
    async getPageSource() { calls.push(`${name}.getPageSource`); return "<hierarchy/>"; },
    async deleteSession() { calls.push(`${name}.deleteSession`); },
  };
  return { driver: driver as unknown as Browser, current: () => current };
}

function session(device: "android" | "ios", execScript: DriverScript) {
  const calls: string[] = [];
  const sleeps: number[] = [];
  const exec = fakeDriver("exec", execScript, calls);
  const probe = fakeDriver("probe", { contexts: [] }, calls);
  const s = createAppiumSession({
    clients: { exec: exec.driver, probe: probe.driver },
    device,
    capabilities: { platformName: device === "ios" ? "iOS" : "Android", "appium:automationName": "XCUITest", platformVersion: "18.6" },
    sleep: async (ms) => { sleeps.push(ms); },
  });
  return { s, calls, sleeps, exec };
}

// ---- 定位规则 ----

test("候选筛选：Android 只认 CHROMIUM，iOS 只认 WEBVIEW_<数字>（可带 .页号）；应用内 WebView 与原生上下文都不算", () => {
  const names = ["NATIVE_APP", "CHROMIUM", "WEBVIEW_chrome", "WEBVIEW_com.example.shop", "WEBVIEW_8152", "WEBVIEW_8152.3", "WEBVIEW_"];
  assert.deepEqual(webContextCandidates(names, "android"), ["CHROMIUM"]);
  assert.deepEqual(webContextCandidates(names, "ios"), ["WEBVIEW_8152", "WEBVIEW_8152.3"]);
  assert.deepEqual(contextNames(["NATIVE_APP", { id: "WEBVIEW_1", title: "Shop" }, 3, null]), ["NATIVE_APP", "WEBVIEW_1"]);
  assert.deepEqual(contextNames("NATIVE_APP"), []);
});

test("定位：一个候选即采用；多个候选立即拒绝、不再列；零候选等 WEB_CONTEXT_RELIST_DELAY_MS 再列一次", async () => {
  const sleeps: number[] = [];
  const sleep = async (ms: number) => { sleeps.push(ms); };
  const lists = (...xs: unknown[][]) => { const q = [...xs]; return async () => q.shift() ?? []; };

  assert.deepEqual(await locateWebContext(lists(["NATIVE_APP", "CHROMIUM"]), "android", { sleep }), { kind: "one", name: "CHROMIUM", count: 1 });
  assert.deepEqual(await locateWebContext(lists(["WEBVIEW_1", "WEBVIEW_2"]), "ios", { sleep }), { kind: "many", count: 2 });
  assert.deepEqual(sleeps, []);
  assert.deepEqual(await locateWebContext(lists(["NATIVE_APP"], ["NATIVE_APP", "WEBVIEW_7"]), "ios", { sleep }), { kind: "one", name: "WEBVIEW_7", count: 1 });
  assert.deepEqual(await locateWebContext(lists(["NATIVE_APP"], ["NATIVE_APP"]), "ios", { sleep }), { kind: "none", count: 0 });
  assert.deepEqual(sleeps, [WEB_CONTEXT_RELIST_DELAY_MS, WEB_CONTEXT_RELIST_DELAY_MS]);
});

// ---- withWebContext ----

const guardCalls = (calls: string[]) => calls.filter((c) => c.startsWith("guard."));

test("withWebContext：经传入的 driver 重新定位、切入、执行 fn 一次，结束后切回原生上下文；执行实例不发命令", async () => {
  const { s, calls } = session("ios", { contexts: [] });
  const guard = fakeDriver("guard", { contexts: [["NATIVE_APP", "WEBVIEW_8152"]] }, calls);
  let runs = 0;
  const value = await s.withWebContext(guard.driver, async () => { runs++; return "done"; });
  assert.equal(value, "done");
  assert.equal(runs, 1);
  assert.deepEqual(guardCalls(calls), ["guard.getContexts", "guard.switchContext:WEBVIEW_8152", "guard.switchContext:NATIVE_APP"]);
  assert.ok(!calls.some((c) => c.startsWith("exec.")));
  assert.equal(guard.current(), NATIVE_CONTEXT);
});

test("withWebContext：多个候选记 engine_error、用 ADR 原文消息，fn 不执行、不切入", async () => {
  const { s, calls } = session("ios", { contexts: [] });
  const guard = fakeDriver("guard", { contexts: [["NATIVE_APP", "WEBVIEW_1", "WEBVIEW_2"]] }, calls);
  let runs = 0;
  await assert.rejects(s.withWebContext(guard.driver, () => { runs++; }), (e) => {
    assert.deepEqual(readClassification(e), { errorType: "engine_error", message: MULTIPLE_WEB_PAGES_MESSAGE });
    return true;
  });
  assert.equal(runs, 0);
  assert.deepEqual(guardCalls(calls), ["guard.getContexts"]);
  assert.equal(MULTIPLE_WEB_PAGES_MESSAGE, "设备上有多个网页页面，无法确定被测页面");
});

test("withWebContext：零候选等一会儿再列一次，仍为零记 engine_error", async () => {
  const { s, calls, sleeps } = session("android", { contexts: [] });
  const guard = fakeDriver("guard", { contexts: [["NATIVE_APP"], ["NATIVE_APP", "WEBVIEW_chrome"]] }, calls);
  await assert.rejects(s.withWebContext(guard.driver, () => 1), (e) => {
    assert.deepEqual(readClassification(e), { errorType: "engine_error", message: NO_WEB_PAGE_MESSAGE });
    return true;
  });
  assert.deepEqual(guardCalls(calls), ["guard.getContexts", "guard.getContexts"]);
  assert.deepEqual(sleeps, [WEB_CONTEXT_RELIST_DELAY_MS]);
});

test("withWebContext：fn 执行中句柄失效直接抛出、不在 fn 内重试，之后仍切回原生上下文", async () => {
  const { s, calls } = session("android", { contexts: [] });
  const guard = fakeDriver("guard", { contexts: [["NATIVE_APP", "CHROMIUM"]] }, calls);
  const stale = new Error("stale element reference");
  let runs = 0;
  await assert.rejects(s.withWebContext(guard.driver, async () => { runs++; throw stale; }), (e) => e === stale);
  assert.equal(runs, 1);
  assert.equal(guardCalls(calls).at(-1), "guard.switchContext:NATIVE_APP");
});

test("withWebContext：切回原生上下文失败不掩盖 fn 的结果（复原核对会再处置）", async () => {
  const { s, calls } = session("android", { contexts: [] });
  const guard = fakeDriver("guard", { contexts: [["NATIVE_APP", "CHROMIUM"]], nativeSwitchFails: true }, calls);
  assert.equal(await s.withWebContext(guard.driver, () => 42), 42);
});

// ---- 设备上的导航 ----

test("openUrl：重新定位后在网页上下文打开地址；多候选记 engine_error 且绝不调 url", async () => {
  const { s, calls } = session("ios", { contexts: [] });
  const guard = fakeDriver("guard", { contexts: [["NATIVE_APP", "WEBVIEW_3"], ["WEBVIEW_3", "WEBVIEW_4"]] }, calls);
  await s.openUrl(guard.driver, "https://shop.example/");
  assert.deepEqual(guardCalls(calls), ["guard.getContexts", "guard.switchContext:WEBVIEW_3", "guard.url:https://shop.example/"]);
  await assert.rejects(s.openUrl(guard.driver, "https://shop.example/next"),
    (e) => readClassification(e)?.message === MULTIPLE_WEB_PAGES_MESSAGE);
  assert.equal(calls.filter((c) => c.includes(".url:")).length, 1);
});

// ---- 为 evidence 读地址 ----

test("readWebAddress：经执行实例定位、读地址、切回原生上下文", async () => {
  const { s, calls, exec } = session("android", { contexts: [["NATIVE_APP", "CHROMIUM"]], url: "https://shop.example/cart" });
  assert.deepEqual(await s.readWebAddress(AbortSignal.timeout(10_000)), { url: "https://shop.example/cart" });
  assert.deepEqual(calls, ["exec.getContexts", "exec.switchContext:CHROMIUM", "exec.getUrl", "exec.switchContext:NATIVE_APP"]);
  assert.equal(exec.current(), NATIVE_CONTEXT);
});

test("readWebAddress：多候选与零候选都只给出读不到的原因 error，不抛出；不调 getUrl", async () => {
  for (const contexts of [[["NATIVE_APP", "WEBVIEW_1", "WEBVIEW_2"]], [["NATIVE_APP"], ["NATIVE_APP"]]]) {
    const { s, calls } = session("ios", { contexts });
    assert.deepEqual(await s.readWebAddress(AbortSignal.timeout(10_000)), { missing: "error" });
    assert.ok(!calls.includes("exec.getUrl"));
  }
});

test("readWebAddress：截止信号已中止记 timeout 且不发命令；读的过程中中止记 timeout；命令出错记 error", async () => {
  const aborted = session("android", { contexts: [["NATIVE_APP", "CHROMIUM"]] });
  assert.deepEqual(await aborted.s.readWebAddress(AbortSignal.abort()), { missing: "timeout" });
  assert.deepEqual(aborted.calls, []);

  const controller = new AbortController();
  const during = session("android", {
    contexts: [["NATIVE_APP", "CHROMIUM"]], url: new Error("aborted"), onGetUrl: () => controller.abort(),
  });
  assert.deepEqual(await during.s.readWebAddress(controller.signal), { missing: "timeout" });

  const failing = session("android", { contexts: [["NATIVE_APP", "CHROMIUM"]], url: new Error("no such window") });
  assert.deepEqual(await failing.s.readWebAddress(AbortSignal.timeout(10_000)), { missing: "error" });
  assert.equal(failing.calls.at(-1), "exec.switchContext:NATIVE_APP", "读失败也尽力切回原生上下文");
});

// ---- 与设备侧接缝连起来 ----

const opened: TargetSurface[] = [];
afterEach(async () => {
  for (const surface of opened.splice(0)) await surface.release("normal");
});

function surfaceWith(webContext: ProbeConclusion["webContext"], execScript: DriverScript) {
  const calls: string[] = [];
  const exec = fakeDriver("exec", execScript, calls);
  const probe = fakeDriver("probe", { contexts: [] }, calls);
  const appium = createAppiumSession({
    clients: { exec: exec.driver, probe: probe.driver }, device: "android",
    capabilities: { platformName: "Android", "appium:automationName": "UiAutomator2", platformVersion: "14" },
    sleep: async () => {},
  });
  const conclusion: ProbeConclusion = {
    webContext, webContextCandidates: webContext === "available" ? 1 : 0, inputContext: null, scale: 1, scaleSource: "fixed",
    appiumVersion: "2.11.5",
  };
  const parts = (): DeviceParts => ({
    sessions: {
      async resolve() { return { ok: true, value: { deviceArn: "arn:device", model: "Pixel 8", osVersion: "14" } }; },
      async create() {
        return { ok: true, value: {
          arn: "arn:session:1", name: "gherkai:run:abcd:1:scope", createRequestedAt: Date.now(),
          device: { platform: "android", model: "Pixel 8", osVersion: "14", unit: null },
        } };
      },
      async waitRunning() { return { ok: true, value: { endpoint: "https://example.invalid/remote-endpoint/TOKEN", unit: null } }; },
      async status() { return "RUNNING"; },
      async retire() {},
    },
    finalizer: { async finalize() { return { releaseFailed: false }; } },
    appium: { async connect() { return { kind: "connected", session: appium }; } },
    probe: { async run() { return { ok: true, value: conclusion }; } },
    adapters: {
      select() {
        return {
          async deepLink(_d: Browser, address: string, appId: string | null) { calls.push(`adapter.deepLink:${address}:${appId}`); },
          extractControls() { return { items: [], total: 0, truncated: false }; },
        };
      },
    },
    guards: { create() { return { driver: exec.driver, openWindow() {}, closeWindow() { return null; }, shutdown() {} }; } },
    agents: { create() { return { fakeAgent: true } as never; } },
    warmup: { async run() { return null; } },
    appStore: { async head() { return { presence: "present", region: "us-west-2", redirected: false }; }, async presign() { return "https://s3.example/app"; } },
  });
  const deps: SurfaceDeps = {
    job: {
      schemaVersion: 1, scope: { id: "features/shop.feature::Cart", name: "Cart" }, engine: "midscene", assertionVotes: 1, timeoutS: 1500,
      target: { device: "android", uiKind: "web" },
      deviceRequest: {
        provider: "aws-device-farm", osVersion: "14", billingMethod: "METERED", projectArn: "arn:project", acquireTimeoutS: 600,
      },
    },
    emit: async () => {},
    log: () => {},
    agentOpts: { generateReport: false, persistExecutionDump: false } as never,
    uploader: { refFor: (p: string) => p, toReportRef: async (p: string) => p } as never,
    artifactRoot: undefined,
    requestFinalization: () => {},
  };
  const surface = createDeviceSurface(deps, {
    parts, env: {}, processEvents: { on() {}, off() {} }, appTiming: { sleep: async () => {} },
  });
  opened.push(surface);
  return { surface, calls };
}

const handler = (fn: (ctx: WebdriverCtx) => Promise<void>, requires: readonly "web_context"[] = []): SelectedHandler =>
  ({ kind: "webdriver", fn: (ctx) => fn(ctx), requires });

test("能力结论为「不提供」：读地址直接得到无地址、导航改走 deepLink，任何实例都不调 url / getUrl", async () => {
  const { surface, calls } = surfaceWith("unavailable", { contexts: [["NATIVE_APP", "CHROMIUM"]] });
  assert.equal((await surface.acquire()).ready, true);
  assert.deepEqual(await surface.readAddress({ kind: "ai", status: "passed" }), { url: null, url_missing: "no_web_context" });
  const snap = await surface.snapshot({ kind: "ai", status: "passed" }, null);
  assert.equal(snap.snapshot.url_missing, "no_web_context");
  await surface.navigate("https://shop.example/");
  assert.ok(calls.includes("adapter.deepLink:https://shop.example/:null"));
  assert.ok(!calls.some((c) => c.endsWith(".getUrl") || c.includes(".url:")), `不应调用 url 或 getUrl：${calls.join(", ")}`);
  assert.ok(!calls.some((c) => c.endsWith(".getContexts")), "不提供时也不去定位网页上下文");
});

test("能力结论为「提供」而定位失败：evidence 读地址置空并记 error；withWebContext 记 engine_error；能力结论不翻转，下一次照常定位", async () => {
  const { surface, calls } = surfaceWith("available", {
    contexts: [["NATIVE_APP", "CHROMIUM", "CHROMIUM"], ["NATIVE_APP", "CHROMIUM", "CHROMIUM"], ["NATIVE_APP", "CHROMIUM"]],
  });
  assert.equal((await surface.acquire()).ready, true);
  assert.deepEqual(await surface.readAddress({ kind: "ai", status: "passed" }), { url: null, url_missing: "error" });

  let ran = 0;
  const call = surface.bindHandler(handler(async (ctx) => { await ctx.withWebContext(() => { ran++; }); }, ["web_context"]));
  await assert.rejects(call({}), (e) => {
    assert.deepEqual(readClassification(e), { errorType: "engine_error", message: MULTIPLE_WEB_PAGES_MESSAGE });
    return true;
  });
  assert.equal(ran, 0);
  // 结论仍是「提供」：需要网页上下文的条目照常绑定、照常重新定位，这一次只有一个候选
  await surface.bindHandler(handler(async (ctx) => { await ctx.withWebContext(() => { ran++; }); }, ["web_context"]))({});
  assert.equal(ran, 1);
  assert.equal(calls.filter((c) => c === "exec.getContexts").length, 3);
});
