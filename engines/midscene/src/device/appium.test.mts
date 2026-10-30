// Appium 建连与上下文切换的单测（ADR 0052 决策 3、5、6；ADR 0051 决策 3、9、11）。运行：npx tsx --test src/device/appium.test.mts。
//
// 两层：
//   - 编排层：WebdriverIO 的 remote / attach 换成记录调用的假入口，核对能力集按目标的字段清单、三个实例各自的超时与重试、执行实例先于
//     探测实例发出第一条会话命令、newSession 的封顶与重试归因、拒装驱动辅助包与非瞬时失败的归类，以及会话能力的唯一读取点；
//   - 真实运行层：真 webdriverio 对本机的假 WebDriver 服务建会话，核对 SDK 的真实行为——iOS Safari 会话上 remote() 返回前由建连实例
//     发出的那条请求确实会把连接池的超时定成建连实例的值（本模块据此修正）、修正之后执行实例的长命令不被建连实例与探测实例的短超时
//     切断、探测实例的短超时自己生效、截止信号中止在途请求、状态码挂到错误对象上、执行期传输层 0 次重试、newSession 失败消息不带端点
//     令牌与签名。Device Farm 端点与真机上的表现（directConnect、服务端是否串行执行）不在这里证明，列入真机验收。
import { test } from "node:test";
import assert from "node:assert";
import * as http from "node:http";
import { attach as wdioAttach, remote as wdioRemote, type Browser } from "webdriverio";
import {
  CLIENT_TIMEOUTS, CONNECTION_ERROR_CODES, TIMEOUT_ERROR_CODES, commandFailureKind, createAppiumConnector, httpStatusOf,
  newSessionCapabilities, newSessionRejectedMessage, readSessionCapabilities, withDeadline, type AppiumConnectorOptions,
  type ClientTimeouts, type WdioEntry,
} from "./appium.mjs";
import {
  EXEC_REQUEST_TIMEOUT_MS, NEW_COMMAND_TIMEOUT_S, NEW_SESSION_TIMEOUT_FLOOR_MS, PAGE_LOAD_TIMEOUT_MS, PROBE_TIMEOUT_MS,
} from "./limits.mjs";
import { ACQUIRE_TIMEOUT_MESSAGE, type AcquireBudget, type ConnectOutcome, type ConnectRequest } from "./surface.mjs";
import { WDIO_LOG_LEVEL, wdioLogMaskingInstalled } from "./wdio-log.mjs";

const TOKEN = "SECRETTOKEN0123456789abcdef";
const ENDPOINT = `https://devicefarm-interactive-global.us-west-2.api.aws/remote-endpoint/${TOKEN}`;
const PRESIGNED = "https://gherkai-apps.s3.us-west-2.amazonaws.com/apps/9f2c/shop.apk?X-Amz-Algorithm=AWS4-HMAC-SHA256" +
  "&X-Amz-Credential=AKIAEXAMPLE%2F20261030%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20261030T000000Z&X-Amz-Expires=3600" +
  "&X-Amz-SignedHeaders=host&X-Amz-Signature=0123456789abcdef0123456789abcdef";

function budgetOf(remaining: { ms: number }): AcquireBudget & { controller: AbortController } {
  const controller = new AbortController();
  return { controller, signal: controller.signal, remainingMs: () => remaining.ms };
}

const webReq = (device: "android" | "ios" = "android", endpoint = ENDPOINT): ConnectRequest =>
  ({ endpoint, device, uiKind: "web", appId: null, appUrl: null });
const appReq = (device: "android" | "ios" = "android"): ConnectRequest =>
  ({ endpoint: ENDPOINT, device, uiKind: "app", appId: device === "android" ? "com.example.shop" : "com.example.Shop", appUrl: PRESIGNED });

// ---- 能力集与会话能力 ----

