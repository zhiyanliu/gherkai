// Device Farm 会话块（ADR 0052 决策 3 的「Device Farm 会话」；ADR 0051 决策 2、3、4、7、10）：实现 device/surface.mts 的
// DeviceFarmSessions 端口——设备解析、Create、等到 RUNNING、查状态、按 Stop 规则处理不再使用的会话（换台时被替换的、获取期按名
// 找回的）——并持有与终结块（device/finalize.mts）共享的会话登记：待清理集（建成或按名找回的会话）、待核尝试（结果未知的 Create）
// 与在途的 Create。
//
// 执行期唯一调用 Device Farm SDK 的地方，`new DeviceFarmClient` 只出现在本文件（ADR 0051 决策 10 的调用归属）：区域固定
// us-west-2（Device Farm 只在这个区域，ADR 0033「region 全可配」的唯一例外）；客户端 maxAttempts 为 1，每次调用显式带中止信号，
// 单次上界取 limits 的 Create / Get / List 10 秒、Stop 3 秒、终结期 Get 5 秒，重试一律由本块在获取预算内手写退避（超时分层表 ④）。
// SDK 收在 DeviceFarmApi 这个窄面后面：会话块与终结块只经它调用，测试注入假的实现。
//
// 几条容易做错的规则：
//   - 设备解析（决策 3）：按条件时完整分页列举，静态过滤平台、手机形态、支持远程访问与公共设备，版本族按点分段匹配；先排除
//     BUSY 与 TEMPORARY_NOT_AVAILABLE，再按版本号高、HIGHLY_AVAILABLE 优先、ARN 字典序取第一台。首轮零候选隔一个短间隔再列一次，
//     仍为零即 precheck_failed；全部繁忙才在预算内按 busyBackoffMs 退避重列，等待期间候选变空不改判。直接给 ARN 时不列举（获取
//     预算从首次 Create 起算）。设备选择读 Device Farm 设备描述的 os 与 model，是系统版本读取点护栏的显式豁免（ADR 0052 决策 8）。
//   - Create 的结果未知（决策 3）：请求超时或连接中断记为待核——没有 HTTP 响应，或响应头已到而响应体没读完（SDK 这时也在错误上
//     带状态码 200，不能据状态码判为被拒）。待核只能由按名列举命中消除：以进入核对时的待核名字为准逐页比较，同名的每个 ARN 都
//     登记进待清理集并发 session_opened(discovered)，命中的名字随之消除；没命中的名字不论列举为空还是分页没扫完都保留待核。
//     每次重试前与每条终结路径各核对一次。
//   - 获取期（重试前的核对）找回的会话不会被本次执行使用，随即按与换台相同的 Stop 规则停止，不等到终结：拖到终结，它最长会
//     计费到 Device Farm 150 分钟的会话上限。它仍留在待清理集，session_closed 归终结（每个会话恰一条）；终结核对找回的由释放
//     阶段停止。终结接手之后（获取预算中止或已进入终结）获取侧即停，不再发新的调用；接手前已发出的 Stop 不撤回，释放阶段照常
//     先 Get 再决定，必要时再发一次幂等 Stop。
//   - Create 返回即登记（ARN 进待清理集，或记为待核），在途记录随之落定；session_opened(created) 的写出在登记之后。终结阶段 1
//     等的是登记：写出慢时已登记的会话不会被重新记为待核（决策 5）。
//   - 在途的 Create 不接获取预算的信号：进入终结时预算被中止，若 Create 也随之中止，它就只能记为结果未知；终结阶段 1 要等它
//     自己返回（至多 10 秒）再登记 ARN（决策 5）。重试之间的等待、列举与查询照常接预算的信号，停止信号由此穿透。
//   - 尝试序号从 1 起，每次 Create 递增（含限流重试与换台），会话名经 session-name 的 encode 生成；同名会话可以并行创建，序号是
//     名字里唯一能区分结果未知的尝试与它的重试的部分。
//   - 状态比较一律用字符串值：SDK 的 ExecutionStatus 枚举把键名拼成了 PENDING_CONCURRNECY（值是 PENDING_CONCURRENCY）。
//   - 会话年龄的后备（到 MAX_SESSION_S 归 session_lost）由接缝按 RemoteSession.createRequestedAt 计算，本块只保证这个起点是发出
//     Create 的时刻（决策 2）；observedS 的起点则是 Create 返回或列举发现的时刻（决策 7），两者不同。
import {
  CreateRemoteAccessSessionCommand, DeviceFarmClient, GetRemoteAccessSessionCommand, ListDevicesCommand,
  ListRemoteAccessSessionsCommand, StopRemoteAccessSessionCommand,
  type BillingMethod, type Device as FarmDevice, type DeviceFarmClientConfig, type RemoteAccessSession,
} from "@aws-sdk/client-device-farm";
import type { Device } from "../worker/deterministic.mjs";
import type { JobDeviceRequest } from "../lib/job-source.mjs";
import { errorText, oneLineError } from "../worker/error-text.mjs";
import type {
  AcquireBudget, DeviceChoice, DeviceFarmSessions, DevicePartsEnv, Outcome, RemoteSession, RunningSession,
} from "./surface.mjs";
import type { ProviderMinutes, SessionDeviceInfo, SessionEventSink, SessionOpenedFact } from "./device-session.mjs";
import { encode, runIdFromEnv } from "./session-name.mjs";
import { DEVICE_FARM_CALL_TIMEOUT_MS, DEVICE_RELIST_DELAY_MS, STOP_CALL_TIMEOUT_MS, busyBackoffMs } from "./limits.mjs";

