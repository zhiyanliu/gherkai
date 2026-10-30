// 终结块的单测（ADR 0051 决策 3、4、5、7）。运行：npx tsx --test src/device/finalize.test.mts。
//
// Device Farm 换成假的 API（不连 AWS），时钟与计时器换成虚拟时钟，会话经会话块的公开调用（create、retire）登记，不手工改登记：
// 两种释放模式的次序（正常路径的 deleteSession 先于终结核对与释放、中断路径不调它）、终结四阶段各自的截止线（含 API 不响应中止
// 时的阶段兜底）、Stop 规则（先 Get；不是 STOPPING / COMPLETED 一律发一次 Stop；Stop 报错补查 Get；确认只认这两个状态）、
// 每个会话恰一条 session_closed、待核尝试只发一对 attempted、observedS 的起止点与缺失记 null、只进入一次。
// 进入终结时撤销执行令牌与中止当前 act 由设备侧接缝负责（device/surface.test.mts 覆盖），这里不重复。
import { test } from "node:test";
import assert from "node:assert";
import type { RemoteAccessSession } from "@aws-sdk/client-device-farm";
import { createDeviceFarmSessions, type DeviceFarmApi, type Timers } from "./session.mjs";
import { createDeviceFinalizer } from "./finalize.mjs";
import { encode } from "./session-name.mjs";
import { sessionEventSink } from "./device-session.mjs";
import {
  DELETE_SESSION_TIMEOUT_MS, FINALIZE_AWAIT_CREATE_MS, FINALIZE_GET_TIMEOUT_MS, FINALIZE_RECONCILE_MS, FINALIZE_RELEASE_MS,
  STOP_CALL_TIMEOUT_MS,
} from "./limits.mjs";
import type { AcquireBudget, DevicePartsEnv, FinalizeHooks } from "./surface.mjs";
import type { Job } from "../lib/job-source.mjs";

// ---- 虚拟时钟（与 session.test.mts 相同的写法）----

async function settle(): Promise<void> {
  for (let i = 0; i < 20; i++) await new Promise((r) => setImmediate(r));
}

function timeoutReason(): Error {
  return new DOMException("The operation was aborted due to timeout", "TimeoutError");
}

class FakeClock {
  t = 1_000_000;
  private queue: { at: number; seq: number; fire: () => void; dead: boolean }[] = [];
  private seq = 0;
  readonly now = (): number => this.t;

  private schedule(ms: number, fire: () => void) {
    const entry = { at: this.t + Math.max(0, ms), seq: this.seq++, fire, dead: false };
    this.queue.push(entry);
    return entry;
  }

  readonly timers: Timers = {
    sleep: (ms, signal) => new Promise<void>((resolve, reject) => {
      if (signal?.aborted) { reject(signal.reason); return; }
      const onAbort = (): void => { entry.dead = true; reject(signal!.reason); };
      const entry = this.schedule(ms, () => { signal?.removeEventListener("abort", onAbort); resolve(); });
      signal?.addEventListener("abort", onAbort, { once: true });
    }),
    timeout: (ms) => {
      const c = new AbortController();
      this.schedule(ms, () => c.abort(timeoutReason()));
      return c.signal;
    },
  };

  private fireNext(limit: number): boolean {
    const live = this.queue.filter((e) => !e.dead && e.at <= limit).sort((a, b) => a.at - b.at || a.seq - b.seq);
    const next = live[0];
    if (!next) return false;
    next.dead = true;
    this.t = Math.max(this.t, next.at);
    next.fire();
    return true;
  }

  async run<T>(p: Promise<T>, limitMs = 3_600_000): Promise<T> {
    let done = false;
    p.then(() => { done = true; }, () => { done = true; });
    const end = this.t + limitMs;
    for (;;) {
      await settle();
      if (done) return p;
      if (!this.fireNext(end)) break;
    }
    await settle();
    if (done) return p;
    throw new Error(`虚拟时间推进到 ${this.t} 仍未落定`);
  }

  /** 推进 ms 的虚拟时间。 */
  advance(ms: number): Promise<void> {
    return this.run(this.timers.sleep(ms));
  }
}

// ---- 假的 Device Farm ----