test("能力集按目标的字段清单：网页目标带 browserName，应用目标带预签名地址、关自动启动与重置，Android 应用另带 appPackage", () => {
  const common = { "appium:newCommandTimeout": NEW_COMMAND_TIMEOUT_S };
  assert.deepEqual(newSessionCapabilities(webReq("android")),
    { platformName: "Android", "appium:automationName": "UiAutomator2", browserName: "Chrome", ...common });
  assert.deepEqual(newSessionCapabilities(webReq("ios")),
    { platformName: "iOS", "appium:automationName": "XCUITest", browserName: "Safari", ...common });
  assert.deepEqual(newSessionCapabilities(appReq("android")), {
    platformName: "Android", "appium:automationName": "UiAutomator2", ...common,
    "appium:app": PRESIGNED, "appium:autoLaunch": false, "appium:noReset": true, "appium:appPackage": "com.example.shop",
  });
  assert.deepEqual(newSessionCapabilities(appReq("ios")), {
    platformName: "iOS", "appium:automationName": "XCUITest", ...common,
    "appium:app": PRESIGNED, "appium:autoLaunch": false, "appium:noReset": true,
  });
  assert.equal(NEW_COMMAND_TIMEOUT_S, 900);
  assert.throws(() => newSessionCapabilities({ ...appReq(), appUrl: null }));
});

test("会话能力的唯一读取点：automationName 与系统版本带不带 appium: 前缀都认，缺失时给空串与 null", () => {
  assert.deepEqual(readSessionCapabilities({ "appium:automationName": "XCUITest", platformVersion: "18.6" }),
    { automationName: "XCUITest", platformVersion: "18.6" });
  assert.deepEqual(readSessionCapabilities({ automationName: "UiAutomator2", "appium:platformVersion": 15 }),
    { automationName: "UiAutomator2", platformVersion: "15" });
  assert.deepEqual(readSessionCapabilities(null), { automationName: "", platformVersion: null });
});

// ---- 编排层：假入口 ----

interface FakeClient {
  role: string;
  options: Record<string, unknown>;
}

interface FakeWdioScript {
  /** 依次的 newSession 结果；"ok" 建好会话。错误可带 status：先经 transformResponse 报给钩子再抛出。 */
  newSession?: Array<"ok" | (Error & { status?: number })>;
  capabilities?: Record<string, unknown>;
  firstCommandFails?: boolean;
  pageLoadFails?: boolean;
  /** remote 返回前调用（测试在这里中止预算或推进剩余时间）。 */
  onRemote?: (attempt: number) => void;
}

function fakeWdio(script: FakeWdioScript = {}) {
  const calls: string[] = [];
  const remotes: Array<{ options: Record<string, unknown>; afterModifier: Record<string, unknown> }> = [];
  const attaches: FakeClient[] = [];
  const queue = [...(script.newSession ?? ["ok"])];
  const capabilities = script.capabilities ?? { platformName: "Android", "appium:automationName": "UiAutomator2", platformVersion: "14" };
  let n = 0;
  const entry: WdioEntry = {
    remote: (async (options: Record<string, unknown>, modifier?: (c: unknown, o: Record<string, unknown>) => unknown) => {
      n++;
      calls.push("remote");
      const record = { options: { ...options }, afterModifier: {} as Record<string, unknown> };
      remotes.push(record);
      script.onRemote?.(n);
      const next = queue.shift() ?? "ok";
      if (next !== "ok") {
        if (next.status !== undefined) {
          (options.transformResponse as (r: { statusCode: number }, o: object) => unknown)({ statusCode: next.status }, {});
        }
        throw next;
      }
      const client = {
        sessionId: `0f0f-${n}`, capabilities,
        async deleteSession() { calls.push("connect.deleteSession"); },
      };
      modifier?.(client, options);
      record.afterModifier = { ...options };
      return client;
    }) as unknown as WdioEntry["remote"],
    attach: (async (options: Record<string, unknown>) => {
      const role = `attach${attaches.length + 1}`;
      calls.push(role);
      attaches.push({ role, options: { ...options } });
      return {
        on() {},
        async getContext() {
          calls.push(`${role}.getContext`);
          if (script.firstCommandFails) throw new Error("UND_ERR_CLOSED");
          return "NATIVE_APP";
        },
        async setTimeout(t: { pageLoad?: number }) {
          calls.push(`${role}.setTimeout:${t.pageLoad}`);
          if (script.pageLoadFails) throw new Error("not implemented");
        },
      } as unknown as Browser;
    }) as unknown as WdioEntry["attach"],
  };
  return { entry, calls, remotes, attaches };
}

