// 隧道会话预热（ADR 0051 决策 13）：worker 在第一个 scenario 之前对预热地址导航一次换到会话 cookie，并按页面的可见结果归因。
//
// 常量与组合根（runtime/gherkai_runtime/tunnel.py）、Nova worker（lib/constants.py）同值，由 engines/fixtures/tunnel-warmup.json 对拍；
// worker 只读预热地址、不感知令牌与 cookie 的值。
//
// 三种可见结果、三端同一条判据（桌面读响应状态与 document.title，设备在控件树里找正文标记）：
// - READY：就绪；
// - DENIED（预热页面脚本向校验路径请求得到 401）或 AUTH REQUIRED（令牌错，预热路径直接 401 页）：确定性拒绝，precheck_failed，不重试；
//   两种拒绝成因不同、各给一句消息（令牌被拒提示核对隧道配置，会话 cookie 未通过校验提示检查隧道与浏览器的 cookie 支持）；
// - ERROR（脚本请求失败）或预算内没有任何标记、导航本身抛出：原地重导航有界重试，耗尽后 engine_error。
// 两者都不归 network_error（ADR 0028 的分类红线），一律经 scope_done{status, errorType} 传递（ADR 0051 决策 4）——所以本模块把导航
// 异常吞在自己的重试里、以 WarmupFailure 返回，外层的建连重试域看不到它。
import { redactSecrets } from "./redact.mjs";

export const SESSION_WARMUP_URL_ENV = "GHERKAI_SESSION_WARMUP_URL";
export const EXTRA_HTTP_HEADERS_ENV = "GHERKAI_EXTRA_HTTP_HEADERS";
export const SESSION_WARMUP_KEY = "session_warmup";  // 能力自述里的布尔键（ADR 0049 决策 1）
export const WARMUP_PATH = "/.well-known/gherkai-tunnel-auth";
export const CHECK_PATH = "/.well-known/gherkai-tunnel-check";
export const TOKEN_PARAM = "gherkai_tunnel_token";
export const COOKIE_NAME = "__Host-gherkai_tunnel";
export const WARMUP_TITLES = {
  ready: "gherkai-tunnel-ready", denied: "gherkai-tunnel-denied", error: "gherkai-tunnel-error", auth_required: "gherkai-tunnel-auth-required",
} as const;
export const WARMUP_MARKERS = {
  ready: "GHERKAI TUNNEL READY", denied: "GHERKAI TUNNEL DENIED", error: "GHERKAI TUNNEL ERROR", auth_required: "GHERKAI TUNNEL AUTH REQUIRED",
} as const;
// 预热的预算：一次导航的上限、等标记的上限、原地重导航的次数（ERROR 或无标记才重试；拒绝是确定性的、不重试）
export const WARMUP_NAV_TIMEOUT_MS = 30_000;
export const WARMUP_MARKER_WAIT_MS = 10_000;
export const WARMUP_ATTEMPTS = 3;
// 产品语言的四句（两个 worker 逐字相同；ADR 0039）；两种拒绝各给一句：令牌被拒（预热路径 401 或 AUTH REQUIRED）、会话 cookie 未通过校验（DENIED）
export const INCOMPLETE_DEFINITION_MESSAGE = "后端未传递会话预热地址，部署版本可能低于命令行工具，请重新部署后再提交";
export const WARMUP_AUTH_REQUIRED_MESSAGE =
  "隧道会话预热被拒绝：访问令牌或会话 cookie 不被边缘节点接受——后端与命令行工具的隧道配置不一致，或隧道已重建；请重新提交这次运行；" +
  "仍出现时核对命令行工具与后端是否同版本";
export const WARMUP_DENIED_MESSAGE =
  "隧道会话预热被拒绝：边缘节点没有收到有效的隧道会话 cookie——浏览器可能没有保存或没有带上它，或隧道在预热期间重建；" +
  "请确认隧道仍在、浏览器允许安全 cookie，必要时换浏览器或设备后重新提交";
export const warmupErrorMessage = (attempts: number, reason: string): string =>
  `隧道会话预热未能确认就绪（已尝试 ${attempts} 次）：${reason}——隧道可能已拆除，或浏览器到隧道入口的网络不通；请确认隧道仍在后重新提交`;

const TERMINAL_TITLES = new Set<string>(Object.values(WARMUP_TITLES));

export interface WarmupFailure {
  errorType: "precheck_failed" | "engine_error";
  message: string;
}

/** 预热失败时主流程的出口（ADR 0051 决策 13、决策 5）：会话已释放之后调用；归因与 sessionId 恒经 scope_done 传递，释放失败只体现在退出码 1
 *  （桌面靠退出码让泄漏可观测），不吞掉归因、不变成 worker fatal。 */
