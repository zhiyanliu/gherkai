// 设备上的会话预热块的单测（ADR 0051 决策 13；ADR 0052 决策 6）。运行：npx tsx --test src/device/warmup.test.mts。
//
// Appium 会话与驱动适配器换成记录调用序列的假对象，时钟由测试推进。验证本块自己的判定：标记归因的真值表（标记取自
// engines/fixtures/tunnel-warmup.json）、路线只由传入的探测结论决定且重试不换路线、导航经执行实例发出（生命周期通道）、读标记前
// 切回原生上下文、就绪后的离开规则、有界重试与永不归 network_error、导航不被本块放弃、命令失败先查会话状态、获取预算的中止
// 信号穿进读取且中止后不再向设备发命令、预热地址不进日志与消息。执行实例的单请求超时由 Appium 块设定，这里只验本块不另设导航上限；真实设备上的标记
// 可见性与路线可用性由真机验收负责。
import { test } from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Browser } from "webdriverio";
import { createDeviceWarmup, findWarmupMarker, type DeviceWarmupArgs } from "./warmup.mjs";
import { DEVICE_WARMUP_ATTEMPTS } from "./limits.mjs";
import { SESSION_LOST_MESSAGE, type AcquireBudget, type AppiumSession, type DriverAdapter } from "./surface.mjs";
import {
  WARMUP_ATTEMPTS, WARMUP_AUTH_REQUIRED_MESSAGE, WARMUP_DENIED_MESSAGE, WARMUP_MARKER_WAIT_MS, WARMUP_MARKERS, warmupErrorMessage,
} from "../lib/tunnel-warmup.mjs";
import { attachClassification } from "../worker/surface.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FIXTURE = JSON.parse(fs.readFileSync(path.resolve(HERE, "../../../fixtures/tunnel-warmup.json"), "utf-8")) as {
  markers: Record<"ready" | "denied" | "error" | "auth_required", string>;
  titles: Record<"ready" | "denied" | "error" | "auth_required", string>;
  token_param: string;
  warmup_path: string;
};
const TOKEN = "T0K3NsecretValue0123456789abcdef";
const WARMUP_URL = `https://tunnel.example${FIXTURE.warmup_path}?${FIXTURE.token_param}=${TOKEN}`;
const ENDPOINT = `https://devicefarm-interactive-global.us-west-2.api.aws/remote-endpoint/${"Ab9".repeat(40)}`;

// ---- 原生控件树样本 ----

/** Android Chrome 的原生控件树：网页正文暴露为可访问性节点，地址栏里是预热地址。 */
function androidTree(text: string): string {
  return `<?xml version="1.0" encoding="UTF-8"?><hierarchy rotation="0">` +
    `<android.widget.EditText resource-id="com.android.chrome:id/url_bar" text="${WARMUP_URL.replace(/&/g, "&amp;")}"/>` +
    `<android.view.View text="" content-desc="${FIXTURE.titles.ready}"/>` +
    `<android.widget.TextView text="${text}"/></hierarchy>`;
}

/** iOS Safari 的原生控件树。 */
function iosTree(text: string): string {
  return `<?xml version="1.0" encoding="UTF-8"?><AppiumAUT><XCUIElementTypeApplication name="Safari">` +
    `<XCUIElementTypeTextField name="URL" value="tunnel.example${FIXTURE.warmup_path}?${FIXTURE.token_param}=${TOKEN}"/>` +
    `<XCUIElementTypeStaticText name="${text}" label="${text}" value="${text}"/></XCUIElementTypeApplication></AppiumAUT>`;
}

const LOADING = androidTree("GHERKAI TUNNEL WARMUP");  // 页面脚本改写标记之前的中间态，不是任何一个标记

// ---- 假会话 ----

const EXEC = { tag: "exec-instance" } as unknown as Browser;
const POLL_MS = 2_000;  // 假时钟：每读一次控件树推进这么久

type SourceReply = string | Error;