interface Call { op: string; at: number; arg: unknown }

function sdkError(name: string, status: number, message = name): Error {
  return Object.assign(new Error(message), { name, $metadata: { httpStatusCode: status } });
}

function connectionReset(): Error {
  return Object.assign(new Error("socket hang up"), { name: "Error", code: "ECONNRESET" });
}

function hang<T>(signal: AbortSignal): Promise<T> {
  return new Promise<T>((_resolve, reject) => {
    if (signal.aborted) { reject(signal.reason); return; }
    signal.addEventListener("abort", () => reject(signal.reason), { once: true });
  });
}

/** 不响应中止、永不落定（模拟忽略中止信号的调用，用来核对阶段兜底的截止线）。 */
function never<T>(): Promise<T> {
  return new Promise<T>(() => {});
}

type Handler<A, R> = (arg: A, signal: AbortSignal) => Promise<R>;

class FakeFarm {
  calls: Call[] = [];
  createImpl: Handler<{ name: string }, RemoteAccessSession | undefined>;
  getImpl: Handler<string, RemoteAccessSession | undefined> = async () => ({ status: "RUNNING" });
  stopImpl: Handler<string, RemoteAccessSession | undefined> = async (arn) => ({ arn, status: "STOPPING" });
  listSessionsImpl: Handler<string | undefined, { remoteAccessSessions?: RemoteAccessSession[]; nextToken?: string }> =
    async () => ({ remoteAccessSessions: [] });
  private createSeq = 0;

  constructor(private readonly clock: FakeClock) {
    this.createImpl = async (input) => {
      this.createSeq += 1;
      return { arn: `arn:session:${this.createSeq}`, name: input.name, status: "PENDING" };
    };
  }

  ops(op: string): Call[] {
    return this.calls.filter((c) => c.op === op);
  }

  readonly api: DeviceFarmApi = {
    listDevices: async () => ({ devices: [] }),
    createRemoteAccessSession: (input, signal) => { this.calls.push({ op: "create", at: this.clock.t, arg: input.name }); return this.createImpl(input, signal); },
    getRemoteAccessSession: (arn, signal) => { this.calls.push({ op: "get", at: this.clock.t, arg: arn }); return this.getImpl(arn, signal); },
    stopRemoteAccessSession: (arn, signal) => { this.calls.push({ op: "stop", at: this.clock.t, arg: arn }); return this.stopImpl(arn, signal); },
    listRemoteAccessSessions: (_project, nextToken, signal) => {
      this.calls.push({ op: "listSessions", at: this.clock.t, arg: nextToken });
      return this.listSessionsImpl(nextToken, signal);
    },
  };
}

// ---- 环境 ----

const RUN_ID = "20261030T120000Z-a1b2c3";
const SCOPE_ID = "features/shop.feature::Checkout";
const DEVICE_ARN = "arn:aws:devicefarm:us-west-2::device:FIXED";
const CHOICE = { deviceArn: DEVICE_ARN, model: "Pixel 8", osVersion: "14" };

function makeJob(): Omit<Job, "scenarios"> {
  return {
    schemaVersion: 1,
    scope: { id: SCOPE_ID, name: "Checkout" },
    engine: "midscene",
    assertionVotes: 1,
    timeoutS: 1500,
    target: { device: "android", uiKind: "web" },
    deviceRequest: {
      provider: "aws-device-farm", deviceArn: DEVICE_ARN, billingMethod: "METERED",
      projectArn: "arn:aws:devicefarm:us-west-2:123456789012:project:p", acquireTimeoutS: 600,
    },
  };
}

type Emitted = Record<string, unknown> & { at: number };

