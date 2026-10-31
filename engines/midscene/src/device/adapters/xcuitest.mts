// XCUITest 驱动适配器（ADR 0052 决策 4 映射表的 iOS 列；决策 5 的 DeepLink 惰性结论；决策 6 的滚动规则；ADR 0048 决策 7）。
//
// 原语与命令（命令名与参数形态由 fixtures/xcuitest.commands.json 的命令契约快照锁定，改动须显式更新快照）：
//   - 坐标单位为点，等于截图像素除以能力探测得到的比例，保留两位小数；
//   - 点击 / 长按：`mobile: tap` / `mobile: touchAndHold`，长按时长以秒传给驱动；
//   - 滚动：`mobile: swipe`，手指方向与要露出的内容方向相反，作用于整个应用窗口、没有距离参数；不用 W3C 指针拖动（iOS 26 的分页
//     视图上不翻页，决策 6）；
//   - 输入：W3C 活动元素 sendKeys（element/active 加 element/value），在哪个上下文取活动元素由能力探测定（网页上下文可用即网页，
//     否则原生）。回车、退格与清空也走这一条路：经活动元素发控制字符（回车 `\n`、退格 `\b`，清空为若干个 `\b`）。不用旧版
//     `POST /keys`，也不在多条输入路线之间试错（被拒方案）；
//   - 收起键盘：WebdriverIO 的 hideKeyboard（Appium 的跨平台端点，不是 `mobile:` 命令），不带参数，在原生上下文发出，不论输入
//     上下文是网页还是原生；
//   - 系统键：`mobile: pressButton` 只用于主屏（它只接受物理按键名）；iOS 没有系统返回键，不向模型注册返回动作；
//   - 导航：`mobile: deepLink` 带 bundleId，地址不经 shell、原样送达，成功只表示已送达且应用在前台。
//
// 只读命令：`mobile: deviceScreenInfo`（坐标比例）与 `mobile: activeAppInfo`（前台应用查询）。它们的完整命令名进只读集合，
// 能力探测与命令守卫只经本模块导出的函数与集合使用它们（决策 4）。
//
// 归类：没有映射的键名（Tab、Escape 等）记 capability_unavailable、不发命令；首次 DeepLink 遇到 WebDriverAgent「不支持打开地址」
// 记 capability_unavailable 并把这个能力否定缓存到本适配器实例，即本会话（决策 5）。只缓存能力否定：会话丢失与结果未知的标记
// 原样传出；只有标记带着守卫查到会话仍为 RUNNING 的事实、结果已知的 engine_error 可按驱动文本再归类并缓存（ADR 0051 决策 4；
// 判定见 interface.mts 的 driverTextMatchAllowed）。其它失败，包括会话状态没有确认的，原样传出、不进缓存。
import type { Browser } from "webdriverio";
import { attachClassification, type ControlItem, type Controls } from "../../worker/surface.mjs";
import {
  attrOrNull, capabilityUnavailable, driverErrorText, driverTextMatchAllowed, identifiable, keyNameKey, scanXmlElements, toControls,
  unmappedKeyMessage, type AdapterEntry, type DeviceAdapter, type Point, type PrimitiveContext, type ScrollDirection,
  type ScrollGesture,
} from "../interface.mjs";

export const XCUITEST = "XCUITest";

/** 网页目标经 DeepLink 交给的系统浏览器：与能力集里的 browserName（Safari）是同一个应用。 */
export const SAFARI_BUNDLE_ID = "com.apple.mobilesafari";

const TAP = "mobile: tap";
const TOUCH_AND_HOLD = "mobile: touchAndHold";
const SWIPE = "mobile: swipe";
const PRESS_BUTTON = "mobile: pressButton";
const DEEP_LINK = "mobile: deepLink";
const DEVICE_SCREEN_INFO = "mobile: deviceScreenInfo";
const ACTIVE_APP_INFO = "mobile: activeAppInfo";

/** 只读的 `mobile:` 命令（命令守卫只读白名单里 `mobile:` 形态的条目）。 */
export const READ_ONLY_MOBILE_COMMANDS: ReadonlySet<string> = new Set([DEVICE_SCREEN_INFO, ACTIVE_APP_INFO]);

