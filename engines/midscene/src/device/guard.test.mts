// 命令守卫的护栏测试（ADR 0052 决策 6「命令守卫」「执行期关闭传输层自动重试」「执行异常的归类由守卫带给 runStep」「结果未知的
// 命令」、决策 8「命令守卫的护栏测试」；ADR 0051 决策 4「会话丢失的判定靠查状态」）。运行：npx tsx --test src/device/guard.test.mts。
//
// 两组用例：
//   - 假客户端组：执行实例换成记录发出命令的假对象，逐条验 ADR 列出的拒绝情形（旧令牌、step 结束后保留的引用、解构或先取后调的
//     方法、缓存的元素句柄、晚到的异步回调、进入终结之后、结果未知之后的有副作用命令）、只读白名单的放行与重试规则、按会话状态的
//     归类与异常上的归类标记；
//   - 真实 WebdriverIO 组：同一进程里起一个只实现少量路由的 WebDriver 服务端，执行实例由 Appium 块的生产建连（appium.mts 的
//     createAppiumConnector）建出，与生产同一套客户端选项与状态码钩子；用它验膜对真实对象成立（链式查询、元素的 parent、元素列表的
//     回调参数、动作构造器）、状态码经生产的 transformResponse 钩子读回（浏览器级命令与元素命令）、连接被重置与客户端超时的真实错误
//     形态被正确分流。它证明的是 webdriverio 10.0.2 的对象形态与错误形态，不证明 Appium 服务端与真机的行为（那些由真机验收负责）。
// 另有一条子进程用例验循环引用下本模块照常加载（装配设备部件的模块被 surface.mts 静态导入的形态）。
//
// 用例里的 step 窗口按设备侧接缝的执行方式开关：先 openWindow，再在同一段同步执行里调用执行函数，结束后 closeWindow。
import { test } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import http from "node:http";
import type { AddressInfo } from "node:net";
import * as os from "node:os";
import * as path from "node:path";
import { spawn } from "node:child_process";
import { pathToFileURL } from "node:url";
import type { Browser } from "webdriverio";
import { createAppiumConnector } from "./appium.mjs";
import {
  AFTER_RESULT_UNKNOWN_MESSAGE, CONNECTION_ERROR_CODES, FINALIZING_COMMAND_MESSAGE, GATEWAY_STATUS_CODES, READ_ONLY_TIMEOUT_MESSAGE,
  RESULT_UNKNOWN_MESSAGE, STALE_COMMAND_MESSAGE, TIMEOUT_ERROR_CODES,
  commandFailedMessage, commandGuardFactory, createCommandGuard, httpStatusOf, isRetryable, recordHttpStatus, retryReadOnce,
} from "./guard.mjs";
import { SESSION_LOST_MESSAGE, type CommandGuard, type DriverAdapter, type WindowOutcome } from "./surface.mjs";
import { attachClassification, readClassification, type StepFailure } from "../worker/surface.mjs";

// ---- 假执行实例 ----

const READ_ONLY_SCRIPTS = new Set(["mobile: deviceScreenInfo", "mobile: activeAppInfo"]);

function adapterWith(readOnly: ReadonlySet<string> | undefined): DriverAdapter {
  const base: DriverAdapter = {
    async deepLink() { /* 守卫测试不经适配器发命令 */ },
    extractControls() { return { items: [], total: 0, truncated: false }; },
  };
  return readOnly === undefined ? base : Object.assign(base, { readOnlyMobileCommands: readOnly });
}

function codeError(code: string, message = `Request failed with error code ${code}`): Error {
  return Object.assign(new Error(message), { code });
}

/** 服务端非 2xx：webdriver 的错误只带名与消息，状态码经 transformResponse 记在它挂的请求选项上（与真实形态相同的取法）。 */
function httpError(status: number): Error {
  const opts = { method: "GET" };
  recordHttpStatus({ statusCode: status, body: {} }, opts);
  return Object.assign(new Error(`server answered ${status}`), { name: "unknown error", opts });
}

const timeoutError = () =>
  codeError("ETIMEDOUT", 'Request timed out! Consider increasing the "connectionRetryTimeout" option.');

class FakeElement {
  constructor(readonly elementId: string, readonly parent: FakeExec) {}
  click() { return this.parent.run(`click:${this.elementId}`, null); }
  setValue(text: string) { return this.parent.run(`setValue:${this.elementId}:${text}`, null); }
  getText() { return this.parent.run(`getText:${this.elementId}`, `text-${this.elementId}`); }
}

class FakeExec {
  readonly sent: string[] = [];
  /** 命令名到待抛异常的队列：每次发出该命令先取一个，取到即抛。 */
  readonly failures = new Map<string, unknown[]>();
  readonly screenshotBytes = Buffer.from("png-bytes");
  readonly contextList = ["NATIVE_APP", "WEBVIEW_1"];
  capabilities = { platformName: "iOS", "appium:automationName": "XCUITest" };
  private elementSeq = 0;
  private hang = new Set<string>();

  failNext(command: string, ...errors: unknown[]): void {
    this.failures.set(command, [...(this.failures.get(command) ?? []), ...errors]);
  }

  hangOn(command: string): void { this.hang.add(command); }

  async run<T>(command: string, value: T): Promise<T> {
    this.sent.push(command);
    if (this.hang.has(command)) await new Promise(() => { /* 永不返回 */ });
    const queue = this.failures.get(command);
    if (queue !== undefined && queue.length > 0) throw queue.shift();
    return value;
  }

  takeScreenshot() { return this.run("takeScreenshot", "iVBORw0KGgo"); }
  saveScreenshotBuffer() { return this.run("saveScreenshotBuffer", this.screenshotBytes); }
  getContexts() { return this.run("getContexts", this.contextList); }
  getContext() { return this.run("getContext", "NATIVE_APP"); }
  getPageSource() { return this.run("getPageSource", "<hierarchy/>"); }
  getUrl() { return this.run("getUrl", "https://example.test/"); }
  getCurrentPackage() { return this.run("getCurrentPackage", "com.example"); }
  status() { return this.run("status", { ready: true, build: { version: "2.11.0" } }); }
  switchContext(name: string) { return this.run(`switchContext:${name}`, null); }
  keys(text: string) { return this.run(`keys:${text}`, null); }
  url(address: string) { return this.run(`url:${address}`, null); }
  terminateApp(appId: string) { return this.run(`terminateApp:${appId}`, true); }
  activateApp(appId: string) { return this.run(`activateApp:${appId}`, null); }
  execute(script: string, ..._args: unknown[]) { return this.run(`execute:${script}`, { scale: 3 }); }
  async $(selector: string) {
    this.sent.push(`$:${selector}`);
    return new FakeElement(`e${++this.elementSeq}`, this);
  }
}