function setup() {
  const clock = new FakeClock();
  const farm = new FakeFarm(clock);
  const emitted: Emitted[] = [];
  const logs: string[] = [];
  let onEmit: ((e: Emitted) => void) | null = null;
  const env: DevicePartsEnv = {
    job: makeJob(),
    log: (line) => logs.push(line),
    events: sessionEventSink(SCOPE_ID, async (e) => { const rec = { ...e, at: clock.t }; emitted.push(rec); onEmit?.(rec); }),
    processEnv: {},
    now: clock.now,
  };
  const sessions = createDeviceFarmSessions(env, { api: farm.api, timers: clock.timers, runId: RUN_ID });
  const finalizer = createDeviceFinalizer(sessions);
  const budget = (): AcquireBudget & { abort(): void } => {
    const c = new AbortController();
    return { signal: c.signal, remainingMs: () => 600_000, abort: () => c.abort(new Error("finalizing")) };
  };
  return {
    clock, farm, emitted, logs, sessions, finalizer, budget,
    watch(fn: (e: Emitted) => void) { onEmit = fn; },
    /** 经会话块建一个会话（Create 成功），返回它的 ARN 与会话名。 */
    async open(): Promise<{ arn: string; name: string }> {
      const got = await clock.run(sessions.create(CHOICE, budget()));
      assert.ok(got.ok);
      return { arn: got.value.arn, name: got.value.name };
    },
    /** 制造一个待核尝试：Create 连接中断，随后在重试等待中预算中止。返回这次尝试的会话名。 */
    async pendingAttempt(): Promise<string> {
      const saved = farm.createImpl;
      farm.createImpl = async () => { throw connectionReset(); };
      const b = budget();
      const p = sessions.create(CHOICE, b);
      await settle();
      b.abort();
      await assert.rejects(clock.run(p));
      farm.createImpl = saved;
      const name = farm.ops("create").at(-1)!.arg as string;
      assert.ok(sessions.registry.pending.has(name));
      return name;
    },
  };
}

const NO_HOOKS: FinalizeHooks = { deleteAppiumSession: null };

function closedOf(h: { emitted: Emitted[] }) {
  return h.emitted.filter((e) => e.type === "session_closed");
}

// ---- 两条路径的次序 ----

test("正常路径：destroy、上传之后，deleteSession 先于终结核对与释放，session_closed 发完才返回，调用方随后发 scope_done、排空", async () => {
  const h = setup();
  const pendingName = await h.pendingAttempt();
  const s = await h.open();
  const order: string[] = [];
  h.farm.getImpl = async (arn) => { order.push(`get:${arn}`); return { status: "RUNNING" }; };
  h.farm.stopImpl = async (arn) => { order.push(`stop:${arn}`); return { arn, status: "STOPPING" }; };
  h.farm.listSessionsImpl = async () => { order.push("listSessions"); return { remoteAccessSessions: [] }; };
  h.watch((e) => order.push(`${e.type}:${String(e.origin ?? e.release)}`));
  order.push("destroy", "upload");                                   // 调用方：Midscene 侧收尾与有界上传
  const out = await h.clock.run(h.finalizer.finalize("normal", { deleteAppiumSession: async () => { order.push("deleteSession"); } }));
  order.push("scope_done", "drain");                                  // 调用方：释放之后才发 scope_done、再排空
  assert.deepEqual(order, [
    "destroy", "upload",
    `get:${s.arn}`, "deleteSession",
    "listSessions", "session_opened:attempted", "session_closed:unconfirmed",
    `get:${s.arn}`, `stop:${s.arn}`, "session_closed:confirmed",
    "scope_done", "drain",
  ]);
  assert.equal(out.releaseFailed, true);                              // 有一个 attempted 的尝试
  assert.ok(h.emitted.some((e) => e.name === pendingName && e.origin === "attempted"));
});

test("正常路径：远程访问会话已是 STOPPING / COMPLETED 时不调 deleteSession、不发 Stop，直接确认", async () => {
  for (const status of ["STOPPING", "COMPLETED"]) {
    const h = setup();
    await h.open();
    h.farm.getImpl = async () => ({ status });
    let deleted = 0;
    const out = await h.clock.run(h.finalizer.finalize("normal", { deleteAppiumSession: async () => { deleted++; } }));
    assert.equal(deleted, 0, status);
    assert.equal(h.farm.ops("stop").length, 0, status);
    assert.equal(h.farm.ops("get").length, 1, status);
    assert.equal(out.releaseFailed, false);
    assert.equal(closedOf(h)[0].release, "confirmed");
  }
});

