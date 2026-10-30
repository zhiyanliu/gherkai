// Device Farm 会话块的单测（ADR 0051 决策 2、3、4、7、10；ADR 0052 决策 3）。运行：npx tsx --test src/device/session.test.mts。
//
// Device Farm 换成假的 API（不连 AWS），时钟与计时器换成虚拟时钟：设备解析的版本族、静态过滤、排序与完整分页，零候选重列与
// 繁忙退避，Create 的尝试序号与会话名、限流重试、结果未知的待核与按名列举消除（扫到分页结束、同名的每个 ARN 都登记），获取期
// 按名找回的会话在 session_opened 写出后随即按 Stop 规则停止（逐会话，不等同页其余会话的事件写完；与剩余分页并行，下一次
// Create 等它处理完），等到 RUNNING（就绪之前已结束即按会话丢失终止），查状态，换台时按同一 Stop 规则处理被替换的会话。另有
// 一组用真的 DeviceFarmClient（网络层换成本地处理器）核对区域、单次尝试、每次调用都带中止信号，以及响应体没读完的失败归结果
// 未知。会话年龄的后备由接缝按 createRequestedAt 计算（device/surface.mts），这里只核对这个起点是发出 Create 的时刻。
import { test } from "node:test";
import assert from "node:assert";
import { PassThrough, Readable } from "node:stream";
import type { Device as FarmDevice, RemoteAccessSession } from "@aws-sdk/client-device-farm";
import {
  DEVICE_FARM_REGION, RUNNING_POLL_INTERVAL_MS, classifyCallFailure, compareVersions, createDeviceFarmSessions, deviceArnRejectedMessage,
  deviceFarmApi, matchesVersionFamily, type DeviceFarmApi, type Timers,
} from "./session.mjs";
import { encode, RUN_ID_ENV } from "./session-name.mjs";
import { sessionEventSink } from "./device-session.mjs";
import { DEVICE_FARM_CALL_TIMEOUT_MS, DEVICE_RELIST_DELAY_MS, STOP_CALL_TIMEOUT_MS, busyBackoffMs } from "./limits.mjs";
import { SESSION_LOST_BEFORE_START_MESSAGE, type AcquireBudget, type DevicePartsEnv } from "./surface.mjs";
import type { Job } from "../lib/job-source.mjs";

// ---- 虚拟时钟 ----

/** 让已就绪的微任务与 I/O 回调执行完。 */
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

  /** 触发最早到期的一个计时器；没有计时器时返回 false。 */
  private fireNext(limit: number): boolean {
    const live = this.queue.filter((e) => !e.dead && e.at <= limit).sort((a, b) => a.at - b.at || a.seq - b.seq);
    const next = live[0];
    if (!next) return false;
    next.dead = true;
    this.t = Math.max(this.t, next.at);
    next.fire();
    return true;
  }

  /** 推进虚拟时间直到 promise 落定（最多 limitMs），返回它的结果；落定不了即失败。 */
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
}

// ---- 假的 Device Farm ----

interface Call { op: string; at: number; arg: unknown; signal: AbortSignal }

function sdkError(name: string, status: number, message = name): Error {
  return Object.assign(new Error(message), { name, $metadata: { httpStatusCode: status } });
}

function connectionReset(): Error {
  return Object.assign(new Error("socket hang up"), { name: "Error", code: "ECONNRESET" });
}

/** 挂起直到信号中止（与真实 SDK 的中止行为一致）。 */
function hang<T>(signal: AbortSignal): Promise<T> {
  return new Promise<T>((_resolve, reject) => {
    if (signal.aborted) { reject(signal.reason); return; }
    signal.addEventListener("abort", () => reject(signal.reason), { once: true });
  });
}

type Handler<A, R> = (arg: A, signal: AbortSignal) => Promise<R>;

class FakeFarm {
  calls: Call[] = [];
  devicePages: FarmDevice[][] = [[]];
  listDevicesImpl: Handler<string | undefined, { devices?: FarmDevice[]; nextToken?: string }> | null = null;
  createImpl: Handler<{ projectArn: string; deviceArn: string; name: string; billingMethod: string }, RemoteAccessSession | undefined>;
  getImpl: Handler<string, RemoteAccessSession | undefined> = async (arn) => ({ arn, status: "RUNNING" });
  stopImpl: Handler<string, RemoteAccessSession | undefined> = async (arn) => ({ arn, status: "STOPPING" });
  sessionPages: RemoteAccessSession[][] = [[]];
  listSessionsImpl: Handler<{ projectArn: string; nextToken?: string }, { remoteAccessSessions?: RemoteAccessSession[]; nextToken?: string }> | null = null;
  private createSeq = 0;

  constructor(private readonly clock: FakeClock) {
    this.createImpl = async (input) => {
      this.createSeq += 1;
      return { arn: `arn:aws:devicefarm:us-west-2:123456789012:session:p/r/${String(this.createSeq).padStart(5, "0")}`, name: input.name, status: "PENDING" };
    };
  }

  private record(op: string, arg: unknown, signal: AbortSignal): void {
    this.calls.push({ op, at: this.clock.t, arg, signal });
  }

  ops(op?: string): Call[] {
    return op === undefined ? this.calls : this.calls.filter((c) => c.op === op);
  }

  readonly api: DeviceFarmApi = {
    listDevices: (nextToken, signal) => {
      this.record("listDevices", nextToken, signal);
      if (this.listDevicesImpl) return this.listDevicesImpl(nextToken, signal);
      const index = nextToken === undefined ? 0 : Number(nextToken.slice("page-".length));
      const next = index + 1 < this.devicePages.length ? `page-${index + 1}` : undefined;
      return Promise.resolve({ devices: this.devicePages[index] ?? [], nextToken: next });
    },
    createRemoteAccessSession: (input, signal) => { this.record("create", input, signal); return this.createImpl(input, signal); },
    getRemoteAccessSession: (arn, signal) => { this.record("get", arn, signal); return this.getImpl(arn, signal); },
    stopRemoteAccessSession: (arn, signal) => { this.record("stop", arn, signal); return this.stopImpl(arn, signal); },
    listRemoteAccessSessions: (projectArn, nextToken, signal) => {
      this.record("listSessions", { projectArn, nextToken }, signal);
      if (this.listSessionsImpl) return this.listSessionsImpl({ projectArn, nextToken }, signal);
      const index = nextToken === undefined ? 0 : Number(nextToken.slice("page-".length));
      const next = index + 1 < this.sessionPages.length ? `page-${index + 1}` : undefined;
      return Promise.resolve({ remoteAccessSessions: this.sessionPages[index] ?? [], nextToken: next });
    },
  };
}

// ---- 环境 ----

const RUN_ID = "20261030T120000Z-a1b2c3";
const SCOPE_ID = "features/shop.feature::Checkout";
const PROJECT = "arn:aws:devicefarm:us-west-2:123456789012:project:p";

function makeJob(request: { osVersion?: string; deviceArn?: string }, device: "android" | "ios" = "ios"): Omit<Job, "scenarios"> {
  return {
    schemaVersion: 1,
    scope: { id: SCOPE_ID, name: "Checkout" },
    engine: "midscene",
    assertionVotes: 1,
    timeoutS: 1500,
    target: { device, uiKind: "web" },
    deviceRequest: { provider: "aws-device-farm", billingMethod: "METERED", projectArn: PROJECT, acquireTimeoutS: 600, ...request },
  };
}

/** emitDelayMs 给出每条会话事件写出所需的虚拟时间（模拟写入变慢的事件出口），缺省为即时；at 记的是写完的时刻。 */
function setup(
  request: { osVersion?: string; deviceArn?: string } = { osVersion: "18" }, device: "android" | "ios" = "ios",
  opts: { emitDelayMs?: (e: Record<string, unknown>) => number } = {},
) {
  const clock = new FakeClock();
  const farm = new FakeFarm(clock);
  const emitted: Record<string, unknown>[] = [];
  const logs: string[] = [];
  const env: DevicePartsEnv = {
    job: makeJob(request, device),
    log: (line) => logs.push(line),
    events: sessionEventSink(SCOPE_ID, async (e) => {
      const delay = opts.emitDelayMs?.(e) ?? 0;
      if (delay > 0) await clock.timers.sleep(delay);
      emitted.push({ ...e, at: clock.t });
    }),
    processEnv: {},
    now: clock.now,
  };
  const block = createDeviceFarmSessions(env, { api: farm.api, timers: clock.timers, runId: RUN_ID });
  const controller = new AbortController();
  const budget: AcquireBudget & { abort(reason?: unknown): void } = {
    signal: controller.signal,
    remainingMs: () => 600_000,
    abort: (reason) => controller.abort(reason ?? new Error("在等待时间内没有拿到可用设备")),
  };
  return { clock, farm, emitted, logs, env, block, budget };
}