interface Harness {
  exec: FakeExec;
  guard: CommandGuard;
  driver: Browser;
  /** 每次查会话状态返回的值（null 表示查询本身失败）。 */
  status: { value: string | null; calls: number };
}

function harness(opts: { readOnly?: ReadonlySet<string> | undefined; status?: string | null } = {}): Harness {
  const exec = new FakeExec();
  const status = { value: opts.status === undefined ? "RUNNING" : opts.status, calls: 0 };
  const guard = createCommandGuard({
    exec: exec as unknown as Browser,
    adapter: adapterWith("readOnly" in opts ? opts.readOnly : READ_ONLY_SCRIPTS),
    sessionStatus: async () => { status.calls++; return status.value; },
  });
  return { exec, guard, driver: guard.driver, status };
}

/** 一个 step 的执行窗口：与设备侧接缝的 execute 相同的开关方式。返回执行函数的结果、抛出物与窗口判定。执行函数里的断言失败
 *  不算抛出物：关闭窗口后照原样抛出，让用例变红。 */
async function inStep<T>(
  guard: CommandGuard, run: (act: AbortController) => Promise<T>,
): Promise<{ value?: T; error?: unknown; outcome: WindowOutcome | null; act: AbortController }> {
  const act = new AbortController();
  guard.openWindow(act);
  try {
    const value = await run(act);
    return { value, outcome: guard.closeWindow(), act };
  } catch (error) {
    const outcome = guard.closeWindow();
    if (error instanceof assert.AssertionError) throw error;
    return { error, outcome, act };
  }
}

async function rejectsWith(promise: unknown, failure: Partial<StepFailure>, message?: string): Promise<unknown> {
  let caught: unknown = undefined;
  await assert.rejects(async () => { await promise; }, (e: unknown) => { caught = e; return true; });
  const mark = readClassification(caught);
  assert.ok(mark !== null, `异常没有归类标记：${String(caught)}`);
  if (failure.errorType !== undefined) assert.equal(mark.errorType, failure.errorType);
  if (failure.message !== undefined) assert.equal(mark.message, failure.message);
  if (message !== undefined) assert.equal((caught as Error).message, message);
  return caught;
}

/** 立即挂上处理：兑现为抛出物（没有抛出时为 undefined），避免晚到的拒绝在断言之前成为未处理的拒绝。 */
function settled(promise: unknown): Promise<unknown> {
  return Promise.resolve(promise).then(() => undefined, (e: unknown) => e);
}

const unknownFailure: StepFailure = { errorType: "engine_error", message: RESULT_UNKNOWN_MESSAGE };
const lostFailure: StepFailure = { errorType: "session_lost", message: SESSION_LOST_MESSAGE };
const staleFailure: StepFailure = { errorType: "engine_error", message: STALE_COMMAND_MESSAGE };

// ---- 执行令牌 ----

test("没有打开的窗口时（step 之前与 step 之间），经守卫的命令一律不发出", async () => {
  const h = harness();
  await rejectsWith(h.driver.takeScreenshot(), staleFailure);
  await inStep(h.guard, async () => { await h.driver.takeScreenshot(); });
  await rejectsWith(h.driver.takeScreenshot(), staleFailure);
  await rejectsWith(h.driver.execute("mobile: tap", { x: 1, y: 1 }), staleFailure);
  assert.deepEqual(h.exec.sent, ["takeScreenshot"]);
});

test("step 结束后保留的代理引用被拒绝，下一个 step 里由新的执行重新取用照常可用", async () => {
  const h = harness();
  let kept: Browser | null = null;
  await inStep(h.guard, async () => { kept = h.driver; await kept.getPageSource(); });
  await rejectsWith(kept!.getPageSource(), staleFailure);
  await rejectsWith(kept!.keys("a"), staleFailure);
  const second = await inStep(h.guard, async () => h.driver.getPageSource());
  assert.equal(second.value, "<hierarchy/>");
  assert.deepEqual(h.exec.sent, ["getPageSource", "getPageSource"]);
});

test("缓存的元素句柄：上一个 step 取得的元素在下一个 step 里调用被拒绝，元素的 parent 同样受约束", async () => {
  const h = harness();
  let cached: { click(): Promise<unknown>; parent: Browser } | null = null;
  await inStep(h.guard, async () => {
    cached = await h.driver.$("~login") as never;
    await cached!.click();
  });
  const later = await inStep(h.guard, async () => {
    await rejectsWith(cached!.click(), staleFailure);
    await rejectsWith(cached!.parent.takeScreenshot(), staleFailure);
    const fresh = await h.driver.$("~login");
    await fresh.click();
  });
  assert.equal(later.error, undefined);
  assert.deepEqual(h.exec.sent, ["$:~login", "click:e1", "$:~login", "click:e2"]);
});

test("从代理提取出的方法：同一 step 内可用，解构或先取后调的引用带进下一个 step 即被拒绝", async () => {
  const h = harness();
  let taken: { takeScreenshot: () => Promise<unknown>; execute: Browser["execute"]; bound: () => Promise<unknown> } | null = null;
  await inStep(h.guard, async () => {
    const { takeScreenshot, execute } = h.driver;
    const keys = h.driver.keys;
    await takeScreenshot();
    await keys.call(undefined, "x");
    taken = { takeScreenshot, execute, bound: h.driver.getPageSource.bind(h.driver) };
  });
  await inStep(h.guard, async () => {
    await rejectsWith(taken!.takeScreenshot(), staleFailure);
    await rejectsWith(taken!.execute("mobile: tap", { x: 1, y: 2 }), staleFailure);
    await rejectsWith(taken!.bound(), staleFailure);
  });
  assert.deepEqual(h.exec.sent, ["takeScreenshot", "keys:x"]);
});