// ---- Device Farm 的窄面 ----

/** Device Farm 只在这个区域（ADR 0051 决策 10）。 */
export const DEVICE_FARM_REGION = "us-west-2";

/** 本块用到的五种调用。abortSignal 必传：客户端没有缺省的请求超时，单次上界只由调用方的信号给出。 */
export interface DeviceFarmApi {
  listDevices(nextToken: string | undefined, abortSignal: AbortSignal): Promise<{ devices?: FarmDevice[]; nextToken?: string }>;
  createRemoteAccessSession(
    input: { projectArn: string; deviceArn: string; name: string; billingMethod: string }, abortSignal: AbortSignal,
  ): Promise<RemoteAccessSession | undefined>;
  getRemoteAccessSession(arn: string, abortSignal: AbortSignal): Promise<RemoteAccessSession | undefined>;
  stopRemoteAccessSession(arn: string, abortSignal: AbortSignal): Promise<RemoteAccessSession | undefined>;
  /** 列举项目里的远程访问会话（没有服务端按名过滤，调用方逐页比较会话名）。 */
  listRemoteAccessSessions(
    projectArn: string, nextToken: string | undefined, abortSignal: AbortSignal,
  ): Promise<{ remoteAccessSessions?: RemoteAccessSession[]; nextToken?: string }>;
}

/** 只供测试注入：网络层与凭证。区域与尝试次数不开放覆盖。 */
export type DeviceFarmClientOverrides = Pick<DeviceFarmClientConfig, "requestHandler" | "credentials">;

/** 缺省的 Device Farm 窄面：SDK 客户端惰性构造（构造期不做 I/O），区域固定、只尝试一次。 */
export function deviceFarmApi(overrides: DeviceFarmClientOverrides = {}): DeviceFarmApi {
  let client: DeviceFarmClient | null = null;
  const c = (): DeviceFarmClient => (client ??= new DeviceFarmClient({ ...overrides, region: DEVICE_FARM_REGION, maxAttempts: 1 }));
  return {
    async listDevices(nextToken, abortSignal) {
      const out = await c().send(new ListDevicesCommand({ nextToken }), { abortSignal });
      return { devices: out.devices ?? [], nextToken: out.nextToken };
    },
    async createRemoteAccessSession(input, abortSignal) {
      const out = await c().send(new CreateRemoteAccessSessionCommand({
        projectArn: input.projectArn, deviceArn: input.deviceArn, name: input.name,
        configuration: { billingMethod: input.billingMethod as BillingMethod },
      }), { abortSignal });
      return out.remoteAccessSession;
    },
    async getRemoteAccessSession(arn, abortSignal) {
      return (await c().send(new GetRemoteAccessSessionCommand({ arn }), { abortSignal })).remoteAccessSession;
    },
    async stopRemoteAccessSession(arn, abortSignal) {
      return (await c().send(new StopRemoteAccessSessionCommand({ arn }), { abortSignal })).remoteAccessSession;
    },
    async listRemoteAccessSessions(projectArn, nextToken, abortSignal) {
      const out = await c().send(new ListRemoteAccessSessionsCommand({ arn: projectArn, nextToken }), { abortSignal });
      return { remoteAccessSessions: out.remoteAccessSessions ?? [], nextToken: out.nextToken };
    },
  };
}

// ---- 计时 ----

/** 等待与单次调用的上界。缺省用真实计时器，测试注入虚拟时钟（与 DevicePartsEnv.now 同一时钟）。 */
export interface Timers {
  /** 等 ms 毫秒；signal 中止时以它的中止原因提前拒绝。 */
  sleep(ms: number, signal?: AbortSignal): Promise<void>;
  /** ms 毫秒后中止的信号。 */
  timeout(ms: number): AbortSignal;
}

export const realTimers: Timers = {
  sleep: (ms, signal) => new Promise<void>((resolve, reject) => {
    if (signal?.aborted) { reject(signal.reason); return; }
    const onAbort = (): void => { clearTimeout(timer); reject(signal!.reason); };
    const timer = setTimeout(() => { signal?.removeEventListener("abort", onAbort); resolve(); }, Math.max(0, ms));
    signal?.addEventListener("abort", onAbort, { once: true });
  }),
  timeout: (ms) => AbortSignal.timeout(Math.max(0, ms)),
};

/** 等远程访问会话到 RUNNING 时两次查询之间的间隔：与零候选重列共用同一个短间隔（实施期校准、真机验收后可调）。
 *  创建到 RUNNING 实测约 1 分钟、排队可达数分钟，短间隔让就绪后尽早建连，查询本身约 0.2 秒。 */
export const RUNNING_POLL_INTERVAL_MS = DEVICE_RELIST_DELAY_MS;

// ---- 状态与调用失败的归类 ----

const RUNNING = "RUNNING";
const STOPPED_STATUSES: ReadonlySet<string> = new Set(["STOPPING", "COMPLETED"]);
/** 机型可用性里要排除的两种取值（ADR 0051 决策 3）。 */
const UNAVAILABLE: ReadonlySet<string> = new Set(["BUSY", "TEMPORARY_NOT_AVAILABLE"]);