function dev(arn: string, os: string, availability: string, extra: Partial<FarmDevice> = {}): FarmDevice {
  return {
    arn: `arn:aws:devicefarm:us-west-2::device:${arn}`, name: `Apple iPhone ${arn}`, model: `iPhone ${arn}`, platform: "IOS",
    os, formFactor: "PHONE", remoteAccessEnabled: true, fleetType: "PUBLIC", availability: availability as FarmDevice["availability"],
    ...extra,
  };
}

// ---- 版本族与版本比较（ADR 0051 决策 3）----

test("版本族按点分段匹配：18 命中 18 与 18.x.y，18.1 不命中 18.10，写全段即精确匹配", () => {
  assert.equal(matchesVersionFamily("18", "18"), true);
  assert.equal(matchesVersionFamily("18", "18.6.2"), true);
  assert.equal(matchesVersionFamily("18", "8.1"), false);
  assert.equal(matchesVersionFamily("8", "18.0"), false);
  assert.equal(matchesVersionFamily("18.1", "18.1.4"), true);
  assert.equal(matchesVersionFamily("18.1", "18.10"), false);
  assert.equal(matchesVersionFamily("18.1", "18.10.2"), false);
  assert.equal(matchesVersionFamily("18.1.4", "18.1.4"), true);
  assert.equal(matchesVersionFamily("18.1.4", "18.1"), false);
  assert.equal(matchesVersionFamily("18.1.4", "18.1.5"), false);
});

test("版本比较逐段按数值：18.10 高于 18.9，缺的段按 0", () => {
  assert.ok(compareVersions("18.10", "18.9") > 0);
  assert.ok(compareVersions("26.3", "18.6.2") > 0);
  assert.equal(compareVersions("18", "18.0"), 0);
  assert.ok(compareVersions("15.8.4", "15.8") > 0);
});

// ---- 设备解析 ----

test("设备解析：静态过滤平台、手机、远程访问与公共设备，排除 BUSY 与 TEMPORARY_NOT_AVAILABLE，按版本号高、HIGHLY_AVAILABLE 优先、ARN 字典序取第一台", async () => {
  const h = setup({ osVersion: "18" });
  h.farm.devicePages = [[
    dev("A17", "17.5", "HIGHLY_AVAILABLE"),                                    // 不在版本族里
    dev("BUSY", "18.7", "BUSY"),                                               // 繁忙
    dev("TNA", "18.7", "TEMPORARY_NOT_AVAILABLE"),                              // 暂不可用
    dev("TAB", "18.9", "HIGHLY_AVAILABLE", { formFactor: "TABLET" }),           // 平板
    dev("NORA", "18.9", "HIGHLY_AVAILABLE", { remoteAccessEnabled: false }),    // 不支持远程访问
    dev("PRIV", "18.9", "HIGHLY_AVAILABLE", { fleetType: "PRIVATE" }),          // 私有设备
    dev("DROID", "18.9", "HIGHLY_AVAILABLE", { platform: "ANDROID" }),          // 别的平台
    dev("C", "18.6", "AVAILABLE"),
    dev("B", "18.6", "HIGHLY_AVAILABLE"),
    dev("A", "18.6", "HIGHLY_AVAILABLE"),
    dev("Z", "18.1", "HIGHLY_AVAILABLE"),
  ]];
  const got = await h.clock.run(h.block.resolve(h.budget, null));
  assert.deepEqual(got, { ok: true, value: { deviceArn: "arn:aws:devicefarm:us-west-2::device:A", model: "iPhone A", osVersion: "18.6" } });
});

test("设备解析：版本号高优先于可用性（同族里 18.6 AVAILABLE 先于 18.1 HIGHLY_AVAILABLE）", async () => {
  const h = setup({ osVersion: "18" });
  h.farm.devicePages = [[dev("LOW", "18.1", "HIGHLY_AVAILABLE"), dev("HIGH", "18.6", "AVAILABLE")]];
  const got = await h.clock.run(h.block.resolve(h.budget, null));
  assert.equal(got.ok && got.value.deviceArn, "arn:aws:devicefarm:us-west-2::device:HIGH");
});

test("设备解析：完整分页（带 nextToken 读完每一页），最合适的设备在最后一页也能选中，每次调用都带中止信号", async () => {
  const h = setup({ osVersion: "18" });
  h.farm.devicePages = [[dev("P1", "18.1", "AVAILABLE")], [dev("P2", "18.2", "AVAILABLE")], [dev("P3", "18.6", "AVAILABLE")]];
  const got = await h.clock.run(h.block.resolve(h.budget, null));
  assert.equal(got.ok && got.value.deviceArn, "arn:aws:devicefarm:us-west-2::device:P3");
  assert.deepEqual(h.farm.ops("listDevices").map((c) => c.arg), [undefined, "page-1", "page-2"]);
  for (const c of h.farm.ops("listDevices")) assert.ok(c.signal instanceof AbortSignal);
});

test("设备解析：首轮零候选间隔 2 秒再列一次，仍为零即 precheck_failed，消息给出条件与最接近的可用版本", async () => {
  const h = setup({ osVersion: "17" });
  h.farm.devicePages = [[dev("A", "16.7", "AVAILABLE"), dev("B", "18.6", "BUSY"), dev("T", "17.2", "AVAILABLE", { formFactor: "TABLET" })]];
  const got = await h.clock.run(h.block.resolve(h.budget, null));
  assert.equal(got.ok, false);
  if (got.ok) return;
  assert.equal(got.termination.errorType, "precheck_failed");
  assert.match(got.termination.message, /17/);
  assert.match(got.termination.message, /iOS/);
  assert.match(got.termination.message, /16\.7/);       // 最接近的可用版本（平板的 17.2 不在静态过滤之内）
  assert.match(got.termination.message, /gherkai\.toml 里 \[devices\.ios\] 的 os-version 改为 "16\.7"/);
  const lists = h.farm.ops("listDevices");
  assert.equal(lists.length, 2);
  assert.equal(lists[1].at - lists[0].at, DEVICE_RELIST_DELAY_MS);
  assert.equal(h.farm.ops("create").length, 0);
});

test("设备解析：没有任何同平台的手机时，零候选的消息不编造版本", async () => {
  const h = setup({ osVersion: "17" }, "android");
  h.farm.devicePages = [[dev("IOS", "17.0", "AVAILABLE")]];
  const got = await h.clock.run(h.block.resolve(h.budget, null));
  assert.equal(got.ok, false);
  if (got.ok) return;
  assert.equal(got.termination.errorType, "precheck_failed");
  assert.match(got.termination.message, /Android/);
  assert.doesNotMatch(got.termination.message, /最接近/);
});

test("设备解析：首轮零候选、重列后出现候选即选中", async () => {
  const h = setup({ osVersion: "18" });
  let round = 0;
  h.farm.listDevicesImpl = async () => ({ devices: round++ === 0 ? [] : [dev("A", "18.6", "AVAILABLE")] });
  const got = await h.clock.run(h.block.resolve(h.budget, null));
  assert.equal(got.ok && got.value.deviceArn, "arn:aws:devicefarm:us-west-2::device:A");
});

test("设备解析：全部繁忙时在预算内等待，重列间隔 5、10、20 秒递增、封顶 30 秒；等待期间候选变空不改判", async () => {
  const h = setup({ osVersion: "18" });
  const rounds: FarmDevice[][] = [
    [dev("A", "18.6", "BUSY")],
    [dev("A", "18.6", "BUSY")],
    [],                                      // 候选变空：仍在等待，不改判为零候选
    [dev("A", "18.6", "BUSY")],
    [dev("A", "18.6", "BUSY")],
    [dev("A", "18.6", "AVAILABLE")],
  ];
  let round = 0;
  h.farm.listDevicesImpl = async () => ({ devices: rounds[Math.min(round++, rounds.length - 1)] });
  const got = await h.clock.run(h.block.resolve(h.budget, null));
  assert.equal(got.ok && got.value.deviceArn, "arn:aws:devicefarm:us-west-2::device:A");
  const at = h.farm.ops("listDevices").map((c) => c.at);
  const gaps = at.slice(1).map((t, i) => t - at[i]);
  assert.deepEqual(gaps, [busyBackoffMs(0), busyBackoffMs(1), busyBackoffMs(2), busyBackoffMs(3), busyBackoffMs(4)]);
  assert.deepEqual(gaps, [5_000, 10_000, 20_000, 30_000, 30_000]);
});