test("晚到的异步回调：step 里排下的定时器与 await 之后才恢复的 handler，落在下一个 step 里发命令也被拒绝", async () => {
  const h = harness();
  let release!: () => void;
  const gate = new Promise<void>((resolve) => { release = resolve; });
  const late: Promise<unknown>[] = [];
  let timerFired!: () => void;
  const timerDone = new Promise<void>((resolve) => { timerFired = resolve; });
  await inStep(h.guard, async () => {
    // handler 不等这两段异步工作就返回：一段在定时器里发命令，一段 await 一个之后才兑现的 promise 再发命令
    setTimeout(() => { late.push(settled(h.driver.keys("timer"))); timerFired(); }, 5);
    late.push(settled((async () => { await gate; return h.driver.execute("mobile: tap", { x: 3, y: 4 }); })()));
  });
  const next = await inStep(h.guard, async () => {
    await timerDone;
    release();
    for (const p of late) assert.deepEqual(readClassification(await p), staleFailure);
    await h.driver.takeScreenshot();  // 本 step 自己的命令不受影响
  });
  assert.equal(next.error, undefined);
  assert.equal(next.outcome, null);
  assert.deepEqual(h.exec.sent, ["takeScreenshot"]);
});

test("被拒绝的调用没人 await 时不产生未处理的拒绝", async () => {
  const h = harness();
  const unhandled: unknown[] = [];
  const onUnhandled = (reason: unknown) => { unhandled.push(reason); };
  process.on("unhandledRejection", onUnhandled);
  try {
    void h.driver.keys("nobody-awaits");
    void (h.driver.$("~x") as unknown as { click(): unknown }).click();
    await new Promise((resolve) => setTimeout(resolve, 20));
  } finally {
    process.off("unhandledRejection", onUnhandled);
  }
  assert.deepEqual(unhandled, []);
  assert.deepEqual(h.exec.sent, []);
});

test("进入终结：当前 act 立即中止，此后经代理的命令（含只读命令）一律被拒绝，之后打开的窗口也不放行", async () => {
  const h = harness();
  const act = new AbortController();
  h.guard.openWindow(act);
  const el = await h.driver.$("~a");
  h.guard.shutdown();
  assert.equal(act.signal.aborted, true);
  const finalizing: StepFailure = { errorType: "engine_error", message: FINALIZING_COMMAND_MESSAGE };
  await rejectsWith(h.driver.takeScreenshot(), finalizing);
  await rejectsWith(el.click(), finalizing);
  const again = new AbortController();
  h.guard.openWindow(again);
  assert.equal(again.signal.aborted, true);
  await rejectsWith(h.driver.getPageSource(), finalizing);
  assert.deepEqual(h.exec.sent, ["$:~a"]);
});

test("生命周期通道不经守卫：结果未知与进入终结之后，直接经执行实例的命令照常发出", async () => {
  const h = harness();
  h.exec.failNext("keys:a", timeoutError());
  await inStep(h.guard, async () => { await h.driver.keys("a").catch(() => undefined); });
  await h.exec.switchContext("NATIVE_APP");
  h.guard.shutdown();
  await h.exec.getPageSource();
  assert.deepEqual(h.exec.sent, ["keys:a", "switchContext:NATIVE_APP", "getPageSource"]);
});

// ---- 结果未知 ----

test("结果未知：有副作用的命令客户端超时即置标志、中止 act、查一次会话状态，本 step 内有副作用的命令全部被拒绝", async () => {
  const h = harness();
  h.exec.failNext("execute:mobile: tap", timeoutError());
  const r = await inStep(h.guard, async (act) => {
    const el = await h.driver.$("~buy");
    await rejectsWith(h.driver.execute("mobile: tap", { x: 10, y: 20 }), unknownFailure);
    assert.equal(act.signal.aborted, true);
    const after = { errorType: "engine_error" as const, message: RESULT_UNKNOWN_MESSAGE };
    await rejectsWith(el.click(), after, AFTER_RESULT_UNKNOWN_MESSAGE);
    await rejectsWith(el.setValue("4111"), after, AFTER_RESULT_UNKNOWN_MESSAGE);
    await rejectsWith(h.driver.keys("4111"), after, AFTER_RESULT_UNKNOWN_MESSAGE);
    await rejectsWith(h.driver.execute("mobile: tap", { x: 10, y: 20 }), after, AFTER_RESULT_UNKNOWN_MESSAGE);
    await rejectsWith(h.driver.$("~other"), after, AFTER_RESULT_UNKNOWN_MESSAGE);
  });
  assert.equal(r.error, undefined);
  assert.deepEqual(r.outcome, { failure: unknownFailure, resultUnknown: true });
  assert.equal(h.status.calls, 1);
  // 有副作用的命令只发出过一次，之后零补发
  assert.deepEqual(h.exec.sent, ["$:~buy", "execute:mobile: tap"]);
});

test("结果未知后只读白名单放行：截图、上下文列表、page source、前台应用、/status、适配器给出的只读命令", async () => {
  const h = harness();
  h.exec.failNext("keys:x", codeError("ECONNRESET"));
  const r = await inStep(h.guard, async () => {
    await rejectsWith(h.driver.keys("x"), unknownFailure);
    assert.equal(await h.driver.takeScreenshot(), "iVBORw0KGgo");
    assert.deepEqual(await h.driver.getContexts(), ["NATIVE_APP", "WEBVIEW_1"]);
    assert.equal(await h.driver.getPageSource(), "<hierarchy/>");
    assert.equal(await h.driver.getCurrentPackage(), "com.example");
    assert.deepEqual(await h.driver.status(), { ready: true, build: { version: "2.11.0" } });
    assert.deepEqual(await h.driver.execute("mobile: deviceScreenInfo"), { scale: 3 });
    assert.deepEqual(await h.driver.execute("mobile: activeAppInfo"), { scale: 3 });
    // 不在白名单里的读取命令同样按有副作用处理
    await rejectsWith(h.driver.getContext(), unknownFailure, AFTER_RESULT_UNKNOWN_MESSAGE);
    // 导航与应用的启动、停止都有副作用，不在只读白名单里（ADR 0052 决策 6：读取地址不含导航），经 execute 发出的非只读 mobile 命令同理
    await rejectsWith(h.driver.url("https://example.test/next"), unknownFailure, AFTER_RESULT_UNKNOWN_MESSAGE);
    await rejectsWith(h.driver.terminateApp("com.example"), unknownFailure, AFTER_RESULT_UNKNOWN_MESSAGE);
    await rejectsWith(h.driver.activateApp("com.example"), unknownFailure, AFTER_RESULT_UNKNOWN_MESSAGE);
    await rejectsWith(h.driver.execute("mobile: activateApp", { bundleId: "com.example" }), unknownFailure,
      AFTER_RESULT_UNKNOWN_MESSAGE);
    await rejectsWith(h.driver.execute("mobile: terminateApp", { bundleId: "com.example" }), unknownFailure,
      AFTER_RESULT_UNKNOWN_MESSAGE);
  });
  assert.deepEqual(r.outcome, { failure: unknownFailure, resultUnknown: true });
  assert.deepEqual(h.exec.sent, [
    "keys:x", "takeScreenshot", "getContexts", "getPageSource", "getCurrentPackage", "status",
    "execute:mobile: deviceScreenInfo", "execute:mobile: activeAppInfo",
  ]);
});

