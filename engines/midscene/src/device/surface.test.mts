// 设备侧界面接缝的编排单测（ADR 0052 决策 2、3；ADR 0051 决策 4、5、8、9；ADR 0050 决策 2）。运行：npx tsx --test src/device/surface.test.mts。
//
// 各设备模块换成记录调用序列的假部件（会话、终结、Appium、探测、适配器、守卫、界面实现、预热、安装包存储），只验本模块的编排：
// 获取期的次序（存在性检查先于 Create；404 / 403 时 Create 零调用）、获取预算到期归 acquire_timeout、进入终结后获取停下、换台的
// 条件、各项义务的失败归类（先查会话状态再分会话丢失与执行出错）、交给探测与预热的会话状态查询、交给界面实现的输入上下文、句柄
// 上下文恰为七个字段、界面快照的读取条件与采集结果、释放的两种模式、device-session.json 的内容、按 scope 分目录的产物落点与
// reportRefs，以及会话事件的线上形状。部件的真实行为（Device Farm、WebdriverIO、Midscene）不在这里证明，由各块自己的测试与真机
// 验收负责。文件末尾另验缺省装配（device/parts.mts）接上的是各块的真实实现，以及接缝模块的静态加载闭包带到两项设备依赖。
import { afterEach, test } from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import ts from "typescript";
import type { Browser } from "webdriverio";
import {
  ACQUIRE_TIMEOUT_MESSAGE, HELPER_REJECTED_AGAIN_MESSAGE, HELPER_REJECTED_NO_TIME_MESSAGE,
  LIVENESS_FAILED_MESSAGE, PRE_STEP_FAILED_MESSAGE, SESSION_LOST_MESSAGE, WEB_CONTEXT_PROBE_ERROR_MESSAGE,
  WEB_CONTEXT_UNAVAILABLE_MESSAGE, createDeviceSurface, deviceAgentOpts, restoreFailedMessage,
  type AddressAttempt, type AppiumSession, type CommandGuard, type ConnectOutcome, type DeviceParts, type DevicePartsEnv,
  type DriverAdapter, type FinalizeHooks, type ProbeConclusion, type ProcessEvents, type WindowOutcome,
} from "./surface.mjs";
import { defaultDeviceParts } from "./parts.mjs";
import { commandGuardFactory } from "./guard.mjs";
import { deviceAgentFactory } from "./interface.mjs";
import { RUN_ID_ENV } from "./session-name.mjs";
import {
  DEVICE_SESSION_FILE, DEVICE_SESSION_REPORT_KIND, sessionClosedEvent, sessionEventSink, sessionOpenedEvent,
} from "./device-session.mjs";
import { APP_LAUNCH_SELF_EXIT_MESSAGE, APP_OBJECT_FORBIDDEN_MESSAGE, APP_OBJECT_MISSING_MESSAGE, APP_STATE } from "./app.mjs";
import {
  DEVICE_REPLANNING_CYCLE_LIMIT, MAX_SESSION_S, PAGE_SOURCE_MAX_BYTES, REPLACE_DEVICE_MIN_REMAINING_MS, REPLANNING_LIMIT_ENV,
} from "./limits.mjs";
import { readClassification, type SurfaceDeps, type TargetSurface } from "../worker/surface.mjs";
import { scenarioKey } from "../worker/evidence.mjs";
import { match, selectHandler, type SelectedHandler, type WebdriverCtx } from "../worker/deterministic.mjs";
import "../worker/deterministic.steps.mjs";
import type { Job } from "../lib/job-source.mjs";

// ---- 假部件 ----

// 内建导航的私有通道是进程级的：每个用例结束时释放它建的接缝，撤销注入、摘掉进程级兜底。
const opened: TargetSurface[] = [];
afterEach(async () => {
  for (const s of opened.splice(0)) await s.release("normal");
});

const ARN1 = "arn:aws:devicefarm:us-west-2:123456789012:session:p/r/00001";
const ARN2 = "arn:aws:devicefarm:us-west-2:123456789012:session:p/r/00002";
const ENDPOINT = "https://devicefarm-interactive-global.us-west-2.api.aws/remote-endpoint/SECRETTOKEN0123456789";
const SCOPE_ID = "features/shop.feature::Checkout";

type Target = { device: "android" | "ios"; uiKind: "web" | "app" };

interface HarnessOptions {
  target?: Target;
  acquireTimeoutS?: number;
  headPresence?: "present" | "missing" | "forbidden";
  connectOutcomes?: Array<"connected" | "replace_device" | ConnectOutcome>;
  conclusion?: Partial<ProbeConclusion>;
  appStates?: number[];
  status?: string | null;
  artifactRoot?: string | undefined;
  waitRunning?: (signal: AbortSignal) => Promise<void>;
  /** newSession 发出时调用（测试在这里推进时钟，模拟建连期间预算用尽）。 */
  beforeConnect?: () => void;
  automationName?: string;
  env?: NodeJS.ProcessEnv;
  scopeId?: string;
  /** 能力探测执行时调用（可抛出、可挂起到预算信号中止）。 */
  probeRun?: (signal: AbortSignal) => Promise<void>;
}

function makeJob(target: Target, acquireTimeoutS: number, scopeId: string = SCOPE_ID): Omit<Job, "scenarios"> {
  return {
    schemaVersion: 1,
    scope: { id: scopeId, name: "Checkout" },
    engine: "midscene",
    assertionVotes: 1,
    timeoutS: 1500,
    target: target.uiKind === "app"
      ? { ...target, app: { alias: "shop", bucket: "gherkai-apps", key: "apps/9f2c/shop.apk", sha256: "9f2c", appId: "com.example.shop" } }
      : { ...target },
    deviceRequest: {
      provider: "aws-device-farm", osVersion: "14", billingMethod: "METERED",
      projectArn: "arn:aws:devicefarm:us-west-2:123456789012:project:p", acquireTimeoutS,
    },
  };
}