function connector(f: ReturnType<typeof fakeWdio>, extra: AppiumConnectorOptions = {}) {
  const logs: string[] = [];
  const order: string[] = f.calls;
  return {
    logs,
    connector: createAppiumConnector({
      wdio: f.entry, installLogMasking: () => { order.push("installLogMasking"); }, log: (l) => logs.push(l), ...extra,
    }),
  };
}

const clientTimeoutError = (): Error => new Error(
  `WebDriverError: Request timed out! Consider increasing the "connectionRetryTimeout" option. when running "${ENDPOINT}/session" with method "POST"`,
);

test("三个实例的超时与重试各自显式设定：建连取下限与剩余预算的较小者，执行与探测各自的单请求超时，传输层都不重试", async () => {
  const f = fakeWdio();
  const { connector: c } = connector(f);
  const outcome = await c.connect(webReq(), budgetOf({ ms: 600_000 }));
  assert.equal(outcome.kind, "connected");
  const [remote] = f.remotes;
  assert.equal(remote!.options.connectionRetryTimeout, NEW_SESSION_TIMEOUT_FLOOR_MS);
  assert.equal(NEW_SESSION_TIMEOUT_FLOOR_MS, 4 * 60_000 + 65_000);
  for (const options of [remote!.options, ...f.attaches.map((a) => a.options)]) {
    assert.equal(options.connectionRetryCount, 0);
    assert.equal(options.logLevel, WDIO_LOG_LEVEL);
    assert.equal(options.logLevel, "error");
    assert.equal(options.enableDirectConnect, false);
    assert.equal(options.protocol, "https");
    assert.equal(options.hostname, "devicefarm-interactive-global.us-west-2.api.aws");
    assert.equal(options.port, 443);
    assert.equal(options.path, `/remote-endpoint/${TOKEN}`);
    assert.equal(typeof options.transformRequest, "function");
    assert.equal(typeof options.transformResponse, "function");
  }
  assert.deepEqual(remote!.options.capabilities, newSessionCapabilities(webReq()));
  assert.deepEqual(f.attaches.map((a) => a.options.connectionRetryTimeout), [EXEC_REQUEST_TIMEOUT_MS, PROBE_TIMEOUT_MS]);
  assert.equal(EXEC_REQUEST_TIMEOUT_MS, 180_000);
  assert.equal(PROBE_TIMEOUT_MS, 5_000);
  assert.deepEqual(f.attaches.map((a) => a.options.sessionId), ["0f0f-1", "0f0f-1"]);
  assert.equal(f.calls[0], "installLogMasking", "建第一个实例之前装好日志掩码");
});

test("建会话之后、探测实例建立之前，第一条会话命令由执行实例发出；网页目标另由执行实例设页面加载超时", async () => {
  const web = fakeWdio();
  await connector(web).connector.connect(webReq(), budgetOf({ ms: 600_000 }));
  assert.deepEqual(web.calls, [
    "installLogMasking", "remote", "attach1", "attach1.getContext", `attach1.setTimeout:${PAGE_LOAD_TIMEOUT_MS}`, "attach2",
  ]);
  assert.equal(web.attaches[0]!.options.connectionRetryTimeout, EXEC_REQUEST_TIMEOUT_MS, "attach1 是执行实例");

  const app = fakeWdio();
  await connector(app).connector.connect(appReq(), budgetOf({ ms: 600_000 }));
  assert.deepEqual(app.calls, ["installLogMasking", "remote", "attach1", "attach1.getContext", "attach2"], "应用目标不设页面加载超时");
});

test("newSession 返回后，建连实例此后的单请求超时改为执行实例的值（iOS Safari 上 remote() 返回前它还会再发一条请求）", async () => {
  const f = fakeWdio();
  await connector(f).connector.connect(webReq("ios"), budgetOf({ ms: 30_000 }));
  assert.equal(f.remotes[0]!.options.connectionRetryTimeout, 30_000, "newSession 本身被剩余预算封顶");
  assert.equal(f.remotes[0]!.afterModifier.connectionRetryTimeout, EXEC_REQUEST_TIMEOUT_MS);
});