interface HarnessOptions {
  route?: "url" | "deep_link";
  /** 第 n 次（从 0 起）读控件树的结果；超出部分重复最后一个。 */
  sources?: SourceReply[];
  /** 第 n 次（从 0 起）预热导航（不含离开时的 about:blank）：返回 Error 即抛出；返回 Promise 即等它。 */
  nav?: (n: number) => Error | Promise<void> | void;
  /** 离开预热页的导航失败。 */
  leaveFails?: Error;
  /** 读控件树一直挂着，直到传入的截止信号中止。 */
  blockSource?: boolean;
  /** 第 n 次（从 0 起）读控件树、给出结果之前调用。 */
  onSource?: (n: number) => void;
  /** 第 n 次（从 0 起）切回原生上下文：返回 Error 即抛出。 */
  nativeFails?: (n: number) => Error | undefined;
  sessionStatus?: DeviceWarmupArgs["sessionStatus"];
  /** 不传 sessionStatus（端口当前的调用形态）。 */
  omitStatus?: boolean;
}

function harness(opts: HarnessOptions = {}) {
  const calls: string[] = [];
  const logs: string[] = [];
  const signals: AbortSignal[] = [];
  let clock = 0;
  let navCount = 0;
  let sourceCount = 0;
  let nativeCount = 0;
  const sources = opts.sources ?? [androidTree(FIXTURE.markers.ready)];
  const who = (driver: Browser) => (driver === EXEC ? "exec" : "other");
  const navigate = async (label: string, address: string): Promise<void> => {
    if (address === "about:blank") {
      calls.push(`${label}:about:blank`);
      if (opts.leaveFails) throw opts.leaveFails;
      return;
    }
    calls.push(label);
    const outcome = opts.nav?.(navCount++);
    if (outcome instanceof Error) throw outcome;
    if (outcome) await outcome;
  };
  const session = {
    exec: EXEC,
    automationName: "UiAutomator2",
    platformVersion: "15",
    async currentContext() { calls.push("currentContext"); return "NATIVE_APP"; },
    async switchToNative() {
      calls.push("native");
      const failure = opts.nativeFails?.(nativeCount++);
      if (failure) throw failure;
    },
    async probeScreenshot() { calls.push("probeScreenshot"); },
    async pageSource(signal: AbortSignal) {
      calls.push("source");
      signals.push(signal);
      if (opts.blockSource) {
        return new Promise<string>((_resolve, reject) => {
          signal.addEventListener("abort", () => reject(new Error("page source aborted")), { once: true });
        });
      }
      opts.onSource?.(sourceCount);
      const reply = sources[Math.min(sourceCount++, sources.length - 1)];
      clock += POLL_MS;
      if (reply instanceof Error) throw reply;
      return reply;
    },
    async readWebAddress() { throw new Error("预热不读地址"); },
    async withWebContext() { throw new Error("预热不进网页上下文执行"); },
    async openUrl(driver: Browser, address: string) { await navigate(`openUrl:${who(driver)}`, address); },
    async deleteSession() { calls.push("deleteSession"); },
  } as unknown as AppiumSession;
  const adapter: DriverAdapter = {
    async deepLink(driver: Browser, address: string, appId: string | null) {
      await navigate(`deepLink:${who(driver)}:${appId === null ? "null" : appId}`, address);
    },
    extractControls() { throw new Error("预热不抽控件摘要"); },
  };
  const controller = new AbortController();
  const budget: AcquireBudget = { signal: controller.signal, remainingMs: () => 600_000 };
  const statusCalls: number[] = [];
  const sessionStatus = opts.omitStatus ? undefined : async () => {
    statusCalls.push(clock);
    return opts.sessionStatus ? opts.sessionStatus() : "RUNNING";
  };
  const block = createDeviceWarmup({ log: (line) => logs.push(line), now: () => clock });
  const args: DeviceWarmupArgs = { session, adapter, route: opts.route ?? "url", url: WARMUP_URL, budget, sessionStatus };
  return {
    calls, logs, signals, statusCalls, controller,
    run: () => block.run(args),
    navCalls: () => calls.filter((c) => c.startsWith("openUrl") || c.startsWith("deepLink")),
  };
}

