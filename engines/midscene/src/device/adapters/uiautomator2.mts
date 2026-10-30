// UiAutomator2 驱动适配器（ADR 0052 决策 4 映射表的 Android 列；决策 6 的滚动规则；ADR 0048 决策 7 的 DeepLink 失败归类）。
//
// 原语与命令（命令名与参数形态由 fixtures/uiautomator2.commands.json 的命令契约快照锁定，改动须显式更新快照）：
//   - 点击 / 长按：`mobile: clickGesture` / `mobile: longClickGesture`，坐标为截图像素（Android 的比例恒为 1），时长为毫秒；
//   - 滚动：`mobile: scrollGesture`，不用 W3C 指针拖动（决策 6）；
//   - 输入：`mobile: type`，不探测、不走 W3C 路线（Android Chrome 上网页活动元素读回为空，原生活动元素指向 WebView 容器）；
//     清空为连发若干次 `mobile: pressKey` 退格键；
//   - 收起键盘：WebdriverIO 的 hideKeyboard（Appium 的跨平台端点，不是 `mobile:` 命令），不带参数；
//   - 按键与系统键：`mobile: pressKey`（回车 66、退格 67、返回 4、主屏 3 等键码），没有映射的键名记 capability_unavailable；
//   - 导航：`mobile: deepLink` 带 package。驱动经 `adb shell am start -d` 传地址，所以发命令前按 RFC 3986 校验地址字符（拦下
//     `; ' ( )` 与一切非 URI 字符，它们会让命令出错或被截断后部分执行），网页目标经同一条驱动路径传地址、同样校验。应用目标
//     命令成功后有界轮询前台包名，确认是被测应用。
//
// 归类（ADR 0051 决策 4 的类别表）：字符校验不过与「unable to resolve Intent」（只在应用目标上，即被测应用未处理该地址）记
// capability_unavailable；命令成功而前台不是被测应用记 engine_error。命令失败时会话状态由命令守卫先核对：会话丢失与结果未知的
// 标记原样传出；只有标记带着守卫查到会话仍为 RUNNING 的事实、结果已知的 engine_error 可按驱动文本再归类（ADR 0051 决策 4「仍为
// RUNNING 时才允许匹配两条实测过的驱动错误文本」；判定见 interface.mts 的 driverTextMatchAllowed）。会话状态没有确认的
// （查询失败、没经过守卫）与其余失败都原样抛出。
import type { Browser } from "webdriverio";
import { attachClassification, type ControlItem, type Controls } from "../../worker/surface.mjs";
import {
  attrOrNull, capabilityUnavailable, driverErrorText, driverTextMatchAllowed, engineFailure, identifiable, keyNameKey,
  scanXmlElements, toControls, unmappedKeyMessage, type AdapterEntry, type DeviceAdapter, type Point, type PrimitiveContext,
  type ScrollGesture,
} from "../interface.mjs";

export const UIAUTOMATOR2 = "UiAutomator2";

/** 网页目标经 DeepLink 交给的系统浏览器：与能力集里的 browserName（Chrome）是同一个应用。 */
export const CHROME_PACKAGE = "com.android.chrome";

const CLICK = "mobile: clickGesture";
const LONG_CLICK = "mobile: longClickGesture";
const SCROLL = "mobile: scrollGesture";
const TYPE = "mobile: type";
const PRESS_KEY = "mobile: pressKey";
const DEEP_LINK = "mobile: deepLink";

/** 只读的 `mobile:` 命令：Android 上前台应用查询是 Appium 的跨平台端点（getCurrentPackage），没有只读的 `mobile:` 命令。 */
export const READ_ONLY_MOBILE_COMMANDS: ReadonlySet<string> = new Set<string>();

const KEYCODE_BACK = 4;
const KEYCODE_HOME = 3;
const KEYCODE_DEL = 67;

/** Midscene 键名（比对时不分大小写）到 Android 键码。 */
export const ANDROID_KEYCODES: Readonly<Record<string, number>> = {
  enter: 66, return: 66, backspace: KEYCODE_DEL, tab: 61, escape: 111,
  arrowup: 19, arrowdown: 20, arrowleft: 21, arrowright: 22,
};

/** 清空输入框时连发的退格键次数。它是命令形态的一部分，改它须同步命令契约快照。 */
export const CLEAR_INPUT_KEY_PRESSES = 40;