test("未能设置页面加载超时只记日志、照常建好会话（它本就只是尽力而为）", async () => {
  const f = fakeWdio({ pageLoadFails: true });
  const { connector: c, logs } = connector(f);
  assert.equal((await c.connect(webReq(), budgetOf({ ms: 600_000 }))).kind, "connected");
  assert.equal(logs.length, 1);
  assert.ok(logs[0]!.startsWith("worker: 未能设置页面加载超时"));
});

test("建好的会话交出执行实例、探测实例与会话回报的事实", async () => {
  const f = fakeWdio({ capabilities: { platformName: "iOS", "appium:automationName": "XCUITest", platformVersion: "18.6" } });
  const outcome = await connector(f).connector.connect(webReq("ios"), budgetOf({ ms: 600_000 }));
  assert.equal(outcome.kind, "connected");
  if (outcome.kind !== "connected") return;
  assert.equal(outcome.session.automationName, "XCUITest");
  assert.equal(outcome.session.platformVersion, "18.6");
  assert.ok(outcome.session.exec !== undefined);
  assert.ok((outcome.session as unknown as { probe?: unknown }).probe !== undefined);
});

// ---- newSession 的封顶与重试归因 ----

async function connectWith(script: FakeWdioScript, remaining: { ms: number }, req: ConnectRequest = webReq()) {
  const f = fakeWdio(script);
  const outcome = await connector(f).connector.connect(req, budgetOf(remaining));
  return { outcome, remotes: f.remotes, calls: f.calls };
}

const ACQUIRE_TIMED_OUT: ConnectOutcome = {
  kind: "terminated", termination: { errorType: "acquire_timeout", message: ACQUIRE_TIMEOUT_MESSAGE },
};

test("被剩余预算封顶的 newSession 客户端超时归 acquire_timeout，不重试", async () => {
  const { outcome, remotes } = await connectWith({ newSession: [clientTimeoutError()] }, { ms: 60_000 });
  assert.deepEqual(outcome, ACQUIRE_TIMED_OUT);
  assert.equal(remotes.length, 1);
  assert.equal(remotes[0]!.options.connectionRetryTimeout, 60_000);
});

test("未封顶的客户端超时是瞬时失败：预算允许时只重试 newSession 一次，第二次的超时取当时的剩余预算", async () => {
  const remaining = { ms: 900_000 };
  const ok = await connectWith({
    newSession: [clientTimeoutError(), "ok"],
    onRemote: (attempt) => { if (attempt === 1) remaining.ms = 900_000 - NEW_SESSION_TIMEOUT_FLOOR_MS; },
  }, remaining);
  assert.equal(ok.outcome.kind, "connected");
  assert.equal(ok.remotes.length, 2);
  assert.equal(ok.remotes[0]!.options.connectionRetryTimeout, NEW_SESSION_TIMEOUT_FLOOR_MS);
  assert.equal(ok.remotes[1]!.options.connectionRetryTimeout, NEW_SESSION_TIMEOUT_FLOOR_MS, "剩余 595 秒，仍取下限");

  const twice = await connectWith({ newSession: [clientTimeoutError(), clientTimeoutError()] }, { ms: 900_000 });
  assert.deepEqual(twice.outcome, ACQUIRE_TIMED_OUT, "只重试一次，重试之后仍超时归 acquire_timeout");
  assert.equal(twice.remotes.length, 2);

  const noBudget = { ms: 600_000 };
  const exhausted = await connectWith({
    newSession: [clientTimeoutError()], onRemote: () => { noBudget.ms = 0; },
  }, noBudget);
  assert.deepEqual(exhausted.outcome, ACQUIRE_TIMED_OUT, "预算不够再重试一次");
  assert.equal(exhausted.remotes.length, 1);
});

test("传输层失败（连接层错误、连接被拒、HTTP 502 / 503 / 504）同样只重试 newSession 一次", async () => {
  const reset = new Error(`WebDriverError: Request failed with error code ECONNRESET when running "${ENDPOINT}/session" with method "POST"`);
  const refused = new Error('Unable to connect to "https://devicefarm-interactive-global.us-west-2.api.aws:443/remote-endpoint/x", make sure browser driver is running on that address.');
  const unavailable = Object.assign(new Error("WebDriverError: Service Unavailable"), { status: 503 });
  for (const failure of [reset, refused, unavailable]) {
    const { outcome, remotes } = await connectWith({ newSession: [failure, "ok"] }, { ms: 900_000 });
    assert.equal(outcome.kind, "connected", failure.message);
    assert.equal(remotes.length, 2);
  }
});