/** 确认停止只认这两个状态（ADR 0051 决策 4、5）。 */
export function isStopped(status: string | null | undefined): boolean {
  return typeof status === "string" && STOPPED_STATUSES.has(status);
}

/** 一次调用失败的性质：
 *  - unknown：没有 HTTP 响应，或响应头已到而响应体没读完、没能解析（请求超时、连接中断、被中止）。对 Create 而言结果未知、
 *    要记待核；对其余调用按可重试处理。
 *  - retryable：限流与服务端错误（429、5xx、限流类错误名）。
 *  - definitive：其余有响应的拒绝（参数无效、不存在、无权限等），重试不会变。凭证解析失败发生在请求发出之前，同样归这里。 */
export type CallFailure = "unknown" | "retryable" | "definitive";

const THROTTLING_ERROR_NAMES: ReadonlySet<string> = new Set([
  "ThrottlingException", "Throttling", "ThrottledException", "TooManyRequestsException", "RequestLimitExceeded",
  "RequestThrottled", "RequestThrottledException", "LimitExceededException",
]);

/** 权限与凭证类的拒绝：不是设备本身被拒，指定 ARN 时也不归 precheck_failed（ADR 0051 决策 3 的同步拒绝只有不存在、已下架、
 *  不支持远程访问三种）。 */
const AUTH_ERROR_NAMES: ReadonlySet<string> = new Set([
  "AccessDeniedException", "NotAuthorized", "UnrecognizedClientException", "InvalidSignatureException", "ExpiredTokenException",
  "CredentialsProviderError",
]);

export function classifyCallFailure(e: unknown): CallFailure {
  const err = (e ?? {}) as { name?: unknown; $metadata?: { httpStatusCode?: unknown } };
  const status = err.$metadata?.httpStatusCode;
  // 2xx 却抛错：响应体读到一半失败（SDK 反序列化时把响应头的状态码写进 $metadata），服务端可能已经执行了请求
  if (typeof status !== "number" || (status >= 200 && status < 300)) return err.name === "CredentialsProviderError" ? "definitive" : "unknown";
  if (status === 429 || status >= 500) return "retryable";
  return typeof err.name === "string" && THROTTLING_ERROR_NAMES.has(err.name) ? "retryable" : "definitive";
}

// ---- 版本族与设备选择（ADR 0051 决策 3）----

function segments(version: string): string[] {
  return version.trim().split(".");
}

/** 版本族匹配：配置值按点切段，设备版本的前几段逐段相等即命中——18 命中 18 与 18.x.y，18.1 不命中 18.10，写全段即精确匹配。 */
export function matchesVersionFamily(requested: string, deviceOs: string): boolean {
  const want = segments(requested);
  const have = segments(deviceOs);
  return want.length <= have.length && want.every((seg, i) => seg === have[i]);
}

/** 逐段按数值比较两个版本号（缺的段按 0，非数字段按字符串），a 高于 b 时为正。 */
export function compareVersions(a: string, b: string): number {
  const x = segments(a);
  const y = segments(b);
  for (let i = 0; i < Math.max(x.length, y.length); i++) {
    const p = x[i] ?? "0";
    const q = y[i] ?? "0";
    const np = Number(p);
    const nq = Number(q);
    const diff = Number.isFinite(np) && Number.isFinite(nq) ? np - nq : p.localeCompare(q);
    if (diff !== 0) return diff;
  }
  return 0;
}

const FARM_PLATFORM: Record<Device, string> = { android: "ANDROID", ios: "IOS" };
const PLATFORM_LABEL: Record<Device, string> = { android: "Android", ios: "iOS" };

/** 可用性的排序键：HIGHLY_AVAILABLE 优于 AVAILABLE，没有取值的排在最后。 */
function availabilityRank(availability: string | undefined): number {
  return availability === "HIGHLY_AVAILABLE" ? 0 : availability === "AVAILABLE" ? 1 : 2;
}

/** 静态过滤：平台、手机形态（固定，不开放配置）、支持远程访问、公共设备。fleetType 缺省时按公共设备处理，只排除明确的私有设备。 */
function eligible(d: FarmDevice, platform: Device): d is FarmDevice & { arn: string; os: string } {
  return typeof d.arn === "string" && typeof d.os === "string" && d.platform === FARM_PLATFORM[platform]
    && d.formFactor === "PHONE" && d.remoteAccessEnabled === true && d.fleetType !== "PRIVATE";
}

interface Selection {
  /** 通过静态过滤的设备（算最接近的可用版本用）。 */
  eligible: (FarmDevice & { arn: string; os: string })[];
  /** 其中命中版本族的。 */
  matching: (FarmDevice & { arn: string; os: string })[];
  /** 按选择规则取到的那台；全部繁忙或零候选为 null。 */
  chosen: (FarmDevice & { arn: string; os: string }) | null;
}

function select(devices: FarmDevice[], platform: Device, osVersion: string): Selection {
  const pool = devices.filter((d) => eligible(d, platform)) as Selection["eligible"];
  const matching = pool.filter((d) => matchesVersionFamily(osVersion, d.os));
  const available = matching
    .filter((d) => !UNAVAILABLE.has(d.availability ?? ""))
    .sort((a, b) => compareVersions(b.os, a.os) || availabilityRank(a.availability) - availabilityRank(b.availability)
      || (a.arn < b.arn ? -1 : a.arn > b.arn ? 1 : 0));
  return { eligible: pool, matching, chosen: available[0] ?? null };
}