/** 滚动区域：整屏宽、从屏高的 20% 处起、高为屏高的 60%（避开状态栏、地址栏与底部导航）。没有给距离时幅度取区域的一半。
 *  幅度是距离除以区域在滚动方向上的长度，不超过 1。这几项是命令形态的一部分，改它们须同步命令契约快照。 */
export const SCROLL_AREA_TOP_RATIO = 0.2;
export const SCROLL_AREA_HEIGHT_RATIO = 0.6;
export const DEFAULT_SCROLL_PERCENT = 0.5;
const MIN_SCROLL_PERCENT = 0.01;

// ---- 给使用方看的消息（ADR 0039；ADR 0048 决策 7 给了原文的照原文）----

/** 被测应用未处理该地址（「unable to resolve Intent」）。 */
export const APP_DID_NOT_HANDLE_ADDRESS_MESSAGE = "被测应用未处理该地址；请改用应用能处理的地址，或确认应用声明了这个链接";
/** DeepLink 命令成功，但前台不是被测应用。 */
export const FOREGROUND_NOT_APP_MESSAGE = "打开地址后前台不是被测应用；请改用应用能处理的地址，或确认应用声明了这个链接";

/** 地址含驱动无法原样传递的字符：给出百分号编码的改法，不做静默改写（`%28` 与 `(` 对应用的链接匹配未必等价）。 */
export function undeliverableAddressMessage(chars: readonly string[]): string {
  const list = chars.map((c) => JSON.stringify(c)).join("、");
  return `地址含有设备无法原样传递的字符 ${list}；请把这些字符改为百分号编码（例如把 ( 写成 %28）后重试`;
}