/** Midscene 键名（比对时不分大小写）到经活动元素发出的控制字符；其余键名没有映射。 */
export const IOS_KEY_CHARACTERS: Readonly<Record<string, string>> = { enter: "\n", return: "\n", backspace: "\b" };

/** 清空输入框时一次发出的退格符个数。它是命令形态的一部分，改它须同步命令契约快照。 */
export const CLEAR_INPUT_BACKSPACES = 40;

/** 要露出的内容方向到手指轻扫方向：向下看内容时手指上滑。 */
const FINGER_DIRECTION: Readonly<Record<ScrollDirection, ScrollDirection>> = { down: "up", up: "down", left: "right", right: "left" };

// W3C 元素引用的键；旧版 JSON Wire 协议的键作后备（同一个元素 id 的两种写法，不是两条路线）。
const W3C_ELEMENT_KEY = "element-6066-11e4-a52f-4f735466cecf";
const LEGACY_ELEMENT_KEY = "ELEMENT";

// ---- 给使用方看的消息（ADR 0039；处置按 ADR 0051 决策 4 的类别表：改写为 AI 步或换设备）----

/** 设备不支持经 DeepLink 打开地址。 */
export const DEEP_LINK_UNSUPPORTED_MESSAGE = "这台设备不支持经系统打开地址，无法执行这一步；请改写为 AI 步，或换一台设备";

// WebDriverAgent 的实测报错：「The current Xcode SDK does not support opening of URLs with given application」。
const OPEN_URL_UNSUPPORTED = /does not support opening of URLs/i;

// ---- 能力探测用的只读函数 ----

/** 经 `mobile: deviceScreenInfo` 读坐标比例（点与像素之比）。返回体里没有有限的正数比例时为 null；命令本身的失败原样抛出。
 *  调用方须已在原生上下文。 */
export async function deviceScreenInfo(driver: Browser): Promise<{ scale: number | null }> {
  const info = await driver.execute(DEVICE_SCREEN_INFO) as { scale?: unknown } | null | undefined;
  const scale = info?.scale;
  return { scale: typeof scale === "number" && Number.isFinite(scale) && scale > 0 ? scale : null };
}

/** 经 `mobile: activeAppInfo` 查前台应用的 bundle id；返回体里没有时为 null，命令本身的失败原样抛出。 */
export async function activeAppInfo(driver: Browser): Promise<{ bundleId: string | null }> {
  const info = await driver.execute(ACTIVE_APP_INFO) as { bundleId?: unknown } | null | undefined;
  const bundleId = info?.bundleId;
  return { bundleId: typeof bundleId === "string" && bundleId !== "" ? bundleId : null };
}

// ---- 控件摘要 ----

/** 从 XCUITest 的原始控件树抽取控件摘要：类型取 type（没有时取标签名）、文本取 label（为空时取 value）、无障碍标识取 name；
 *  XCUITest 的控件树没有独立的 id 属性，id 恒为 null。不在屏幕上（visible 为 false）的元素与没有文本、无障碍标识的容器不计入。
 *  真机控件树的根是 AppiumAUT，它不带属性，按上一条不计入；XCUIElementTypeApplication 是它的第一个子节点，也是第一个控件。 */
export function extractIosControls(pageSource: string): Controls {
  const items: ControlItem[] = [];
  for (const el of scanXmlElements(pageSource)) {
    if (el.attrs.get("visible") === "false") continue;
    const item: ControlItem = {
      type: attrOrNull(el, "type") ?? el.tag,
      id: null,
      text: attrOrNull(el, "label") ?? attrOrNull(el, "value"),
      a11y_id: attrOrNull(el, "name"),
    };
    if (identifiable(item)) items.push(item);
  }
  return toControls(items);
}

// ---- 适配器 ----

/** 截图像素到点，保留两位小数。 */
function toPoints(v: number, scale: number): number {
  return Math.round((v / scale) * 100) / 100;
}