function harness(opts: HarnessOptions = {}) {
  const target: Target = opts.target ?? { device: "android", uiKind: "web" };
  const calls: string[] = [];
  const emitted: Record<string, unknown>[] = [];
  const logs: string[] = [];
  const clock = { t: 1_000_000 };
  let status: string | null = opts.status ?? "RUNNING";
  let createSeq = 0;
  const connectQueue = [...(opts.connectOutcomes ?? ["connected"])];
  const appStates = [...(opts.appStates ?? [])];
  const processListeners = new Map<string, (r: unknown) => void>();
  const finalizations: { mode: string; hooks: FinalizeHooks }[] = [];
  let finalizeResult = { releaseFailed: false };
  let guardOutcome: WindowOutcome | null = null;
  const guardDriver = { guarded: true } as unknown as Browser;
  const execDriver = {
    activateApp: async (id: string) => { calls.push(`exec.activateApp:${id}`); },
    terminateApp: async (id: string) => { calls.push(`exec.terminateApp:${id}`); },
    queryAppState: async () => appStates.shift() ?? APP_STATE.FOREGROUND,
  } as unknown as Browser;
  const appiumSession = {
    exec: execDriver,
    automationName: opts.automationName ?? "UiAutomator2",
    // 与 Device Farm 设备描述的 "14.0" 故意不同：句柄上下文的系统版本只认会话回报的值。
    platformVersion: "14" as string | null,
    context: "NATIVE_APP",
    switchFails: false,
    screenshotFails: false,
    pageSourceText: "<hierarchy><node text=\"ok\"/></hierarchy>",
    pageSourceFails: false,
    address: { url: "https://shop.example/cart" } as AddressAttempt,
    async currentContext() { calls.push("appium.currentContext"); return this.context; },
    async switchToNative() {
      calls.push("appium.switchToNative");
      if (this.switchFails) throw new Error("UND_ERR_CLOSED");
      this.context = "NATIVE_APP";
    },
    async probeScreenshot() { calls.push("appium.probeScreenshot"); if (this.screenshotFails) throw new Error("timeout"); },
    async pageSource(signal: AbortSignal) {
      calls.push("appium.pageSource");
      if (signal.aborted) throw new Error("aborted");
      if (this.pageSourceFails) throw new Error("socket hang up");
      return this.pageSourceText;
    },
    async readWebAddress() { calls.push("appium.readWebAddress"); return this.address; },
    async withWebContext<T>(driver: Browser, fn: () => Promise<T> | T) {
      calls.push(`appium.withWebContext:${driver === guardDriver}`);
      return fn();
    },
    async openUrl(driver: Browser, address: string) { calls.push(`appium.openUrl:${driver === guardDriver}:${address}`); },
    async deleteSession() { calls.push("appium.deleteSession"); },
  };
  const adapter: DriverAdapter & { deepLinkError: Error | null; controlsItems: number | null } = {
    deepLinkError: null,
    controlsItems: null,
    async deepLink(driver, address, appId) {
      calls.push(`adapter.deepLink:${driver === guardDriver}:${address}:${appId}`);
      if (this.deepLinkError) throw this.deepLinkError;
    },
    extractControls(source) {
      calls.push("adapter.extractControls");
      if (this.controlsItems !== null) {
        const items = Array.from({ length: this.controlsItems }, (_, i) => ({ type: "node", id: `n${i}`, text: null, a11y_id: null }));
        return { items, total: this.controlsItems, truncated: false };
      }
      return { items: [{ type: "node", id: null, text: source.startsWith("<") ? "ok" : "?", a11y_id: null }], total: 1, truncated: false };
    },
  };
  const guard: CommandGuard & { opened: number; closed: number; shut: number; act: AbortController | null } = {
    driver: guardDriver, opened: 0, closed: 0, shut: 0, act: null,
    openWindow(act) { this.opened++; this.act = act; calls.push("guard.openWindow"); },
    closeWindow() { this.closed++; calls.push("guard.closeWindow"); const o = guardOutcome; guardOutcome = null; return o; },
    shutdown() { this.shut++; calls.push("guard.shutdown"); },
  };
  const conclusion: ProbeConclusion = {
    webContext: target.uiKind === "app" ? null : "available",
    webContextCandidates: target.uiKind === "app" ? null : 1,
    inputContext: null, scale: 1, scaleSource: "fixed", appiumVersion: "2.11.5",
    ...opts.conclusion,
  };
  let env: DevicePartsEnv | null = null;
  const created: { arn: string; name: string }[] = [];
  const statusQueries: { probe: (() => Promise<string | null>) | null; warmup: (() => Promise<string | null>) | null } = {
    probe: null, warmup: null,
  };
  const agentArgs: { inputContext: "web" | "native" | null; scale: number }[] = [];
  const parts = (e: DevicePartsEnv): DeviceParts => {
    env = e;
    return {
      sessions: {
        async resolve(_budget, replacing) {
          calls.push(`sessions.resolve:${replacing?.arn ?? "-"}`);
          return { ok: true, value: { deviceArn: "arn:aws:devicefarm:us-west-2::device:PIXEL", model: "Pixel 8", osVersion: "14.0" } };
        },
        async create(choice, _budget) {
          createSeq++;
          const arn = createSeq === 1 ? ARN1 : ARN2;
          const name = `gherkai:run-1:abcd:${createSeq}:features%2Fshop`;
          calls.push(`sessions.create:${choice.deviceArn}`);
          const device = { platform: target.device, model: choice.model, osVersion: choice.osVersion, unit: null };
          await e.events.opened({ sessionId: arn, name, origin: "created", device });
          created.push({ arn, name });
          return { ok: true, value: { arn, name, createRequestedAt: clock.t, device } };
        },
        async waitRunning(session, budget) {
          calls.push(`sessions.waitRunning:${session.arn}`);
          if (opts.waitRunning) await opts.waitRunning(budget.signal);
          return { ok: true, value: { endpoint: ENDPOINT, unit: "arn:aws:devicefarm:us-west-2::deviceinstance:U1" } };
        },
        async status(arn) { calls.push(`sessions.status:${arn}`); return status; },
        async retire(arn) { calls.push(`sessions.retire:${arn}`); },
      },
      finalizer: {
        async finalize(mode, hooks) {
          calls.push(`finalizer.finalize:${mode}`);
          finalizations.push({ mode, hooks });
          if (hooks.deleteAppiumSession) await hooks.deleteAppiumSession();
          for (const c of created) {
            await e.events.closed({ sessionId: c.arn, name: c.name, release: "confirmed", observedS: 12.5 });
          }
          return finalizeResult;
        },
      },
      appium: {
        async connect(req, _budget) {
          calls.push(`appium.connect:${req.uiKind}:${req.appUrl === null ? "-" : "presigned"}`);
          opts.beforeConnect?.();
          assert.equal(req.endpoint, ENDPOINT);
          const next = connectQueue.shift() ?? "connected";
          if (next === "connected") return { kind: "connected", session: appiumSession as unknown as AppiumSession };
          if (next === "replace_device") return { kind: "replace_device", reason: "INSTALL_FAILED_USER_RESTRICTED" };
          return next;
        },
      },
      probe: {
        async run(_s, t, budget, sessionStatus) {
          calls.push(`probe.run:${t.uiKind}`);
          statusQueries.probe = sessionStatus;
          if (opts.probeRun) await opts.probeRun(budget.signal);
          return { ok: true, value: conclusion };
        },
      },
      adapters: { select(name) { calls.push(`adapters.select:${name}`); return name === "UiAutomator2" || name === "XCUITest" ? adapter : null; } },
      guards: { create(args) { calls.push(`guards.create:${args.exec === execDriver}`); return guard; } },
      agents: {
        create(args) {
          calls.push(`agents.create:${args.driver === guardDriver}:${args.opts.replanningCycleLimit}`);
          agentArgs.push({ inputContext: args.inputContext, scale: args.scale });
          return { fakeAgent: true } as never;
        },
      },
      warmup: {
        async run(args) {
          calls.push(`warmup.run:${args.route}`);
          statusQueries.warmup = args.sessionStatus;
          return null;
        },
      },
      appStore: {
        async head(loc) { calls.push(`appStore.head:${loc.key}`); return opts.headPresence ?? "present"; },
        async presign(loc, expiresS) { calls.push(`appStore.presign:${expiresS}`); return `https://s3.example/${loc.key}?X-Amz-Signature=abc`; },
      },
    };
  };
  const processEvents: ProcessEvents = {
    on(event, listener) { processListeners.set(event, listener); },
    off(event) { processListeners.delete(event); },
  };
  let finalizationRequests = 0;
  const reportRefCalls: string[] = [];
  const artifactRoot = "artifactRoot" in opts ? opts.artifactRoot : fs.mkdtempSync(path.join(os.tmpdir(), "device-surface-"));
  const deps: SurfaceDeps = {
    job: makeJob(target, opts.acquireTimeoutS ?? 600, opts.scopeId),
    emit: async (event) => { emitted.push(event); },
    log: (line) => { logs.push(line); },
    agentOpts: { generateReport: false, persistExecutionDump: false } as never,
    uploader: {
      refFor: (p: string) => `s3://bucket/${path.basename(p)}`,
      toReportRef: async (p: string) => { reportRefCalls.push(p); return `s3://bucket/${path.basename(p)}`; },
    } as never,
    artifactRoot,
    requestFinalization: () => { finalizationRequests++; },
  };
  const surface = createDeviceSurface(deps, {
    parts, now: () => clock.t, env: opts.env ?? {}, processEvents, appTiming: { sleep: async () => {} },
  });
  opened.push(surface);
  // 设备产物按 scope 分目录：同一 run 的各 scope 共用产物根（MIDSCENE_RUN_DIR），文件名不能撞。
  const deviceDir = artifactRoot === undefined ? undefined : path.join(artifactRoot, "device", scenarioKey(opts.scopeId ?? SCOPE_ID));
  return {
    surface, calls, emitted, logs, clock, guard, adapter, appiumSession, finalizations, reportRefCalls, artifactRoot, deviceDir,
    processListeners, guardDriver, execDriver, statusQueries, agentArgs,
    get env() { return env!; },
    get finalizationRequests() { return finalizationRequests; },
    setStatus(s: string | null) { status = s; },
    setGuardOutcome(o: WindowOutcome | null) { guardOutcome = o; },
    setFinalizeResult(r: { releaseFailed: boolean }) { finalizeResult = r; },
  };
}