test("正常路径：查状态失败时照常 deleteSession（状态未知不跳过），之后照常释放", async () => {
  const h = setup();
  await h.open();
  let gets = 0;
  h.farm.getImpl = async () => { gets++; if (gets === 1) throw sdkError("InternalServiceException", 500); return { status: "RUNNING" }; };
  let deleted = 0;
  const out = await h.clock.run(h.finalizer.finalize("normal", { deleteAppiumSession: async () => { deleted++; } }));
  assert.equal(deleted, 1);
  assert.equal(h.farm.ops("stop").length, 1);
  assert.equal(out.releaseFailed, false);
});

test("正常路径：deleteSession 不返回时至多等 5 秒，不阻塞 Stop", async () => {
  const h = setup();
  await h.open();
  const t0 = h.clock.t;
  const out = await h.clock.run(h.finalizer.finalize("normal", { deleteAppiumSession: () => never() }));
  assert.equal(out.releaseFailed, false);
  assert.equal(h.farm.ops("stop")[0].at - t0, DELETE_SESSION_TIMEOUT_MS);
});

test("正常路径：查状态不响应中止时至多等 5 秒，照常 deleteSession 并释放", async () => {
  const h = setup();
  await h.open();
  let gets = 0;
  h.farm.getImpl = async () => { gets++; return gets === 1 ? never() : { status: "RUNNING" }; };
  const deletedAt: number[] = [];
  const t0 = h.clock.t;
  const out = await h.clock.run(h.finalizer.finalize("normal", { deleteAppiumSession: async () => { deletedAt.push(h.clock.t); } }));
  assert.deepEqual(deletedAt, [t0 + FINALIZE_GET_TIMEOUT_MS]);
  assert.equal(h.farm.ops("stop").length, 1);
  assert.equal(closedOf(h)[0].release, "confirmed");
  assert.equal(out.releaseFailed, false);
});

test("中断路径：不调 deleteSession（即使给了钩子），也不为它查状态", async () => {
  const h = setup();
  await h.open();
  let deleted = 0;
  const out = await h.clock.run(h.finalizer.finalize("interrupt", { deleteAppiumSession: async () => { deleted++; } }));
  assert.equal(deleted, 0);
  assert.equal(h.farm.ops("get").length, 1);                          // 只有释放阶段的那一次
  assert.equal(out.releaseFailed, false);
});

// ---- Stop 规则（ADR 0051 决策 5）----

test("Stop 规则：先 Get；排队、准备与 RUNNING 等一切不是 STOPPING / COMPLETED 的状态都发一次 Stop，这两个状态不发", async () => {
  const cases: Array<[string, number]> = [
    ["PENDING", 1], ["PENDING_CONCURRENCY", 1], ["PENDING_DEVICE", 1], ["PROCESSING", 1], ["SCHEDULING", 1],
    ["PREPARING", 1], ["RUNNING", 1], ["STOPPING", 0], ["COMPLETED", 0],
  ];
  for (const [status, stops] of cases) {
    const h = setup();
    await h.open();
    h.farm.getImpl = async () => ({ status });
    const out = await h.clock.run(h.finalizer.finalize("interrupt", NO_HOOKS));
    assert.equal(h.farm.ops("stop").length, stops, status);
    assert.ok(h.farm.ops("get")[0].at <= (h.farm.ops("stop")[0]?.at ?? Infinity), status);
    assert.equal(out.releaseFailed, false, status);
    assert.equal(closedOf(h)[0].release, "confirmed", status);
  }
});

test("Stop 规则：Get 失败时照常发 Stop，Stop 返回体为 STOPPING 即确认", async () => {
  const h = setup();
  await h.open();
  h.farm.getImpl = async () => { throw sdkError("InternalServiceException", 500); };
  const out = await h.clock.run(h.finalizer.finalize("interrupt", NO_HOOKS));
  assert.equal(h.farm.ops("stop").length, 1);
  assert.equal(out.releaseFailed, false);
});

test("Stop 规则：Stop 报错补查一次 Get，读到 COMPLETED 即确认，不再发 Stop", async () => {
  const h = setup();
  await h.open();
  const statuses = ["RUNNING", "COMPLETED"];
  h.farm.getImpl = async () => ({ status: statuses.shift() });
  h.farm.stopImpl = async () => { throw sdkError("ArgumentException", 400, "Invalid parameter RemoteAccessSession"); };
  const out = await h.clock.run(h.finalizer.finalize("interrupt", NO_HOOKS));
  assert.equal(h.farm.ops("stop").length, 1);
  assert.equal(h.farm.ops("get").length, 2);
  assert.equal(out.releaseFailed, false);
  assert.equal(closedOf(h)[0].release, "confirmed");
});