test("读地址只在经守卫切入的网页上下文里属于只读白名单，原生上下文里按有副作用处理", async () => {
  const h = harness();
  h.exec.failNext("keys:x", timeoutError());
  await inStep(h.guard, async () => {
    await h.driver.keys("x").catch(() => undefined);
    await rejectsWith(h.driver.getUrl(), unknownFailure, AFTER_RESULT_UNKNOWN_MESSAGE);
  });
  h.exec.failNext("getUrl", codeError("UND_ERR_SOCKET"));
  h.exec.failNext("keys:y", timeoutError());
  const web = await inStep(h.guard, async () => {
    await h.driver.switchContext("WEBVIEW_1");
    await h.driver.keys("y").catch(() => undefined);
    assert.equal(await h.driver.getUrl(), "https://example.test/");  // 白名单：放行，且连接层错误重试一次
    // 网页上下文里放行的只是读地址，导航不在白名单里
    await rejectsWith(h.driver.url("https://example.test/next"), unknownFailure, AFTER_RESULT_UNKNOWN_MESSAGE);
  });
  assert.deepEqual(web.outcome, { failure: unknownFailure, resultUnknown: true });
  // 下一个 step 开始时会话已由 step 前核对切回原生上下文：读地址回到按有副作用处理
  h.exec.failNext("keys:z", timeoutError());
  await inStep(h.guard, async () => {
    await h.driver.keys("z").catch(() => undefined);
    await rejectsWith(h.driver.getUrl(), unknownFailure, AFTER_RESULT_UNKNOWN_MESSAGE);
  });
  assert.deepEqual(h.exec.sent, ["keys:x", "switchContext:WEBVIEW_1", "keys:y", "getUrl", "getUrl", "keys:z"]);
});

test("结果未知时会话已不在运行：归 session_lost，窗口判定不再要求存活探测", async () => {
  const h = harness({ status: "STOPPING" });
  h.exec.failNext("keys:x", codeError("UND_ERR_CLOSED"));
  const r = await inStep(h.guard, async (act) => {
    await rejectsWith(h.driver.keys("x"), lostFailure);
    assert.equal(act.signal.aborted, true);
    // 会话丢失之后连只读命令也不再发往设备
    await rejectsWith(h.driver.takeScreenshot(), lostFailure);
  });
  assert.deepEqual(r.outcome, { failure: lostFailure, resultUnknown: false });
  // 会话丢失锁存：之后再打开的窗口里一律按会话丢失拒绝，窗口判定照样交回
  const next = await inStep(h.guard, async () => { await rejectsWith(h.driver.takeScreenshot(), lostFailure); });
  assert.deepEqual(next.outcome, { failure: lostFailure, resultUnknown: false });
  assert.deepEqual(h.exec.sent, ["keys:x"]);
});

test("查会话状态本身失败时不据此判会话丢失，按结果未知归 engine_error", async () => {
  const h = harness({ status: null });
  h.exec.failNext("keys:x", codeError("EPIPE"));
  const r = await inStep(h.guard, async () => { await rejectsWith(h.driver.keys("x"), unknownFailure); });
  assert.deepEqual(r.outcome, { failure: unknownFailure, resultUnknown: true });
});

test("查会话状态本身失败时，结果已知的命令失败归 engine_error，标记不带会话仍在运行的事实", async () => {
  const h = harness({ status: null });
  const serverError = Object.assign(new Error("An element could not be located on the page"), { name: "no such element" });
  h.exec.failNext("keys:x", serverError);
  const r = await inStep(h.guard, async () => {
    const e = await rejectsWith(h.driver.keys("x"), {
      errorType: "engine_error", message: commandFailedMessage("no such element: An element could not be located on the page"),
    });
    assert.ok(!("sessionRunningConfirmed" in readClassification(e)!));
  });
  assert.equal(r.outcome, null);
  assert.equal(h.status.calls, 1);
});

test("有副作用的命令遇到任何传输层故障都不补发，一律记结果未知", async () => {
  // 连接层错误码、超时码与网关类状态码逐个取自守卫导出的集合（Appium 块的建连与探测归类用的也是这三份），两边不会各自分叉
  const faults: Array<[string, () => unknown]> = [
    ...[...CONNECTION_ERROR_CODES].map((code): [string, () => unknown] => [code, () => codeError(code)]),
    ...[...TIMEOUT_ERROR_CODES].map((code): [string, () => unknown] => [code, () => codeError(code)]),
    ["ETIMEDOUT（webdriver 的客户端超时）", timeoutError],
    ...[...GATEWAY_STATUS_CODES].map((status): [string, () => unknown] => [String(status), () => httpError(status)]),
    ["cause 链里的错误码", () => new Error("fetch failed", { cause: codeError("ECONNRESET") })],
  ];
  for (const [label, fault] of faults) {
    const h = harness();
    h.exec.failNext("execute:mobile: tap", fault());
    const r = await inStep(h.guard, async () => {
      await rejectsWith(h.driver.execute("mobile: tap", { x: 1, y: 1 }), unknownFailure);
    });
    assert.deepEqual(h.exec.sent, ["execute:mobile: tap"], label);
    assert.deepEqual(r.outcome, { failure: unknownFailure, resultUnknown: true }, label);
  }
});

// ---- 只读白名单的重试 ----

test("只读白名单只对连接层错误码与 HTTP 502 / 503 / 504 重试一次", async () => {
  const retryable: Array<[string, () => unknown]> = [
    ...[...CONNECTION_ERROR_CODES].map((code): [string, () => unknown] => [code, () => codeError(code)]),
    ...[...GATEWAY_STATUS_CODES].map((status): [string, () => unknown] => [String(status), () => httpError(status)]),
  ];
  for (const [label, fault] of retryable) {
    const h = harness();
    h.exec.failNext("getPageSource", fault());
    const r = await inStep(h.guard, async () => h.driver.getPageSource());
    assert.equal(r.value, "<hierarchy/>", label);
    assert.deepEqual(h.exec.sent, ["getPageSource", "getPageSource"], label);
    assert.equal(r.outcome, null, label);
    assert.equal(h.status.calls, 0, label);
  }
});