async function ready(h: ReturnType<typeof harness>): Promise<void> {
  const r = await h.surface.acquire();
  assert.equal(r.ready, true, JSON.stringify(r));
}

function webdriverSelected(fn: (ctx: WebdriverCtx, groups: Record<string, string>) => void | Promise<void>,
                           requires: readonly "web_context"[] = []): SelectedHandler {
  return { kind: "webdriver", fn, requires };
}

// ---- 获取期的编排 ----

test("网页目标的获取次序：解析、Create、等到 RUNNING、newSession、探测、适配器、守卫、Agent；sessionId 是会话 ARN", async () => {
  const h = harness();
  const r = await h.surface.acquire();
  assert.equal(r.ready, true);
  assert.equal(r.ready && r.sessionId, ARN1);
  assert.equal(h.surface.sessionId(), ARN1);
  assert.deepEqual(h.calls, [
    "sessions.resolve:-", "sessions.create:arn:aws:devicefarm:us-west-2::device:PIXEL", `sessions.waitRunning:${ARN1}`,
    "appium.connect:web:-", "probe.run:web", "adapters.select:UiAutomator2", "guards.create:true",
    `agents.create:true:${DEVICE_REPLANNING_CYCLE_LIMIT}`,
  ]);
});

test("scope_started 之前接缝只经会话事件出口发出 session_opened，自己不发任何其它事件", async () => {
  const h = harness();
  await ready(h);
  assert.equal(await h.surface.warmup("https://tunnel.example/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=T"), null);
  assert.deepEqual(h.emitted.map((e) => e.type), ["session_opened"]);
  assert.deepEqual(h.emitted[0], {
    type: "session_opened", scopeId: "features/shop.feature::Checkout", sessionId: ARN1,
    name: "gherkai:run-1:abcd:1:features%2Fshop", origin: "created",
    device: { platform: "android", model: "Pixel 8", osVersion: "14.0", unit: null },
  });
});

test("应用目标：存在性检查先于 Create，预签名在 newSession 之前，建好后经执行实例显式启动并采样", async () => {
  const h = harness({ target: { device: "android", uiKind: "app" } });
  await ready(h);
  const order = (prefix: string) => h.calls.findIndex((c) => c.startsWith(prefix));
  assert.ok(order("appStore.head") < order("sessions.resolve"));
  assert.ok(order("sessions.waitRunning") < order("appStore.presign:3600"));
  assert.ok(order("appStore.presign") < order("appium.connect:app:presigned"));
  assert.ok(order("appium.connect") < order("exec.activateApp:com.example.shop"));
  assert.ok(order("exec.activateApp") < order("probe.run:app"));
});

for (const [presence, message] of [["missing", APP_OBJECT_MISSING_MESSAGE], ["forbidden", APP_OBJECT_FORBIDDEN_MESSAGE]] as const) {
  test(`安装包 HeadObject 为 ${presence} 时记 precheck_failed，Device Farm 零调用、不发任何事件`, async () => {
    const h = harness({ target: { device: "ios", uiKind: "app" }, headPresence: presence });
    const r = await h.surface.acquire();
    assert.deepEqual(r, { ready: false, termination: { errorType: "precheck_failed", message } });
    assert.deepEqual(h.calls, ["appStore.head:apps/9f2c/shop.apk"]);
    assert.deepEqual(h.emitted, []);
    assert.equal(h.surface.sessionId(), null);
  });
}

test("获取预算到期：在途的等待被预算信号中止，归 acquire_timeout 并用原文消息", async () => {
  const h = harness({
    acquireTimeoutS: 0.05,
    waitRunning: (signal) => new Promise((_resolve, reject) => {
      signal.addEventListener("abort", () => { h.clock.t += 60_000; reject(new Error("aborted")); }, { once: true });
    }),
  });
  const r = await h.surface.acquire();
  assert.deepEqual(r, { ready: false, termination: { errorType: "acquire_timeout", message: ACQUIRE_TIMEOUT_MESSAGE } });
  assert.equal(h.surface.sessionId(), ARN1);  // 已建的会话照常由释放收尾
});

test("预算到期后部件给出的非判据型失败也归 acquire_timeout，precheck_failed 保持原归因", async () => {
  const clockRef: { h?: ReturnType<typeof harness> } = {};
  const h = harness({
    connectOutcomes: [{ kind: "terminated", termination: { errorType: "engine_error", message: "newSession 失败" } }],
    beforeConnect: () => { clockRef.h!.clock.t += 601_000; },  // newSession 期间预算用尽
  });
  clockRef.h = h;
  const r = await h.surface.acquire();
  assert.deepEqual(r, { ready: false, termination: { errorType: "acquire_timeout", message: ACQUIRE_TIMEOUT_MESSAGE } });

  const h2 = harness({ target: { device: "android", uiKind: "app" }, headPresence: "missing" });
  const p2 = h2.surface.acquire();
  h2.clock.t += 601_000;
  assert.deepEqual(await p2, { ready: false, termination: { errorType: "precheck_failed", message: APP_OBJECT_MISSING_MESSAGE } });
});

test("进入终结后获取停下：等到 RUNNING 期间中断，之后不再建连、不建守卫", async () => {
  let entered!: () => void;
  const inWait = new Promise<void>((resolve) => { entered = resolve; });
  // 部件没有先看已中止的信号、照常返回成功：接缝自己也要停下。
  const h = harness({
    waitRunning: (signal) => { entered(); return new Promise((resolve) => signal.addEventListener("abort", () => resolve(), { once: true })); },
  });
  const acquiring = h.surface.acquire();
  await inWait;
  const releasing = h.surface.release("interrupt");
  const r = await acquiring;
  await releasing;
  assert.equal(r.ready, false);
  assert.ok(!h.calls.some((c) => c.startsWith("appium.connect")), h.calls.join(", "));
  assert.ok(!h.calls.some((c) => c.startsWith("guards.create")), h.calls.join(", "));
});

test("进入终结后获取停下：探测在终结开始时成功返回，之后不建守卫与 Agent、不注入导航", async () => {
  let entered!: () => void;
  const inProbe = new Promise<void>((resolve) => { entered = resolve; });
  const h = harness({
    probeRun: (signal) => { entered(); return new Promise((resolve) => signal.addEventListener("abort", () => resolve(), { once: true })); },
  });
  const acquiring = h.surface.acquire();
  await inProbe;
  const releasing = h.surface.release("interrupt");
  const r = await acquiring;
  await releasing;
  assert.equal(r.ready, false);
  for (const prefix of ["adapters.select", "guards.create", "agents.create"]) {
    assert.ok(!h.calls.some((c) => c.startsWith(prefix)), `${prefix}: ${h.calls.join(", ")}`);
  }
  const next = harness();
  await ready(next);  // 导航注入留下时这里会抛出
});