test("设备解析：繁忙等待中预算到期或进入终结，等待立即中止并把中止原因抛给调用方，不再列举", async () => {
  const h = setup({ osVersion: "18" });
  h.farm.devicePages = [[dev("A", "18.6", "BUSY")]];
  const pending = h.block.resolve(h.budget, null);
  await settle();
  const reason = new Error("在等待时间内没有拿到可用设备");
  h.budget.abort(reason);
  await assert.rejects(h.clock.run(pending), (e) => e === reason);
  assert.equal(h.farm.ops("listDevices").length, 1);
});

test("设备解析：列举被拒（非限流的 4xx）直接报错；限流与服务端错误在预算内退避后重列", async () => {
  const denied = setup({ osVersion: "18" });
  denied.farm.listDevicesImpl = async () => { throw sdkError("AccessDeniedException", 400); };
  await assert.rejects(denied.clock.run(denied.block.resolve(denied.budget, null)), /AccessDeniedException/);
  assert.equal(denied.farm.ops("listDevices").length, 1);

  const throttled = setup({ osVersion: "18" });
  let n = 0;
  throttled.farm.listDevicesImpl = async () => {
    n += 1;
    if (n === 1) throw sdkError("ThrottlingException", 400);
    if (n === 2) throw sdkError("InternalServiceException", 500);
    return { devices: [dev("A", "18.6", "AVAILABLE")] };
  };
  const got = await throttled.clock.run(throttled.block.resolve(throttled.budget, null));
  assert.equal(got.ok, true);
  assert.equal(throttled.farm.ops("listDevices").length, 3);
});

test("设备解析：直接给 ARN 时不列举、不做静态过滤", async () => {
  const h = setup({ deviceArn: "arn:aws:devicefarm:us-west-2::device:FIXED" });
  const got = await h.clock.run(h.block.resolve(h.budget, null));
  assert.deepEqual(got, { ok: true, value: { deviceArn: "arn:aws:devicefarm:us-west-2::device:FIXED", model: null, osVersion: null } });
  assert.equal(h.farm.calls.length, 0);
});

// ---- Create ----

const CHOICE = { deviceArn: "arn:aws:devicefarm:us-west-2::device:A", model: "iPhone A", osVersion: "18.6" };

test("Create：尝试序号从 1 起、每次请求递增（含限流重试），会话名按规则编码；Create 返回 ARN 后、调用返回之前发 session_opened(created)", async () => {
  const h = setup();
  let n = 0;
  h.farm.createImpl = async (input) => {
    n += 1;
    if (n === 1) throw sdkError("LimitExceededException", 400);
    if (n === 2) throw sdkError("ThrottlingException", 429);
    return { arn: "arn:session:3", name: input.name, status: "PENDING", instanceArn: "arn:aws:devicefarm:us-west-2::deviceinstance:U3" };
  };
  const got = await h.clock.run(h.block.create(CHOICE, h.budget));
  const creates = h.farm.ops("create");
  assert.deepEqual(creates.map((c) => (c.arg as { name: string }).name), [1, 2, 3].map((a) => encode(RUN_ID, SCOPE_ID, a)));
  for (const c of creates) {
    assert.deepEqual({ ...(c.arg as object), name: undefined }, { projectArn: PROJECT, deviceArn: CHOICE.deviceArn, billingMethod: "METERED", name: undefined });
  }
  assert.deepEqual(creates.slice(1).map((c, i) => c.at - creates[i].at), [busyBackoffMs(0), busyBackoffMs(1)]);
  assert.equal(got.ok, true);
  if (!got.ok) return;
  const device = { platform: "ios", model: "iPhone A", osVersion: "18.6", unit: "arn:aws:devicefarm:us-west-2::deviceinstance:U3" };
  assert.deepEqual(got.value, { arn: "arn:session:3", name: encode(RUN_ID, SCOPE_ID, 3), createRequestedAt: creates[2].at, device });
  assert.equal(h.emitted.length, 1);
  assert.deepEqual({ ...h.emitted[0], at: undefined }, {
    type: "session_opened", scopeId: SCOPE_ID, sessionId: "arn:session:3", name: encode(RUN_ID, SCOPE_ID, 3), origin: "created", device, at: undefined,
  });
  // 限流不是结果未知：不登记待核，重试前也不按名核对
  assert.equal(h.farm.ops("listSessions").length, 0);
  assert.deepEqual([...h.block.registry.pending.keys()], []);
});

test("Create：会话年龄的起点 createRequestedAt 是发出 Create 的时刻，不是它返回的时刻", async () => {
  const h = setup();
  h.farm.createImpl = (input) => h.clock.timers.sleep(4_000).then(() => ({ arn: "arn:session:1", name: input.name, status: "PENDING" }));
  const sentAt = h.clock.t;
  const got = await h.clock.run(h.block.create(CHOICE, h.budget));
  assert.equal(got.ok && got.value.createRequestedAt, sentAt);
  assert.equal(h.clock.t, sentAt + 4_000);
});

test("Create：请求超时即记为待核；重试前按名列举，列举为空不构成排除，待核保留到终结", async () => {
  const h = setup();
  let n = 0;
  h.farm.createImpl = (input, signal) => {
    n += 1;
    return n === 1 ? hang(signal) : Promise.resolve({ arn: "arn:session:2", name: input.name, status: "PENDING" });
  };
  const got = await h.clock.run(h.block.create(CHOICE, h.budget));
  assert.equal(got.ok && got.value.name, encode(RUN_ID, SCOPE_ID, 2));
  const [first, second] = h.farm.ops("create");
  assert.equal(second.at - first.at, DEVICE_FARM_CALL_TIMEOUT_MS + busyBackoffMs(0));
  const lists = h.farm.ops("listSessions");
  assert.equal(lists.length, 1);
  assert.deepEqual(lists[0].arg, { projectArn: PROJECT, nextToken: undefined });
  assert.ok(lists[0].at <= second.at);
  assert.deepEqual([...h.block.registry.pending.keys()], [encode(RUN_ID, SCOPE_ID, 1)]);
});

test("Create：在途的 Create 不因获取预算到期而被中止（结果未知只来自它自己的请求超时或连接中断）", async () => {
  const h = setup();
  h.farm.createImpl = (input) => h.clock.timers.sleep(3_000).then(() => ({ arn: "arn:session:1", name: input.name, status: "PENDING" }));
  const pending = h.block.create(CHOICE, h.budget);
  await settle();
  h.budget.abort();
  const got = await h.clock.run(pending);
  assert.equal(got.ok && got.value.arn, "arn:session:1");
  assert.equal(h.farm.ops("create")[0].signal.aborted, false);
  assert.deepEqual([...h.block.registry.pending.keys()], []);
});

test("Create：连接中断记为待核；按名列举（含分页）命中即登记待清理并发 session_opened(discovered)，待核消除", async () => {
  const h = setup();
  const name1 = encode(RUN_ID, SCOPE_ID, 1);
  let n = 0;
  h.farm.createImpl = async (input) => {
    n += 1;
    if (n === 1) throw connectionReset();
    return { arn: "arn:session:2", name: input.name, status: "PENDING" };
  };
  h.farm.sessionPages = [
    [{ arn: "arn:other", name: encode(RUN_ID, "features/other.feature::X", 1), status: "RUNNING" }],
    [{ arn: "arn:orphan", name: name1, status: "PENDING", device: { model: "iPhone A", os: "18.6" }, instanceArn: "arn:unit:9" }],
  ];
  const got = await h.clock.run(h.block.create(CHOICE, h.budget));
  assert.equal(got.ok, true);
  assert.deepEqual(h.farm.ops("listSessions").map((c) => (c.arg as { nextToken?: string }).nextToken), [undefined, "page-1"]);
  assert.deepEqual([...h.block.registry.pending.keys()], []);
  assert.deepEqual([...h.block.registry.sessions.keys()], ["arn:orphan", "arn:session:2"]);
  assert.equal(h.block.registry.sessions.get("arn:orphan")!.origin, "discovered");
  assert.deepEqual(h.emitted.map((e) => [e.type, e.origin, e.sessionId, e.name]), [
    ["session_opened", "discovered", "arn:orphan", name1],
    ["session_opened", "created", "arn:session:2", encode(RUN_ID, SCOPE_ID, 2)],
  ]);
  assert.deepEqual(h.emitted[0].device, { platform: "ios", model: "iPhone A", osVersion: "18.6", unit: "arn:unit:9" });
  // 当前执行所用的会话是新建的那个，孤儿只进待清理集
  assert.equal(h.block.registry.current?.arn, "arn:session:2");
});