const navLabel = (route: "url" | "deep_link") => (route === "url" ? "openUrl:exec" : "deepLink:exec:null");

// ---- 标记：与桌面同源 ----

test("标记字符串与桌面预热同源：tunnel-warmup.mts 的常量逐项等于 fixture；尝试次数与桌面共用同一常量", () => {
  assert.deepEqual({ ...WARMUP_MARKERS }, FIXTURE.markers);
  assert.equal(DEVICE_WARMUP_ATTEMPTS, WARMUP_ATTEMPTS);
});

test("标记查找：按大小写精确匹配 fixture 的四个正文标记；页面标题（小写连字符）、地址栏里的预热路径与中间态都不算标记", () => {
  for (const [key, marker] of Object.entries(FIXTURE.markers)) {
    assert.equal(findWarmupMarker(androidTree(marker)), key, `Android ${marker}`);
    assert.equal(findWarmupMarker(iosTree(marker)), key, `iOS ${marker}`);
  }
  assert.equal(findWarmupMarker(androidTree(`${FIXTURE.markers.error} 503`)), "error", "ERROR 后带状态码仍是 ERROR");
  assert.equal(findWarmupMarker(LOADING), null);
  const titlesOnly = Object.values(FIXTURE.titles).map((t) => `<node text="${t}"/>`).join("");
  assert.equal(findWarmupMarker(titlesOnly), null);
  assert.equal(findWarmupMarker(androidTree(FIXTURE.markers.ready.toLowerCase())), null);
});

// ---- 归因真值表 ----

test("READY：就绪（返回 null），只导航一次", async () => {
  for (const route of ["url", "deep_link"] as const) {
    const h = harness({ route, sources: [iosTree(FIXTURE.markers.ready)] });
    assert.equal(await h.run(), null);
    assert.deepEqual(h.navCalls().filter((c) => !c.endsWith("about:blank")), [navLabel(route)]);
  }
});

test("AUTH REQUIRED：precheck_failed，消息与桌面预热逐字相同，不重试", async () => {
  const h = harness({ sources: [androidTree(FIXTURE.markers.auth_required)] });
  assert.deepEqual(await h.run(), { errorType: "precheck_failed", message: WARMUP_AUTH_REQUIRED_MESSAGE });
  assert.deepEqual(h.navCalls(), ["openUrl:exec"]);
});

test("DENIED：precheck_failed，消息与令牌被拒不同，不重试", async () => {
  const h = harness({ route: "deep_link", sources: [iosTree(FIXTURE.markers.denied)] });
  assert.deepEqual(await h.run(), { errorType: "precheck_failed", message: WARMUP_DENIED_MESSAGE });
  assert.deepEqual(h.navCalls(), ["deepLink:exec:null"]);
  assert.notEqual(WARMUP_DENIED_MESSAGE, WARMUP_AUTH_REQUIRED_MESSAGE);
});

test("ERROR 一直不变：每次在标记等待期内读到 ERROR 后原地重导航，共 3 次，耗尽归 engine_error", async () => {
  const h = harness({ sources: [androidTree(`${FIXTURE.markers.error} 503`)] });
  const got = await h.run();
  assert.deepEqual(got, {
    errorType: "engine_error", message: warmupErrorMessage(DEVICE_WARMUP_ATTEMPTS, `预热页面标记为 ${FIXTURE.markers.error}`),
  });
  assert.deepEqual(h.navCalls(), Array(DEVICE_WARMUP_ATTEMPTS).fill("openUrl:exec"));
});