test("只读白名单对一切超时与 500 不重试；失败后先查会话状态，仍在运行归 engine_error、不置结果未知", async () => {
  const cases: Array<[string, () => unknown, string]> = [
    ["ETIMEDOUT", timeoutError, READ_ONLY_TIMEOUT_MESSAGE],
    ["UND_ERR_HEADERS_TIMEOUT", () => codeError("UND_ERR_HEADERS_TIMEOUT"), READ_ONLY_TIMEOUT_MESSAGE],
    ["TimeoutError", () => Object.assign(new Error("The operation was aborted due to timeout"), { name: "TimeoutError" }),
      READ_ONLY_TIMEOUT_MESSAGE],
    ["500", () => httpError(500), commandFailedMessage("unknown error: server answered 500")],
  ];
  for (const [label, fault, message] of cases) {
    const h = harness();
    h.exec.failNext("takeScreenshot", fault());
    const r = await inStep(h.guard, async () => {
      await rejectsWith(h.driver.takeScreenshot(), { errorType: "engine_error", message });
      await h.driver.keys("still-allowed");  // 只读命令失败不置结果未知标志
    });
    assert.equal(r.error, undefined, label);
    assert.deepEqual(h.exec.sent, ["takeScreenshot", "keys:still-allowed"], label);
    assert.equal(h.status.calls, 1, label);
    assert.equal(r.outcome, null, label);
  }
});

test("只读白名单重试后仍失败：先查会话状态，不在运行即 session_lost", async () => {
  const h = harness({ status: "COMPLETED" });
  h.exec.failNext("getContexts", codeError("ECONNRESET"), httpError(503));
  const r = await inStep(h.guard, async () => { await rejectsWith(h.driver.getContexts(), lostFailure); });
  assert.deepEqual(h.exec.sent, ["getContexts", "getContexts"]);
  assert.equal(h.status.calls, 1);
  assert.deepEqual(r.outcome, { failure: lostFailure, resultUnknown: false });
});

test("第一次失败期间 step 已结束：只读命令不再重试", async () => {
  const h = harness();
  let reject!: (e: unknown) => void;
  const pending = new Promise((_resolve, rej) => { reject = rej; });
  const exec = h.exec as unknown as { getPageSource(): Promise<unknown> };
  exec.getPageSource = () => { h.exec.sent.push("getPageSource"); return pending; };
  let call: Promise<unknown> | null = null;
  await inStep(h.guard, async () => { call = Promise.resolve(h.driver.getPageSource()); });
  reject(codeError("ECONNRESET"));
  const e = await rejectsWith(call!, { errorType: "engine_error" });
  assert.deepEqual(h.exec.sent, ["getPageSource"]);
  // 晚到的失败不查会话状态，标记不带会话仍在运行的事实
  assert.equal(h.status.calls, 0);
  assert.ok(!("sessionRunningConfirmed" in readClassification(e)!));
});

test("适配器没有给出只读命令集合时，mobile 命令一律按有副作用处理", async () => {
  const h = harness({ readOnly: undefined });
  h.exec.failNext("execute:mobile: deviceScreenInfo", codeError("ECONNRESET"));
  const r = await inStep(h.guard, async () => {
    await rejectsWith(h.driver.execute("mobile: deviceScreenInfo"), unknownFailure);
  });
  assert.deepEqual(h.exec.sent, ["execute:mobile: deviceScreenInfo"]);
  assert.deepEqual(r.outcome, { failure: unknownFailure, resultUnknown: true });
});

// ---- 普通失败与归类标记 ----

test("服务端已报错的命令（结果已知）：先查会话状态，仍在运行归 engine_error 并保留原因，本 step 后续命令照常", async () => {
  const h = harness();
  const serverError = Object.assign(new Error("An element could not be located on the page"), { name: "no such element" });
  h.exec.failNext("keys:x", serverError);
  const r = await inStep(h.guard, async () => {
    const e = await rejectsWith(h.driver.keys("x"), {
      errorType: "engine_error", message: commandFailedMessage("no such element: An element could not be located on the page"),
    });
    assert.strictEqual(e, serverError);  // 标记挂在原异常上，适配器仍可按原消息再归类
    assert.equal(readClassification(e)?.sessionRunningConfirmed, true);  // 查到会话仍为 RUNNING，标记带这项事实
    await h.driver.keys("y");
  });
  assert.equal(r.outcome, null);
  assert.equal(h.status.calls, 1);
  assert.deepEqual(h.exec.sent, ["keys:x", "keys:y"]);
});

test("服务端已报错且会话已不在运行：归 session_lost", async () => {
  const h = harness({ status: "STOPPING" });
  h.exec.failNext("keys:x", Object.assign(new Error("A session is either terminated or not started"), { name: "invalid session id" }));
  const r = await inStep(h.guard, async () => { await rejectsWith(h.driver.keys("x"), lostFailure); });
  assert.deepEqual(r.outcome, { failure: lostFailure, resultUnknown: false });
});

test("已带归类标记的异常原样透传，不再查会话状态", async () => {
  const h = harness();
  const marked = new Error("already");
  attachClassification(marked, { errorType: "capability_unavailable", message: "这台设备不支持打开地址" });
  h.exec.failNext("keys:x", marked);
  await inStep(h.guard, async () => {
    await rejectsWith(h.driver.keys("x"), { errorType: "capability_unavailable", message: "这台设备不支持打开地址" });
  });
  assert.equal(h.status.calls, 0);
});

test("纯数据结果原样返回，不套代理", async () => {
  const h = harness();
  await inStep(h.guard, async () => {
    assert.strictEqual(await h.driver.getContexts(), h.exec.contextList);
    const exec = h.exec as unknown as { saveScreenshotBuffer(): Promise<Buffer> };
    const driver = h.driver as unknown as { saveScreenshotBuffer(): Promise<Buffer> };
    assert.strictEqual(await driver.saveScreenshotBuffer(), await exec.saveScreenshotBuffer());
    assert.strictEqual(h.driver.capabilities, h.exec.capabilities);
  });
});

test("工厂按端口形状构造守卫，交出的 driver 不是执行实例本身", () => {
  const exec = new FakeExec();
  const guard = commandGuardFactory.create({
    exec: exec as unknown as Browser, adapter: adapterWith(READ_ONLY_SCRIPTS), sessionStatus: async () => "RUNNING",
  });
  assert.notStrictEqual(guard.driver, exec as unknown as Browser);
  assert.equal(guard.closeWindow(), null);
});