test("Stop 规则：Stop 报错且补查仍未停止时退避后再 Stop 一次、再补查，至多两次 Stop；仍未确认记 unconfirmed", async () => {
  const h = setup();
  const s = await h.open();
  h.farm.getImpl = async () => ({ status: "RUNNING" });
  h.farm.stopImpl = async () => { throw sdkError("InternalServiceException", 500); };
  const out = await h.clock.run(h.finalizer.finalize("interrupt", NO_HOOKS));
  assert.equal(h.farm.ops("stop").length, 2);
  assert.equal(h.farm.ops("get").length, 3);
  assert.equal(out.releaseFailed, true);
  const closed = closedOf(h);
  assert.equal(closed.length, 1);
  assert.equal(closed[0].sessionId, s.arn);
  assert.equal(closed[0].release, "unconfirmed");
  assert.ok(h.logs.some((l) => l.includes(s.name)));
});

test("Stop 规则：确认只认 STOPPING / COMPLETED——Stop 成功但返回体与补查都是 RUNNING，不算确认", async () => {
  const h = setup();
  await h.open();
  h.farm.getImpl = async () => ({ status: "RUNNING" });
  h.farm.stopImpl = async (arn) => ({ arn, status: "RUNNING" });
  const out = await h.clock.run(h.finalizer.finalize("interrupt", NO_HOOKS));
  assert.equal(out.releaseFailed, true);
  assert.equal(closedOf(h)[0].release, "unconfirmed");
});

// ---- 终结四阶段的截止线（相对进入终结的时刻）----

test("截止线：各调用按单次超时中止——释放阶段 Get 5 秒、Stop 3 秒、补查 5 秒、退避、再 Stop、再补查，全部落在 25 秒之内", async () => {
  const h = setup();
  await h.open();
  h.farm.getImpl = (_arn, signal) => hang(signal);
  h.farm.stopImpl = (_arn, signal) => hang(signal);
  const t0 = h.clock.t;
  const out = await h.clock.run(h.finalizer.finalize("interrupt", NO_HOOKS));
  const rel = (op: string) => h.farm.ops(op).map((c) => c.at - t0);
  assert.deepEqual(rel("get"), [0, FINALIZE_GET_TIMEOUT_MS + STOP_CALL_TIMEOUT_MS, 15_000 + STOP_CALL_TIMEOUT_MS]);
  assert.deepEqual(rel("stop"), [FINALIZE_GET_TIMEOUT_MS, 15_000]);
  assert.ok(h.clock.t - t0 <= FINALIZE_RELEASE_MS);
  assert.equal(out.releaseFailed, true);
  // 没有发出 Stop 之前的那一段不计；observedS 的止点是第一次发出 Stop 的时刻
  assert.equal(typeof closedOf(h)[0].observedS, "number");
});

test("截止线：调用不响应中止时由阶段兜底——等在途 Create 10 秒、终结核对 5 秒、释放 25 秒，依次接续", async () => {
  const h = setup();
  const s = await h.open();
  h.farm.createImpl = () => never();                                  // 在途、永不返回的 Create
  void h.sessions.create(CHOICE, h.budget());
  await settle();
  const inflightName = h.farm.ops("create").at(-1)!.arg as string;
  h.farm.listSessionsImpl = () => never();
  h.farm.getImpl = () => never();
  const t0 = h.clock.t;
  const out = await h.clock.run(h.finalizer.finalize("interrupt", NO_HOOKS));
  const t1 = t0 + FINALIZE_AWAIT_CREATE_MS;
  const t2 = t1 + FINALIZE_RECONCILE_MS;
  const t3 = t2 + FINALIZE_RELEASE_MS;
  assert.equal(h.farm.ops("listSessions")[0].at, t1);                // 阶段 1 到线，在途的 Create 记为结果未知
  const attempted = h.emitted.filter((e) => e.name === inflightName);
  assert.deepEqual(attempted.map((e) => [e.type, e.at]), [["session_opened", t2], ["session_closed", t2]]);
  assert.equal(h.farm.ops("get")[0].at, t2);
  const closed = closedOf(h).find((e) => e.sessionId === s.arn)!;
  assert.equal(closed.at, t3);
  assert.equal(closed.release, "unconfirmed");
  assert.equal(closed.observedS, null);                               // 没发出 Stop、也没确认：缺失记 null，不记 0
  assert.equal(h.clock.t, t3);
  assert.equal(out.releaseFailed, true);
});