test("设备单元拒装驱动辅助包：返回 replace_device（换不换台由接缝决定），原因已脱敏、去掉端点与能力集，不重试", async () => {
  const refusal = new Error(
    "WebDriverError: An unknown server-side error occurred while processing the command. Original error: Failure " +
    `[INSTALL_FAILED_USER_RESTRICTED: Install canceled by user] when running "${ENDPOINT}/session" with method "POST" and args "{}"`,
  );
  const { outcome, remotes } = await connectWith({ newSession: [refusal] }, { ms: 900_000 });
  assert.equal(outcome.kind, "replace_device");
  if (outcome.kind !== "replace_device") return;
  assert.ok(outcome.reason.includes("INSTALL_FAILED_USER_RESTRICTED"));
  assert.ok(!outcome.reason.includes(TOKEN) && !outcome.reason.includes("when running"));
  assert.equal(remotes.length, 1);
});

test("newSession 的非瞬时失败（服务端拒绝建会话、安装失败）归 precheck_failed，消息带脱敏后的服务端原因，不重试", async () => {
  const rejected = Object.assign(new Error(
    `WebDriverError: An unknown server-side error occurred while processing the command. Original error: Could not install app from ${PRESIGNED} ` +
    `when running "${ENDPOINT}/session" with method "POST" and args "{\\"capabilities\\":{}}"`,
  ), { status: 500 });
  const { outcome, remotes } = await connectWith({ newSession: [rejected] }, { ms: 900_000 }, appReq());
  assert.equal(outcome.kind, "terminated");
  if (outcome.kind !== "terminated") return;
  assert.equal(outcome.termination.errorType, "precheck_failed");
  assert.ok(outcome.termination.message.startsWith("设备未能建立执行测试所需的 Appium 会话：An unknown server-side error"));
  assert.ok(!outcome.termination.message.includes(TOKEN));
  assert.ok(!outcome.termination.message.includes("0123456789abcdef0123456789abcdef"), "预签名地址的签名已盖住");
  assert.ok(!outcome.termination.message.includes("AKIAEXAMPLE"));
  assert.equal(remotes.length, 1);
  assert.equal(newSessionRejectedMessage(""), "设备未能建立执行测试所需的 Appium 会话；请换一台设备后重试；应用目标请同时确认安装包能在这台设备上安装");
});

test("获取预算已中止（到期或进入终结）：不发 newSession，归 acquire_timeout；newSession 进行中中止同样归 acquire_timeout", async () => {
  const f = fakeWdio();
  const b = budgetOf({ ms: 600_000 });
  b.controller.abort(new Error("finalizing"));
  assert.deepEqual(await connector(f).connector.connect(webReq(), b), ACQUIRE_TIMED_OUT);
  assert.ok(!f.calls.includes("remote"));

  const b2 = budgetOf({ ms: 600_000 });
  const g = fakeWdio({
    newSession: [new Error("WebDriverError: finalizing when running \"x\" with method \"POST\"")],
    onRemote: () => b2.controller.abort(new Error("finalizing")),
  });
  assert.deepEqual(await connector(g).connector.connect(webReq(), b2), ACQUIRE_TIMED_OUT);
  assert.equal(g.remotes.length, 1);
});

test("newSession 之后的准备失败：先尽力删掉刚建好的 Appium 会话再抛出；预算已中止时不再发命令", async () => {
  const f = fakeWdio({ firstCommandFails: true });
  await assert.rejects(connector(f).connector.connect(webReq(), budgetOf({ ms: 600_000 })), /UND_ERR_CLOSED/);
  assert.equal(f.calls.at(-1), "connect.deleteSession");
  assert.ok(!f.calls.includes("attach2"), "第一条命令失败就不再建探测实例");

  const b = budgetOf({ ms: 600_000 });
  const g = fakeWdio({ firstCommandFails: true });
  const origAttach = g.entry.attach;
  g.entry.attach = (async (o: never) => { b.controller.abort(new Error("finalizing")); return origAttach(o); }) as never;
  await assert.rejects(connector(g).connector.connect(webReq(), b));
  assert.ok(!g.calls.includes("connect.deleteSession"));
});