test("HTTP 状态码的读取约定：错误自身的 statusCode、经 transformResponse 记在请求选项上的状态码、cause 链", () => {
  assert.equal(httpStatusOf(Object.assign(new Error("x"), { statusCode: 502 })), 502);
  assert.equal(httpStatusOf(httpError(503)), 503);
  assert.equal(httpStatusOf(new Error("outer", { cause: httpError(504) })), 504);
  assert.equal(httpStatusOf(new Error("plain")), null);
  assert.equal(httpStatusOf("not an error"), null);
  const response = { statusCode: 200, body: { value: null } };
  assert.strictEqual(recordHttpStatus(response, {}), response);
});

test("传输故障的错误码只有一份：连接层含 ADR 0052 决策 6 列出的五个与解析、路由失败，不含任何超时码；网关类状态码为 502 / 503 / 504", () => {
  for (const code of ["ECONNRESET", "ECONNREFUSED", "EPIPE", "UND_ERR_SOCKET", "UND_ERR_CLOSED"]) {
    assert.ok(CONNECTION_ERROR_CODES.has(code), code);
  }
  for (const code of ["EHOSTUNREACH", "ENETUNREACH", "ENOTFOUND", "EAI_AGAIN"]) assert.ok(CONNECTION_ERROR_CODES.has(code), code);
  for (const code of TIMEOUT_ERROR_CODES) assert.ok(!CONNECTION_ERROR_CODES.has(code), `${code} 是超时，不是连接层错误`);
  assert.deepEqual([...TIMEOUT_ERROR_CODES], ["ETIMEDOUT", "UND_ERR_CONNECT_TIMEOUT", "UND_ERR_HEADERS_TIMEOUT", "UND_ERR_BODY_TIMEOUT"]);
  assert.deepEqual([...GATEWAY_STATUS_CODES], [502, 503, 504]);
});

test("只读原语的一次重试由守卫与生命周期通道共用：连接层错误码与 502 / 503 / 504 再发一次，超时与 500 不重试，不许再发时不重试", async () => {
  const sendSeq = (...results: unknown[]) => {
    let calls = 0;
    const send = async (): Promise<string> => {
      const next = results[calls++];
      if (next instanceof Error) throw next;
      return String(next);
    };
    return { send, calls: () => calls };
  };
  for (const fault of [codeError("ENOTFOUND"), httpError(503), new Error("fetch failed", { cause: codeError("UND_ERR_SOCKET") })]) {
    assert.equal(isRetryable(fault), true, String(fault));
    const s = sendSeq(fault, "ok");
    assert.equal(await retryReadOnce(s.send), "ok");
    assert.equal(s.calls(), 2);
  }
  for (const fault of [timeoutError(), codeError("UND_ERR_HEADERS_TIMEOUT"), httpError(500), new Error("no such element")]) {
    assert.equal(isRetryable(fault), false, String(fault));
    const s = sendSeq(fault, "ok");
    await assert.rejects(retryReadOnce(s.send), (e) => e === fault);
    assert.equal(s.calls(), 1);
  }
  // 重试之后仍失败：抛出第二次的失败，不再发第三次
  const again = httpError(502);
  const twice = sendSeq(codeError("ECONNRESET"), again, "ok");
  await assert.rejects(retryReadOnce(twice.send), (e) => e === again);
  assert.equal(twice.calls(), 2);
  // 调用方不许再发（截止信号已中止、窗口已关闭）：不重试
  const held = sendSeq(codeError("ECONNRESET"), "ok");
  await assert.rejects(retryReadOnce(held.send, () => false));
  assert.equal(held.calls(), 1);
});

// ---- 真实 WebdriverIO：膜对真实对象成立、真实错误形态的分流 ----

interface FakeServer {
  url: URL;
  hits: string[];
  /** 路由键（"GET /source" 一类）到下一次请求的处置。 */
  plan: Map<string, Array<"reset" | "hang" | number>>;
  close(): Promise<void>;
}

const ELEMENT_KEY = "element-6066-11e4-a52e-4f735466cecf";
const SESSION = "4f2b1c9e-0000-4000-8000-00000000abcd";