test("设备单元拒装驱动辅助包：剩余预算足够时停掉被替换的会话、换一台重建一次", async () => {
  const h = harness({ connectOutcomes: ["replace_device", "connected"] });
  await ready(h);
  assert.deepEqual(h.calls.slice(0, 9), [
    "sessions.resolve:-", "sessions.create:arn:aws:devicefarm:us-west-2::device:PIXEL", `sessions.waitRunning:${ARN1}`,
    "appium.connect:web:-", `sessions.retire:${ARN1}`, `sessions.resolve:${ARN1}`,
    "sessions.create:arn:aws:devicefarm:us-west-2::device:PIXEL", `sessions.waitRunning:${ARN2}`, "appium.connect:web:-",
  ]);
  assert.equal(h.surface.sessionId(), ARN2);
  assert.deepEqual(h.emitted.map((e) => e.sessionId), [ARN1, ARN2]);
});

test("换过一次仍拒装，或剩余预算不足 150 秒，记 precheck_failed、不再换台", async () => {
  const again = harness({ connectOutcomes: ["replace_device", "replace_device"] });
  assert.deepEqual(await again.surface.acquire(),
    { ready: false, termination: { errorType: "precheck_failed", message: HELPER_REJECTED_AGAIN_MESSAGE } });
  assert.equal(again.calls.filter((c) => c.startsWith("sessions.create")).length, 2);

  const short = harness({ connectOutcomes: ["replace_device"], acquireTimeoutS: (REPLACE_DEVICE_MIN_REMAINING_MS - 1000) / 1000 });
  assert.deepEqual(await short.surface.acquire(),
    { ready: false, termination: { errorType: "precheck_failed", message: HELPER_REJECTED_NO_TIME_MESSAGE } });
  assert.equal(short.calls.filter((c) => c.startsWith("sessions.retire")).length, 0);
});

test("启动即自退记 precheck_failed；Appium 会话已建成，正常收尾先 deleteSession 再释放", async () => {
  const h = harness({ target: { device: "android", uiKind: "app" }, appStates: [APP_STATE.FOREGROUND, APP_STATE.NOT_RUNNING] });
  assert.deepEqual(await h.surface.acquire(),
    { ready: false, termination: { errorType: "precheck_failed", message: APP_LAUNCH_SELF_EXIT_MESSAGE } });
  assert.ok(!h.calls.some((c) => c.startsWith("probe.run")));
  const out = await h.surface.release("normal");
  assert.equal(out.releaseFailed, false);
  assert.equal(h.finalizations[0].mode, "normal");
  assert.ok(h.finalizations[0].hooks.deleteAppiumSession !== null);
  assert.ok(h.calls.includes("appium.deleteSession"));
});

test("Appium 会话建成后探测抛出未归类异常：记 engine_error，正常收尾仍先 deleteSession", async () => {
  const h = harness({ probeRun: async () => { throw new Error("x"); } });
  const r = await h.surface.acquire();
  assert.equal(r.ready, false);
  assert.equal(!r.ready && r.termination.errorType, "engine_error");
  assert.ok(!h.calls.some((c) => c.startsWith("guards.create")));
  await h.surface.release("normal");
  assert.notEqual(h.finalizations[0].hooks.deleteAppiumSession, null);
  assert.ok(h.calls.includes("appium.deleteSession"));
});

test("没有对应驱动适配器的 automationName 记 engine_error 的执行前失败", async () => {
  const h = harness({ automationName: "Espresso" });
  const r = await h.surface.acquire();
  assert.equal(r.ready, false);
  assert.equal(!r.ready && r.termination.errorType, "engine_error");
  assert.match(!r.ready ? r.termination.message : "", /Espresso/);
});

test("预热：网页目标按探测结论选路线（提供走 url，不提供与探测出错走 deep_link）；应用目标不预热", async () => {
  for (const [webContext, route] of [["available", "url"], ["unavailable", "deep_link"], ["probe_error", "deep_link"]] as const) {
    const h = harness({ conclusion: { webContext } });
    await ready(h);
    assert.equal(await h.surface.warmup("https://tunnel.example/w"), null);
    assert.ok(h.calls.includes(`warmup.run:${route}`), `${webContext} 应走 ${route}`);
    await h.surface.release("normal");
  }
  const app = harness({ target: { device: "ios", uiKind: "app" } });
  await ready(app);
  assert.equal(await app.surface.warmup("https://tunnel.example/w"), null);
  assert.ok(!app.calls.some((c) => c.startsWith("warmup.run")));
});

test("能力探测与预热拿到的会话状态查询绑定当前会话 ARN：两处的命令失败据此先查会话状态再归类（ADR 0051 决策 4、ADR 0052 决策 5）", async () => {
  const h = harness();
  await ready(h);
  assert.equal(await h.surface.warmup("https://tunnel.example/w"), null);
  for (const which of ["probe", "warmup"] as const) {
    const query = h.statusQueries[which];
    assert.ok(query, `${which} 应收到会话状态查询`);
    h.calls.length = 0;
    h.setStatus("STOPPING");
    assert.equal(await query(), "STOPPING");
    assert.deepEqual(h.calls, [`sessions.status:${ARN1}`]);
  }
});

test("界面实现拿到能力探测给出的输入上下文与坐标比例：iOS 按探测结论，Android 为 null（ADR 0052 决策 5、7）", async () => {
  for (const [device, inputContext] of [["ios", "web"], ["ios", "native"], ["android", null]] as const) {
    const h = harness({ target: { device, uiKind: "web" }, conclusion: { inputContext, scale: device === "ios" ? 3 : 1 } });
    await ready(h);
    assert.deepEqual(h.agentArgs, [{ inputContext, scale: device === "ios" ? 3 : 1 }]);
    await h.surface.release("normal");
  }
});

test("部件工厂收到的环境带构造项里的 env：缺省装配从这里读本次运行编号，不另读进程 env", async () => {
  const h = harness({ env: { [RUN_ID_ENV]: "run-from-options" } });
  assert.equal(h.env.processEnv[RUN_ID_ENV], "run-from-options");
});

// ---- 确定性句柄 ----

test("句柄上下文恰为七个字段：driver 是守卫代理；应用目标带 appId 与 app.restart，网页目标两者为 null", async () => {
  const web = harness();
  await ready(web);
  let seen: WebdriverCtx | null = null;
  await web.surface.bindHandler(webdriverSelected((ctx) => { seen = ctx; }))({});
  assert.deepEqual(Object.keys(seen!).sort(), ["app", "appId", "device", "driver", "log", "uiKind", "withWebContext"]);
  assert.strictEqual(seen!.driver, web.guardDriver);
  assert.deepEqual(seen!.device, { platform: "android", osVersion: "14", scale: 1 });
  assert.equal(seen!.uiKind, "web");
  assert.equal(seen!.appId, null);
  assert.equal(seen!.app, null);
  await web.surface.release("normal");

  const app = harness({ target: { device: "ios", uiKind: "app" }, conclusion: { scale: 3, scaleSource: "device_screen_info" } });
  app.appiumSession.platformVersion = null;  // 会话没有回报系统版本时为空串，不回落到 Device Farm 的设备描述
  await ready(app);
  let appCtx: WebdriverCtx | null = null;
  await app.surface.bindHandler(webdriverSelected((ctx) => { appCtx = ctx; }))({});
  assert.equal(appCtx!.appId, "com.example.shop");
  assert.deepEqual(appCtx!.device, { platform: "ios", osVersion: "", scale: 3 });
  assert.equal(typeof appCtx!.app?.restart, "function");
  await assert.rejects(appCtx!.withWebContext(() => 1), (e) => readClassification(e)?.errorType === "capability_unavailable");
});

test("requires web_context：不提供记 capability_unavailable、探测出错记 engine_error，都同步抛出、不调 handler", async () => {
  for (const [webContext, errorType, message] of [
    ["unavailable", "capability_unavailable", WEB_CONTEXT_UNAVAILABLE_MESSAGE],
    ["probe_error", "engine_error", WEB_CONTEXT_PROBE_ERROR_MESSAGE],
  ] as const) {
    const h = harness({ conclusion: { webContext } });
    await ready(h);
    let called = false;
    assert.throws(() => h.surface.bindHandler(webdriverSelected(() => { called = true; }, ["web_context"])),
      (e) => { assert.deepEqual(readClassification(e), { errorType, message }); return true; });
    assert.equal(called, false);
    await h.surface.release("normal");
  }
  const ok = harness();
  await ready(ok);
  let ran = false;
  await ok.surface.bindHandler(webdriverSelected(async (ctx) => { await ctx.withWebContext(() => { ran = true; }); }, ["web_context"]))({});
  assert.equal(ran, true);
  assert.ok(ok.calls.includes("appium.withWebContext:true"));
});