test("截止线：释放阶段全部会话并行、共享一条截止线（两个都不响应也只等 25 秒）", async () => {
  const h = setup();
  await h.open();
  await h.open();
  h.farm.getImpl = () => never();
  const t0 = h.clock.t;
  await h.clock.run(h.finalizer.finalize("interrupt", NO_HOOKS));
  assert.equal(h.clock.t - t0, FINALIZE_RELEASE_MS);
  assert.deepEqual(h.farm.ops("get").map((c) => c.at - t0), [0, 0]);
  assert.deepEqual(closedOf(h).map((e) => e.release), ["unconfirmed", "unconfirmed"]);
});

test("阶段 1：在途的 Create 在等待窗口内返回即登记 ARN、发 session_opened(created)，与其他会话一样释放并确认，不发 attempted", async () => {
  const h = setup();
  h.farm.createImpl = (input) => h.clock.timers.sleep(4_000).then(() => ({ arn: "arn:late", name: input.name, status: "PENDING" }));
  const creating = h.sessions.create(CHOICE, h.budget());
  await h.clock.advance(1_000);
  const t0 = h.clock.t;
  const out = await h.clock.run(h.finalizer.finalize("interrupt", NO_HOOKS));
  const got = await creating;
  assert.ok(got.ok);
  assert.deepEqual(h.emitted.map((e) => [e.type, e.sessionId, e.origin ?? e.release]), [
    ["session_opened", "arn:late", "created"], ["session_closed", "arn:late", "confirmed"],
  ]);
  assert.equal(h.farm.ops("get")[0].at - t0, 3_000);
  assert.equal(out.releaseFailed, false);
  assert.equal(h.farm.ops("create").length, 1);
});

test("阶段 1 到线后的 Create 在终结核对结束之后才带 ARN 返回：只记日志，不登记、不发 session_opened，仍按一对 attempted 上报", async () => {
  const h = setup();
  const s = await h.open();
  let resolveLate: (v: RemoteAccessSession) => void = () => {};
  h.farm.createImpl = (input) => new Promise<RemoteAccessSession>((resolve) => {   // 不响应中止，由测试决定何时返回
    resolveLate = (v) => resolve({ ...v, name: input.name });
  });
  const b = h.budget();
  const creating = h.sessions.create(CHOICE, b).then(() => null, (e: unknown) => e);
  await settle();
  const lateName = h.farm.ops("create").at(-1)!.arg as string;
  h.farm.getImpl = async () => {                                      // 释放阶段（阶段 3）期间才返回
    resolveLate({ arn: "arn:late", status: "PENDING" });
    await settle();
    return { status: "RUNNING" };
  };
  const finalizing = h.finalizer.finalize("interrupt", NO_HOOKS);
  b.abort();
  const out = await h.clock.run(finalizing);
  assert.ok((await h.clock.run(creating)) instanceof Error);
  await settle();
  assert.equal(h.emitted.filter((e) => e.type === "session_opened" && e.sessionId === "arn:late").length, 0);
  assert.equal(h.sessions.registry.sessions.has("arn:late"), false);
  assert.deepEqual(h.emitted.filter((e) => e.name === lateName).map((e) => [e.type, e.origin ?? e.release]), [
    ["session_opened", "attempted"], ["session_closed", "unconfirmed"],
  ]);
  assert.deepEqual(closedOf(h).filter((e) => e.sessionId !== null).map((e) => e.sessionId), [s.arn]);
  assert.ok(h.logs.some((l) => l.includes(lateName) && l.includes("arn:late")));
  assert.equal(out.releaseFailed, true);
});

