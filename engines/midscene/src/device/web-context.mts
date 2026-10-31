// 网页上下文的重新定位（ADR 0052 决策 5「当前上下文的身份是动态事实，每次进入网页上下文都重新定位」；ADR 0050 决策 2 的
// withWebContext）：Appium 块的 withWebContext、设备上的导航、为 evidence 读地址，以及能力探测，都经这里列出上下文、按类别筛选、
// 确定被测页面。本模块不持有任何客户端实例，列上下文的调用由调用方传入（经哪个实例发出由调用方决定），也不缓存上下文名。
//
// 类别筛选只认属于被测对象的网页上下文：Android Chrome 的 CHROMIUM，iOS Safari 的 WEBVIEW_<数字>。原生应用会话里出现的
// WEBVIEW_chrome 与 Android 应用自身的 WEBVIEW_<包名> 都不算（应用内 WebView，拿不到被测内容的 DOM，ADR 0052 被拒方案）。
// iOS 的上下文名在数字之后可能还带一段「.页号」：真机验收中 iOS 15.8、18.6、26.3 出现的都是 WEBVIEW_<数字>.1；XCUITest 驱动也可能
// 给出不带页号的形态，两种都只指 Safari 里的页面，一并接受。
//
// 1.5 的过渡规则：只有一个候选才采用；多个候选拒绝歧义，不猜；零候选等 WEB_CONTEXT_RELIST_DELAY_MS 后再列一次，仍为零即零候选。
// 定位失败对调用方的含义各不相同（withWebContext 与设备上的导航记 step 级 engine_error；为 evidence 读地址只把 url 置空；能力探测按
// 证据性质归类），所以本模块只给出定位结果与 step 级失败的归类，不替调用方决定处置。同一路线内有界地重新定位同一目标不算
// 「失败后换路线」（ADR 0052 决策 5 末句）。
import type { Device } from "../worker/deterministic.mjs";
import { attachClassification, type StepFailure } from "../worker/surface.mjs";
import { WEB_CONTEXT_RELIST_DELAY_MS } from "./limits.mjs";

/** 原生上下文的名字（Appium 的固定取值）。 */
export const NATIVE_CONTEXT = "NATIVE_APP";

// ---- 给使用方看的消息（ADR 0039；ADR 给了原文的照原文）----

/** 多个候选：ADR 0052 决策 5 的原文。 */
export const MULTIPLE_WEB_PAGES_MESSAGE = "设备上有多个网页页面，无法确定被测页面";
/** 重新列举之后仍然零候选。 */
export const NO_WEB_PAGE_MESSAGE = "设备上没有找到被测网页页面，无法进入网页上下文；请确认浏览器仍在前台后重试";

const ANDROID_WEB_CONTEXT = "CHROMIUM";
const IOS_WEB_CONTEXT = /^WEBVIEW_[0-9]+(?:\.[0-9]+)?$/;

/** 上下文列表的字符串形态：Appium 回的是字符串数组；WebdriverIO 打开详细列表时回对象，取其 id。其余形态的项丢弃。 */
export function contextNames(raw: unknown): string[] {
  if (!Array.isArray(raw)) return [];
  const names: string[] = [];
  for (const item of raw) {
    if (typeof item === "string") names.push(item);
    else if (item !== null && typeof item === "object" && typeof (item as { id?: unknown }).id === "string") {
      names.push((item as { id: string }).id);
    }
  }
  return names;
}

/** 属于被测对象的网页上下文候选（按列出的次序）。 */
export function webContextCandidates(names: readonly string[], device: Device): string[] {
  return device === "android"
    ? names.filter((n) => n === ANDROID_WEB_CONTEXT)
    : names.filter((n) => IOS_WEB_CONTEXT.test(n));
}

/** 一次重新定位的结果：恰一个候选（可采用）、多个候选（拒绝歧义）、或重新列举之后仍为零。count 是最后一次列出的候选数，写进诊断。 */
export type WebContextLocation =
  | { kind: "one"; name: string; count: 1 }
  | { kind: "many"; count: number }
  | { kind: "none"; count: 0 };

export interface LocateDeps {
  /** 零候选之后、再列一次之前的等待；调用方可传入受截止信号约束的等待。 */
  sleep?: (ms: number) => Promise<void>;
}

const defaultSleep = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

/** 重新定位一次：列出上下文、按类别筛选；零候选等 WEB_CONTEXT_RELIST_DELAY_MS 再列一次。多个候选不再列，直接拒绝。
 *  列上下文的调用失败原样抛出（调用方按自己的规则归类）。 */
export async function locateWebContext(
  list: () => Promise<unknown>, device: Device, deps: LocateDeps = {},
): Promise<WebContextLocation> {
  const sleep = deps.sleep ?? defaultSleep;
  for (let pass = 0; pass < 2; pass++) {
    if (pass > 0) await sleep(WEB_CONTEXT_RELIST_DELAY_MS);
    const candidates = webContextCandidates(contextNames(await list()), device);
    if (candidates.length === 1) return { kind: "one", name: candidates[0]!, count: 1 };
    if (candidates.length > 1) return { kind: "many", count: candidates.length };
  }
  return { kind: "none", count: 0 };
}

/** 定位不成功时的 step 级归类（withWebContext 入口与设备上的导航用）：多候选与零候选都记 engine_error（ADR 0052 决策 5）。 */
export function locateFailure(location: Exclude<WebContextLocation, { kind: "one" }>): StepFailure {
  return { errorType: "engine_error", message: location.kind === "many" ? MULTIPLE_WEB_PAGES_MESSAGE : NO_WEB_PAGE_MESSAGE };
}

/** 带 step 级归类标记的异常，供 withWebContext 与设备上的导航抛出。 */
export function locateError(location: Exclude<WebContextLocation, { kind: "one" }>): Error {
  const failure = locateFailure(location);
  return attachClassification(new Error(failure.message), failure);
}