export function warmupFailureOutcome(failure: WarmupFailure, scopeId: string, sessionId: string | null, cleanupFailed: boolean):
    { event: Record<string, unknown>; exitCode: number } {
  return {
    event: { type: "scope_done", scopeId, sessionId, status: "error", errorType: failure.errorType, message: failure.message },
    exitCode: cleanupFailed ? 1 : 0,
  };
}

/** 预热失败在 run-scope 主流程里以异常形态穿出 try（好让既有的 cleanup / 排空路径照常执行），catch 里按它发 scope_done。 */
export class WarmupFailureError extends Error {
  constructor(public readonly failure: WarmupFailure) {
    super(failure.message);
  }
}

/** 预热要用到的 Page 面：导航与读标题（Playwright Page 的子集，便于单测注 fake）。 */
export interface WarmupPage {
  goto(url: string, opts: { waitUntil: "domcontentloaded"; timeout: number }): Promise<{ status(): number } | null>;
  title(): Promise<string>;
}

export interface WarmupDeps {
  log: (line: string) => void;
  sleep?: (ms: number) => Promise<void>;
  now?: () => number;
}

function oneLine(e: unknown): string {
  const raw = e instanceof Error ? e.message : String(e);
  const first = raw.split(/\r\n|\r|\n/).find((ln) => ln.trim() !== "") ?? "";
  return [...redactSecrets(first.trim().split(/\s+/).join(" "))].slice(0, 200).join("");
}

/** 对 page 导航预热地址、等页面标题落成四个标记之一；返回 null 表示就绪，否则返回归因与产品语言的消息。 */
export async function warmupSession(page: WarmupPage, url: string, deps: WarmupDeps): Promise<WarmupFailure | null> {
  const sleep = deps.sleep ?? ((ms: number) => new Promise<void>((r) => setTimeout(r, ms)));
  const now = deps.now ?? (() => Date.now());
  let last = "没有拿到预热页面";
  for (let attempt = 0; attempt < WARMUP_ATTEMPTS; attempt++) {
    if (attempt > 0) await sleep(Math.min(2000 * attempt, 5000));
    let status: number | null = null;
    try {
      const resp = await page.goto(url, { waitUntil: "domcontentloaded", timeout: WARMUP_NAV_TIMEOUT_MS });
      status = resp ? resp.status() : null;
    } catch (e) {  // 导航失败（含网络类异常）走 ERROR 路线：有界重试、不向上抛、不进建连重试域
      last = `预热导航失败：${oneLine(e)}`;
      deps.log(`worker: tunnel warmup navigation failed (attempt ${attempt + 1}): ${last}`);
      continue;
    }
    if (status === 401) return { errorType: "precheck_failed", message: WARMUP_AUTH_REQUIRED_MESSAGE };  // 令牌错：预热路径直接 401 页
    const title = await waitForMarker(page, sleep, now);
    if (title === WARMUP_TITLES.ready) {
      await leaveWarmupPage(page, deps.log);
      return null;
    }
    if (title === WARMUP_TITLES.auth_required) return { errorType: "precheck_failed", message: WARMUP_AUTH_REQUIRED_MESSAGE };
    // 预热页已下发 cookie、校验请求仍被拒：浏览器没有保存或没有带上它，或隧道在预热期间重建
    if (title === WARMUP_TITLES.denied) return { errorType: "precheck_failed", message: WARMUP_DENIED_MESSAGE };
    last = title === WARMUP_TITLES.error ? `预热页面标记为 ${title}`
      : `预热页面在 ${WARMUP_MARKER_WAIT_MS / 1000} 秒内没有给出任何标记（响应状态 ${status ?? "未知"}，页面标题 ${title || "空"}）`;
    deps.log(`worker: tunnel warmup not ready (attempt ${attempt + 1}): ${last}`);
  }
  return { errorType: "engine_error", message: warmupErrorMessage(WARMUP_ATTEMPTS, last) };
}

/** 就绪后离开预热页到 about:blank：令牌不留在当前文档地址（确定性 step 能读 page.url()）。离开失败只记日志、不影响判定：会话已换到
 *  cookie，代价只是令牌可能留在当前地址（ADR 0051 决策 13）。 */
async function leaveWarmupPage(page: WarmupPage, log: (line: string) => void): Promise<void> {
  try {
    await page.goto("about:blank", { waitUntil: "domcontentloaded", timeout: WARMUP_NAV_TIMEOUT_MS });
  } catch (e) {
    log(`worker: tunnel warmup page could not be left: ${oneLine(e)}`);
  }
}

async function waitForMarker(page: WarmupPage, sleep: (ms: number) => Promise<void>, now: () => number): Promise<string | null> {
  const deadline = now() + WARMUP_MARKER_WAIT_MS;
  for (;;) {
    let title: string | null = null;
    try {
      title = await page.title();
    } catch {
      title = null;
    }
    if (title !== null && TERMINAL_TITLES.has(title)) return title;
    if (now() >= deadline) return title;
    await sleep(250);
  }
}