function elementIdOf(ref: unknown): string {
  const r = (ref ?? {}) as Record<string, unknown>;
  const id = r[W3C_ELEMENT_KEY] ?? r[LEGACY_ELEMENT_KEY];
  if (typeof id !== "string" || id === "") throw new Error("设备没有返回当前获得焦点的元素");
  return id;
}

/** 对活动元素 sendKeys：在能力探测定下的上下文里取活动元素（网页上下文经 withWebContext 进入并在结束后切回原生）。 */
async function sendKeysToActive(ctx: PrimitiveContext, text: string): Promise<void> {
  const send = async (): Promise<void> => {
    const active = await ctx.driver.getActiveElement();
    await ctx.driver.elementSendKeys(elementIdOf(active), text);
  };
  if (ctx.inputContext === "web") await ctx.withWebContext(send);
  else if (ctx.inputContext === "native") await send();
  else throw new Error("iOS 设备的输入需要能力探测给出的输入上下文");
}

export function createXcuitestAdapter(): DeviceAdapter {
  // 本会话的能力否定：设备不支持经 DeepLink 打开地址（ADR 0052 决策 5 的惰性例外）。
  let deepLinkUnsupported = false;

  return {
    automationName: XCUITEST,
    device: "ios",
    readOnlyMobileCommands: READ_ONLY_MOBILE_COMMANDS,
    systemButtons: {
      home: {
        action: { name: "IOSHomeButton", description: "Trigger the system \"home\" operation on iOS devices" },
        press: async (ctx) => { await ctx.driver.execute(PRESS_BUTTON, { name: "home" }); },
      },
      back: null,
    },

    async tap(ctx: PrimitiveContext, p: Point): Promise<void> {
      await ctx.driver.execute(TAP, { x: toPoints(p.x, ctx.scale), y: toPoints(p.y, ctx.scale) });
    },

    async longPress(ctx: PrimitiveContext, p: Point, durationMs: number): Promise<void> {
      await ctx.driver.execute(TOUCH_AND_HOLD, {
        x: toPoints(p.x, ctx.scale), y: toPoints(p.y, ctx.scale), duration: durationMs / 1000,
      });
    },

    async scroll(ctx: PrimitiveContext, g: ScrollGesture): Promise<void> {
      await ctx.driver.execute(SWIPE, { direction: FINGER_DIRECTION[g.direction] });
    },

    async typeText(ctx: PrimitiveContext, text: string): Promise<void> {
      await sendKeysToActive(ctx, text);
    },

    async keyboardPress(ctx: PrimitiveContext, keyName: string): Promise<void> {
      const ch = IOS_KEY_CHARACTERS[keyNameKey(keyName)];
      if (ch === undefined) throw capabilityUnavailable(unmappedKeyMessage(keyName));
      await sendKeysToActive(ctx, ch);
    },

    async clearInput(ctx: PrimitiveContext): Promise<void> {
      await sendKeysToActive(ctx, "\b".repeat(CLEAR_INPUT_BACKSPACES));
    },

    async hideKeyboard(ctx: PrimitiveContext): Promise<void> {
      await ctx.driver.hideKeyboard();
    },

    async deepLink(driver: Browser, address: string, appId: string | null): Promise<void> {
      if (deepLinkUnsupported) throw capabilityUnavailable(DEEP_LINK_UNSUPPORTED_MESSAGE);
      try {
        await driver.execute(DEEP_LINK, { url: address, bundleId: appId ?? SAFARI_BUNDLE_ID });
      } catch (e) {
        if (driverTextMatchAllowed(e) && OPEN_URL_UNSUPPORTED.test(driverErrorText(e))) {
          deepLinkUnsupported = true;
          throw attachClassification(e, { errorType: "capability_unavailable", message: DEEP_LINK_UNSUPPORTED_MESSAGE });
        }
        throw e;
      }
    },

    extractControls: extractIosControls,
  };
}

/** 适配器清单的一项（交给 interface.mts 的 adapterRegistry）。 */
export const xcuitestEntry: AdapterEntry = { automationName: XCUITEST, create: createXcuitestAdapter };