test("Create：按名列举的分页没扫完视为未核对，待核保留（即使已扫的页里没有命中）", async () => {
  const h = setup();
  let n = 0;
  h.farm.createImpl = async (input) => {
    n += 1;
    if (n === 1) throw connectionReset();
    return { arn: "arn:session:2", name: input.name, status: "PENDING" };
  };
  h.farm.listSessionsImpl = async ({ nextToken }) => {
    if (nextToken === undefined) return { remoteAccessSessions: [], nextToken: "page-1" };
    throw sdkError("InternalServiceException", 500);
  };
  await h.clock.run(h.block.create(CHOICE, h.budget));
  assert.equal(h.farm.ops("listSessions").length, 2);
  assert.deepEqual([...h.block.registry.pending.keys()], [encode(RUN_ID, SCOPE_ID, 1)]);
});

test("Create：按名核对以进入时的待核名字为准扫页——首页命中一个名字后仍翻页找其余名字，后页出错时命中的已登记并消除、没命中的保留待核", async () => {
  const h = setup();
  const [name1, name2] = [1, 2].map((a) => encode(RUN_ID, SCOPE_ID, a));
  let n = 0;
  h.farm.createImpl = async (input) => {
    n += 1;
    if (n <= 2) throw connectionReset();
    return { arn: "arn:session:3", name: input.name, status: "PENDING" };
  };
  let lists = 0;
  h.farm.listSessionsImpl = async ({ nextToken }) => {
    lists += 1;
    if (lists === 1) throw sdkError("InternalServiceException", 500);   // 第二次 Create 之前的核对没有完成：两个名字都待核
    if (nextToken === undefined) return { remoteAccessSessions: [{ arn: "arn:orphan1", name: name1, status: "RUNNING" }], nextToken: "page-1" };
    throw sdkError("InternalServiceException", 500);
  };
  const got = await h.clock.run(h.block.create(CHOICE, h.budget));
  assert.equal(got.ok, true);
  assert.deepEqual(h.farm.ops("listSessions").map((c) => (c.arg as { nextToken?: string }).nextToken), [undefined, undefined, "page-1"]);
  assert.deepEqual([...h.block.registry.pending.keys()], [name2]);
  assert.deepEqual([...h.block.registry.sessions.keys()], ["arn:orphan1", "arn:session:3"]);
  assert.deepEqual(h.emitted.map((e) => [e.origin, e.sessionId]), [["discovered", "arn:orphan1"], ["created", "arn:session:3"]]);
});

test("Create：按名核对扫到分页结束——首页已命中全部待核名字，后页同名的 ARN 也登记、各发一条 session_opened(discovered)，获取期都按 Stop 规则停止", async () => {
  const h = setup();
  const name1 = encode(RUN_ID, SCOPE_ID, 1);
  let n = 0;
  h.farm.createImpl = async (input) => {
    n += 1;
    if (n === 1) throw connectionReset();
    return { arn: "arn:session:2", name: input.name, status: "PENDING" };
  };
  h.farm.sessionPages = [
    [{ arn: "arn:dupA", name: name1, status: "RUNNING" }],
    [{ arn: "arn:old", name: "gherkai:other", status: "COMPLETED" }],
    [{ arn: "arn:dupB", name: name1, status: "PENDING" }],
  ];
  const got = await h.clock.run(h.block.create(CHOICE, h.budget));
  assert.equal(got.ok, true);
  assert.deepEqual(h.farm.ops("listSessions").map((c) => (c.arg as { nextToken?: string }).nextToken), [undefined, "page-1", "page-2"]);
  assert.deepEqual([...h.block.registry.pending.keys()], []);
  assert.deepEqual([...h.block.registry.sessions.keys()], ["arn:dupA", "arn:dupB", "arn:session:2"]);
  assert.deepEqual(h.emitted.map((e) => [e.origin, e.sessionId]), [
    ["discovered", "arn:dupA"], ["discovered", "arn:dupB"], ["created", "arn:session:2"],
  ]);
  assert.deepEqual(h.farm.ops("stop").map((c) => c.arg).sort(), ["arn:dupA", "arn:dupB"]);
  const secondCreateAt = h.farm.ops("create")[1].at;
  for (const c of h.farm.ops("stop")) assert.ok(c.at <= secondCreateAt, `Stop ${String(c.arg)} 晚于下一次 Create`);
});

test("Create：按名核对逐 ARN 登记——同一页里同名的两个会话都进待清理集、各发一条 session_opened(discovered)", async () => {
  const h = setup();
  const name1 = encode(RUN_ID, SCOPE_ID, 1);
  let n = 0;
  h.farm.createImpl = async (input) => {
    n += 1;
    if (n === 1) throw connectionReset();
    return { arn: "arn:session:2", name: input.name, status: "PENDING" };
  };
  h.farm.sessionPages = [[{ arn: "arn:dupA", name: name1, status: "RUNNING" }, { arn: "arn:dupB", name: name1, status: "PENDING" }]];
  await h.clock.run(h.block.create(CHOICE, h.budget));
  assert.deepEqual([...h.block.registry.sessions.keys()], ["arn:dupA", "arn:dupB", "arn:session:2"]);
  assert.deepEqual(h.emitted.map((e) => [e.origin, e.sessionId]), [
    ["discovered", "arn:dupA"], ["discovered", "arn:dupB"], ["created", "arn:session:2"],
  ]);
  // 两个找回的会话都随即按 Stop 规则处理
  assert.deepEqual(h.farm.ops("stop").map((c) => c.arg).sort(), ["arn:dupA", "arn:dupB"]);
});

// ---- 获取期按名找回的孤儿会话：找回即按 Stop 规则停止，不等到终结 ----

/** 第一次 Create 连接中断、之后的 Create 成功；重试前的按名核对在首页找回第一次尝试建立的会话 arn:orphan。 */
function orphanSetup(opts: Parameters<typeof setup>[2] = {}) {
  const h = setup(undefined, undefined, opts);
  const name1 = encode(RUN_ID, SCOPE_ID, 1);
  let n = 0;
  h.farm.createImpl = async (input) => {
    n += 1;
    if (n === 1) throw connectionReset();
    return { arn: "arn:session:2", name: input.name, status: "PENDING" };
  };
  h.farm.sessionPages = [[{ arn: "arn:orphan", name: name1, status: "PENDING" }]];
  return { ...h, name1 };
}

/** 调用序列：op 与 Get / Stop 的对象（其余调用的参数不看）。 */
function sequence(h: { farm: FakeFarm }): [string, unknown][] {
  return h.farm.calls.map((c) => [c.op, c.op === "get" || c.op === "stop" ? c.arg : undefined]);
}

test("获取期找回的孤儿会话：session_opened(discovered) 写出之后即按 Stop 规则先 Get，仍在排队即发一次 Stop，返回体为 STOPPING 即确认，然后才发下一次 Create", async () => {
  const h = orphanSetup();
  h.farm.getImpl = async (arn) => ({ arn, status: arn === "arn:orphan" ? "PENDING_CONCURRENCY" : "RUNNING" });
  let emittedAtStop = -1;
  h.farm.stopImpl = async (arn) => {
    emittedAtStop = h.emitted.length;
    return { arn, status: "STOPPING", deviceMinutes: { total: 0.2, metered: 0.2, unmetered: 0 } };
  };
  const got = await h.clock.run(h.block.create(CHOICE, h.budget));
  assert.equal(got.ok && got.value.arn, "arn:session:2");
  assert.deepEqual(sequence(h), [
    ["create", undefined], ["listSessions", undefined], ["get", "arn:orphan"], ["stop", "arn:orphan"], ["create", undefined],
  ]);
  assert.equal(emittedAtStop, 1);                                     // Stop 发出时 session_opened(discovered) 已写出
  const orphan = h.block.registry.sessions.get("arn:orphan")!;
  assert.equal(orphan.stopSentAt, h.farm.ops("stop")[0].at);
  assert.notEqual(orphan.confirmedAt, null);
  assert.deepEqual(orphan.providerMinutes, { total: 0.2, metered: 0.2, unmetered: 0 });
  // 孤儿仍在待清理集（session_closed 归终结），执行所用的是新建的会话；获取期不发 session_closed
  assert.deepEqual([...h.block.registry.sessions.keys()], ["arn:orphan", "arn:session:2"]);
  assert.equal(h.block.registry.current?.arn, "arn:session:2");
  assert.deepEqual(h.emitted.map((e) => [e.type, e.origin, e.sessionId]), [
    ["session_opened", "discovered", "arn:orphan"], ["session_opened", "created", "arn:session:2"],
  ]);
  // Get 与 Stop 接获取预算的信号：预算中止即随之中止
  h.budget.abort();
  for (const op of ["get", "stop"]) assert.equal(h.farm.ops(op)[0].signal.aborted, true, op);
});