test("playwright 句柄落到设备上同步抛出 engine_error", async () => {
  const h = harness();
  await ready(h);
  assert.throws(() => h.surface.bindHandler({ kind: "playwright", fn: () => {} }),
    (e) => readClassification(e)?.errorType === "engine_error");
});

// ---- 导航 ----

test("内建导航经模块私有通道取到接缝的导航原语：应用目标经 DeepLink 带应用标识，网页目标按探测结论择路", async () => {
  const cases = [
    [{ device: "android", uiKind: "app" }, "available", "myshop://cart", "adapter.deepLink:true:myshop://cart:com.example.shop"],
    [{ device: "android", uiKind: "web" }, "available", "https://shop.example/", "appium.openUrl:true:https://shop.example/"],
    [{ device: "ios", uiKind: "web" }, "unavailable", "https://shop.example/", "adapter.deepLink:true:https://shop.example/:null"],
  ] as const;
  for (const [target, webContext, address, expected] of cases) {
    const h = harness({ target, conclusion: { webContext: target.uiKind === "app" ? null : webContext } });
    await ready(h);
    const hit = match(`"${address}"`, "Given")!;
    assert.equal(hit.builtin, "navigation");
    const selected = selectHandler(hit, target)!;
    await h.surface.execute(() => h.surface.bindHandler(selected)(hit.groups));
    assert.ok(h.calls.includes(expected), `${JSON.stringify(target)}: ${h.calls.join(", ")}`);
    await h.surface.release("normal");
  }
});

test("导航失败没有归类时挂 engine_error；已带归类的原样传出", async () => {
  const h = harness({ target: { device: "android", uiKind: "app" } });
  await ready(h);
  h.adapter.deepLinkError = new Error("boom");
  await assert.rejects(h.surface.navigate("myshop://x"), (e) => readClassification(e)?.errorType === "engine_error");
  const { attachClassification } = await import("../worker/surface.mjs");
  h.adapter.deepLinkError = attachClassification(new Error("unable to resolve Intent"),
    { errorType: "capability_unavailable", message: "应用没有处理这个地址" });
  await assert.rejects(h.surface.navigate("myshop://x"),
    (e) => readClassification(e)?.errorType === "capability_unavailable");
});

// ---- 四项边界义务 ----

test("step 前核对：在原生上下文只读一次；不在则切回；切回失败且会话仍在运行记 engine_error", async () => {
  const h = harness();
  await ready(h);
  h.calls.length = 0;
  assert.equal(await h.surface.preStep(), null);
  assert.deepEqual(h.calls, ["appium.currentContext"]);
  h.appiumSession.context = "CHROMIUM";
  assert.equal(await h.surface.preStep(), null);
  assert.ok(h.calls.includes("appium.switchToNative"));
  h.appiumSession.context = "CHROMIUM";
  h.appiumSession.switchFails = true;
  assert.deepEqual(await h.surface.preStep(), { errorType: "engine_error", message: PRE_STEP_FAILED_MESSAGE });
  assert.ok(h.calls.includes(`sessions.status:${ARN1}`));
});

test("命令失败先查会话状态：不是 RUNNING 即会话丢失并锁存，之后的义务与快照不再向设备发命令", async () => {
  const h = harness();
  await ready(h);
  h.appiumSession.context = "CHROMIUM";
  h.appiumSession.switchFails = true;
  h.setStatus("STOPPING");
  assert.deepEqual(await h.surface.preStep(), { errorType: "session_lost", message: SESSION_LOST_MESSAGE });
  h.calls.length = 0;
  assert.equal(await h.surface.restore({ status: "error", message: SESSION_LOST_MESSAGE }), null);
  const snap = await h.surface.snapshot({ kind: "ai", status: "error" }, null);
  assert.equal(snap.failure, null);
  assert.deepEqual(snap.snapshot, {
    url: null, url_missing: "error", step_kind: "ai",
    controls: null, controls_missing: "error", page_source_path: null, page_source_truncated: false,
  });
  assert.deepEqual(await h.surface.preScenarioCheck(), { errorType: "session_lost", message: SESSION_LOST_MESSAGE });
  assert.deepEqual(h.calls, []);
});

test("step 后复原失败：原判定写进消息；原判定已是 error 时以它的消息开头", async () => {
  const h = harness();
  await ready(h);
  h.appiumSession.context = "WEBVIEW_1234";
  h.appiumSession.switchFails = true;
  assert.deepEqual(await h.surface.restore({ status: "passed", message: null }), {
    errorType: "engine_error", message: "原判定为 passed；之后未能切回原生界面，后续 step 的截图坐标会错位",
  });
  const unknown = "设备在等待时间内没有回应，这一步可能已执行也可能未执行";
  assert.equal(restoreFailedMessage({ status: "error", message: unknown }),
    `${unknown}；之后未能切回原生界面，后续 step 的截图坐标会错位`);
  assert.equal(restoreFailedMessage({ status: "failed", message: "断言不成立" }),
    "原判定为 failed；之后未能切回原生界面，后续 step 的截图坐标会错位");
});

test("执行窗口：进入时发令牌、结束时撤销；守卫判过结果未知时以带标记的异常拒绝，下一条 scenario 前做一次存活探测", async () => {
  const h = harness();
  await ready(h);
  assert.equal(await h.surface.execute(async (signal) => { assert.ok(signal instanceof AbortSignal); return 7; }), 7);
  assert.deepEqual([h.guard.opened, h.guard.closed], [1, 1]);
  assert.equal(await h.surface.preScenarioCheck(), null);
  assert.ok(!h.calls.includes("appium.probeScreenshot"));

  const unknown = { errorType: "engine_error" as const, message: "设备在等待时间内没有回应，这一步可能已执行也可能未执行" };
  h.setGuardOutcome({ failure: unknown, resultUnknown: true });
  await assert.rejects(h.surface.execute(async () => "handler 吞掉了守卫的异常"), (e) => {
    assert.deepEqual(readClassification(e), unknown);
    return true;
  });
  assert.equal(await h.surface.preScenarioCheck(), null);
  assert.equal(h.calls.filter((c) => c === "appium.probeScreenshot").length, 1);
  assert.equal(await h.surface.preScenarioCheck(), null);  // 记录在核对后清掉
  assert.equal(h.calls.filter((c) => c === "appium.probeScreenshot").length, 1);
});

test("存活探测失败按会话状态分流：仍在运行记 engine_error，否则记 session_lost", async () => {
  const unknown = { errorType: "engine_error" as const, message: "设备在等待时间内没有回应，这一步可能已执行也可能未执行" };
  for (const [status, expected] of [
    ["RUNNING", { errorType: "engine_error", message: LIVENESS_FAILED_MESSAGE }],
    ["COMPLETED", { errorType: "session_lost", message: SESSION_LOST_MESSAGE }],
  ] as const) {
    const h = harness();
    await ready(h);
    h.setGuardOutcome({ failure: unknown, resultUnknown: true });
    await assert.rejects(h.surface.execute(async () => {}));
    h.appiumSession.screenshotFails = true;
    h.setStatus(status);
    assert.deepEqual(await h.surface.preScenarioCheck(), expected);
    await h.surface.release("normal");
  }
});