/** 版本号取前三段换成一个可比较的数，算「最接近」用。 */
function versionScalar(version: string): number {
  const [a = 0, b = 0, c = 0] = segments(version).slice(0, 3).map((s) => (Number.isFinite(Number(s)) ? Number(s) : 0));
  return a * 1_000_000 + b * 1_000 + c;
}

/** 静态过滤之内、与要求的版本最接近的版本（距离相同取较高者）；一台都没有时为 null。 */
function closestVersion(pool: Selection["eligible"], osVersion: string): string | null {
  const want = versionScalar(osVersion);
  let best: string | null = null;
  for (const d of pool) {
    if (best === null) { best = d.os; continue; }
    const dist = Math.abs(versionScalar(d.os) - want);
    const bestDist = Math.abs(versionScalar(best) - want);
    if (dist < bestDist || (dist === bestDist && compareVersions(d.os, best) > 0)) best = d.os;
  }
  return best;
}

// ---- 给使用方看的消息（ADR 0039）----

/** 设备解析零候选（ADR 0051 决策 4 的类别表：precheck_failed，消息给出条件与最接近的可用版本）。 */
export function noMatchingDeviceMessage(platform: Device, osVersion: string, closest: string | null): string {
  const label = PLATFORM_LABEL[platform];
  const head = `Device Farm 的公共设备里没有系统版本为 ${osVersion} 的 ${label} 手机可以建立远程访问会话` +
    `（系统版本按点分段比较，${osVersion} 匹配 ${osVersion} 本身与以 ${osVersion}. 开头的版本）`;
  return closest === null
    ? `${head}；设备池里没有支持远程访问的 ${label} 手机，请换一个平台，或稍后重试`
    : `${head}；最接近的可用版本是 ${closest}，可以把 gherkai.toml 里 [devices.${platform}] 的 os-version 改为 "${closest}" 后重试`;
}

/** 直接给 ARN 时 Create 被同步拒绝（ADR 0051 决策 3：不存在、已下架、不支持远程访问，记 precheck_failed）。权限与凭证类的
 *  拒绝不走这里（见 AUTH_ERROR_NAMES）。ARN 可能来自配置文件或命令行选项，消息不指明来源。 */
export function deviceArnRejectedMessage(reason: string): string {
  return `Device Farm 拒绝为指定的设备建立远程访问会话：${reason}；请确认设备 ARN 正确、这台设备仍在设备池里并支持远程访问，` +
    "或换一台设备后重试";
}

// ---- 会话登记 ----

/** 待清理集里的一个会话：建成（created）或按名找回（discovered）。终结块按它发 session_closed。 */
export interface TrackedSession {
  readonly arn: string;
  readonly name: string;
  readonly origin: "created" | "discovered";
  /** observedS 的起点：Create 返回或列举发现的时刻（ADR 0051 决策 7）。 */
  readonly observedFrom: number;
  /** 第一次发出 Stop 的时刻；没发过为 null。 */
  stopSentAt: number | null;
  /** 读到 STOPPING / COMPLETED 的时刻；未确认为 null。 */
  confirmedAt: number | null;
  /** 最近一次返回体里的设备分钟原形（可缺）。 */
  providerMinutes: ProviderMinutes | null;
  /** 这个会话的 session_opened（session_closed 必须在它之后发）。 */
  opened: Promise<void>;
}

/** 在途的 Create：终结阶段 1 等它返回并登记。 */
export interface InflightCreate {
  readonly name: string;
  readonly attempt: number;
  /** Create 返回或失败、结果已登记时落定（不含 session_opened(created) 的写出）。 */
  readonly recorded: Promise<unknown>;
  /** 结果已登记之后为真：ARN 进了待清理集、这次尝试记为待核，或请求被明确拒绝。与登记在同一个同步段里置位。 */
  settled: boolean;
}

/** 会话块与终结块共享的会话登记。 */
export class SessionRegistry {
  /** 待清理集，按登记先后排列，按 ARN 去重。 */
  readonly sessions = new Map<string, TrackedSession>();
  /** 待核尝试：会话名到尝试序号。 */
  readonly pending = new Map<string, number>();
  readonly inflight = new Set<InflightCreate>();
  /** 执行所用的会话（最近建成且没有被换台替换的那个）。 */
  current: TrackedSession | null = null;
  /** 进入终结之后为真：不再发新的 Create，获取侧处理不再使用的会话（换台、按名找回）时也不再发新的调用。 */
  closed = false;
  /** 终结核对结束之后为真：晚到的 Create 结果只记日志、晚到的列举页丢弃，都不再登记、不再发事件（仍待核的尝试已按结果未知
   *  上报，释放阶段的会话清单也已取定）。 */
  attemptedFrozen = false;
  private attempts = 0;

  nextAttempt(): number {
    this.attempts += 1;
    return this.attempts;
  }

  track(entry: Omit<TrackedSession, "stopSentAt" | "confirmedAt" | "providerMinutes" | "opened">): TrackedSession {
    const existing = this.sessions.get(entry.arn);
    if (existing) return existing;
    const tracked: TrackedSession = { ...entry, stopSentAt: null, confirmedAt: null, providerMinutes: null, opened: Promise.resolve() };
    this.sessions.set(entry.arn, tracked);
    return tracked;
  }
}

