// 应用启停（ADR 0052 决策 3 的「应用启停」块；ADR 0051 决策 9、14）：应用目标在获取期的三件事与句柄上下文的 app.restart()。
//
// 获取期按固定次序调用（编排归设备侧接缝实现，本模块只给原语与判定）：
//   1. 建会话之前：对安装包的 S3 键做存在性检查（checkAppObject）。404 与 403 都记 precheck_failed、消息不同（404 提示重新提交，
//      403 说明是权限问题）。它排在 CreateRemoteAccessSession 之前，缺包或无权时零会话费用退出。检查同时确定应用桶所在的区域：
//      HeadObject 先按 worker 运行区域的客户端发出，桶在别的区域时 S3 回 301、响应头 x-amz-bucket-region 给出真实区域（实测，同区域
//      的 200 响应不带这个头），换到该区域的客户端重做一次再判 404 / 403；只跟随一次重定向。
//   2. newSession 之前：对同一个键按桶所在区域预签名（presignAppObject），交给 `appium:app`；有效期取 limits 的 APP_PRESIGN_EXPIRES_S，
//      只需覆盖 newSession 期间的下载。预签名地址绑定区域（按错区域签的地址 S3 回 301，Device Farm 只报文件不存在）。预签名地址是
//      凭证（签名在查询串里），只进能力集，不进事件、日志与诊断；经 WebdriverIO 错误文本外泄的那条路由 wdio-log 的掩码与 redactSecrets
//      盖住（ADR 0051 决策 11）。
//   3. newSession 之后：显式 activateApp 并采样应用状态（launchApp），任一次回到「未运行」即判启动即自退，记 precheck_failed
//      （ADR 0051 决策 14：不做任何规避）。启动与采样接收获取预算的中止信号，预算到期或进入终结之后不再发命令。
// 句柄上下文（ADR 0050 决策 2）的 app.restart() 由 appHandle 给出：terminate、activate、启动采样三个原语依次执行，采样到自退抛出
// 带 engine_error 归类标记的异常（这时是 step 级失败，不是 precheck_failed）。
//
// 归类的边界：本模块只做 ADR 写明的判定（404、403、自退）。其余失败——HeadObject 的其它状态码与网络错误、activateApp 或采样命令
// 本身报错——原样抛给调用方，由它按会话状态与所在阶段归类（ADR 0051 决策 4「会话丢失的判定靠查状态」）；本模块不查会话状态。
// restart() 的命令由调用方传入的 driver 发出：设备侧接缝传命令守卫代理，命令受执行令牌约束，守卫挂在异常上的归类原样传出。
//
// 依赖：S3 客户端沿用 lib/artifact-upload.mts 的构造（首个客户端的 region 取 AWS_REGION，即后端所在区域，不是 Device Farm 的
// us-west-2，ADR 0051 决策 10；桶在别的区域时按 301 给出的区域再建一个；maxAttempts 为 1，不设单次超时）。存在性检查与预签名的
// 上界不在本模块：S3 SDK 在发出请求之前先等凭据，传给 HeadObject 的截止信号对这一段不起作用、预签名不接受信号，所以由调用方
// 在等待结果时同时等待获取预算的截止信号，到期即停止等待（ADR 0051 决策 2「安装包准备的上界」）；传给 SDK 的信号只作尽力取消。
// 应用状态的三条命令是 Appium 的跨平台端点（activate_app、terminate_app、app_state），不是 `mobile:` 扩展命令，两个平台写法相同，
// 不需要经驱动适配器。
import { GetObjectCommand, HeadObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import type { Browser } from "webdriverio";
import { attachClassification, type ScopeTermination } from "../worker/surface.mjs";
import type { WebdriverApp } from "../worker/deterministic.mjs";
import { APP_PRESIGN_EXPIRES_S, LAUNCH_SAMPLE_COUNT, LAUNCH_SAMPLE_INTERVAL_MS } from "./limits.mjs";
import { defaultSleep, type Sleep } from "./sleep.mjs";

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

/** 一次存在性检查的结果：对象的判定，以及应用桶所在的区域（预签名按它签）。redirected 为真表示桶不在 worker 的运行区域、
 *  区域由 S3 的 301 响应头给出（ADR 0051 决策 9）。 */
export interface AppObjectHead {
  presence: AppObjectPresence;
  region: string;
  redirected: boolean;
}

/** 安装包存储的 I/O 面：设备侧接缝与测试各自注入，缺省实现是 s3AppObjectStore。 */
export interface AppObjectStore {
  /** 检查安装包是否存在并确定桶所在的区域，区域重定向至多跟随一次。404 与 403 返回判定，无法确定区域时抛出区域错误，其余失败原样
   *  抛出。abortSignal 是调用方的截止信号（获取预算），交给每次 HeadObject 以尽力取消在途的请求；它不是上界：等凭据的一段不响应
   *  中止，调用可能在信号中止之后仍不返回，上界是调用方对同一信号的等待（见模块头「依赖」）。 */
  head(loc: AppObjectLocation, abortSignal: AbortSignal): Promise<AppObjectHead>;
  /** 对安装包的 GetObject 按给定区域预签名，返回带签名的 https 地址；本地计算、不发请求（凭证解析除外）。不接受截止信号，凭证解析
   *  卡住时一直不返回，上界由调用方的等待给出（见模块头「依赖」）。 */
  presign(loc: AppObjectLocation, expiresS: number, region: string): Promise<string>;
}

/** 存在性检查的结论：放行（带桶所在区域与是否经过重定向），或 precheck_failed 的 scope 级终止。 */
export type AppObjectCheck =
  | { ok: true; region: string; redirected: boolean }
  | { ok: false; termination: ScopeTermination };

/** 建会话前的存在性检查：对象存在时放行并给出桶所在区域；404 与 403 返回 precheck_failed 的 scope 级终止（消息不同）；其余失败原样抛出。
 *  调用方在信号中止之后不再采信它的结果（迟到的 404 / 403 不改判，见模块头「依赖」）。 */
export async function checkAppObject(
  store: AppObjectStore, loc: AppObjectLocation, abortSignal: AbortSignal,
): Promise<AppObjectCheck> {
  const head = await store.head(loc, abortSignal);
  if (head.presence === "missing") return { ok: false, termination: { errorType: "precheck_failed", message: APP_OBJECT_MISSING_MESSAGE } };
  if (head.presence === "forbidden") return { ok: false, termination: { errorType: "precheck_failed", message: APP_OBJECT_FORBIDDEN_MESSAGE } };
  return { ok: true, region: head.region, redirected: head.redirected };
}

/** newSession 前对安装包按桶所在区域预签名，有效期取 limits 的 APP_PRESIGN_EXPIRES_S（实施期校准值，只改那里）。 */
export function presignAppObject(store: AppObjectStore, loc: AppObjectLocation, region: string): Promise<string> {
  return store.presign(loc, APP_PRESIGN_EXPIRES_S, region);
}

/** 桶在别的区域时 S3 回 301 并以这个响应头给出真实区域（实测；同区域的 200 响应不带它）。 */
const BUCKET_REGION_HEADER = "x-amz-bucket-region";
/** 301 却没有区域头，或跟随一次之后仍被重定向：不再跟随，抛出区域无法确定的错误（接缝按未归类的准备失败处置）。 */
export const BUCKET_REGION_UNKNOWN_MESSAGE = "应用桶所在的区域无法确定：存储服务返回了重定向却没有给出可用的区域；请确认应用桶名正确、桶仍然存在后重试";

/** 缺省的安装包存储：S3。按区域各持一个客户端：首个取 AWS_REGION（按 artifact-upload 的写法惰性构造），桶在别的区域时按 301 给出的
 *  区域再建一个。client / clientFactory 只供测试注入（真实的 S3Client，网络层换成本地处理器）：client 供全部区域共用，clientFactory 按区域
 *  分别构造客户端以核对主机名的切换。 */
export function s3AppObjectStore(opts: { client?: S3Client; clientFactory?: (region: string | undefined) => S3Client } = {}): AppObjectStore {
  const clients = new Map<string, S3Client>();
  const factory = opts.clientFactory ?? (opts.client ? () => opts.client! : (region) => new S3Client({ region, maxAttempts: 1 }));
  const client_ = (region: string | undefined): S3Client => {
    const key = region ?? "";
    let c = clients.get(key);
    if (!c) { c = factory(region); clients.set(key, c); }
    return c;
  };
  // HEAD 的错误响应没有正文，错误名随 SDK 版本可能是 NotFound / Forbidden 或状态码字样；判据只取响应状态码。
  // 中止与网络错误没有响应，状态码为空，落到原样抛出。301 的区域头在错误对象所带的原始响应上。
  const headOnce = async (
    client: S3Client, loc: AppObjectLocation, abortSignal: AbortSignal,
  ): Promise<{ presence: AppObjectPresence } | { redirectTo: string | null }> => {
    try {
      await client.send(new HeadObjectCommand({ Bucket: loc.bucket, Key: loc.key }), { abortSignal });
      return { presence: "present" };
    } catch (e) {
      const err = e as { $metadata?: { httpStatusCode?: number }; $response?: { headers?: Record<string, string> } };
      const status = err?.$metadata?.httpStatusCode;
      if (status === 404) return { presence: "missing" };
      if (status === 403) return { presence: "forbidden" };
      if (status === 301) return { redirectTo: err.$response?.headers?.[BUCKET_REGION_HEADER] ?? null };
      throw e;
    }
  };
  return {
    async head(loc, abortSignal) {
      const first = client_(process.env.AWS_REGION);
      const r1 = await headOnce(first, loc, abortSignal);
      if ("presence" in r1) {
        const region = await first.config.region();
        if (!clients.has(region)) clients.set(region, first);
        return { presence: r1.presence, region, redirected: false };
      }
      if (r1.redirectTo === null) throw new Error(BUCKET_REGION_UNKNOWN_MESSAGE);
      const r2 = await headOnce(client_(r1.redirectTo), loc, abortSignal);
      if (!("presence" in r2)) throw new Error(BUCKET_REGION_UNKNOWN_MESSAGE);
      return { presence: r2.presence, region: r1.redirectTo, redirected: true };
    },
    presign: (loc, expiresS, region) => presignGetObject(client_(region), loc, expiresS),
  };
}

// 预签名由官方 `@aws-sdk/s3-request-presigner` 的 getSignedUrl 用桶所在区域的客户端生成，本包不另写请求截获与地址拼接，
// 理由见 ADR 0051 决策 9「预签名的生成」。
function presignGetObject(client: S3Client, loc: AppObjectLocation, expiresS: number): Promise<string> {
  return getSignedUrl(client, new GetObjectCommand({ Bucket: loc.bucket, Key: loc.key }), { expiresIn: expiresS });
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
  /** 采样间隔的等待，只供测试注入。第二个参数是调用方的中止信号（可能没有）；缺省实现（sleep.mts 的 defaultSleep）在信号中止时
   *  提前结束、不抛出，由采样在等待之后核对。 */
  sleep?: Sleep;
}

/** 启动后的状态采样：每隔 LAUNCH_SAMPLE_INTERVAL_MS 采一次、共 LAUNCH_SAMPLE_COUNT 次（第一次也在间隔之后，覆盖启动后的头几秒），
 *  任一次不在运行即返回 "exited" 并停止采样。「不在运行」取 NOT_RUNNING 与 NOT_INSTALLED：两者都表示应用进程不存在；后台运行
 *  （2、3）不算自退。采样命令报错原样抛出。
 *  abortSignal 是获取期的截止信号（获取预算到期或进入终结时中止）：每次等待之后、发采样命令之前核对，已中止即抛出信号的原因、
 *  不再发命令。app.restart() 的采样不传：它的命令经命令守卫发出，进入终结时执行令牌即撤销（ADR 0052 决策 6）。 */
export async function sampleLaunch(
  control: AppControl, appId: string, deps: AppTimingDeps = {}, abortSignal?: AbortSignal,
): Promise<"running" | "exited"> {
  const sleep = deps.sleep ?? defaultSleep;
  for (let i = 0; i < LAUNCH_SAMPLE_COUNT; i++) {
    await sleep(LAUNCH_SAMPLE_INTERVAL_MS, abortSignal);
    abortSignal?.throwIfAborted();
    const state = await control.queryAppState(appId);
    if (state <= APP_STATE.NOT_RUNNING) return "exited";
  }
  return "running";
}

/** 获取期的启动：newSession 之后显式 activateApp，再做启动采样。正常返回 null；自退返回 precheck_failed 的 scope 级终止。
 *  命令失败原样抛出。调用方经生命周期通道传执行实例（获取期还没有执行令牌），并传获取预算的中止信号：发 activateApp 之前、
 *  它返回之后与每次采样等待之后各核对一次，已中止即抛出信号的原因、不再发命令。在途的那条命令不被打断（WebDriver 命令不接收
 *  中止信号，它的上界是执行实例的单请求超时）。 */
export async function launchApp(
  control: AppControl, appId: string, deps: AppTimingDeps = {}, abortSignal?: AbortSignal,
): Promise<ScopeTermination | null> {
  abortSignal?.throwIfAborted();
  await control.activateApp(appId);
  abortSignal?.throwIfAborted();
  if (await sampleLaunch(control, appId, deps, abortSignal) === "exited") {
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