test("守卫判会话丢失时锁存：后续执行直接拒绝、不再发令牌", async () => {
  const h = harness();
  await ready(h);
  h.setGuardOutcome({ failure: { errorType: "session_lost", message: "x" }, resultUnknown: false });
  await assert.rejects(h.surface.execute(async () => {}),
    (e) => readClassification(e)?.message === SESSION_LOST_MESSAGE);
  const opened = h.guard.opened;
  await assert.rejects(h.surface.execute(async () => {}), (e) => readClassification(e)?.errorType === "session_lost");
  assert.equal(h.guard.opened, opened);
});

test("会话年龄到 max_session_s：scenario 前核对与 step 前核对都归 session_lost，执行窗口不再打开", async () => {
  const h = harness();
  await ready(h);
  h.clock.t += MAX_SESSION_S * 1000;
  h.calls.length = 0;
  assert.deepEqual(await h.surface.preScenarioCheck(), { errorType: "session_lost", message: SESSION_LOST_MESSAGE });
  assert.deepEqual(await h.surface.preStep(), { errorType: "session_lost", message: SESSION_LOST_MESSAGE });
  await assert.rejects(h.surface.execute(async () => {}), (e) => readClassification(e)?.errorType === "session_lost");
  assert.equal(h.guard.opened, 0);
  assert.deepEqual(h.calls, []);
});

test("会话年龄在执行中途到点：中止当前 act、撤销令牌，这一步归 session_lost 并锁存", async () => {
  const h = harness();
  await ready(h);
  h.clock.t = 1_000_000 + MAX_SESSION_S * 1000 - 30;
  await assert.rejects(
    h.surface.execute((signal) => new Promise((_, rej) => signal!.addEventListener("abort", () => rej(new Error("aborted"))))),
    (e) => { assert.deepEqual(readClassification(e), { errorType: "session_lost", message: SESSION_LOST_MESSAGE }); return true; },
  );
  assert.equal(h.guard.closed, 1);
  assert.equal(h.guard.act?.signal.aborted, true);
  assert.deepEqual(await h.surface.preStep(), { errorType: "session_lost", message: SESSION_LOST_MESSAGE });
});

// ---- 界面快照 ----

test("读地址的条件：AI step 一律读，确定性与导航 step 只在暂定判定为 failed / error 时读", async () => {
  const h = harness();
  await ready(h);
  await h.surface.preStep();
  assert.equal(await h.surface.readAddress({ kind: "deterministic", status: "passed" }), null);
  assert.equal(await h.surface.readAddress({ kind: "navigation", status: "passed" }), null);
  assert.ok(!h.calls.includes("appium.readWebAddress"));
  assert.deepEqual(await h.surface.readAddress({ kind: "ai", status: "passed" }), { url: "https://shop.example/cart", url_missing: null });
  h.appiumSession.address = { missing: "error" };
  assert.deepEqual(await h.surface.readAddress({ kind: "deterministic", status: "failed" }), { url: null, url_missing: "error" });
});

test("不发命令即可确定的地址：应用目标 not_applicable，不提供网页上下文 no_web_context，探测出错 error", async () => {
  for (const [target, webContext, missing] of [
    [{ device: "android", uiKind: "app" }, null, "not_applicable"],
    [{ device: "ios", uiKind: "web" }, "unavailable", "no_web_context"],
    [{ device: "ios", uiKind: "web" }, "probe_error", "error"],
  ] as const) {
    const h = harness({ target, conclusion: { webContext } });
    await ready(h);
    await h.surface.preStep();
    assert.deepEqual(await h.surface.readAddress({ kind: "ai", status: "passed" }), { url: null, url_missing: missing });
    assert.ok(!h.calls.includes("appium.readWebAddress"));
    await h.surface.release("normal");
  }
});

test("快照：passed 只有地址与 step_kind；failed / error 采控件摘要与原始控件树，原始树写盘前脱敏", async () => {
  const h = harness();
  await ready(h);
  await h.surface.preStep();
  const passed = await h.surface.snapshot({ kind: "ai", status: "passed" }, { url: "https://a/", url_missing: null });
  assert.deepEqual(passed, { snapshot: { url: "https://a/", url_missing: null, step_kind: "ai" }, failure: null });

  h.appiumSession.pageSourceText = `<node text="${ENDPOINT}" href="https://s3.example/a?X-Amz-Signature=deadbeef"/>`;
  const failed = await h.surface.snapshot({ kind: "deterministic", status: "failed" }, null);
  assert.equal(failed.failure, null);
  const s = failed.snapshot;
  assert.equal(s.step_kind, "deterministic");
  assert.equal(s.url, null);
  assert.equal(s.url_missing, "error");  // 第 4 步没读、而本 step 要产 evidence：不补读
  assert.deepEqual(s.controls, { items: [{ type: "node", id: null, text: "ok", a11y_id: null }], total: 1, truncated: false });
  assert.equal(s.controls_missing, null);
  assert.equal(s.page_source_truncated, false);
  const written = fs.readFileSync(s.page_source_path!, "utf-8");
  assert.ok(!written.includes("SECRETTOKEN") && !written.includes("deadbeef"), written);
  assert.ok(s.page_source_path!.startsWith(path.join(h.deviceDir!, "page-source") + path.sep), s.page_source_path!);
});

test("原始控件树超过 1 MiB 时按字节截断、不切断多字节字符，并标记截断", async () => {
  const h = harness();
  await ready(h);
  await h.surface.preStep();
  h.appiumSession.pageSourceText = "<a>" + "控".repeat(PAGE_SOURCE_MAX_BYTES / 3 + 10) + "</a>";
  const { snapshot } = await h.surface.snapshot({ kind: "ai", status: "error" }, { url: null, url_missing: "timeout" });
  assert.equal(snapshot.page_source_truncated, true);
  const bytes = fs.readFileSync(snapshot.page_source_path!);
  assert.ok(bytes.length <= PAGE_SOURCE_MAX_BYTES);
  assert.ok(!bytes.toString("utf-8").includes("�"));
  assert.equal(snapshot.url_missing, "timeout");
});

test("控件摘要超过 200 条时截断到 200 条，total 记原有条数并标记截断", async () => {
  const h = harness();
  await ready(h);
  await h.surface.preStep();
  h.adapter.controlsItems = 250;
  const { snapshot } = await h.surface.snapshot({ kind: "ai", status: "failed" }, { url: "https://a/", url_missing: null });
  assert.equal(snapshot.controls!.items.length, 200);
  assert.equal(snapshot.controls!.total, 250);
  assert.equal(snapshot.controls!.truncated, true);
});

test("快照采集失败只标原因、不改判定；采集中发现会话丢失时改判 session_lost", async () => {
  const h = harness();
  await ready(h);
  await h.surface.preStep();
  h.appiumSession.pageSourceFails = true;
  const r1 = await h.surface.snapshot({ kind: "ai", status: "failed" }, { url: "https://a/", url_missing: null });
  assert.equal(r1.failure, null);
  assert.equal(r1.snapshot.controls, null);
  assert.equal(r1.snapshot.controls_missing, "error");
  assert.equal(r1.snapshot.page_source_path, null);
  h.setStatus("STOPPING");
  const r2 = await h.surface.snapshot({ kind: "ai", status: "failed" }, { url: "https://a/", url_missing: null });
  assert.deepEqual(r2.failure, { errorType: "session_lost", message: SESSION_LOST_MESSAGE });
});

test("evidence 采集预算用尽时不再发命令，记 timeout", async () => {
  const h = harness();
  await ready(h);
  await h.surface.preStep();
  await h.surface.readAddress({ kind: "ai", status: "failed" });
  h.clock.t += 10_001;
  h.calls.length = 0;
  const { snapshot } = await h.surface.snapshot({ kind: "ai", status: "failed" }, { url: "https://a/", url_missing: null });
  assert.equal(snapshot.controls_missing, "timeout");
  assert.deepEqual(h.calls, []);
  await h.surface.preStep();  // 下一个 step 重新起算
  const next = await h.surface.snapshot({ kind: "ai", status: "failed" }, { url: "https://a/", url_missing: null });
  assert.equal(next.snapshot.controls_missing, null);
});

