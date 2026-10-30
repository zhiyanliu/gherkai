// 应用启停（ADR 0052 决策 3 的「应用启停」块；ADR 0051 决策 9、14）：应用目标在获取期的三件事与句柄上下文的 app.restart()。
//
// 获取期按固定次序调用（编排归设备侧接缝实现，本模块只给原语与判定）：
//   1. 建会话之前：对安装包的 S3 键做存在性检查（checkAppObject）。404 与 403 都记 precheck_failed、消息不同（404 提示重新提交，
//      403 说明是权限问题）。它排在 CreateRemoteAccessSession 之前，缺包或无权时零会话费用退出。
//   2. newSession 之前：对同一个键预签名（presignAppObject），交给 `appium:app`；有效期取 limits 的 APP_PRESIGN_EXPIRES_S，只需覆盖
//      newSession 期间的下载。预签名地址是凭证（签名在查询串里），只进能力集，不进事件、日志与诊断；经 WebdriverIO 错误文本外泄的
//      那条路由 wdio-log 的掩码与 redactSecrets 盖住（ADR 0051 决策 11）。
//   3. newSession 之后：显式 activateApp 并采样应用状态（launchApp），任一次回到「未运行」即判启动即自退，记 precheck_failed
//      （ADR 0051 决策 14：不做任何规避）。
// 句柄上下文（ADR 0050 决策 2）的 app.restart() 由 appHandle 给出：terminate、activate、启动采样三个原语依次执行，采样到自退抛出
// 带 engine_error 归类标记的异常（这时是 step 级失败，不是 precheck_failed）。
//
// 归类的边界：本模块只做 ADR 写明的判定（404、403、自退）。其余失败——HeadObject 的其它状态码与网络错误、activateApp 或采样命令
// 本身报错——原样抛给调用方，由它按会话状态与所在阶段归类（ADR 0051 决策 4「会话丢失的判定靠查状态」）；本模块不查会话状态。
// restart() 的命令由调用方传入的 driver 发出：设备侧接缝传命令守卫代理，命令受执行令牌约束，守卫挂在异常上的归类原样传出。
//
// 依赖：S3 客户端沿用 lib/artifact-upload.mts 的构造（region 取 AWS_REGION，即后端所在区域，不是 Device Farm 的 us-west-2，
// ADR 0051 决策 10；maxAttempts 为 1，单次调用的上界由调用方的截止信号给出）。应用状态的三条命令是 Appium 的跨平台端点
// （activate_app、terminate_app、app_state），不是 `mobile:` 扩展命令，两个平台写法相同，不需要经驱动适配器。
import { GetObjectCommand, HeadObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { SignatureV4 } from "@aws-sdk/signature-v4";
import { Sha256 } from "@aws-crypto/sha256-js";
import type { Browser } from "webdriverio";
import { attachClassification, type ScopeTermination } from "../worker/surface.mjs";
import type { WebdriverApp } from "../worker/deterministic.mjs";
import { APP_PRESIGN_EXPIRES_S, LAUNCH_SAMPLE_COUNT, LAUNCH_SAMPLE_INTERVAL_MS } from "./limits.mjs";

// ---- 给使用方看的消息（ADR 0039；ADR 0051 决策 4 给了原文的照原文）----

/** 存在性检查 404：ADR 0051 决策 9 的原文。 */
export const APP_OBJECT_MISSING_MESSAGE = "安装包已不在存储桶里，请重新提交";
/** 存在性检查 403：说明是权限问题（ADR 0051 决策 9）。两种后端的读取身份不同：云端是后端部署的任务角色，本机是当前凭证。 */
export const APP_OBJECT_FORBIDDEN_MESSAGE =
  "没有读取安装包的权限，存储桶拒绝了读取请求：使用云端后端时请确认后端已按与命令行工具相同的版本部署；" +
  "使用本机后端时请确认当前凭证以及应用桶的访问策略和加密密钥允许读取这个安装包。核对后重新提交";
/** 启动即自退：ADR 0051 决策 4 的原文。 */
export const APP_LAUNCH_SELF_EXIT_MESSAGE = "应用启动后立即自行退出，通常是应用带有运行环境检测；请提供关闭检测的测试包";
/** app.restart() 后自退：这一步记 error。获取期已确认过首次启动正常，所以不把原因限定为运行环境检测。 */
export const APP_RESTART_SELF_EXIT_MESSAGE =
  "应用重新启动后立即自行退出，未能回到刚启动时的界面；请检查应用是否在启动时崩溃，或带有运行环境检测";

// ---- 安装包对象：存在性检查与预签名（ADR 0051 决策 9）----

/** 安装包在 S3 上的位置：Job 应用条目的 bucket 与 key（definition 里只有带位置的完整形态，见 lib/job-source.mts 的 JobApp）。 */
export interface AppObjectLocation {
  bucket: string;
  key: string;
}

/** HeadObject 的三种可判定结果：存在、缺失（404）、无权（403）。 */
export type AppObjectPresence = "present" | "missing" | "forbidden";

/** 安装包存储的 I/O 面：设备侧接缝与测试各自注入，缺省实现是 s3AppObjectStore。 */
export interface AppObjectStore {
  /** 对安装包做一次 HeadObject。404 与 403 之外的失败原样抛出。abortSignal 是调用方的截止信号（获取预算），必传：
   *  SDK 缺省没有请求超时，不带信号的调用在退化网络下会一直挂着。 */
  head(loc: AppObjectLocation, abortSignal: AbortSignal): Promise<AppObjectPresence>;
  /** 对安装包的 GetObject 预签名，返回带签名的 https 地址；本地计算、不发请求（凭证解析除外）。 */
  presign(loc: AppObjectLocation, expiresS: number): Promise<string>;
}

/** 建会话前的存在性检查：对象存在时返回 null；404 与 403 返回 precheck_failed 的 scope 级终止（消息不同）；其余失败原样抛出。 */
export async function checkAppObject(
  store: AppObjectStore, loc: AppObjectLocation, abortSignal: AbortSignal,
): Promise<ScopeTermination | null> {
  const presence = await store.head(loc, abortSignal);
  if (presence === "missing") return { errorType: "precheck_failed", message: APP_OBJECT_MISSING_MESSAGE };
  if (presence === "forbidden") return { errorType: "precheck_failed", message: APP_OBJECT_FORBIDDEN_MESSAGE };
  return null;
}

/** newSession 前对安装包预签名，有效期取 limits 的 APP_PRESIGN_EXPIRES_S（实施期校准值，只改那里）。 */
export function presignAppObject(store: AppObjectStore, loc: AppObjectLocation): Promise<string> {
  return store.presign(loc, APP_PRESIGN_EXPIRES_S);
}

/** 缺省的安装包存储：S3。client 只供测试注入（真实的 S3Client，网络层换成本地处理器）；缺省按 artifact-upload 的写法惰性构造。 */
export function s3AppObjectStore(opts: { client?: S3Client } = {}): AppObjectStore {
  let client = opts.client;
  const client_ = (): S3Client => (client ??= new S3Client({ region: process.env.AWS_REGION, maxAttempts: 1 }));
  return {
    async head(loc, abortSignal) {
      try {
        await client_().send(new HeadObjectCommand({ Bucket: loc.bucket, Key: loc.key }), { abortSignal });
        return "present";
      } catch (e) {
        // HEAD 的错误响应没有正文，错误名随 SDK 版本可能是 NotFound / Forbidden 或状态码字样；判据只取响应状态码。
        // 中止与网络错误没有响应，状态码为空，落到原样抛出。
        const status = (e as { $metadata?: { httpStatusCode?: number } })?.$metadata?.httpStatusCode;
        if (status === 404) return "missing";
        if (status === 403) return "forbidden";
        throw e;
      }
    },
    presign: (loc, expiresS) => presignGetObject(client_(), loc, expiresS),
  };
}

// 预签名的写法：让 S3 客户端自己的中间件栈组装 GetObject 请求（终端节点规则、虚拟主机或路径形态、键的编码都由 SDK 决定），
// 在签名中间件之前截下请求，改用查询串签名，不发出请求。这与官方 `@aws-sdk/s3-request-presigner` 的 getSignedUrl 做法相同，
// 本包没有依赖那个包，签名器用本包已有的 `@aws-sdk/signature-v4`。签名形态与官方一致：载荷记 UNSIGNED-PAYLOAD（下载方的
// 请求体与内容哈希不可预知），x-amz- 前缀的请求头移进查询串，其余请求头只留 host，所以 SignedHeaders 只有 host，下载方
// （Appium 服务端）不必带任何额外请求头。在 client-s3 3.1074 上，同一签名时刻产出的地址与官方 getSignedUrl 逐字节相同；
// 升级 client-s3 后应重新与官方对拍一次。app.test.mts 另按 SigV4 规范独立复算签名值。
const PRESIGN_INTERCEPT = "gherkaiAppPresignIntercept";
const UNSIGNED_PAYLOAD = "UNSIGNED-PAYLOAD";

/** 截下来的请求（SDK 的 HttpRequest 的结构子集）。 */
interface InterceptedRequest {
  protocol: string;
  hostname: string;
  port?: number;
  path: string;
  query: Record<string, string | string[] | null>;
  headers: Record<string, string>;
}

async function presignGetObject(client: S3Client, loc: AppObjectLocation, expiresS: number): Promise<string> {
  const signer = new SignatureV4({
    service: "s3",
    region: await client.config.region(),
    credentials: client.config.credentials,
    sha256: Sha256,
    uriEscapePath: false,   // S3 的规范 URI 不做二次编码（SDK 序列化出的路径已经编码过一次）
    applyChecksum: false,
  });
  const intercept = () => async (args: { request: unknown }) => {
    const request = args.request as InterceptedRequest;
    // 请求头只留 host 与 x-amz- 前缀的项（签名时后者移进查询串，如 x-amz-checksum-mode），去掉 SDK 自己加的记账类请求头
    // （调用 id、重试计数、用户代理）：它们若进入签名，下载方必须原样带上才能通过校验。与官方预签名的取舍相同。
    const host = request.headers.host ?? (request.port ? `${request.hostname}:${request.port}` : request.hostname);
    const kept: Record<string, string> = { host };
    for (const [name, value] of Object.entries(request.headers)) {
      const lower = name.toLowerCase();
      if (lower.startsWith("x-amz-") && lower !== "x-amz-user-agent") kept[name] = value;
    }
    kept["X-Amz-Content-Sha256"] = UNSIGNED_PAYLOAD;
    request.headers = kept;
    const presigned = await signer.presign(request as never, { expiresIn: expiresS });
    return { response: {}, output: { $metadata: {}, presigned } };
  };
  const command = new GetObjectCommand({ Bucket: loc.bucket, Key: loc.key });
  const stack = client.middlewareStack.clone();
  stack.addRelativeTo(intercept as never, {
    name: PRESIGN_INTERCEPT, relation: "before", toMiddleware: "awsAuthMiddleware", override: true,
  });
  const handler = command.resolveMiddleware(stack, client.config, {});
  const { output } = (await handler({ input: command.input } as never)) as unknown as { output: { presigned: InterceptedRequest } };
  return formatUrl(output.presigned);
}

/** RFC 3986 的严格编码（与 SDK 拼查询串的规则相同）：只有 A-Z a-z 0-9 - . _ ~ 不编码。 */
function escapeQueryPart(s: string): string {
  return encodeURIComponent(s).replace(/[!'()*]/g, (c) => `%${c.charCodeAt(0).toString(16).toUpperCase()}`);
}

function formatUrl(req: InterceptedRequest): string {
  const query = Object.keys(req.query).sort().flatMap((k) => {
    const v = req.query[k];
    if (v === null) return [escapeQueryPart(k)];
    return (Array.isArray(v) ? v : [v]).map((one) => `${escapeQueryPart(k)}=${escapeQueryPart(one)}`);
  }).join("&");
  const port = req.port ? `:${req.port}` : "";
  return `${req.protocol}//${req.hostname}${port}${req.path}${query ? `?${query}` : ""}`;
}

// ---- 启动与启动采样（ADR 0051 决策 9、14）----

/** Appium app_state 的取值（两个平台同一编码）。 */
export const APP_STATE = {
  NOT_INSTALLED: 0,
  NOT_RUNNING: 1,
  BACKGROUND_SUSPENDED: 2,
  BACKGROUND: 3,
  FOREGROUND: 4,
} as const;

/** 启动与重启要用的 driver 面：WebdriverIO 客户端（或命令守卫代理）的三条应用命令。应用标识是包名或 bundle id，按 Appium 的
 *  约定以 appId 一个参数传给两个平台。 */
export interface AppControl {
  activateApp(appId: string): Promise<unknown>;
  terminateApp(appId: string): Promise<unknown>;
  queryAppState(appId: string): Promise<number>;
}

// 编译期核对：WebdriverIO 客户端满足 AppControl，设备侧接缝可以直接把执行实例或守卫代理传进来。
type _BrowserIsAppControl = Browser extends AppControl ? true : never;
const _browserIsAppControl: _BrowserIsAppControl = true;
void _browserIsAppControl;

export interface AppTimingDeps {
  /** 采样间隔的等待，只供测试注入。 */
  sleep?: (ms: number) => Promise<void>;
}

const defaultSleep = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

/** 启动后的状态采样：每隔 LAUNCH_SAMPLE_INTERVAL_MS 采一次、共 LAUNCH_SAMPLE_COUNT 次（第一次也在间隔之后，覆盖启动后的头几秒），
 *  任一次不在运行即返回 "exited" 并停止采样。「不在运行」取 NOT_RUNNING 与 NOT_INSTALLED：两者都表示应用进程不存在；后台运行
 *  （2、3）不算自退。采样命令报错原样抛出。 */
export async function sampleLaunch(control: AppControl, appId: string, deps: AppTimingDeps = {}): Promise<"running" | "exited"> {
  const sleep = deps.sleep ?? defaultSleep;
  for (let i = 0; i < LAUNCH_SAMPLE_COUNT; i++) {
    await sleep(LAUNCH_SAMPLE_INTERVAL_MS);
    const state = await control.queryAppState(appId);
    if (state <= APP_STATE.NOT_RUNNING) return "exited";
  }
  return "running";
}

/** 获取期的启动：newSession 之后显式 activateApp，再做启动采样。正常返回 null；自退返回 precheck_failed 的 scope 级终止。
 *  命令失败原样抛出。调用方经生命周期通道传执行实例（获取期还没有执行令牌）。 */
export async function launchApp(control: AppControl, appId: string, deps: AppTimingDeps = {}): Promise<ScopeTermination | null> {
  await control.activateApp(appId);
  if (await sampleLaunch(control, appId, deps) === "exited") {
    return { errorType: "precheck_failed", message: APP_LAUNCH_SELF_EXIT_MESSAGE };
  }
  return null;
}

/** ctx.app.restart() 的原语串：terminate、activate、启动采样。采样到自退抛出带 engine_error 归类标记的异常；任一命令失败原样
 *  抛出、不继续后面的原语，也不补发。 */
export async function restartApp(control: AppControl, appId: string, deps: AppTimingDeps = {}): Promise<void> {
  await control.terminateApp(appId);
  await control.activateApp(appId);
  if (await sampleLaunch(control, appId, deps) === "exited") {
    throw attachClassification(new Error(APP_RESTART_SELF_EXIT_MESSAGE), {
      errorType: "engine_error", message: APP_RESTART_SELF_EXIT_MESSAGE,
    });
  }
}

/** 句柄上下文的 app 字段（ADR 0050 决策 2，只在应用目标上有值）：只有 restart 一个方法。control 传命令守卫代理。 */
export function appHandle(control: AppControl, appId: string, deps: AppTimingDeps = {}): WebdriverApp {
  return { restart: () => restartApp(control, appId, deps) };
}