async function fakeWebDriver(): Promise<FakeServer> {
  const hits: string[] = [];
  const plan = new Map<string, Array<"reset" | "hang" | number>>();
  const server = http.createServer((req, res) => {
    let body = "";
    req.on("data", (chunk) => { body += chunk; });
    req.on("end", () => {
      const path = (req.url ?? "").replace(`/session/${SESSION}`, "");
      const parsed = body ? JSON.parse(body) as { script?: string; value?: string } : {};
      const key = `${req.method} ${path}${parsed.script ? ` ${parsed.script}` : ""}`;
      hits.push(key);
      const step = plan.get(key)?.shift();
      if (step === "reset") { req.socket.destroy(); return; }
      if (step === "hang") return;
      const send = (status: number, value: unknown) => {
        res.writeHead(status, { "content-type": "application/json" });
        res.end(JSON.stringify({ value }));
      };
      if (typeof step === "number") {
        send(step, { error: "unknown error", message: `planned ${step}`, stacktrace: "" });
        return;
      }
      if (req.method === "POST" && path === "/session") {
        send(200, { sessionId: SESSION, capabilities: { platformName: "iOS", "appium:automationName": "XCUITest" } });
      } else if (path === "/element") {
        send(200, { [ELEMENT_KEY]: "el-1" });
      } else if (path === "/elements") {
        // 严格选择器要求 $() 恰好命中一个：~login 一个，其余两个
        send(200, parsed.value === "login" ? [{ [ELEMENT_KEY]: "el-1" }] : [{ [ELEMENT_KEY]: "el-1" }, { [ELEMENT_KEY]: "el-2" }]);
      } else if (/^\/element\/[^/]+\/text$/.test(path)) {
        send(200, `text of ${path.split("/")[2]}`);
      } else if (path === "/screenshot") {
        send(200, "iVBORw0KGgo");
      } else if (path === "/source") {
        send(200, "<hierarchy/>");
      } else if (path === "/contexts") {
        send(200, ["NATIVE_APP", "WEBVIEW_7"]);
      } else if (req.method === "DELETE" && path === "") {
        send(200, null);
      } else {
        send(200, null);  // 点击、执行脚本、动作序列等：成功、无返回值
      }
    });
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const { port } = server.address() as AddressInfo;
  return {
    url: new URL(`http://127.0.0.1:${port}/`), hits, plan,
    close: () => new Promise<void>((resolve) => { server.closeAllConnections(); server.close(() => resolve()); }),
  };
}

/** 执行实例经 Appium 块的生产建连建出：客户端选项（含 transformResponse 状态码钩子与 0 次传输层重试）与生产相同，只把单请求超时
 *  缩到 0.4 秒，让客户端超时的用例几百毫秒内结束。 */
async function realHarness(): Promise<{ server: FakeServer; exec: Browser; guard: CommandGuard; status: { calls: number } }> {
  const server = await fakeWebDriver();
  const outcome = await createAppiumConnector({ timeouts: { newSessionFloorMs: 10_000, execRequestMs: 400, probeRequestMs: 400 } })
    .connect(
      { endpoint: server.url.href, device: "ios", uiKind: "app", appId: "com.example.Shop", appUrl: "https://apps.example.test/shop.ipa" },
      { signal: new AbortController().signal, remainingMs: () => 600_000 },
    );
  assert.equal(outcome.kind, "connected");
  if (outcome.kind !== "connected") throw new Error("未能建立测试用的 Appium 会话");
  const exec = outcome.session.exec;
  const status = { calls: 0 };
  const guard = createCommandGuard({
    exec, adapter: adapterWith(READ_ONLY_SCRIPTS), sessionStatus: async () => { status.calls++; return "RUNNING"; },
  });
  server.hits.length = 0;  // 只看建会话之后的请求
  return { server, exec, guard, status };
}

test("真实 WebdriverIO：链式查询、元素句柄与元素的 parent 都在膜内，跨 step 使用被拒绝", async () => {
  const { server, guard } = await realHarness();
  try {
    let el: WebdriverIO.Element | null = null;
    const first = await inStep(guard, async () => {
      await guard.driver.$("~login").click();
      el = await guard.driver.$("~login");
      await el.click();
    });
    assert.equal(first.error, undefined, String(first.error));
    const clicks = () => server.hits.filter((k) => /^POST \/element\/el-1\/click$/.test(k)).length;
    assert.equal(clicks(), 2);
    await inStep(guard, async () => {
      await rejectsWith(el!.click(), staleFailure);
      await rejectsWith(el!.parent.takeScreenshot(), staleFailure);
    });
    assert.equal(clicks(), 2);
    assert.ok(!server.hits.includes("GET /screenshot"), server.hits.join(", "));
  } finally {
    await server.close();
  }
});

test("真实 WebdriverIO：元素列表回调收到的元素在膜内，回调里的命令受结果未知标志约束", async () => {
  const { server, guard } = await realHarness();
  try {
    server.plan.set("POST /actions", ["reset"]);
    let leaked: WebdriverIO.Element | null = null;
    const r = await inStep(guard, async () => {
      const texts = await guard.driver.$$("~item").map((item) => { leaked = item; return item.getText(); });
      assert.deepEqual(texts, ["text of el-1", "text of el-2"]);
      const items = await guard.driver.$$("~item");
      assert.equal(items.length, 2);
      const builder = guard.driver.action("pointer").move({ x: 5, y: 5 }).down().up();
      await rejectsWith(builder.perform(), unknownFailure);
      // 结果未知之后：列表回调里的有副作用命令、新的动作序列都不发出
      await rejectsWith(items.map((item) => item.click()), unknownFailure, AFTER_RESULT_UNKNOWN_MESSAGE);
      // 遍历本身不发命令、照常进行，遍历出的元素仍在膜内
      let seen = 0;
      for (const item of items) {
        seen++;
        await rejectsWith(item.click(), unknownFailure, AFTER_RESULT_UNKNOWN_MESSAGE);
      }
      assert.equal(seen, 2);
      await rejectsWith(guard.driver.action("pointer").move({ x: 1, y: 1 }).perform(), unknownFailure);
    });
    assert.deepEqual(r.outcome, { failure: unknownFailure, resultUnknown: true });
    // WebdriverIO 交给回调的元素也在膜内：带出 step 之后调用被拒绝
    await inStep(guard, async () => { await rejectsWith(leaked!.click(), staleFailure); });
    assert.equal(server.hits.filter((k) => k === "POST /actions").length, 1);
    assert.ok(!server.hits.some((k) => k.endsWith("/click")), server.hits.join(", "));
  } finally {
    await server.close();
  }
});

test("真实 WebdriverIO：上一个 step 取得的元素列表在下一个 step 里照常遍历，遍历出的元素上的命令被拒绝", async () => {
  const { server, guard } = await realHarness();
  try {
    let pending: ReturnType<Browser["$$"]> | null = null;
    let items: Awaited<ReturnType<Browser["$$"]>> | null = null;
    const first = await inStep(guard, async () => {
      pending = guard.driver.$$("~item");
      items = await pending;
    });
    assert.equal(first.error, undefined, String(first.error));
    await inStep(guard, async () => {
      let seen = 0;
      for (const item of items!) {
        seen++;
        await rejectsWith(item.click(), staleFailure);
      }
      assert.equal(seen, 2);
      let seenAsync = 0;
      for await (const item of pending!) {
        seenAsync++;
        await rejectsWith(item.click(), staleFailure);
      }
      assert.equal(seenAsync, 2);
    });
    assert.equal(server.hits.filter((k) => k === "POST /elements").length, 1);
    assert.ok(!server.hits.some((k) => k.endsWith("/click")), server.hits.join(", "));
  } finally {
    await server.close();
  }
});

test("真实 WebdriverIO：经守卫切入网页上下文之后，结果未知时读地址仍放行；切回原生之后不再放行", async () => {
  const { server, guard } = await realHarness();
  try {
    server.plan.set("POST /execute/sync mobile: tap", ["reset", "reset"]);
    const r = await inStep(guard, async () => {
      await guard.driver.switchContext("WEBVIEW_7");
      await rejectsWith(guard.driver.execute("mobile: tap", { x: 1, y: 2 }), unknownFailure);
      assert.equal(await guard.driver.getUrl(), null);
    });
    assert.deepEqual(r.outcome, { failure: unknownFailure, resultUnknown: true });
    await inStep(guard, async () => {
      await guard.driver.switchContext("WEBVIEW_7");
      await guard.driver.switchContext("NATIVE_APP");
      await rejectsWith(guard.driver.execute("mobile: tap", { x: 1, y: 2 }), unknownFailure);
      await rejectsWith(guard.driver.getUrl(), unknownFailure, AFTER_RESULT_UNKNOWN_MESSAGE);
    });
    assert.equal(server.hits.filter((k) => k === "GET /url").length, 1);
  } finally {
    await server.close();
  }
});

test("真实 WebdriverIO：503 经 transformResponse 记下状态码、只读命令重试一次；500 不重试", async () => {
  const { server, guard, status } = await realHarness();
  try {
    server.plan.set("GET /source", [503]);
    server.plan.set("GET /screenshot", [500]);
    const r = await inStep(guard, async () => {
      assert.equal(await guard.driver.getPageSource(), "<hierarchy/>");
      await rejectsWith(guard.driver.takeScreenshot(), { errorType: "engine_error" });
    });
    assert.equal(r.outcome, null);
    assert.equal(server.hits.filter((k) => k === "GET /source").length, 2);
    assert.equal(server.hits.filter((k) => k === "GET /screenshot").length, 1);
    assert.equal(status.calls, 1);
  } finally {
    await server.close();
  }
});

test("真实 WebdriverIO：元素命令的 503 同样经生产的状态码钩子读回，有副作用的元素命令记结果未知且只发出一次", async () => {
  const { server, guard } = await realHarness();
  try {
    server.plan.set("POST /element/el-1/click", [503]);
    const r = await inStep(guard, async () => {
      const el = await guard.driver.$("~login");
      await rejectsWith(el.click(), unknownFailure);
    });
    assert.deepEqual(r.outcome, { failure: unknownFailure, resultUnknown: true });
    assert.equal(server.hits.filter((k) => k === "POST /element/el-1/click").length, 1);
  } finally {
    await server.close();
  }
});

test("真实 WebdriverIO：连接被重置时只读命令重试一次，有副作用的命令记结果未知且只发出一次", async () => {
  const { server, guard } = await realHarness();
  try {
    server.plan.set("GET /contexts", ["reset"]);
    server.plan.set("POST /execute/sync mobile: tap", ["reset"]);
    const r = await inStep(guard, async () => {
      assert.deepEqual(await guard.driver.getContexts(), ["NATIVE_APP", "WEBVIEW_7"]);
      await rejectsWith(guard.driver.execute("mobile: tap", { x: 1, y: 2 }), unknownFailure);
    });
    assert.deepEqual(r.outcome, { failure: unknownFailure, resultUnknown: true });
    assert.equal(server.hits.filter((k) => k === "GET /contexts").length, 2);
    assert.equal(server.hits.filter((k) => k === "POST /execute/sync mobile: tap").length, 1);
  } finally {
    await server.close();
  }
});

test("真实 WebdriverIO：客户端超时时只读命令不重试，有副作用的命令记结果未知", async () => {
  const { server, guard } = await realHarness();
  try {
    server.plan.set("POST /execute/sync mobile: deviceScreenInfo", ["hang"]);
    server.plan.set("POST /execute/sync mobile: tap", ["hang"]);
    const r = await inStep(guard, async () => {
      await rejectsWith(guard.driver.execute("mobile: deviceScreenInfo"), {
        errorType: "engine_error", message: READ_ONLY_TIMEOUT_MESSAGE,
      });
      await rejectsWith(guard.driver.execute("mobile: tap", { x: 1, y: 2 }), unknownFailure);
    });
    assert.deepEqual(r.outcome, { failure: unknownFailure, resultUnknown: true });
    assert.equal(server.hits.filter((k) => k === "POST /execute/sync mobile: deviceScreenInfo").length, 1);
    assert.equal(server.hits.filter((k) => k === "POST /execute/sync mobile: tap").length, 1);
  } finally {
    await server.close();
  }
});

// ---- 循环引用下的加载 ----

// 子进程里的加载钩子给 surface.mts 的源码前面加一行静态导入中间模块，中间模块再静态导入本模块，构成「surface.mts → 中间模块 →
// 本模块 → surface.mts」的环，本模块因此先于 surface.mts 求值。中间模块同时确认此刻 surface.mts 的绑定确实还不可读，入口再确认
// surface.mts 只求值一次（本模块与入口拿到的是同一个模块实例），两条都成立这条环才算形成，否则用例会空过。
const CYCLE_HOOK = `
let surface; let middle;
export function initialize(data) { surface = data.surface; middle = data.middle; }
export async function load(url, context, next) {
  const result = await next(url, context);
  if (url.split("?")[0] !== surface) return result;
  const source = typeof result.source === "string" ? result.source : Buffer.from(result.source).toString("utf8");
  const prefix = "import " + JSON.stringify(middle) + ";\\nglobalThis.surfaceEvaluations = (globalThis.surfaceEvaluations ?? 0) + 1;\\n";
  return { ...result, source: prefix + source };
}
`;

test("装配设备部件的模块被 surface.mts 静态导入、构成循环引用时，本模块照常加载", async () => {
  const guardHref = new URL("./guard.mts", import.meta.url).href;
  const surfaceHref = new URL("./surface.mts", import.meta.url).href;
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "gherkai-guard-cycle-"));
  try {
    const hook = path.join(dir, "cycle-hook.mjs");
    const middle = path.join(dir, "middle.mjs");
    const entry = path.join(dir, "entry.mjs");
    fs.writeFileSync(hook, CYCLE_HOOK);
    fs.writeFileSync(middle, [
      `import ${JSON.stringify(guardHref)};`,
      `import * as surface from ${JSON.stringify(surfaceHref)};`,
      "let readable = true;",
      "try { void surface.SESSION_LOST_MESSAGE; } catch { readable = false; }",
      "globalThis.cycleFormed = !readable;",
    ].join("\n"));
    fs.writeFileSync(entry, [
      'import { register } from "node:module";',
      `register(${JSON.stringify(pathToFileURL(hook).href)}, { data: { surface: ${JSON.stringify(surfaceHref)}, middle: ${
        JSON.stringify(pathToFileURL(middle).href)} } });`,
      `await import(${JSON.stringify(surfaceHref)});`,
      'if (globalThis.cycleFormed !== true) throw new Error("the import cycle did not form");',
      'if (globalThis.surfaceEvaluations !== 1) throw new Error("surface.mts evaluated " + globalThis.surfaceEvaluations + " times");',
      'process.stdout.write("loaded");',
    ].join("\n"));
    const proc = spawn(process.execPath, ["--import", import.meta.resolve("tsx"), entry], { cwd: dir, stdio: ["ignore", "pipe", "pipe"] });
    let stdout = ""; let stderr = "";
    proc.stdout.on("data", (chunk) => { stdout += chunk; });
    proc.stderr.on("data", (chunk) => { stderr += chunk; });
    const code = await new Promise<number | null>((resolve) => { proc.on("close", resolve); });
    assert.equal(code, 0, stderr);
    assert.equal(stdout, "loaded", stderr);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