/** 返回体里的设备分钟原形；没有时为 null。 */
export function minutesOf(session: RemoteAccessSession | undefined): ProviderMinutes | null {
  const m = session?.deviceMinutes;
  if (!m) return null;
  const out: ProviderMinutes = {};
  if (typeof m.total === "number") out.total = m.total;
  if (typeof m.metered === "number") out.metered = m.metered;
  if (typeof m.unmetered === "number") out.unmetered = m.unmetered;
  return Object.keys(out).length > 0 ? out : null;
}

/** 截止线：终结各阶段的绝对时刻，或获取期的外层中止信号（获取预算）；两者可以同时给。 */
export interface CallBound {
  deadline: number | null;
  outer: AbortSignal | null;
}

// ---- 会话块 ----

export interface DeviceFarmSessionOptions {
  /** 缺省为 deviceFarmApi()。 */
  api?: DeviceFarmApi;
  /** 缺省为真实计时器。 */
  timers?: Timers;
  /** 本次运行的编号；缺省读部件环境 processEnv 里的 RUN_ID（缺失即构造期报错）。 */
  runId?: string;
}

type CreateResult =
  | { kind: "created"; remote: RemoteSession }
  | { kind: "unknown"; error: unknown }
  | { kind: "rejected"; retryable: boolean; error: unknown };

/** 一次 Create 登记之后的结果，以及要等它写完才返回的 session_opened（没有要发的事件时为 null）。 */
interface RecordedCreate {
  result: CreateResult;
  opened: Promise<void> | null;
}

export class DeviceFarmSessionBlock implements DeviceFarmSessions {
  readonly registry = new SessionRegistry();
  readonly api: DeviceFarmApi;
  readonly timers: Timers;
  readonly now: () => number;
  readonly log: (line: string) => void;
  readonly events: SessionEventSink;
  private readonly runId: string;
  private readonly scopeId: string;
  private readonly platform: Device;
  private readonly request: JobDeviceRequest;

  constructor(env: DevicePartsEnv, options: DeviceFarmSessionOptions = {}) {
    if (env.job.deviceRequest === null) throw new Error("这个 job 是移动设备目标，却没有带获取设备的请求");
    this.request = env.job.deviceRequest;
    this.platform = env.job.target.device as Device;
    this.scopeId = env.job.scope.id;
    this.runId = options.runId ?? runIdFromEnv(env.processEnv);
    this.api = options.api ?? deviceFarmApi();
    this.timers = options.timers ?? realTimers;
    this.now = env.now;
    this.log = env.log;
    this.events = env.events;
  }

  // ---- DeviceFarmSessions ----

  async resolve(budget: AcquireBudget, _replacing: RemoteSession | null): Promise<Outcome<DeviceChoice>> {
    // 换台按同一规则重新解析：拒装驱动辅助包是那台设备单元的状态，同一机型的另一台单元即正常（ADR 0051 实测依据）。
    const { deviceArn, osVersion } = this.request;
    if (deviceArn) return { ok: true, value: { deviceArn, model: null, osVersion: null } };
    if (!osVersion) throw new Error("这个 job 的设备请求既没有设备 ARN，也没有系统版本");
    let pick = select(await this.listAllDevices(budget.signal), this.platform, osVersion);
    if (pick.matching.length === 0) {
      await this.timers.sleep(DEVICE_RELIST_DELAY_MS, budget.signal);
      pick = select(await this.listAllDevices(budget.signal), this.platform, osVersion);
      if (pick.matching.length === 0) {
        const message = noMatchingDeviceMessage(this.platform, osVersion, closestVersion(pick.eligible, osVersion));
        return { ok: false, termination: { errorType: "precheck_failed", message } };
      }
    }
    for (let waits = 0; pick.chosen === null; waits++) {
      if (waits === 0) this.log(`worker: 符合条件的 ${PLATFORM_LABEL[this.platform]} 设备都在使用中，等待空闲设备`);
      await this.timers.sleep(busyBackoffMs(waits), budget.signal);
      pick = select(await this.listAllDevices(budget.signal), this.platform, osVersion);
    }
    const { arn, os } = pick.chosen;
    return { ok: true, value: { deviceArn: arn, model: pick.chosen.model ?? pick.chosen.name ?? null, osVersion: os } };
  }

  async create(choice: DeviceChoice, budget: AcquireBudget): Promise<Outcome<RemoteSession>> {
    for (let waits = 0; ; waits++) {
      this.throwIfStopped(budget.signal);
      if (waits > 0 && this.registry.pending.size > 0) {
        const found = await this.reconcile({ deadline: null, outer: budget.signal });
        // 找回的会话不会被本次执行使用：随即停止，接预算的信号（预算中止即交给终结）
        await Promise.all(found.map((t) => this.stopUnused(t.arn, t, "按名找回的", budget.signal)));
        this.throwIfStopped(budget.signal);
      }
      const result = await this.sendCreate(choice);
      if (result.kind === "created") return { ok: true, value: result.remote };
      if (result.kind === "rejected" && !result.retryable) {
        if (this.request.deviceArn && !AUTH_ERROR_NAMES.has(String((result.error as { name?: unknown })?.name))) {
          const message = deviceArnRejectedMessage(errorText(result.error));
          return { ok: false, termination: { errorType: "precheck_failed", message } };
        }
        throw new Error(
          `Device Farm 拒绝建立远程访问会话：${errorText(result.error)}；若是权限或凭证问题，请核对运行凭证对这个 Device Farm 项目的权限`,
        );
      }
      if (result.kind === "rejected") this.log(`worker: 建立远程访问会话的请求被限流或服务端出错，稍后重试：${errorText(result.error)}`);
      await this.timers.sleep(busyBackoffMs(waits), budget.signal);
    }
  }