test("获取期找回的孤儿会话：session_opened 写出后即开始按 Stop 规则处理，与剩余分页并行——下一页延迟返回时，对首页会话的 Get / Stop 在它返回之前已发出，下一次 Create 等分页扫完才发出", async () => {
  const h = setup();
  const name1 = encode(RUN_ID, SCOPE_ID, 1);
  let n = 0;
  h.farm.createImpl = async (input) => {
    n += 1;
    if (n === 1) throw connectionReset();
    return { arn: "arn:session:2", name: input.name, status: "PENDING" };
  };
  const nextPageDelayMs = 9_000;                                        // 在单次列举的 10 秒上界之内
  h.farm.listSessionsImpl = ({ nextToken }, signal) => nextToken === undefined
    ? Promise.resolve({ remoteAccessSessions: [{ arn: "arn:orphan", name: name1, status: "RUNNING" }], nextToken: "page-1" })
    : h.clock.timers.sleep(nextPageDelayMs, signal).then(() => ({ remoteAccessSessions: [] }));
  const got = await h.clock.run(h.block.create(CHOICE, h.budget));
  assert.equal(got.ok && got.value.arn, "arn:session:2");
  const [firstPage, nextPage] = h.farm.ops("listSessions");
  const nextPageReturnedAt = nextPage.at + nextPageDelayMs;
  const [get] = h.farm.ops("get");
  const [stop] = h.farm.ops("stop");
  assert.deepEqual([get.arg, stop.arg], ["arn:orphan", "arn:orphan"]);
  assert.equal(get.at, firstPage.at);                                   // 首页的 session_opened 写出即发 Get，不等下一页
  assert.ok(stop.at < nextPageReturnedAt, `Stop 在 ${stop.at - firstPage.at} 毫秒时才发出`);
  assert.notEqual(h.block.registry.sessions.get("arn:orphan")!.confirmedAt, null);
  assert.equal(h.farm.ops("create")[1].at, nextPageReturnedAt);         // 分页扫完才发下一次 Create
});

test("获取期找回的孤儿会话：事件出口写入变慢时，Get 在这个会话的 session_opened 写完之后才发出", async () => {
  const h = orphanSetup({ emitDelayMs: (e) => (e.origin === "discovered" ? 1_500 : 0) });
  await h.clock.run(h.block.create(CHOICE, h.budget));
  const opened = h.emitted.find((e) => e.origin === "discovered")!;
  const [get] = h.farm.ops("get");
  assert.equal(get.arg, "arn:orphan");
  assert.equal(h.farm.ops("listSessions")[0].at + 1_500, opened.at);
  assert.equal(get.at, opened.at);
});

test("获取期找回的孤儿会话：同一页找回两个会话时各自在自己的 session_opened 写出后即开始处理，不等同页其余会话的事件写完", async () => {
  const h = setup(undefined, undefined, { emitDelayMs: (e) => (e.sessionId === "arn:slow" ? 3_000 : 0) });
  const name1 = encode(RUN_ID, SCOPE_ID, 1);
  let n = 0;
  h.farm.createImpl = async (input) => {
    n += 1;
    if (n === 1) throw connectionReset();
    return { arn: "arn:session:2", name: input.name, status: "PENDING" };
  };
  h.farm.sessionPages = [[{ arn: "arn:fast", name: name1, status: "RUNNING" }, { arn: "arn:slow", name: name1, status: "RUNNING" }]];
  await h.clock.run(h.block.create(CHOICE, h.budget));
  const listedAt = h.farm.ops("listSessions")[0].at;
  const slowOpenedAt = h.emitted.find((e) => e.sessionId === "arn:slow")!.at as number;
  assert.equal(slowOpenedAt, listedAt + 3_000);
  assert.equal(h.farm.ops("get").find((c) => c.arg === "arn:fast")!.at, listedAt);
  assert.equal(h.farm.ops("get").find((c) => c.arg === "arn:slow")!.at, slowOpenedAt);
});

test("获取期找回的孤儿会话：分页扫完时停止还没处理完，下一次 Create 等它处理完才发出", async () => {
  const h = orphanSetup();
  const getDelayMs = 5_000;
  h.farm.getImpl = (arn, signal) => arn === "arn:orphan"
    ? h.clock.timers.sleep(getDelayMs, signal).then(() => ({ arn, status: "RUNNING" }))
    : Promise.resolve({ arn, status: "RUNNING" });
  await h.clock.run(h.block.create(CHOICE, h.budget));
  const [get] = h.farm.ops("get");
  const [stop] = h.farm.ops("stop");
  assert.equal(stop.at, get.at + getDelayMs);
  assert.equal(h.farm.ops("create")[1].at, stop.at);
  assert.ok(h.farm.ops("listSessions")[0].at <= get.at);
});

test("获取期找回的孤儿会话：Get 已是 STOPPING / COMPLETED 即确认，不发 Stop", async () => {
  for (const status of ["STOPPING", "COMPLETED"]) {
    const h = orphanSetup();
    h.farm.getImpl = async (arn) => ({ arn, status, deviceMinutes: { total: 1 } });
    await h.clock.run(h.block.create(CHOICE, h.budget));
    assert.deepEqual(sequence(h), [["create", undefined], ["listSessions", undefined], ["get", "arn:orphan"], ["create", undefined]], status);
    const orphan = h.block.registry.sessions.get("arn:orphan")!;
    assert.notEqual(orphan.confirmedAt, null, status);
    assert.equal(orphan.stopSentAt, null, status);
    assert.deepEqual(orphan.providerMinutes, { total: 1 }, status);
  }
});

test("获取期找回的孤儿会话：Stop 报错或返回体不是 STOPPING / COMPLETED 时补查一次 Get；补查仍未停止即留给收尾，不重试 Stop", async () => {
  const stops: Array<() => Promise<RemoteAccessSession>> = [
    async () => { throw sdkError("InternalServiceException", 500); },
    async () => ({ status: "RUNNING" }),
  ];
  for (const stop of stops) {
    const h = orphanSetup();
    h.farm.stopImpl = stop;
    const got = await h.clock.run(h.block.create(CHOICE, h.budget));
    assert.equal(got.ok, true);
    assert.deepEqual(sequence(h), [
      ["create", undefined], ["listSessions", undefined], ["get", "arn:orphan"], ["stop", "arn:orphan"], ["get", "arn:orphan"],
      ["create", undefined],
    ]);
    const orphan = h.block.registry.sessions.get("arn:orphan")!;
    assert.notEqual(orphan.stopSentAt, null);
    assert.equal(orphan.confirmedAt, null);
    assert.ok(h.logs.some((l) => l.includes("arn:orphan") && l.includes("收尾")), h.logs.join("\n"));
  }
});

test("获取期找回的孤儿会话：不重复 Stop——之后的重试再按名核对时，已找回的会话即使又被列出也不再 Get / Stop、不再发 session_opened", async () => {
  const h = setup();
  const [name1, name2] = [1, 2].map((a) => encode(RUN_ID, SCOPE_ID, a));
  let n = 0;
  h.farm.createImpl = async (input) => {
    n += 1;
    if (n <= 2) throw connectionReset();
    return { arn: "arn:session:3", name: input.name, status: "PENDING" };
  };
  h.farm.sessionPages = [[{ arn: "arn:orphan1", name: name1, status: "RUNNING" }]];    // 两次核对都列出它
  const got = await h.clock.run(h.block.create(CHOICE, h.budget));
  assert.equal(got.ok, true);
  assert.equal(h.farm.ops("listSessions").length, 2);
  assert.deepEqual(h.farm.ops("stop").map((c) => c.arg), ["arn:orphan1"]);
  assert.deepEqual(h.farm.ops("get").map((c) => c.arg), ["arn:orphan1"]);
  assert.deepEqual([...h.block.registry.pending.keys()], [name2]);
  assert.deepEqual(h.emitted.map((e) => [e.origin, e.sessionId]), [["discovered", "arn:orphan1"], ["created", "arn:session:3"]]);
});