// ---- 失败种类与状态码（纯函数）----

test("失败种类：一切超时（含真实网络的 ETIMEDOUT 与 undici 的三种超时码）归 client_timeout；连接层错误码、网关类状态码与其它服务端错误各自归类", () => {
  const timeout = Object.assign(new Error('WebDriverError: Request timed out! Consider increasing the "connectionRetryTimeout" option.'), { code: "ETIMEDOUT" });
  const netTimeout = Object.assign(new Error("WebDriverError: Request failed with error code ETIMEDOUT"), { code: "ETIMEDOUT" });
  assert.equal(commandFailureKind(timeout), "client_timeout");
  assert.equal(commandFailureKind(netTimeout), "client_timeout");
  for (const code of TIMEOUT_ERROR_CODES) assert.equal(commandFailureKind(Object.assign(new Error(code), { code })), "client_timeout");
  for (const code of CONNECTION_ERROR_CODES) assert.equal(commandFailureKind(Object.assign(new Error(code), { code })), "connection");
  for (const status of [502, 503, 504]) assert.equal(commandFailureKind(Object.assign(new Error("x"), { statusCode: status })), "gateway");
  assert.equal(commandFailureKind(Object.assign(new Error("x"), { statusCode: 500 })), "server");
  assert.equal(commandFailureKind(new Error("aborted")), "other");
  assert.equal(httpStatusOf("not an error"), null);
});

// ---- 真实运行层 ----

interface ServerScript {
  sessionCapabilities: Record<string, unknown>;
  /** 按「方法 路径尾」覆盖响应：延时、状态码与响应体，或直接断开连接。 */
  routes?: Record<string, { delayMs?: number; status?: number; body?: unknown; destroy?: boolean }>;
}

let sessionSeq = 0;

async function fakeWebDriver(script: ServerScript) {
  const seen: string[] = [];
  const bodies: Record<string, string> = {};
  const sessionId = `5e55${(++sessionSeq).toString(16).padStart(4, "0")}-0000`;
  const server = http.createServer((req, res) => {
    let body = "";
    req.on("data", (c) => { body += c; });
    req.on("end", () => {
      const url = req.url ?? "";
      const tail = url.includes("/session/") ? url.slice(url.indexOf("/session/") + `/session/${sessionId}`.length) : url.endsWith("/session") ? "/session" : url.slice(url.lastIndexOf("/"));
      const key = `${req.method} ${tail === "" ? "/" : tail}`;
      seen.push(key);
      bodies[key] = body;
      const route = script.routes?.[key];
      const reply = (status: number, value: unknown) => {
        res.writeHead(status, { "content-type": "application/json" });
        res.end(JSON.stringify({ value }));
      };
      setTimeout(() => {
        if (route?.destroy) return req.socket.destroy();
        if (route?.status !== undefined) return reply(route.status, route.body ?? { error: "unknown error", message: "boom", stacktrace: "" });
        if (key === "POST /session") return reply(200, { sessionId, capabilities: script.sessionCapabilities });
        if (key === "GET /context") return reply(200, "NATIVE_APP");
        if (key === "GET /contexts") return reply(200, ["NATIVE_APP", "WEBVIEW_1"]);
        if (key === "GET /source") return reply(200, "<hierarchy/>");
        if (key === "GET /screenshot") return reply(200, "iVBORw0KGgo=");
        if (key === "GET /status") return reply(200, { ready: true, build: { version: "2.11.5" } });
        return reply(200, null);
      }, route?.delayMs ?? 0);
    });
  });
  await new Promise<void>((r) => server.listen(0, "127.0.0.1", r));
  const port = (server.address() as { port: number }).port;
  return {
    sessionId, seen, bodies,
    endpoint: `http://127.0.0.1:${port}/remote-endpoint/${TOKEN}`,
    close: () => new Promise<void>((r) => { server.closeAllConnections(); server.close(() => r()); }),
  };
}