test("没有产物落点时不写原始控件树，也不写 device-session.json", async () => {
  const h = harness({ artifactRoot: undefined });
  await ready(h);
  await h.surface.preStep();
  const { snapshot } = await h.surface.snapshot({ kind: "ai", status: "failed" }, { url: "https://a/", url_missing: null });
  assert.equal(snapshot.page_source_path, null);
  assert.notEqual(snapshot.controls, null);
  assert.deepEqual((await h.surface.release("normal")).reportRefs, []);
});

test("同一产物根下不同 scope 的原始控件树与 device-session.json 各写各的目录", async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "device-surface-shared-"));
  const outputs: { pageSource: string; sessionFile: string }[] = [];
  for (const scopeId of ["features/shop.feature::Checkout", "features/shop.feature::Refund"]) {
    const h = harness({ artifactRoot: root, scopeId });
    await ready(h);
    await h.surface.preStep();
    const { snapshot } = await h.surface.snapshot({ kind: "ai", status: "failed" }, { url: "https://a/", url_missing: null });
    await h.surface.release("normal");
    const dir = path.join(root, "device", scenarioKey(scopeId));
    assert.ok(snapshot.page_source_path!.startsWith(dir + path.sep), snapshot.page_source_path!);
    assert.deepEqual(h.reportRefCalls, [path.join(dir, DEVICE_SESSION_FILE)]);
    outputs.push({ pageSource: snapshot.page_source_path!, sessionFile: h.reportRefCalls[0] });
  }
  assert.notEqual(outputs[0].pageSource, outputs[1].pageSource);
  assert.notEqual(outputs[0].sessionFile, outputs[1].sessionFile);
  for (const o of outputs) assert.ok(fs.existsSync(o.pageSource) && fs.existsSync(o.sessionFile));
});

// ---- 释放 ----

test("正常释放：交终结块处理（带 deleteSession 钩子），写 device-session.json 并作为 device_session 链接返回", async () => {
  const h = harness();
  await ready(h);
  await h.surface.warmup("https://tunnel.example/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=T0K3N");
  const out = await h.surface.release("normal");
  assert.equal(out.releaseFailed, false);
  assert.deepEqual(out.reportRefs, [{ kind: DEVICE_SESSION_REPORT_KIND, ref: `s3://bucket/${DEVICE_SESSION_FILE}` }]);
  assert.ok(h.calls.indexOf("guard.shutdown") < h.calls.indexOf("finalizer.finalize:normal"));
  assert.ok(h.calls.includes("appium.deleteSession"));
  assert.deepEqual(h.emitted.map((e) => e.type), ["session_opened", "session_closed"]);
  const doc = JSON.parse(fs.readFileSync(path.join(h.deviceDir!, DEVICE_SESSION_FILE), "utf-8"));
  assert.equal(doc.session.arn, ARN1);
  assert.deepEqual(doc.session.device, { platform: "android", model: "Pixel 8", osVersion: "14.0", unit: "arn:aws:devicefarm:us-west-2::deviceinstance:U1" });
  assert.deepEqual(doc.probe, {
    web_context: "available", web_context_candidates: 1, input_context: null, scale: 1, scale_source: "fixed", appium_version: "2.11.5",
  });
  assert.equal(doc.automation_name, "UiAutomator2");
  assert.equal(doc.release_failed, false);
  assert.equal(doc.acquire_failure, null);
  for (const k of ["acquire_started_at", "session_created_at", "session_running_at", "appium_connected_at", "probe_done_at", "ready_at", "warmup_done_at", "released_at"]) {
    assert.equal(typeof doc.timings[k], "string", k);
  }
  const raw = fs.readFileSync(path.join(h.deviceDir!, DEVICE_SESSION_FILE), "utf-8");
  assert.ok(!raw.includes("remote-endpoint") && !raw.includes("T0K3N"));
});

test("中断释放：撤销令牌并中止当前 act，不给 deleteSession 钩子，不返回链接；重复调用只进入一次", async () => {
  const h = harness();
  await ready(h);
  let actSignal: AbortSignal | undefined;
  const running = h.surface.execute((signal) => { actSignal = signal; return new Promise(() => {}); });
  void running;
  const a = h.surface.release("interrupt");
  const b = h.surface.release("normal");
  assert.strictEqual(a, b);
  const out = await a;
  assert.equal(actSignal?.aborted, true);
  assert.equal(h.guard.shut, 1);
  assert.equal(h.finalizations.length, 1);
  assert.deepEqual(h.finalizations[0], { mode: "interrupt", hooks: { deleteAppiumSession: null } });
  assert.deepEqual(out.reportRefs, []);
  assert.ok(fs.existsSync(path.join(h.deviceDir!, DEVICE_SESSION_FILE)));
  assert.deepEqual(h.reportRefCalls, []);
});

test("执行前失败在 Appium 会话建成之前：正常释放不给 deleteSession 钩子；释放未确认如实返回", async () => {
  const h = harness({ connectOutcomes: [{ kind: "terminated", termination: { errorType: "precheck_failed", message: "x" } }] });
  const r = await h.surface.acquire();
  assert.equal(r.ready, false);
  h.setFinalizeResult({ releaseFailed: true });
  const out = await h.surface.release("normal");
  assert.equal(out.releaseFailed, true);
  assert.equal(h.finalizations[0].hooks.deleteAppiumSession, null);
  const doc = JSON.parse(fs.readFileSync(path.join(h.deviceDir!, DEVICE_SESSION_FILE), "utf-8"));
  assert.deepEqual(doc.acquire_failure, { error_type: "precheck_failed", message: "x" });
  assert.equal(doc.release_failed, true);
});

test("进程级兜底只在 acquire 开始后注册，触发时请求进入终结，释放后摘除", async () => {
  const h = harness();
  assert.equal(h.processListeners.size, 0);
  await ready(h);
  assert.deepEqual([...h.processListeners.keys()].sort(), ["uncaughtException", "unhandledRejection"]);
  h.processListeners.get("unhandledRejection")!(new Error(`newSession 超时 ${ENDPOINT}`));
  assert.equal(h.finalizationRequests, 1);
  await h.surface.release("interrupt");
  assert.equal(h.processListeners.size, 0);
});

test("释放后内建导航的私有通道被撤销，下一个接缝可以重新注入", async () => {
  const first = harness();
  await ready(first);
  await first.surface.release("normal");
  const second = harness();
  await ready(second);  // 注入未撤销时这里会抛出
  await second.surface.release("normal");
});

// ---- 构造期 ----

test("构造期：重规划上限缺省 12，env 覆盖为正整数，非法值即抛出并点名该键", () => {
  const base = { generateReport: true, persistExecutionDump: true } as never;
  assert.equal(deviceAgentOpts(base, {}).replanningCycleLimit, DEVICE_REPLANNING_CYCLE_LIMIT);
  assert.equal(deviceAgentOpts(base, { [REPLANNING_LIMIT_ENV]: "20" }).replanningCycleLimit, 20);
  // 与 worker 启动期的校验同一读法（limits 的 replanningCycleLimit）：前导零与首尾空白按 SDK 的读法忽略，启动时放行的值这里不另拒
  assert.equal(deviceAgentOpts(base, { [REPLANNING_LIMIT_ENV]: " 012 " }).replanningCycleLimit, 12);
  for (const bad of ["0", "-1", "1.5", "abc", "", "1e3"]) {
    assert.throws(() => deviceAgentOpts(base, { [REPLANNING_LIMIT_ENV]: bad }), new RegExp(REPLANNING_LIMIT_ENV), bad);
  }
  assert.throws(() => harness({ env: { [REPLANNING_LIMIT_ENV]: "x" } }), new RegExp(REPLANNING_LIMIT_ENV));
});