  async waitRunning(session: RemoteSession, budget: AcquireBudget): Promise<Outcome<RunningSession>> {
    for (;;) {
      this.throwIfStopped(budget.signal);
      let info: RemoteAccessSession | undefined;
      try {
        info = await this.api.getRemoteAccessSession(session.arn, this.callSignal(DEVICE_FARM_CALL_TIMEOUT_MS, budget.signal));
      } catch (e) {
        this.throwIfStopped(budget.signal);
        if (classifyCallFailure(e) === "definitive") throw new Error(`查询远程访问会话的状态时出错：${errorText(e)}`);
        info = undefined;
      }
      const status = info?.status ?? null;
      const endpoint = info?.endpoints?.remoteDriverEndpoint ?? null;
      if (status === RUNNING && endpoint) return { ok: true, value: { endpoint, unit: info?.instanceArn ?? null } };
      if (isStopped(status)) {
        const detail = info?.message ? `：${oneLineError(info.message)}` : "";
        throw new Error(`远程访问会话在就绪之前就结束了（状态 ${status}${detail}）`);
      }
      await this.timers.sleep(RUNNING_POLL_INTERVAL_MS, budget.signal);
    }
  }

  async status(arn: string): Promise<string | null> {
    try {
      return (await this.api.getRemoteAccessSession(arn, this.timers.timeout(DEVICE_FARM_CALL_TIMEOUT_MS)))?.status ?? null;
    } catch {
      return null;
    }
  }

  /** 换台时处理被替换的会话：不再作为执行所用的会话，按 Stop 规则停止（见 stopUnused）。换台只在剩余获取预算充足时发生，这里
   *  不另接预算的信号。 */
  async retire(arn: string): Promise<void> {
    if (this.registry.current?.arn === arn) this.registry.current = null;
    await this.stopUnused(arn, this.registry.sessions.get(arn) ?? null, "被替换的", null);
  }

  // ---- 终结块也用的调用 ----

  /** 按名核对待核尝试（ADR 0051 决策 3）。以进入时的待核名字为准逐页列举项目里的会话：会话名与其中某个名字整名相等即登记进
   *  待清理集并发 session_opened(discovered)，同名的每个 ARN 都登记，这个名字的待核随之消除——命中是正面证据，不论之后的页是否
   *  扫完。没命中的名字没有任何结论：列举为空不构成排除，列举出错或到截止线即停在这里，没扫完的页视为未核对，待核保留。
   *  全部名字都已命中即停止翻页：尝试序号是名字的一部分，一次尝试至多建立一个会话，再翻页只会推迟终结的释放。
   *  每一页的命中在同一个同步段里登记；终结核对结束之后才返回的页不再登记（仍待核的名字已按 attempted 上报，此时登记会多出一个
   *  不释放、不发 session_closed 的会话）。返回这次新登记的会话（它们的 session_opened 都已写出）：获取期的调用方随即按 Stop 规则
   *  停止它们，终结核对找回的由释放阶段停止。获取期的外层信号中止时抛出（已登记的会话由终结释放）。 */
  async reconcile(bound: CallBound): Promise<TrackedSession[]> {
    const wanted: ReadonlySet<string> = new Set(this.registry.pending.keys());
    const hit = new Set<string>();
    const found: TrackedSession[] = [];
    let nextToken: string | undefined;
    while (hit.size < wanted.size) {
      const signal = this.boundedSignal(DEVICE_FARM_CALL_TIMEOUT_MS, bound);
      if (signal === null) return found;
      let page: { remoteAccessSessions?: RemoteAccessSession[]; nextToken?: string };
      try {
        page = await this.api.listRemoteAccessSessions(this.request.projectArn, nextToken, signal);
      } catch (e) {
        if (bound.outer?.aborted) throw bound.outer.reason;
        this.log(`worker: 按会话名核对结果未知的建会话请求时出错，这次核对没有完成：${errorText(e)}`);
        return found;
      }
      if (this.registry.attemptedFrozen) return found;
      const opened: Promise<void>[] = [];
      for (const s of page.remoteAccessSessions ?? []) {
        if (typeof s.arn !== "string" || typeof s.name !== "string" || !wanted.has(s.name)) continue;
        hit.add(s.name);
        this.registry.pending.delete(s.name);
        if (this.registry.sessions.has(s.arn)) continue;
        const tracked = this.registry.track({ arn: s.arn, name: s.name, origin: "discovered", observedFrom: this.now() });
        this.log(`worker: 按会话名找到了一个结果未知的建会话请求所建立的远程访问会话 ${s.arn}，这个会话不会用于执行，随即停止它`);
        tracked.opened = this.emitOpened({ sessionId: s.arn, name: s.name, origin: "discovered", device: this.deviceInfo(s, null) });
        opened.push(tracked.opened);
        found.push(tracked);
      }
      await Promise.all(opened);
      nextToken = page.nextToken || undefined;
      if (nextToken === undefined) return found;
    }
    return found;
  }

  /** 查一次状态，失败或到截止线返回 undefined。 */
  async getWithin(arn: string, callMs: number, bound: CallBound): Promise<RemoteAccessSession | undefined> {
    const signal = this.boundedSignal(callMs, bound);
    if (signal === null) return undefined;
    try {
      return await this.api.getRemoteAccessSession(arn, signal);
    } catch {
      return undefined;
    }
  }