test("等待期内没有任何标记：每次尝试读到等待期结束（与桌面同一常量），再原地重导航，耗尽归 engine_error", async () => {
  const h = harness({ route: "deep_link", sources: [LOADING] });
  const got = await h.run();
  assert.equal(got?.errorType, "engine_error");
  assert.equal(got?.message, warmupErrorMessage(DEVICE_WARMUP_ATTEMPTS, `预热页面在 ${WARMUP_MARKER_WAIT_MS / 1000} 秒内没有给出任何标记`));
  assert.deepEqual(h.navCalls(), Array(DEVICE_WARMUP_ATTEMPTS).fill("deepLink:exec:null"));
  const perAttempt = WARMUP_MARKER_WAIT_MS / POLL_MS;
  assert.equal(h.calls.filter((c) => c === "source").length, DEVICE_WARMUP_ATTEMPTS * perAttempt);
});

test("ERROR 之后的重导航读到 READY：就绪，共导航两次", async () => {
  const perAttempt = WARMUP_MARKER_WAIT_MS / POLL_MS;
  const sources = [...Array(perAttempt).fill(androidTree(FIXTURE.markers.error)), androidTree(FIXTURE.markers.ready)];
  const h = harness({ sources });
  assert.equal(await h.run(), null);
  assert.deepEqual(h.navCalls(), ["openUrl:exec", "openUrl:exec", "openUrl:exec:about:blank"]);
});

test("等待期内先读到 ERROR、随后变成 READY（导航返回时界面还是上一页）：同一次尝试内就绪，不重导航", async () => {
  const h = harness({ route: "deep_link", sources: [androidTree(FIXTURE.markers.error), LOADING, androidTree(FIXTURE.markers.ready)] });
  assert.equal(await h.run(), null);
  assert.deepEqual(h.navCalls(), ["deepLink:exec:null"]);
});

test("任何失败情形都不归 network_error：连接中断、客户端超时、导航挂到执行实例超时，耗尽后一律 engine_error", async () => {
  const errors = [
    Object.assign(new Error("Request failed with error code ECONNRESET"), { code: "ECONNRESET" }),
    Object.assign(new Error('Request timed out! Consider increasing the "connectionRetryTimeout" option.'), { code: "ETIMEDOUT" }),
    Object.assign(new Error("Request failed with error code UND_ERR_CLOSED"), { code: "UND_ERR_CLOSED" }),
    new Error("net::ERR_NAME_NOT_RESOLVED"),
  ];
  for (const e of errors) {
    const h = harness({ nav: () => e });
    const got = await h.run();
    assert.equal(got?.errorType, "engine_error", e.message);
    assert.notEqual(got?.errorType, "network_error");
    assert.equal(h.navCalls().length, DEVICE_WARMUP_ATTEMPTS);
  }
});

// ---- 导航预算与重试上限 ----

test("导航超时计一次尝试：第一次导航报客户端超时，第二次导航后 READY，就绪", async () => {
  const timeout = Object.assign(new Error('Request timed out! Consider increasing the "connectionRetryTimeout" option.'), {
    code: "ETIMEDOUT",
  });
  const h = harness({ nav: (n) => (n === 0 ? timeout : undefined) });
  assert.equal(await h.run(), null);
  assert.deepEqual(h.navCalls(), ["openUrl:exec", "openUrl:exec", "openUrl:exec:about:blank"]);
  assert.ok(h.logs.some((l) => l.includes("Request timed out")), "失败原因进 worker 日志");
});

test("重试上限：导航每次都失败时恰好导航 DEVICE_WARMUP_ATTEMPTS 次，消息记已尝试次数与最后一次的原因", async () => {
  const h = harness({ route: "deep_link", nav: (n) => new Error(`第 ${n + 1} 次导航失败`) });
  const got = await h.run();
  assert.equal(h.navCalls().length, DEVICE_WARMUP_ATTEMPTS);
  assert.deepEqual(got, {
    errorType: "engine_error", message: warmupErrorMessage(DEVICE_WARMUP_ATTEMPTS, `预热导航失败：第 ${DEVICE_WARMUP_ATTEMPTS} 次导航失败`),
  });
});