test("构造期：不注入部件时用缺省装配，只组装、不发事件；缺本次运行编号时同步抛出并点名该键；桌面目标不能构造设备接缝", () => {
  const emitted: Record<string, unknown>[] = [];
  const logs: string[] = [];
  const deps = {
    job: makeJob({ device: "android", uiKind: "web" }, 600), emit: async (e) => { emitted.push(e); }, log: (l) => { logs.push(l); },
    agentOpts: {} as never, uploader: {} as never, artifactRoot: undefined, requestFinalization: () => {},
  } satisfies SurfaceDeps;
  const surface = createDeviceSurface(deps, { env: { [RUN_ID_ENV]: "run-1" } });
  assert.equal(surface.sessionId(), null);
  assert.deepEqual([emitted, logs], [[], []]);
  // 本次运行编号只从构造项的 env 读：进程 env 里有值也不顶替
  const saved = process.env[RUN_ID_ENV];
  process.env[RUN_ID_ENV] = "run-from-process";
  try {
    assert.throws(() => createDeviceSurface(deps, { env: {} }), new RegExp(RUN_ID_ENV));
  } finally {
    if (saved === undefined) delete process.env[RUN_ID_ENV]; else process.env[RUN_ID_ENV] = saved;
  }
  const desktop = { ...deps, job: { ...deps.job, target: { device: "desktop", uiKind: "web" }, deviceRequest: null } };
  assert.throws(() => createDeviceSurface(desktop, { env: { [RUN_ID_ENV]: "run-1" } }));
});

// ---- 会话事件的线上形状（与 core 的协议解码逐条对照） ----

test("session_opened：三种来源的形状；attempted 只带会话名，空名与 attempted 带 sessionId 都拒绝", () => {
  const device = { platform: "ios" as const, model: "iPhone 15", osVersion: "18.6", unit: null };
  assert.deepEqual(sessionOpenedEvent("s", { sessionId: ARN1, name: "n", origin: "created", device }),
    { type: "session_opened", scopeId: "s", sessionId: ARN1, name: "n", origin: "created", device });
  assert.deepEqual(sessionOpenedEvent("s", { sessionId: ARN1, name: "n", origin: "discovered" }),
    { type: "session_opened", scopeId: "s", sessionId: ARN1, name: "n", origin: "discovered" });
  assert.deepEqual(sessionOpenedEvent("s", { sessionId: null, name: "n", origin: "attempted" }),
    { type: "session_opened", scopeId: "s", sessionId: null, name: "n", origin: "attempted" });
  assert.throws(() => sessionOpenedEvent("s", { sessionId: null, name: "", origin: "attempted" }));
  assert.throws(() => sessionOpenedEvent("s", { sessionId: ARN1, name: "n", origin: "attempted" }));
});

test("session_closed：observedS 为数值或 null（null 不改成 0），providerMinutes 可缺；同一会话只发一条", async () => {
  assert.deepEqual(sessionClosedEvent("s", { sessionId: ARN1, name: "n", release: "confirmed", observedS: null }),
    { type: "session_closed", scopeId: "s", sessionId: ARN1, name: "n", release: "confirmed", observedS: null });
  assert.deepEqual(
    sessionClosedEvent("s", { sessionId: null, name: "n", release: "unconfirmed", observedS: 3.5, providerMinutes: { total: 2, metered: 2, unmetered: 0 } }),
    { type: "session_closed", scopeId: "s", sessionId: null, name: "n", release: "unconfirmed", observedS: 3.5, providerMinutes: { total: 2, metered: 2, unmetered: 0 } });
  assert.throws(() => sessionClosedEvent("s", { sessionId: ARN1, name: "n", release: "confirmed", observedS: Number.NaN }));
  const out: Record<string, unknown>[] = [];
  const sink = sessionEventSink("s", async (e) => { out.push(e); });
  await sink.closed({ sessionId: ARN1, name: "n", release: "unconfirmed", observedS: null });
  await sink.closed({ sessionId: ARN1, name: "n", release: "confirmed", observedS: 1 });
  await sink.closed({ sessionId: null, name: "attempt", release: "unconfirmed", observedS: null });
  await sink.closed({ sessionId: null, name: "attempt", release: "unconfirmed", observedS: null });
  assert.deepEqual(out.map((e) => [e.sessionId, e.release]), [[ARN1, "unconfirmed"], [null, "unconfirmed"]]);
});

// ---- 缺省装配（device/parts.mts）----

function partsEnv(processEnv: NodeJS.ProcessEnv): DevicePartsEnv {
  return {
    job: makeJob({ device: "android", uiKind: "app" }, 600), log: () => {}, now: Date.now, processEnv,
    events: sessionEventSink(SCOPE_ID, async () => {}),
  };
}

test("缺省装配：适配器按会话回报的 automationName 选出两种驱动（不分大小写、每次一个新实例），没有对应的为 null", () => {
  const parts = defaultDeviceParts(partsEnv({ [RUN_ID_ENV]: "run-1" }));
  const android = parts.adapters.select("UiAutomator2");
  assert.equal(android?.automationName, "UiAutomator2");
  assert.equal(android?.device, "android");
  assert.equal(parts.adapters.select("xcuitest")?.device, "ios");
  assert.equal(parts.adapters.select("Espresso"), null);
  // 适配器里按会话缓存的结论（如设备不支持打开地址）只属于一个会话
  assert.notEqual(parts.adapters.select("XCUITest"), parts.adapters.select("XCUITest"));
});

test("缺省装配：守卫与 Agent 工厂是命令守卫与设备 Agent 的构造处；缺本次运行编号时构造即抛出", () => {
  const parts = defaultDeviceParts(partsEnv({ [RUN_ID_ENV]: "run-1" }));
  assert.equal(parts.guards, commandGuardFactory);
  assert.equal(parts.agents, deviceAgentFactory);
  assert.throws(() => defaultDeviceParts(partsEnv({})), new RegExp(RUN_ID_ENV));
});

// 镜像里的设备依赖冒烟（engines/midscene/Dockerfile）只 import dist/device/surface.mjs、不调用任何导出：它能拦住依赖没装进镜像，
// 前提是接缝模块的静态 import 闭包带到这两个包（ADR 0052 决策 3、7）。缺省装配一旦改成动态加载，冒烟就会在缺依赖时照样通过。
test("接缝模块的静态加载闭包带到 WebdriverIO 与 Device Farm SDK（镜像冒烟只 import 这个模块）", () => {
  const visited = new Set<string>();
  const packages = new Set<string>();
  const walk = (file: string): void => {
    if (visited.has(file)) return;
    visited.add(file);
    const sf = ts.createSourceFile(file, fs.readFileSync(file, "utf-8"), ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
    for (const stmt of sf.statements) {
      if (!ts.isImportDeclaration(stmt) || !ts.isStringLiteral(stmt.moduleSpecifier)) continue;
      const clause = stmt.importClause;
      // 类型导入在编译期擦除，不算加载
      if (clause?.isTypeOnly) continue;
      const bindings = clause?.namedBindings;
      if (clause && !clause.name && bindings && ts.isNamedImports(bindings) && bindings.elements.length > 0
        && bindings.elements.every((e) => e.isTypeOnly)) continue;
      const spec = stmt.moduleSpecifier.text;
      if (spec.startsWith(".")) walk(path.resolve(path.dirname(file), spec.replace(/\.mjs$/, ".mts")));
      else packages.add(spec);
    }
  };
  walk(path.join(import.meta.dirname, "surface.mts"));
  assert.ok(visited.has(path.join(import.meta.dirname, "parts.mts")), "接缝模块应静态 import 缺省装配");
  for (const pkg of ["webdriverio", "@aws-sdk/client-device-farm"]) {
    assert.ok(packages.has(pkg), `静态闭包里应有 ${pkg}，实际 ${[...packages].sort().join(", ")}`);
  }
});