test("进入终结之后不再发新的 Create：重试等待中的获取随之停下，失败的那次尝试按待核处理", async () => {
  const h = setup();
  h.farm.createImpl = async () => { throw connectionReset(); };
  const b = h.budget();
  const creating = h.sessions.create(CHOICE, b).then(() => null, (e: unknown) => e);
  await settle();
  const finalizing = h.finalizer.finalize("interrupt", NO_HOOKS);
  b.abort();                                                          // 接缝进入终结时中止获取预算
  const out = await h.clock.run(finalizing);
  assert.ok((await h.clock.run(creating)) instanceof Error);
  await h.clock.advance(60_000);
  assert.equal(h.farm.ops("create").length, 1);
  assert.equal(out.releaseFailed, true);
  assert.deepEqual(h.emitted.map((e) => [e.type, e.origin ?? e.release]), [["session_opened", "attempted"], ["session_closed", "unconfirmed"]]);
});

// ---- 待核尝试 ----

test("终结核对：按名列举（含分页）命中待核尝试即发 session_opened(discovered)，随后释放并确认；observedS 从发现时刻起算", async () => {
  const h = setup();
  const name = await h.pendingAttempt();
  await h.clock.advance(30_000);                                      // 发出 Create 到发现之间的时间不计入 observedS
  h.farm.listSessionsImpl = async (token) => token === undefined
    ? { remoteAccessSessions: [{ arn: "arn:other", name: encode(RUN_ID, SCOPE_ID, 99) }], nextToken: "p2" }
    : { remoteAccessSessions: [{ arn: "arn:orphan", name, status: "PENDING_CONCURRENCY" }] };
  h.farm.getImpl = async () => ({ status: "PENDING_CONCURRENCY" });
  h.farm.stopImpl = (arn) => h.clock.timers.sleep(600).then(() => ({ arn, status: "STOPPING" }));
  const t0 = h.clock.t;
  const out = await h.clock.run(h.finalizer.finalize("interrupt", NO_HOOKS));
  assert.deepEqual(h.farm.ops("listSessions").map((c) => c.arg), [undefined, "p2"]);
  assert.deepEqual(h.emitted.map((e) => [e.type, e.sessionId, e.origin ?? e.release]), [
    ["session_opened", "arn:orphan", "discovered"], ["session_closed", "arn:orphan", "confirmed"],
  ]);
  assert.equal(h.farm.ops("stop")[0].arg, "arn:orphan");             // 排队中的会话也发 Stop
  assert.equal(closedOf(h)[0].observedS, (h.farm.ops("stop")[0].at - t0) / 1000);
  assert.equal(closedOf(h)[0].observedS, 0);
  assert.equal(out.releaseFailed, false);
});

test("终结核对：列举扫完也没命中，待核不被排除——发一对 attempted（sessionId 为 null，只带会话名），以未确认结束", async () => {
  const h = setup();
  const name = await h.pendingAttempt();
  const out = await h.clock.run(h.finalizer.finalize("interrupt", NO_HOOKS));
  assert.equal(h.farm.ops("listSessions").length, 1);
  assert.deepEqual(h.emitted.map(({ at: _at, ...e }) => e), [
    { type: "session_opened", scopeId: SCOPE_ID, sessionId: null, name, origin: "attempted" },
    { type: "session_closed", scopeId: SCOPE_ID, sessionId: null, name, release: "unconfirmed", observedS: null },
  ]);
  assert.equal(out.releaseFailed, true);
  assert.ok(h.logs.some((l) => l.includes(name)));
});

test("终结核对：分页没扫完（下一页出错）视为未核对，待核照样发 attempted", async () => {
  const h = setup();
  await h.pendingAttempt();
  h.farm.listSessionsImpl = async (token) => {
    if (token === undefined) return { remoteAccessSessions: [], nextToken: "p2" };
    throw sdkError("InternalServiceException", 500);
  };
  const out = await h.clock.run(h.finalizer.finalize("interrupt", NO_HOOKS));
  assert.equal(h.farm.ops("listSessions").length, 2);
  assert.equal(h.emitted.filter((e) => e.origin === "attempted").length, 1);
  assert.equal(out.releaseFailed, true);
});