  /** 发一次 Stop：记下第一次发出的时刻与返回体里的设备分钟，返回返回体；失败原样抛出。 */
  async stopOnce(tracked: TrackedSession | null, arn: string, signal: AbortSignal): Promise<RemoteAccessSession | undefined> {
    if (tracked && tracked.stopSentAt === null) tracked.stopSentAt = this.now();
    const info = await this.api.stopRemoteAccessSession(arn, signal);
    if (tracked) tracked.providerMinutes = minutesOf(info) ?? tracked.providerMinutes;
    return info;
  }

  /** 单次调用的中止信号：取单次上界与截止线剩余时间的较小者，再并上外层信号；截止线已过返回 null。 */
  boundedSignal(callMs: number, bound: CallBound): AbortSignal | null {
    const ms = bound.deadline === null ? callMs : Math.min(callMs, bound.deadline - this.now());
    if (ms <= 0) return null;
    const own = this.timers.timeout(ms);
    return bound.outer ? AbortSignal.any([own, bound.outer]) : own;
  }

  /** 等 ms 毫秒，但不越过截止线；到线即返回 false。 */
  async sleepWithin(ms: number, deadline: number): Promise<boolean> {
    const left = deadline - this.now();
    if (left <= 0) return false;
    await this.timers.sleep(Math.min(ms, left));
    return this.now() < deadline;
  }

  // ---- 内部 ----

  /** 按 Stop 规则处理一个本次执行不再使用的会话（换台时被替换的、获取期按名找回的）。规则与终结的释放阶段是同一条（ADR 0051
   *  决策 5）：先 Get，已是 STOPPING / COMPLETED 即确认、不发 Stop；其余状态（含排队与准备中）或 Get 失败时发一次 Stop；Stop 报错
   *  或返回体不是这两个状态时补查一次 Get。不重试、不等到确认：仍未确认的由终结的释放阶段再处理，它的 session_closed 也归终结
   *  （每个会话恰一条）。Get 用获取期的单次超时，Stop 用 Stop 的单次超时，给了 outer 时并上它。
   *  终结接手之后（已进入终结，或 outer 已中止）即停：不再发新的调用、不再据返回体记确认，这个会话整个交给释放阶段，截止线之后的
   *  结论也不会被这里改写；接手前已发出的 Stop 不撤回，释放阶段仍按规则先 Get 再决定。label 只用于日志（「被替换的」「按名找回的」）。 */
  private async stopUnused(arn: string, tracked: TrackedSession | null, label: string, outer: AbortSignal | null): Promise<void> {
    const bound: CallBound = { deadline: null, outer };
    const handedOver = (): boolean => this.registry.closed || outer?.aborted === true;
    if (handedOver()) return;
    const info = await this.getWithin(arn, DEVICE_FARM_CALL_TIMEOUT_MS, bound);
    if (handedOver() || this.confirmStopped(tracked, info)) return;
    const signal = this.boundedSignal(STOP_CALL_TIMEOUT_MS, bound);
    if (signal === null) return;
    try {
      const stopped = await this.stopOnce(tracked, arn, signal);
      if (handedOver() || this.confirmStopped(tracked, stopped)) return;
    } catch (e) {
      if (handedOver()) return;
      this.log(`worker: 停止${label}远程访问会话 ${arn} 时出错，补查一次状态：${errorText(e)}`);
    }
    const again = await this.getWithin(arn, DEVICE_FARM_CALL_TIMEOUT_MS, bound);
    if (handedOver() || this.confirmStopped(tracked, again)) return;
    this.log(`worker: ${label}远程访问会话 ${arn} 还没有确认停止，收尾时会再核对一次`);
  }

  /** 发一次 Create 并登记它的结果。登记在 Create 返回或失败的那个同步段里完成（ARN 进待清理集，或这次尝试记为待核），在途记录
   *  同时落定；session_opened(created) 的写出在登记之后，本调用等它写完才返回。终结阶段 1 等的是登记：在途的 Create 返回即登记
   *  ARN（ADR 0051 决策 5），事件写出慢也不会让已登记的会话被重新记为待核。 */
  private sendCreate(choice: DeviceChoice): Promise<CreateResult> {
    const attempt = this.registry.nextAttempt();
    const name = encode(this.runId, this.scopeId, attempt);
    const requestedAt = this.now();
    const input = { projectArn: this.request.projectArn, deviceArn: choice.deviceArn, name, billingMethod: this.request.billingMethod };
    const settle = (): void => { entry.settled = true; this.registry.inflight.delete(entry); };
    // 只接自己的请求超时：进入终结时被中止的 Create 只能记为结果未知，而阶段 1 要的是等它返回。
    const recorded: Promise<RecordedCreate> = this.api.createRemoteAccessSession(input, this.timers.timeout(DEVICE_FARM_CALL_TIMEOUT_MS))
      .then(
        (session) => { settle(); return this.recordReturned(session, choice, name, attempt, requestedAt); },
        (e: unknown) => { settle(); return { result: this.recordFailed(e, name, attempt), opened: null }; },
      );
    const entry: InflightCreate = { name, attempt, recorded, settled: false };
    this.registry.inflight.add(entry);
    return recorded.then(async ({ result, opened }) => {
      if (opened !== null) await opened;
      return result;
    });
  }