const IOS_SAFARI = { platformName: "iOS", browserName: "Safari", "appium:automationName": "XCUITest", platformVersion: "18.6" };
const ANDROID_APP = { platformName: "Android", "appium:automationName": "UiAutomator2", platformVersion: "14" };
const SHORT: ClientTimeouts = { newSessionFloorMs: 10_000, execRequestMs: 6_000, probeRequestMs: 200 };
// undici 连接池的超时计时器粒度约 0.5 到 1 秒：慢命令取 2.5 秒，才分得清「被池的短超时切断」与「完成」。
const SLOW_MS = 2_500;

test("真实运行：iOS Safari 会话上 remote() 返回前由建连实例再发一条请求，连接池的超时因此取建连实例的值（本模块修正的 SDK 行为）", async () => {
  const fake = await fakeWebDriver({ sessionCapabilities: IOS_SAFARI, routes: { "GET /source": { delayMs: SLOW_MS } } });
  const u = new URL(fake.endpoint);
  const base = { protocol: "http", hostname: u.hostname, port: Number(u.port), path: u.pathname, logLevel: WDIO_LOG_LEVEL, connectionRetryCount: 0 } as const;
  try {
    const connect = await wdioRemote({ ...base, connectionRetryTimeout: 300, capabilities: { platformName: "iOS", browserName: "Safari" } });
    assert.deepEqual(fake.seen, ["POST /session", "GET /context"], "remote() 返回前建连实例读了一次当前上下文");
    const exec = await wdioAttach({ ...base, sessionId: connect.sessionId, capabilities: connect.capabilities, connectionRetryTimeout: 6_000 });
    const started = Date.now();
    await assert.rejects(exec.getPageSource(), (e) => {
      assert.equal((e as { code?: string }).code, "UND_ERR_HEADERS_TIMEOUT", "执行实例 6 秒的超时被连接池里建连实例的 0.3 秒切断");
      assert.equal(commandFailureKind(e), "client_timeout", "池的超时同属超时，不是连接层错误");
      return true;
    });
    assert.ok(Date.now() - started < SLOW_MS);
  } finally {
    await fake.close();
  }
});

test("真实运行：修正之后执行实例的长命令不被建连实例与探测实例的短超时切断；探测实例自己的短超时照常生效", async () => {
  const fake = await fakeWebDriver({
    sessionCapabilities: IOS_SAFARI,
    routes: { "GET /source": { delayMs: SLOW_MS }, "GET /screenshot": { delayMs: SLOW_MS } },
  });
  try {
    const c = createAppiumConnector({ timeouts: SHORT });
    const outcome = await c.connect(webReq("ios", fake.endpoint), budgetOf({ ms: 300 }));
    assert.equal(outcome.kind, "connected");
    if (outcome.kind !== "connected") return;
    assert.ok(wdioLogMaskingInstalled(), "建连之前装上了日志掩码");
    assert.equal(fake.seen[0], "POST /session");
    assert.ok(fake.seen.includes("POST /timeouts"));
    assert.equal(JSON.parse(fake.bodies["POST /timeouts"]!).pageLoad, PAGE_LOAD_TIMEOUT_MS);
    const session = outcome.session;
    assert.equal(await session.pageSource(AbortSignal.timeout(10_000)), "<hierarchy/>", "2.5 秒的命令在 6 秒的执行实例上完成");

    const started = Date.now();
    await assert.rejects(session.probeScreenshot(), (e) => {
      assert.equal(commandFailureKind(e), "client_timeout");
      return true;
    });
    assert.ok(Date.now() - started < SLOW_MS - 1_000, "探测实例在自己的 0.2 秒超时上结束");
    assert.equal(await session.pageSource(AbortSignal.timeout(10_000)), "<hierarchy/>", "探测实例超时之后执行实例照常");
    await session.deleteSession();
    assert.equal(fake.seen.at(-1), "DELETE /");
  } finally {
    await fake.close();
  }
});

test("真实运行：截止信号中止在途请求本身（不是放弃等待）", async () => {
  const fake = await fakeWebDriver({ sessionCapabilities: ANDROID_APP, routes: { "GET /source": { delayMs: 2_000 } } });
  try {
    const outcome = await createAppiumConnector({ timeouts: SHORT }).connect(
      { ...appReq(), endpoint: fake.endpoint }, budgetOf({ ms: 600_000 }),
    );
    assert.equal(outcome.kind, "connected");
    if (outcome.kind !== "connected") return;
    const started = Date.now();
    await assert.rejects(outcome.session.pageSource(AbortSignal.timeout(150)));
    assert.ok(Date.now() - started < 1_000);
    // 截止信号只约束 withDeadline 之下的调用链：之后同一实例上的命令不受影响
    const ok = await withDeadline(AbortSignal.timeout(5_000), () => outcome.session.exec.getContext());
    assert.equal(ok, "NATIVE_APP");
  } finally {
    await fake.close();
  }
});