test("获取期找回的孤儿会话：处理中获取预算中止（到期或进入终结）即停——在途的 Get 随之中止，不再发 Stop，会话留在待清理集交给终结", async () => {
  const h = orphanSetup();
  h.farm.getImpl = (_arn, signal) => { h.budget.abort(); return hang(signal); };
  await assert.rejects(h.clock.run(h.block.create(CHOICE, h.budget)));
  assert.deepEqual(sequence(h), [["create", undefined], ["listSessions", undefined], ["get", "arn:orphan"]]);
  const orphan = h.block.registry.sessions.get("arn:orphan")!;
  assert.equal(orphan.stopSentAt, null);
  assert.equal(orphan.confirmedAt, null);
});

test("Create：返回了却没带会话 ARN 时记为待核，并写一行日志说明原因与会话名", async () => {
  const h = setup();
  const name1 = encode(RUN_ID, SCOPE_ID, 1);
  let n = 0;
  h.farm.createImpl = async (input) => {
    n += 1;
    return n === 1 ? { status: "PENDING" } : { arn: "arn:session:2", name: input.name, status: "PENDING" };
  };
  await h.clock.run(h.block.create(CHOICE, h.budget));
  assert.deepEqual([...h.block.registry.pending.keys()], [name1]);
  assert.ok(h.logs.some((l) => l.includes("没有带会话 ARN") && l.includes(name1)), h.logs.join("\n"));
});

test("Create：指定 ARN 被同步拒绝（非限流的 4xx）记 precheck_failed；按条件选出的设备被拒则报错交接缝归类", async () => {
  const fixed = setup({ deviceArn: "arn:aws:devicefarm:us-west-2::device:GONE" });
  fixed.farm.createImpl = async () => { throw sdkError("ArgumentException", 400, "Invalid device"); };
  const choice = { deviceArn: "arn:aws:devicefarm:us-west-2::device:GONE", model: null, osVersion: null };
  const got = await fixed.clock.run(fixed.block.create(choice, fixed.budget));
  assert.equal(got.ok, false);
  if (got.ok) return;
  assert.equal(got.termination.errorType, "precheck_failed");
  assert.match(got.termination.message, /Invalid device/);
  assert.equal(fixed.farm.ops("create").length, 1);
  assert.equal(fixed.emitted.length, 0);

  const filtered = setup();
  filtered.farm.createImpl = async () => { throw sdkError("NotEligibleException", 400, "not eligible"); };
  await assert.rejects(filtered.clock.run(filtered.block.create(CHOICE, filtered.budget)), /not eligible/);
});

test("Create：指定 ARN 时权限或凭证类的拒绝不归 precheck_failed（不是设备被拒），报错交接缝归类并提示核对权限", async () => {
  const errors = [
    sdkError("AccessDeniedException", 400, "not authorized to perform devicefarm:CreateRemoteAccessSession"),
    Object.assign(new Error("Could not load credentials from any providers"), { name: "CredentialsProviderError" }),
  ];
  for (const error of errors) {
    const h = setup({ deviceArn: "arn:aws:devicefarm:us-west-2::device:FIXED" });
    h.farm.createImpl = async () => { throw error; };
    const choice = { deviceArn: "arn:aws:devicefarm:us-west-2::device:FIXED", model: null, osVersion: null };
    const got = await h.clock.run(h.block.create(choice, h.budget)).then((v) => v, (e: unknown) => e);
    assert.ok(got instanceof Error, error.name);
    assert.match(got.message, new RegExp(error.message));
    assert.match(got.message, /权限/);
    assert.equal(h.farm.ops("create").length, 1);
  }
});

test("指定 ARN 被拒的消息不说设备来自配置文件（ARN 也可能来自命令行选项）", () => {
  const message = deviceArnRejectedMessage("Invalid device");
  assert.match(message, /^Device Farm 拒绝为指定的设备建立远程访问会话：Invalid device；/);
  assert.doesNotMatch(message, /配置/);
});

test("Create：直接给 ARN 时 session_opened.device 的机型与系统版本取 Create 返回的设备描述", async () => {
  const h = setup({ deviceArn: "arn:aws:devicefarm:us-west-2::device:FIXED" });
  h.farm.createImpl = async (input) => ({ arn: "arn:session:1", name: input.name, status: "PENDING", device: { model: "Pixel 8", os: "14" } });
  const got = await h.clock.run(h.block.create({ deviceArn: "arn:aws:devicefarm:us-west-2::device:FIXED", model: null, osVersion: null }, h.budget));
  assert.equal(got.ok, true);
  assert.deepEqual(h.emitted[0].device, { platform: "ios", model: "Pixel 8", osVersion: "14", unit: null });
});

test("Create：重试等待中预算中止即停，不再发新的 Create", async () => {
  const h = setup();
  h.farm.createImpl = async () => { throw sdkError("ThrottlingException", 429); };
  const pending = h.block.create(CHOICE, h.budget);
  await settle();
  h.budget.abort();
  await assert.rejects(h.clock.run(pending));
  assert.equal(h.farm.ops("create").length, 1);
});

// ---- 等到 RUNNING、查状态、换台 ----

test("waitRunning：排队与准备中继续等，RUNNING 且端点可用才返回，设备单元取 instanceArn；查询偶发失败不中断等待", async () => {
  const h = setup();
  const created = await h.clock.run(h.block.create(CHOICE, h.budget));
  assert.ok(created.ok);
  if (!created.ok) return;
  const endpoint = "https://devicefarm-interactive-global.us-west-2.api.aws/remote-endpoint/TOKEN";
  const replies: Array<RemoteAccessSession | Error> = [
    { status: "PENDING_CONCURRENCY" },
    sdkError("InternalServiceException", 500),
    { status: "PREPARING" },
    { status: "RUNNING" },                                                    // 端点还没出现
    { status: "RUNNING", endpoints: { remoteDriverEndpoint: endpoint }, instanceArn: "arn:unit:7" },
  ];
  h.farm.getImpl = async () => { const r = replies.shift()!; if (r instanceof Error) throw r; return r; };
  const got = await h.clock.run(h.block.waitRunning(created.value, h.budget));
  assert.deepEqual(got, { ok: true, value: { endpoint, unit: "arn:unit:7" } });
  const gets = h.farm.ops("get");
  assert.equal(gets.length, 5);
  assert.deepEqual(gets.slice(1).map((c, i) => c.at - gets[i].at), Array(4).fill(RUNNING_POLL_INTERVAL_MS));
});

test("waitRunning：就绪之前读到 STOPPING / COMPLETED 即按会话丢失终止——消息用准备阶段那句，状态与 Device Farm 的说明只进 worker 日志，不再查询、不发 Stop", async () => {
  for (const status of ["STOPPING", "COMPLETED"]) {
    const h = setup();
    const created = await h.clock.run(h.block.create(CHOICE, h.budget));
    assert.ok(created.ok);
    if (!created.ok) return;
    h.farm.getImpl = async () => ({ status, result: "ERRORED", message: "device setup failed" });
    const got = await h.clock.run(h.block.waitRunning(created.value, h.budget));
    assert.deepEqual(got, { ok: false, termination: { errorType: "session_lost", message: SESSION_LOST_BEFORE_START_MESSAGE } }, status);
    assert.equal(h.farm.ops("get").length, 1, status);
    assert.equal(h.farm.ops("stop").length, 0, status);                 // 释放归终结
    const line = h.logs.find((l) => l.includes(created.value.arn) && l.includes(status));
    assert.ok(line && line.includes("device setup failed") && line.includes("ERRORED"), h.logs.join("\n"));
  }
});

test("waitRunning：预算中止即停（停止信号穿透查询之间的等待）", async () => {
  const h = setup();
  const created = await h.clock.run(h.block.create(CHOICE, h.budget));
  assert.ok(created.ok);
  if (!created.ok) return;
  h.farm.getImpl = async () => ({ status: "PENDING_CONCURRENCY" });
  const pending = h.block.waitRunning(created.value, h.budget);
  await settle();
  h.budget.abort();
  await assert.rejects(h.clock.run(pending));
  assert.equal(h.farm.ops("get").length, 1);
});