  /** Create 返回之后的登记（同步，不含事件写出）。 */
  private recordReturned(
    session: RemoteAccessSession | undefined, choice: DeviceChoice, name: string, attempt: number, requestedAt: number,
  ): RecordedCreate {
    if (typeof session?.arn !== "string" || session.arn === "") {
      this.registry.pending.set(name, attempt);
      this.log(`worker: 建立远程访问会话的请求返回了，但没有带会话 ARN（会话名 ${name}），会话是否已建立未知，之后按会话名核对`);
      return { result: { kind: "unknown", error: new Error("建立远程访问会话的请求返回了，但没有带会话 ARN") }, opened: null };
    }
    if (this.registry.attemptedFrozen) {
      this.log(`worker: 建立远程访问会话的请求在等待时间之后才返回（会话名 ${name}，会话 ${session.arn}），已按结果未知上报，` +
        "请在设备控制台按这个会话名核对并手动停止");
      return { result: { kind: "unknown", error: new Error("建立远程访问会话的请求在等待时间之后才返回") }, opened: null };
    }
    const device = this.deviceInfo(session, choice);
    // 终结核对可能已按名找回了同一个会话（Create 在阶段 1 到线之后、核对结束之前返回）：沿用那条登记，不发第二条 session_opened
    const known = this.registry.sessions.has(session.arn);
    const tracked = this.registry.track({ arn: session.arn, name, origin: "created", observedFrom: this.now() });
    this.registry.pending.delete(name);
    this.registry.current = tracked;
    if (!known) tracked.opened = this.emitOpened({ sessionId: session.arn, name, origin: "created", device });
    return { result: { kind: "created", remote: { arn: session.arn, name, createRequestedAt: requestedAt, device } }, opened: tracked.opened };
  }

  /** Create 失败之后的登记：结果未知的记为待核，有响应的拒绝按是否可重试交给调用方。 */
  private recordFailed(e: unknown, name: string, attempt: number): CreateResult {
    const failure = classifyCallFailure(e);
    if (failure !== "unknown") return { kind: "rejected", retryable: failure === "retryable", error: e };
    this.registry.pending.set(name, attempt);
    this.log(`worker: 建立远程访问会话的请求没有得到完整的回应（会话名 ${name}），会话是否已建立未知，之后按会话名核对：${errorText(e)}`);
    return { kind: "unknown", error: e };
  }

  /** 返回体是 STOPPING / COMPLETED 即记为确认（时刻与设备分钟），返回是否已确认。 */
  private confirmStopped(tracked: TrackedSession | null, info: RemoteAccessSession | undefined): boolean {
    if (!isStopped(info?.status)) return false;
    if (tracked) {
      tracked.confirmedAt ??= this.now();
      tracked.providerMinutes = minutesOf(info) ?? tracked.providerMinutes;
    }
    return true;
  }

  private deviceInfo(session: RemoteAccessSession, choice: DeviceChoice | null): SessionDeviceInfo {
    return {
      platform: this.platform,
      model: choice?.model ?? session.device?.model ?? session.device?.name ?? null,
      osVersion: choice?.osVersion ?? session.device?.os ?? null,
      unit: session.instanceArn ?? null,
    };
  }

  private async emitOpened(fact: SessionOpenedFact): Promise<void> {
    try {
      await this.events.opened(fact);
    } catch (e) {
      this.log(`worker: 会话事件没能写出：${errorText(e)}`);
    }
  }

  /** 完整分页列举设备。限流、服务端错误与没有响应的失败在预算内退避后从第一页重列；明确的拒绝直接报错。 */
  private async listAllDevices(signal: AbortSignal): Promise<FarmDevice[]> {
    for (let retries = 0; ; retries++) {
      const devices: FarmDevice[] = [];
      let nextToken: string | undefined;
      try {
        do {
          const page = await this.api.listDevices(nextToken, this.callSignal(DEVICE_FARM_CALL_TIMEOUT_MS, signal));
          devices.push(...(page.devices ?? []));
          nextToken = page.nextToken || undefined;
        } while (nextToken !== undefined);
        return devices;
      } catch (e) {
        this.throwIfStopped(signal);
        if (classifyCallFailure(e) === "definitive") throw new Error(`列举 Device Farm 设备时出错：${errorText(e)}`);
        this.log(`worker: 列举 Device Farm 设备时出错，稍后重试：${errorText(e)}`);
      }
      await this.timers.sleep(busyBackoffMs(retries), signal);
    }
  }

  private callSignal(callMs: number, outer: AbortSignal): AbortSignal {
    return AbortSignal.any([this.timers.timeout(callMs), outer]);
  }

  /** 获取预算到期、进入终结即停：抛出中止原因，由接缝按预算是否到期归类。 */
  private throwIfStopped(signal: AbortSignal): void {
    if (signal.aborted) throw signal.reason ?? new Error("获取设备已停止");
    if (this.registry.closed) throw new Error("获取设备已停止：正在释放远程访问会话");
  }
}

/** Device Farm 会话块的构造（部件工厂调用）：只组装、不做 I/O；缺 RUN_ID 时同步报错。终结块用同一个实例
 *  （device/finalize.mts 的 createDeviceFinalizer），两者共享会话登记。 */
export function createDeviceFarmSessions(env: DevicePartsEnv, options: DeviceFarmSessionOptions = {}): DeviceFarmSessionBlock {
  return new DeviceFarmSessionBlock(env, options);
}