test("真实运行：服务端非 2xx 的状态码挂到错误对象上；连接被断开时没有状态码；执行实例对每条失败命令只发一次请求", async () => {
  const fake = await fakeWebDriver({
    sessionCapabilities: ANDROID_APP,
    routes: {
      "GET /source": { status: 503, body: { error: "unknown error", message: "Service Unavailable", stacktrace: "" } },
      "GET /screenshot": { status: 500, body: { error: "unknown error", message: "boom", stacktrace: "" } },
      "GET /url": { destroy: true },
    },
  });
  try {
    const outcome = await createAppiumConnector({ timeouts: SHORT }).connect(
      { ...appReq(), endpoint: fake.endpoint }, budgetOf({ ms: 600_000 }),
    );
    assert.equal(outcome.kind, "connected");
    if (outcome.kind !== "connected") return;
    const { exec } = outcome.session;
    await assert.rejects(exec.getPageSource(), (e) => {
      assert.equal((e as { statusCode?: number }).statusCode, 503);
      assert.equal(httpStatusOf(e), 503);
      assert.equal(commandFailureKind(e), "gateway");
      return true;
    });
    await assert.rejects(exec.takeScreenshot(), (e) => httpStatusOf(e) === 500 && commandFailureKind(e) === "server");
    await assert.rejects(exec.getUrl(), (e) => httpStatusOf(e) === null && commandFailureKind(e) === "connection");
    for (const key of ["GET /source", "GET /screenshot", "GET /url"]) {
      assert.equal(fake.seen.filter((k) => k === key).length, 1, `${key} 只发一次，不重试`);
    }
  } finally {
    await fake.close();
  }
});

test("真实运行：newSession 被服务端拒绝时，消息里的服务端原因不带端点令牌与预签名签名；503 只重试一次", async () => {
  const rejected = await fakeWebDriver({
    sessionCapabilities: ANDROID_APP,
    routes: { "POST /session": { status: 500, body: { error: "session not created", message: `Could not download app from ${PRESIGNED}`, stacktrace: "" } } },
  });
  try {
    const outcome = await createAppiumConnector({ timeouts: SHORT }).connect(
      { ...appReq(), endpoint: rejected.endpoint }, budgetOf({ ms: 600_000 }),
    );
    assert.equal(outcome.kind, "terminated");
    if (outcome.kind !== "terminated") return;
    assert.equal(outcome.termination.errorType, "precheck_failed");
    assert.ok(outcome.termination.message.includes("Could not download app from https://gherkai-apps.s3"));
    assert.ok(!outcome.termination.message.includes(TOKEN));
    assert.ok(!outcome.termination.message.includes("0123456789abcdef0123456789abcdef"));
    assert.equal(rejected.seen.filter((k) => k === "POST /session").length, 1);
  } finally {
    await rejected.close();
  }

  const busy = await fakeWebDriver({ sessionCapabilities: ANDROID_APP, routes: { "POST /session": { status: 503, body: { error: "unknown error", message: "Service Unavailable", stacktrace: "" } } } });
  try {
    const outcome = await createAppiumConnector({ timeouts: SHORT }).connect(
      { ...appReq(), endpoint: busy.endpoint }, budgetOf({ ms: 600_000 }),
    );
    assert.deepEqual(outcome, ACQUIRE_TIMED_OUT);
    assert.equal(busy.seen.filter((k) => k === "POST /session").length, 2);
  } finally {
    await busy.close();
  }
});

test("缺省的三个超时取自 limits", () => {
  assert.deepEqual(CLIENT_TIMEOUTS, {
    newSessionFloorMs: NEW_SESSION_TIMEOUT_FLOOR_MS, execRequestMs: EXEC_REQUEST_TIMEOUT_MS, probeRequestMs: PROBE_TIMEOUT_MS,
  });
});