test("status：返回 Get 的状态值，请求带 10 秒超时；查询失败返回 null", async () => {
  const h = setup();
  h.farm.getImpl = async () => ({ status: "STOPPING" });
  assert.equal(await h.clock.run(h.block.status("arn:session:1")), "STOPPING");
  h.farm.getImpl = (_arn, signal) => hang(signal);
  const started = h.clock.t;
  assert.equal(await h.clock.run(h.block.status("arn:session:1")), null);
  assert.equal(h.clock.t - started, DEVICE_FARM_CALL_TIMEOUT_MS);
});

test("换台：被替换的会话按 Stop 规则先 Get，仍在运行即发一次 Stop（3 秒超时）、出错补查一次 Get，不重试、不等到确认；再按同一规则重新解析与 Create，两个会话都留在待清理集", async () => {
  const h = setup();
  h.farm.devicePages = [[dev("A", "18.6", "AVAILABLE")]];
  const choice1 = await h.clock.run(h.block.resolve(h.budget, null));
  assert.ok(choice1.ok);
  if (!choice1.ok) return;
  const first = await h.clock.run(h.block.create(choice1.value, h.budget));
  assert.ok(first.ok);
  if (!first.ok) return;
  h.farm.stopImpl = (_arn, signal) => hang(signal);
  const retireAt = h.clock.t;
  await h.clock.run(h.block.retire(first.value.arn));
  assert.equal(h.clock.t - retireAt, STOP_CALL_TIMEOUT_MS);
  const choice2 = await h.clock.run(h.block.resolve(h.budget, first.value));
  assert.ok(choice2.ok);
  if (!choice2.ok) return;
  const second = await h.clock.run(h.block.create(choice2.value, h.budget));
  assert.ok(second.ok);
  if (!second.ok) return;
  const ops = h.farm.calls.map((c) => c.op);
  assert.deepEqual(ops, ["listDevices", "create", "get", "stop", "get", "listDevices", "create"]);
  for (const op of ["get", "stop"]) assert.equal(h.farm.ops(op)[0].arg, first.value.arn);
  assert.equal(second.value.name, encode(RUN_ID, SCOPE_ID, 2));
  assert.deepEqual([...h.block.registry.sessions.keys()], [first.value.arn, second.value.arn]);
  assert.equal(h.block.registry.sessions.get(first.value.arn)!.stopSentAt, retireAt);
  assert.equal(h.block.registry.sessions.get(first.value.arn)!.confirmedAt, null);
  assert.equal(h.block.registry.current?.arn, second.value.arn);
  assert.ok(h.logs.some((l) => l.includes(first.value.arn)));
});

test("换台：Get 读到 STOPPING / COMPLETED 即确认，不发 Stop", async () => {
  for (const status of ["STOPPING", "COMPLETED"]) {
    const h = setup();
    const first = await h.clock.run(h.block.create(CHOICE, h.budget));
    assert.ok(first.ok);
    if (!first.ok) return;
    h.farm.getImpl = async (arn) => ({ arn, status, deviceMinutes: { total: 1.5 } });
    await h.clock.run(h.block.retire(first.value.arn));
    assert.equal(h.farm.ops("stop").length, 0, status);
    assert.equal(h.farm.ops("get").length, 1, status);
    const tracked = h.block.registry.sessions.get(first.value.arn)!;
    assert.notEqual(tracked.confirmedAt, null, status);
    assert.equal(tracked.stopSentAt, null, status);
    assert.deepEqual(tracked.providerMinutes, { total: 1.5 }, status);
  }
});

test("换台：Get 失败时照常发 Stop，Stop 的返回体已是 STOPPING 即确认、不再补查（确认只认状态）", async () => {
  const h = setup();
  const first = await h.clock.run(h.block.create(CHOICE, h.budget));
  assert.ok(first.ok);
  if (!first.ok) return;
  h.farm.getImpl = (_arn, signal) => hang(signal);
  h.farm.stopImpl = async (arn) => ({ arn, status: "STOPPING" });
  const t0 = h.clock.t;
  await h.clock.run(h.block.retire(first.value.arn));
  assert.deepEqual(h.farm.calls.slice(1).map((c) => [c.op, c.at - t0]), [["get", 0], ["stop", DEVICE_FARM_CALL_TIMEOUT_MS]]);
  assert.notEqual(h.block.registry.sessions.get(first.value.arn)!.confirmedAt, null);
});

test("换台：Get 读到运行中的状态即发 Stop，返回体为 STOPPING 时确认", async () => {
  const h = setup();
  const first = await h.clock.run(h.block.create(CHOICE, h.budget));
  assert.ok(first.ok);
  if (!first.ok) return;
  h.farm.stopImpl = async (arn) => ({ arn, status: "STOPPING" });
  await h.clock.run(h.block.retire(first.value.arn));
  assert.deepEqual(h.farm.calls.slice(1).map((c) => c.op), ["get", "stop"]);
  assert.notEqual(h.block.registry.sessions.get(first.value.arn)!.confirmedAt, null);
});

test("换台：Stop 报错或返回体不是 STOPPING / COMPLETED 时补查一次 Get，读到 COMPLETED 即确认；补查仍在运行则留给收尾，不再发 Stop", async () => {
  const stops: Array<() => Promise<RemoteAccessSession>> = [
    async () => { throw sdkError("InternalServiceException", 500); },
    async () => ({ status: "RUNNING" }),
  ];
  for (const stop of stops) {
    for (const [after, confirmed] of [["COMPLETED", true], ["RUNNING", false]] as const) {
      const h = setup();
      const first = await h.clock.run(h.block.create(CHOICE, h.budget));
      assert.ok(first.ok);
      if (!first.ok) return;
      const statuses = ["RUNNING", after];
      h.farm.getImpl = async (arn) => ({ arn, status: statuses.shift() });
      h.farm.stopImpl = stop;
      await h.clock.run(h.block.retire(first.value.arn));
      assert.deepEqual(h.farm.calls.slice(1).map((c) => c.op), ["get", "stop", "get"], after);
      assert.equal(h.block.registry.sessions.get(first.value.arn)!.confirmedAt !== null, confirmed, after);
      if (!confirmed) assert.ok(h.logs.some((l) => l.includes(first.value.arn) && l.includes("收尾")), h.logs.join("\n"));
    }
  }
});

// ---- 构造 ----

test("构造：缺 RUN_ID 时同步报错（会话名不能缺本次运行的编号）", () => {
  const saved = process.env[RUN_ID_ENV];
  process.env[RUN_ID_ENV] = "run-from-process";  // 进程 env 有值也不顶替：会话块只读部件环境的 processEnv
  try {
    const clock = new FakeClock();
    const env: DevicePartsEnv = {
      job: makeJob({ osVersion: "18" }), log: () => {}, events: sessionEventSink(SCOPE_ID, async () => {}), now: clock.now,
      processEnv: {},
    };
    assert.throws(() => createDeviceFarmSessions(env, { api: new FakeFarm(clock).api, timers: clock.timers }), new RegExp(RUN_ID_ENV));
  } finally {
    if (saved === undefined) delete process.env[RUN_ID_ENV]; else process.env[RUN_ID_ENV] = saved;
  }
});

// ---- 错误归类 ----

test("调用失败的归类：没有 HTTP 响应或响应体没读完为结果未知，限流与服务端错误可重试，其余 4xx 为明确拒绝", () => {
  assert.equal(classifyCallFailure(timeoutReason()), "unknown");
  assert.equal(classifyCallFailure(connectionReset()), "unknown");
  // 响应头已到（SDK 把 200 写进 $metadata）而响应体没读完：服务端可能已经建好了会话
  assert.equal(classifyCallFailure(Object.assign(new Error("aborted"), { name: "AbortError", $metadata: { httpStatusCode: 200 } })), "unknown");
  assert.equal(classifyCallFailure(Object.assign(connectionReset(), { $metadata: { httpStatusCode: 200 } })), "unknown");
  assert.equal(classifyCallFailure(sdkError("ThrottlingException", 400)), "retryable");
  assert.equal(classifyCallFailure(sdkError("LimitExceededException", 400)), "retryable");
  assert.equal(classifyCallFailure(sdkError("TooManyRequestsException", 429)), "retryable");
  assert.equal(classifyCallFailure(sdkError("InternalServiceException", 500)), "retryable");
  assert.equal(classifyCallFailure(sdkError("ServiceUnavailable", 503)), "retryable");
  assert.equal(classifyCallFailure(sdkError("ArgumentException", 400)), "definitive");
  assert.equal(classifyCallFailure(sdkError("NotFoundException", 400)), "definitive");
  assert.equal(classifyCallFailure(sdkError("AccessDeniedException", 400)), "definitive");
  assert.equal(classifyCallFailure(Object.assign(new Error("no creds"), { name: "CredentialsProviderError" })), "definitive");
});