test("导航不被本块放弃：导航迟迟不返回时本块一直等它（上界只由执行实例的单请求超时给出），返回后照常读标记", async () => {
  let release!: () => void;
  const pending = new Promise<void>((resolve) => { release = resolve; });
  const h = harness({ nav: (n) => (n === 0 ? pending : undefined) });
  let settled = false;
  const result = h.run().then((v) => { settled = true; return v; });
  for (let i = 0; i < 20; i++) await new Promise((r) => setImmediate(r));
  assert.equal(settled, false);
  assert.deepEqual(h.calls, ["openUrl:exec"], "导航未返回前不读控件树、不重导航");
  release();
  assert.equal(await result, null);
});

test("本块不在导航上另设上限：代码（不含注释）里没有 Promise.race、setTimeout，也不引用桌面预热的 30 秒导航超时（标记等待期的截止信号只交给控件树的读取）", () => {
  const source = fs.readFileSync(path.resolve(HERE, "warmup.mts"), "utf-8")
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .split("\n").filter((line) => !line.trim().startsWith("//")).map((line) => line.replace(/\s\/\/ .*$/, "")).join("\n");
  assert.ok(!source.includes("Promise.race"));
  assert.ok(!source.includes("WARMUP_NAV_TIMEOUT_MS"));
  assert.ok(!/setTimeout\s*\(/.test(source));
});

// ---- 路线与通道 ----

test("路线只由传入的探测结论决定：url 经 openUrl 在网页上下文打开，deep_link 交给系统浏览器（appId 为 null）", async () => {
  const url = harness({ route: "url" });
  await url.run();
  assert.ok(url.calls.includes("openUrl:exec"));
  assert.ok(!url.calls.some((c) => c.startsWith("deepLink")));
  const dl = harness({ route: "deep_link" });
  await dl.run();
  assert.ok(dl.calls.includes("deepLink:exec:null"));
  assert.ok(!dl.calls.some((c) => c.startsWith("openUrl")));
});

test("重试不换路线：url 路线导航失败三次也不改走 deepLink，deep_link 路线同理", async () => {
  for (const route of ["url", "deep_link"] as const) {
    const h = harness({ route, nav: () => new Error("导航失败") });
    await h.run();
    assert.deepEqual(h.navCalls(), Array(DEVICE_WARMUP_ATTEMPTS).fill(navLabel(route)), route);
  }
});

test("生命周期通道：导航命令由执行实例发出（不是命令守卫代理），每次读标记之前先切回原生上下文", async () => {
  const h = harness({ route: "url", sources: [LOADING, androidTree(FIXTURE.markers.ready)] });
  await h.run();
  assert.deepEqual(h.calls.slice(0, 4), ["openUrl:exec", "native", "source", "source"]);
  assert.ok(h.navCalls().every((c) => c.startsWith("openUrl:exec")), "所有导航都经执行实例");
});

// ---- 就绪后的离开规则 ----

test("url 路线就绪后导航到 about:blank 并切回原生上下文", async () => {
  const h = harness({ route: "url" });
  assert.equal(await h.run(), null);
  assert.deepEqual(h.calls.slice(-2), ["openUrl:exec:about:blank", "native"]);
});

test("deep_link 路线就绪后不离开预热页：读到 READY 之后不再发任何导航", async () => {
  const h = harness({ route: "deep_link" });
  assert.equal(await h.run(), null);
  assert.equal(h.calls.at(-1), "source");
  assert.ok(!h.calls.some((c) => c.includes("about:blank")));
});

test("离开失败只记日志、不影响判定（仍为就绪），日志里没有预热地址的令牌", async () => {
  const h = harness({ route: "url", leaveFails: new Error(`cannot navigate from ${WARMUP_URL}`) });
  assert.equal(await h.run(), null);
  const line = h.logs.find((l) => l.includes("离开预热页"));
  assert.ok(line, "离开失败写进 worker 日志");
  assert.ok(!line.includes(TOKEN));
});

test("拒绝与无法确认时不离开：DENIED 与重试耗尽都不导航 about:blank", async () => {
  for (const sources of [[androidTree(FIXTURE.markers.denied)], [LOADING]]) {
    const h = harness({ route: "url", sources });
    assert.notEqual(await h.run(), null);
    assert.ok(!h.calls.some((c) => c.includes("about:blank")));
  }
});

// ---- 会话状态与获取预算 ----

test("导航失败先查会话状态：非 RUNNING 归 session_lost，不再重导航", async () => {
  for (const status of ["STOPPING", "COMPLETED"]) {
    const h = harness({ nav: () => new Error("connection closed"), sessionStatus: async () => status });
    assert.deepEqual(await h.run(), { errorType: "session_lost", message: SESSION_LOST_MESSAGE });
    assert.equal(h.navCalls().length, 1, status);
    assert.equal(h.statusCalls.length, 1);
  }
});

test("会话仍在运行、状态查询失败（null 或抛出）或未传状态查询时：不据此判会话丢失，照常重试", async () => {
  const cases: Array<Pick<HarnessOptions, "sessionStatus" | "omitStatus">> = [
    { sessionStatus: async () => "RUNNING" },
    { sessionStatus: async () => null },
    { sessionStatus: async () => { throw new Error("GetRemoteAccessSession 超时"); } },
    { omitStatus: true },
  ];
  for (const c of cases) {
    const h = harness({ ...c, nav: () => new Error("导航失败") });
    assert.equal((await h.run())?.errorType, "engine_error");
    assert.equal(h.navCalls().length, DEVICE_WARMUP_ATTEMPTS);
  }
});

test("导航异常带非会话丢失的归类标记：计一次尝试并原地重导航，耗尽后的消息用标记的消息作原因", async () => {
  const marked = attachClassification(new Error("deepLink failed"), {
    errorType: "capability_unavailable", message: "这台设备不支持打开地址",
  });
  const h = harness({ route: "deep_link", nav: () => marked });
  assert.deepEqual(await h.run(), {
    errorType: "engine_error", message: warmupErrorMessage(DEVICE_WARMUP_ATTEMPTS, "预热导航失败：这台设备不支持打开地址"),
  });
  assert.equal(h.navCalls().length, DEVICE_WARMUP_ATTEMPTS);
});

test("归类标记的消息同样先脱敏再截断：标记消息里带着预热地址时，终止消息只剩掩码", async () => {
  const marked = attachClassification(new Error("deepLink failed"), {
    errorType: "engine_error", message: `无法打开 ${WARMUP_URL}`,
  });
  const h = harness({ route: "deep_link", nav: () => marked });
  const got = await h.run();
  assert.equal(got?.errorType, "engine_error");
  assert.ok(!got!.message.includes(TOKEN), got!.message);
  assert.ok(got!.message.includes("***"));
});

test("异常已带 session_lost 归类标记时直接归 session_lost，不必再查状态", async () => {
  const lost = attachClassification(new Error("session ended"), { errorType: "session_lost", message: SESSION_LOST_MESSAGE });
  const h = harness({ omitStatus: true, nav: () => lost });
  assert.deepEqual(await h.run(), { errorType: "session_lost", message: SESSION_LOST_MESSAGE });
  assert.equal(h.navCalls().length, 1);
});

test("读控件树失败：先查会话状态，仍在运行则计一次尝试、原地重导航；非 RUNNING 归 session_lost", async () => {
  const running = harness({ sources: [new Error("getPageSource failed"), androidTree(FIXTURE.markers.ready)] });
  assert.equal(await running.run(), null);
  assert.deepEqual(running.navCalls(), ["openUrl:exec", "openUrl:exec", "openUrl:exec:about:blank"]);
  assert.equal(running.statusCalls.length, 1);
  const lost = harness({ sources: [new Error("getPageSource failed")], sessionStatus: async () => "COMPLETED" });
  assert.equal((await lost.run())?.errorType, "session_lost");
  assert.equal(lost.navCalls().length, 1);
});

test("切回原生上下文失败计一次尝试并先查会话状态：仍在运行则原地重导航", async () => {
  const h = harness({ nativeFails: (n) => (n === 0 ? new Error("switchContext failed") : undefined) });
  assert.equal(await h.run(), null);
  assert.deepEqual(h.navCalls(), ["openUrl:exec", "openUrl:exec", "openUrl:exec:about:blank"]);
  assert.equal(h.statusCalls.length, 1);
  const lost = harness({ nativeFails: () => new Error("switchContext failed"), sessionStatus: async () => "STOPPING" });
  assert.equal((await lost.run())?.errorType, "session_lost");
  assert.equal(lost.navCalls().length, 1);
});

test("获取预算中止后不再发起新的尝试：导航失败的同时预算到期，只导航一次", async () => {
  const h = harness({ nav: () => new Error("导航失败") });
  const pending = h.run();
  h.controller.abort(new Error("获取预算到期"));
  const got = await pending;
  assert.equal(got?.errorType, "engine_error", "归因由设备侧接缝按预算改写为 acquire_timeout");
  assert.equal(h.navCalls().length, 1);
});

test("获取预算的中止信号穿进控件树的读取：读取挂着时预算中止，读取随之结束，不再重导航", async () => {
  const h = harness({ route: "deep_link", blockSource: true });
  const pending = h.run();
  for (let i = 0; i < 5; i++) await new Promise((r) => setImmediate(r));
  assert.deepEqual(h.calls, ["deepLink:exec:null", "native", "source"]);
  h.controller.abort(new Error("进入终结"));
  assert.equal((await pending)?.errorType, "engine_error");
  assert.ok(h.signals[0].aborted);
  assert.deepEqual(h.navCalls(), ["deepLink:exec:null"]);
});

test("导航挂着时获取预算中止：导航返回后不再切回原生上下文、不读控件树、不重导航", async () => {
  let release!: () => void;
  const pending = new Promise<void>((resolve) => { release = resolve; });
  const h = harness({ nav: (n) => (n === 0 ? pending : undefined) });
  const result = h.run();
  for (let i = 0; i < 5; i++) await new Promise((r) => setImmediate(r));
  h.controller.abort(new Error("进入终结"));
  release();
  assert.equal((await result)?.errorType, "engine_error");
  assert.deepEqual(h.calls, ["openUrl:exec"]);
});

test("url 路线读到 READY 的同时获取预算中止：不再离开预热页，读到 READY 之后不向设备发任何命令", async () => {
  const h: ReturnType<typeof harness> = harness({ route: "url", onSource: () => h.controller.abort(new Error("进入终结")) });
  assert.equal(await h.run(), null);
  assert.equal(h.calls.at(-1), "source");
  assert.ok(!h.calls.some((c) => c.includes("about:blank")));
});

// ---- 脱敏 ----

test("预热地址不进日志与消息：导航错误文本带着预热地址与设备端点时，日志与终止消息里只剩掩码", async () => {
  const leak = new Error(`WebDriverError: Request failed when running "${ENDPOINT}/session/abc/url" with body {"url":"${WARMUP_URL}"}`);
  const h = harness({ nav: () => leak });
  const got = await h.run();
  assert.equal(got?.errorType, "engine_error");
  for (const text of [got!.message, ...h.logs]) {
    assert.ok(!text.includes(TOKEN), `令牌外泄：${text}`);
    assert.ok(!text.includes("Ab9Ab9Ab9"), `端点令牌外泄：${text}`);
  }
  assert.ok(got!.message.includes("***"));
});

test("就绪路径的日志同样不带预热地址", async () => {
  for (const route of ["url", "deep_link"] as const) {
    const h = harness({ route, sources: [LOADING, androidTree(FIXTURE.markers.ready)] });
    await h.run();
    assert.ok(h.logs.length > 0);
    for (const line of h.logs) assert.ok(!line.includes(TOKEN) && !line.includes(FIXTURE.warmup_path), line);
  }
});