test("没有待核尝试时终结核对不调列举", async () => {
  const h = setup();
  await h.open();
  await h.clock.run(h.finalizer.finalize("interrupt", NO_HOOKS));
  assert.equal(h.farm.ops("listSessions").length, 0);
});

// ---- 每会话恰一条 session_closed、只进入一次 ----

test("去重：换台留下的会话与执行所用的会话各恰一条 session_closed；换台时 Stop 已确认的不再查状态", async () => {
  const h = setup();
  const first = await h.open();
  await h.clock.advance(10_000);
  await h.clock.run(h.sessions.retire(first.arn));                    // Stop 返回体 STOPPING：已确认
  const retiredAt = h.farm.ops("stop")[0].at;
  await h.clock.advance(30_000);
  const second = await h.open();
  const out = await h.clock.run(h.finalizer.finalize("normal", NO_HOOKS));
  assert.deepEqual(h.farm.ops("get").map((c) => c.arg), [second.arn]);
  const closed = closedOf(h);
  assert.deepEqual(closed.map((e) => [e.sessionId, e.release]), [[first.arn, "confirmed"], [second.arn, "confirmed"]]);
  const opened = h.emitted.filter((e) => e.type === "session_opened");
  assert.equal(closed[0].observedS, (retiredAt - (opened[0].at as number)) / 1000);
  assert.equal(closed[0].observedS, 10);
  assert.equal(out.releaseFailed, false);
});

test("只进入一次：信号重复到达、超时与信号交叠时返回同一个结果，Get / Stop 与事件都只有一份", async () => {
  const h = setup();
  await h.open();
  await h.pendingAttempt();
  const a = h.finalizer.finalize("interrupt", NO_HOOKS);
  const b = h.finalizer.finalize("interrupt", NO_HOOKS);
  const c = h.finalizer.finalize("normal", { deleteAppiumSession: async () => { throw new Error("不应调用"); } });
  assert.equal(a, b);
  assert.equal(a, c);
  await h.clock.run(a);
  assert.equal(h.farm.ops("get").length, 1);
  assert.equal(h.farm.ops("stop").length, 1);
  assert.equal(h.farm.ops("listSessions").length, 1);
  assert.equal(closedOf(h).length, 2);                                // 一个真实会话加一个 attempted 尝试
  assert.equal(h.emitted.filter((e) => e.origin === "attempted").length, 1);
  assert.deepEqual(await h.clock.run(h.finalizer.finalize("interrupt", NO_HOOKS)), await a);
});

// ---- 计量（ADR 0051 决策 7）----

test("observedS：起点为 Create 返回（不是发出 Create），止点为发出 Stop；providerMinutes 取返回体的 deviceMinutes 原形", async () => {
  const h = setup();
  h.farm.createImpl = (input) => h.clock.timers.sleep(4_000).then(() => ({ arn: "arn:s", name: input.name, status: "PENDING" }));
  await h.open();
  const returnedAt = h.clock.t;
  await h.clock.advance(60_000);
  h.farm.stopImpl = async (arn) => ({ arn, status: "STOPPING", deviceMinutes: { total: 2.16, metered: 2.16, unmetered: 0 } });
  await h.clock.run(h.finalizer.finalize("interrupt", NO_HOOKS));
  const closed = closedOf(h)[0];
  assert.equal(closed.observedS, (h.farm.ops("stop")[0].at - returnedAt) / 1000);
  assert.equal(closed.observedS, 60);
  assert.deepEqual(closed.providerMinutes, { total: 2.16, metered: 2.16, unmetered: 0 });
});

test("observedS：已停止的会话（如被外部停止）不发 Stop，止点为确认停止的时刻", async () => {
  const h = setup();
  await h.open();
  const returnedAt = h.clock.t;
  await h.clock.advance(90_000);
  h.farm.getImpl = (_arn) => h.clock.timers.sleep(200).then(() => ({ status: "COMPLETED" }));
  await h.clock.run(h.finalizer.finalize("interrupt", NO_HOOKS));
  assert.equal(h.farm.ops("stop").length, 0);
  assert.equal(closedOf(h)[0].observedS, 90.2);
  assert.equal(closedOf(h)[0].at - returnedAt, 90_200);
});