// ---- 真的 DeviceFarmClient，网络层换成本地处理器 ----

interface SeenRequest { hostname: string; target: string; body: Record<string, unknown>; abortSignal: unknown }

function offlineHandler(seen: SeenRequest[], reply: (target: string) => { status: number; body: unknown }) {
  return {
    handle: async (req: { hostname: string; headers: Record<string, string>; body?: Uint8Array | string }, opts?: { abortSignal?: unknown }) => {
      const target = req.headers["x-amz-target"] ?? req.headers["X-Amz-Target"] ?? "";
      // JSON 协议的请求体是字节数组：按字节解码，不调字符串方法。
      const text = req.body === undefined ? "" : typeof req.body === "string" ? req.body : new TextDecoder().decode(req.body);
      seen.push({ hostname: req.hostname, target, body: text ? JSON.parse(text) : {}, abortSignal: opts?.abortSignal });
      const r = reply(target);
      return {
        response: {
          statusCode: r.status,
          headers: { "content-type": "application/x-amz-json-1.1" },
          body: Readable.from([Buffer.from(JSON.stringify(r.body))]),
        },
      };
    },
  };
}

const FAKE_CREDS = { accessKeyId: "AKIDEXAMPLE", secretAccessKey: "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY" };

test("Device Farm 客户端：区域固定 us-west-2，五种调用的命令与参数形态，每次调用都把中止信号交给网络层", async () => {
  assert.equal(DEVICE_FARM_REGION, "us-west-2");
  const seen: SeenRequest[] = [];
  const api = deviceFarmApi({
    requestHandler: offlineHandler(seen, (target) => {
      if (target.endsWith("ListDevices")) return { status: 200, body: { devices: [{ arn: "arn:d", os: "18.6" }], nextToken: "n2" } };
      if (target.endsWith("ListRemoteAccessSessions")) return { status: 200, body: { remoteAccessSessions: [{ arn: "arn:s", name: "x" }] } };
      return { status: 200, body: { remoteAccessSession: { arn: "arn:s", status: "STOPPING" } } };
    }) as never,
    credentials: FAKE_CREDS,
  });
  const signal = AbortSignal.timeout(60_000);
  assert.deepEqual(await api.listDevices("n1", signal), { devices: [{ arn: "arn:d", os: "18.6" }], nextToken: "n2" });
  assert.equal((await api.createRemoteAccessSession({ projectArn: PROJECT, deviceArn: "arn:d", name: "gherkai:r:h:1:s", billingMethod: "UNMETERED" }, signal))?.arn, "arn:s");
  assert.equal((await api.getRemoteAccessSession("arn:s", signal))?.status, "STOPPING");
  assert.equal((await api.stopRemoteAccessSession("arn:s", signal))?.status, "STOPPING");
  assert.deepEqual(await api.listRemoteAccessSessions(PROJECT, "t1", signal), { remoteAccessSessions: [{ arn: "arn:s", name: "x" }], nextToken: undefined });
  assert.deepEqual(seen.map((s) => s.target.split(".").pop()), [
    "ListDevices", "CreateRemoteAccessSession", "GetRemoteAccessSession", "StopRemoteAccessSession", "ListRemoteAccessSessions",
  ]);
  for (const s of seen) {
    assert.equal(s.hostname, "devicefarm.us-west-2.amazonaws.com");
    assert.ok(s.abortSignal, "每次调用都带中止信号");
  }
  assert.deepEqual(seen[0].body, { nextToken: "n1" });
  assert.deepEqual(seen[1].body, { projectArn: PROJECT, deviceArn: "arn:d", name: "gherkai:r:h:1:s", configuration: { billingMethod: "UNMETERED" } });
  assert.deepEqual(seen[2].body, { arn: "arn:s" });
  assert.deepEqual(seen[3].body, { arn: "arn:s" });
  assert.deepEqual(seen[4].body, { arn: PROJECT, nextToken: "t1" });
});

test("Device Farm 客户端：只尝试一次（服务端 500 不在 SDK 内重试），错误带状态码供归类", async () => {
  const seen: SeenRequest[] = [];
  const api = deviceFarmApi({
    requestHandler: offlineHandler(seen, () => ({ status: 500, body: { __type: "InternalServiceException", message: "boom" } })) as never,
    credentials: FAKE_CREDS,
  });
  const err = await api.getRemoteAccessSession("arn:s", AbortSignal.timeout(60_000)).then(() => null, (e: unknown) => e);
  assert.ok(err);
  assert.equal(seen.length, 1);
  assert.equal(classifyCallFailure(err), "retryable");

  const rejected: SeenRequest[] = [];
  const api2 = deviceFarmApi({
    requestHandler: offlineHandler(rejected, () => ({ status: 400, body: { __type: "ArgumentException", message: "Invalid parameter RemoteAccessSession" } })) as never,
    credentials: FAKE_CREDS,
  });
  const err2 = await api2.stopRemoteAccessSession("arn:s", AbortSignal.timeout(60_000)).then(() => null, (e: unknown) => e);
  assert.equal((err2 as { name?: string }).name, "ArgumentException");
  assert.equal(classifyCallFailure(err2), "definitive");
  assert.equal(rejected.length, 1);
});

/** 响应头为 200、响应体写到一半连接即被重置的网络层。 */
function truncatedBodyHandler(seen: string[]) {
  return {
    handle: async (req: { headers: Record<string, string> }) => {
      seen.push(req.headers["x-amz-target"] ?? req.headers["X-Amz-Target"] ?? "");
      const body = new PassThrough();
      body.write('{"remoteAccessSession":{"arn":"arn:aws:devicefarm:us-west-2:123456789012:session:p/r/0');
      setImmediate(() => body.destroy(connectionReset()));
      return { response: { statusCode: 200, headers: { "content-type": "application/x-amz-json-1.1" }, body } };
    },
  };
}

/** 按真实时间轮询，直到条件成立（真的 SDK 走真实 I/O，虚拟时钟推不动它）。 */
async function waitUntil(cond: () => boolean, limitMs = 5_000): Promise<void> {
  const end = Date.now() + limitMs;
  while (!cond()) {
    if (Date.now() > end) throw new Error("等待条件超时");
    await new Promise((r) => setTimeout(r, 5));
  }
}

test("Device Farm 客户端：Create 收到 200 响应头后读响应体时连接中断，错误带 200 状态码、归结果未知，这次尝试记为待核", async () => {
  const seen: string[] = [];
  const api = deviceFarmApi({ requestHandler: truncatedBodyHandler(seen) as never, credentials: FAKE_CREDS });
  const input = { projectArn: PROJECT, deviceArn: "arn:d", name: "gherkai:r:h:1:s", billingMethod: "METERED" };
  const err = await api.createRemoteAccessSession(input, AbortSignal.timeout(60_000)).then(() => null, (e: unknown) => e);
  assert.ok(err);
  assert.equal((err as { $metadata?: { httpStatusCode?: number } }).$metadata?.httpStatusCode, 200);
  assert.equal(classifyCallFailure(err), "unknown");
  assert.equal(seen.length, 1);

  const h = setup();
  const block = createDeviceFarmSessions(h.env, {
    api: deviceFarmApi({ requestHandler: truncatedBodyHandler([]) as never, credentials: FAKE_CREDS }), timers: h.clock.timers, runId: RUN_ID,
  });
  const creating = block.create(CHOICE, h.budget).then(() => null, (e: unknown) => e);
  await waitUntil(() => block.registry.pending.size > 0);
  h.budget.abort();
  assert.ok((await h.clock.run(creating)) instanceof Error);
  assert.deepEqual([...block.registry.pending.keys()], [encode(RUN_ID, SCOPE_ID, 1)]);
  assert.equal(block.registry.sessions.size, 0);
  assert.equal(h.emitted.length, 0);
});