// RFC 3986 允许出现在 URI 里的字符：unreserved、gen-delims、sub-delims 与百分号编码用的 `%`。其中 `; ' ( )` 四个 sub-delims
// 经 adb shell 传递时出错，一并拦下（ADR 0048 决策 7 的实测）；其余字符（含 `+ % [ ] & = # ! * $ , ~`）实测逐字送达。
// `{ }` 实测同样逐字送达，但不在 RFC 3986 字符集内，按字符集拒收（ADR 0048 决策 7 规定发命令前按 RFC 3986 字符集校验）。
const DELIVERABLE = /^[A-Za-z0-9\-._~:/?#[\]@!$&*+,=%]$/;

/** 地址里驱动无法原样传递的字符，按出现顺序、各列一次；全部可传时为空数组。 */
export function undeliverableAddressChars(address: string): string[] {
  const bad: string[] = [];
  for (const ch of address) if (!DELIVERABLE.test(ch) && !bad.includes(ch)) bad.push(ch);
  return bad;
}

const UNRESOLVED_INTENT = /unable to resolve intent/i;

// ---- 控件摘要 ----

/** 从 UiAutomator2 的原始控件树抽取控件摘要：类型取 class（没有时取标签名）、id 取 resource-id、文本取 text、无障碍标识取
 *  content-desc；不在屏幕上（displayed 为 false）的元素与没有 id、文本、无障碍标识的容器不计入。 */
export function extractAndroidControls(pageSource: string): Controls {
  const items: ControlItem[] = [];
  for (const el of scanXmlElements(pageSource)) {
    if (el.attrs.get("displayed") === "false") continue;
    const item: ControlItem = {
      type: attrOrNull(el, "class") ?? el.tag,
      id: attrOrNull(el, "resource-id"),
      text: attrOrNull(el, "text"),
      a11y_id: attrOrNull(el, "content-desc"),
    };
    if (identifiable(item)) items.push(item);
  }
  return toControls(items);
}

// ---- 适配器 ----

export interface UiAutomator2Options {
  /** DeepLink 成功后核对前台包名的轮询：次数（含第一次，第一次不等待）与间隔。取值由装配方给出（ADR 0048 决策 7「允许短暂轮询」）。 */
  foregroundPoll: { attempts: number; intervalMs: number };
  /** 轮询间隔的等待，只供测试注入。 */
  sleep?: (ms: number) => Promise<void>;
}

const defaultSleep = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

function pressKey(ctx: PrimitiveContext, keycode: number): Promise<unknown> {
  return ctx.driver.execute(PRESS_KEY, { keycode });
}

function roundPercent(value: number): number {
  return Math.min(1, Math.max(MIN_SCROLL_PERCENT, Math.round(value * 100) / 100));
}

export function createUiAutomator2Adapter(options: UiAutomator2Options): DeviceAdapter {
  const { attempts, intervalMs } = options.foregroundPoll;
  if (!Number.isSafeInteger(attempts) || attempts < 1 || !Number.isFinite(intervalMs) || intervalMs < 0) {
    throw new Error(`foregroundPoll 须为正整数次与非负间隔，收到 ${JSON.stringify(options.foregroundPoll)}`);
  }
  const sleep = options.sleep ?? defaultSleep;

  async function awaitForeground(driver: Browser, appId: string): Promise<void> {
    for (let i = 0; i < attempts; i++) {
      if (i > 0) await sleep(intervalMs);
      if (await driver.getCurrentPackage() === appId) return;
    }
    throw engineFailure(FOREGROUND_NOT_APP_MESSAGE);
  }

  return {
    automationName: UIAUTOMATOR2,
    device: "android",
    readOnlyMobileCommands: READ_ONLY_MOBILE_COMMANDS,
    systemButtons: {
      home: {
        action: { name: "AndroidHomeButton", description: "Trigger the system \"home\" operation on Android devices" },
        press: async (ctx) => { await pressKey(ctx, KEYCODE_HOME); },
      },
      back: {
        action: { name: "AndroidBackButton", description: "Trigger the system \"back\" operation on Android devices" },
        press: async (ctx) => { await pressKey(ctx, KEYCODE_BACK); },
      },
    },

    async tap(ctx: PrimitiveContext, p: Point): Promise<void> {
      await ctx.driver.execute(CLICK, { x: Math.round(p.x), y: Math.round(p.y) });
    },

    async longPress(ctx: PrimitiveContext, p: Point, durationMs: number): Promise<void> {
      await ctx.driver.execute(LONG_CLICK, { x: Math.round(p.x), y: Math.round(p.y), duration: Math.round(durationMs) });
    },

    async scroll(ctx: PrimitiveContext, g: ScrollGesture): Promise<void> {
      const { width, height } = g.screen;
      const areaTop = Math.round(height * SCROLL_AREA_TOP_RATIO);
      const areaHeight = Math.round(height * SCROLL_AREA_HEIGHT_RATIO);
      const extent = g.direction === "up" || g.direction === "down" ? areaHeight : width;
      const percent = g.distance === null ? DEFAULT_SCROLL_PERCENT : roundPercent(g.distance / extent);
      await ctx.driver.execute(SCROLL, { left: 0, top: areaTop, width, height: areaHeight, direction: g.direction, percent });
    },

    async typeText(ctx: PrimitiveContext, text: string): Promise<void> {
      await ctx.driver.execute(TYPE, { text });
    },

    async keyboardPress(ctx: PrimitiveContext, keyName: string): Promise<void> {
      const keycode = ANDROID_KEYCODES[keyNameKey(keyName)];
      if (keycode === undefined) throw capabilityUnavailable(unmappedKeyMessage(keyName));
      await pressKey(ctx, keycode);
    },

    async clearInput(ctx: PrimitiveContext): Promise<void> {
      for (let i = 0; i < CLEAR_INPUT_KEY_PRESSES; i++) await pressKey(ctx, KEYCODE_DEL);
    },

    async hideKeyboard(ctx: PrimitiveContext): Promise<void> {
      await ctx.driver.hideKeyboard();
    },

    async deepLink(driver: Browser, address: string, appId: string | null): Promise<void> {
      const bad = undeliverableAddressChars(address);
      if (bad.length > 0) throw capabilityUnavailable(undeliverableAddressMessage(bad));
      try {
        await driver.execute(DEEP_LINK, { url: address, package: appId ?? CHROME_PACKAGE });
      } catch (e) {
        if (appId !== null && driverTextMatchAllowed(e) && UNRESOLVED_INTENT.test(driverErrorText(e))) {
          throw attachClassification(e, { errorType: "capability_unavailable", message: APP_DID_NOT_HANDLE_ADDRESS_MESSAGE });
        }
        throw e;
      }
      if (appId !== null) await awaitForeground(driver, appId);
    },

    extractControls: extractAndroidControls,
  };
}

/** 适配器清单的一项（交给 interface.mts 的 adapterRegistry）。 */
export function uiautomator2Entry(options: UiAutomator2Options): AdapterEntry {
  return { automationName: UIAUTOMATOR2, create: () => createUiAutomator2Adapter(options) };
}
