// 界面实现与驱动适配器的公共面（ADR 0052 决策 3 的「界面实现」与「驱动适配器」两块；决策 4、6、7）。
//
// 本模块给出四样东西：
//   - DeviceAdapter：驱动适配器的完整面。它在设备侧接缝的 DriverAdapter 端口（deepLink、extractControls）之上加上界面实现要用的
//     原语、向模型注册的系统键与只读 `mobile:` 命令名集合。两个实现在 adapters/ 下（UiAutomator2 与 XCUITest），平台专属的
//     `mobile:` 命令只出现在那里（决策 4，护栏见 read-points.test.mts）；命令契约快照见 adapters/adapters.contract.test.mts。
//   - 两个适配器共用的小工具：控件树的元素扫描、带归类标记的失败、驱动错误文本的读取。本模块不 import 适配器，适配器只 import
//     本模块，没有循环依赖。
//   - adapterRegistry：按会话回报的 automationName 选一次适配器（决策 3）；适配器清单由装配方传入，每次选择得到一个新实例，
//     适配器里按会话缓存的结论（如设备不支持打开地址）因此只属于一个会话。
//   - AppiumInterface 与设备 Agent 工厂：继承 Midscene 的 AbstractInterface（决策 7）。截图在原生上下文（决策 6：step 前核对与
//     复原核对保证 AI 步开始与结束时会话都在原生上下文，所以截图前不再读当前上下文），尺寸取截图的像素尺寸；动作集只经
//     defineActionsFromInputPrimitives 定义，includeSwipe 关、系统动作显式给出（Android 返回与主屏、iOS 只有主屏）；原语全部经
//     适配器下发，命令经构造时传入的 driver（命令守卫代理）发出。收不收键盘沿用 Midscene 的决定（决策 7）：Input 动作带来的
//     autoDismissKeyboard 为 true 时，输入完成后经适配器收起键盘一次并核键盘是否仍在（这个参数的说明由本模块替换为「只在用例要求输入后
//     收起键盘时给」，给了即视为用例的要求），仍在即让动作失败；「收起键盘」动作同一口径（ADR 0052 决策 7）。
//     设备 Agent 在这里构造。
//
// 不做：按系统版本或机型分支（决策 1）——本模块与适配器都不读系统版本与机型，坐标比例与 iOS 的输入上下文是能力探测的结论，
// 由构造方传入（决策 5）；不在运行期试错换路线，每个原语只有一条路线（决策 4，被拒方案「运行期试错、失败再回落」）。
// 命令失败时的会话状态核对不在这里：经守卫代理发出的命令失败时，守卫已先查会话状态并在异常上挂好归类（ADR 0051 决策 4
// 「会话丢失的判定靠查状态」）。会话丢失与结果未知的标记原样传出；只有标记带着「守卫查到会话仍为 RUNNING」这项事实、结果已知的
// engine_error 才可按驱动文本再归类（判定见 driverTextMatchAllowed）。
import { Agent } from "@midscene/core/agent";
import {
  AbstractInterface, defineAction, defineActionsFromInputPrimitives,
  type DeviceAction, type InputPrimitives, type KeyboardInputPrimitives, type ScrollInputPrimitives, type SystemInputActionConfig,
  type SystemInputActionOptions,
} from "@midscene/core/device";
import { z, type AgentOpt } from "@midscene/core";
import type { Browser } from "webdriverio";
import { errorText } from "../worker/error-text.mjs";
import { attachClassification, readClassification, type ControlItem, type Controls } from "../worker/surface.mjs";
import type { Device } from "../worker/deterministic.mjs";
import { RESULT_UNKNOWN_MESSAGE } from "./guard.mjs";
import { CONTROLS_MAX_ITEMS } from "./limits.mjs";
import type { AdapterRegistry, AppiumSession, DriverAdapter } from "./surface.mjs";

// ---- 原语的上下文与适配器的面 ----

/** iOS 取活动元素的上下文（能力探测的结论，ADR 0052 决策 5「输入路线」）。 */
export type InputContext = "web" | "native";

/** 截图像素坐标。 */
export interface Point {
  x: number;
  y: number;
}

/** 原语下发时的会话上下文。 */
export interface PrimitiveContext {
  /** 命令守卫代理：原语的命令都经它发出（ADR 0052 决策 6）。 */
  readonly driver: Browser;
  /** 截图像素与手势坐标单位之比：iOS 为能力探测得到的比例（点等于像素除以它），Android 恒为 1。 */
  readonly scale: number;
  /** iOS 取活动元素的上下文；Android 固定用 mobile 输入命令，为 null。 */
  readonly inputContext: InputContext | null;
  /** 重新定位网页上下文、切入执行 fn、结束后切回原生上下文（即 AppiumSession.withWebContext 经守卫代理）。 */
  withWebContext<T>(fn: () => Promise<T> | T): Promise<T>;
}

export type ScrollDirection = "up" | "down" | "left" | "right";

/** 一次滚动手势。direction 是要露出的内容所在的方向（与 Midscene 的 Scroll 动作同义）；distance 为截图像素，null 时取适配器的
 *  缺省幅度；screen 是当前截图的像素尺寸。 */
export interface ScrollGesture {
  direction: ScrollDirection;
  distance: number | null;
  screen: { width: number; height: number };
}

/** 一个系统键：向模型注册的动作（名字与说明），以及按下它的原语。 */
export interface SystemButton {
  readonly action: SystemInputActionConfig;
  press(ctx: PrimitiveContext): Promise<void>;
}

/** 驱动适配器的完整面（ADR 0052 决策 4 的映射表）。在设备侧接缝的 DriverAdapter 端口之上加界面实现用的原语。 */
export interface DeviceAdapter extends DriverAdapter {
  /** 适配器对应的自动化驱动名（与会话回报的 automationName 比对时不分大小写）。 */
  readonly automationName: string;
  readonly device: Device;
  /** 只读 `mobile:` 命令的完整命令名。命令守卫的只读白名单与能力探测只用这里的名字，不自己拼 `mobile:` 命令（决策 4）。 */
  readonly readOnlyMobileCommands: ReadonlySet<string>;
  /** 向模型注册的系统键：Android 有返回与主屏，iOS 没有系统返回键（back 为 null）。 */
  readonly systemButtons: { readonly home: SystemButton; readonly back: SystemButton | null };
  tap(ctx: PrimitiveContext, p: Point): Promise<void>;
  longPress(ctx: PrimitiveContext, p: Point, durationMs: number): Promise<void>;
  scroll(ctx: PrimitiveContext, gesture: ScrollGesture): Promise<void>;
  /** 向当前获得焦点的输入框输入文本。 */
  typeText(ctx: PrimitiveContext, text: string): Promise<void>;
  /** 按一个键；没有映射的键名抛出带 capability_unavailable 标记的异常、不发命令（决策 4）。 */
  keyboardPress(ctx: PrimitiveContext, keyName: string): Promise<void>;
  /** 清空当前获得焦点的输入框。 */
  clearInput(ctx: PrimitiveContext): Promise<void>;
  /** 收起软键盘。命令失败原样抛出，失败的处置由界面实现决定。 */
  hideKeyboard(ctx: PrimitiveContext): Promise<void>;
  /** 软键盘此刻是否显示（只读命令；收起之后核一次，驱动报成功而键盘仍在的情形由此识别）。 */
  keyboardShown(ctx: PrimitiveContext): Promise<boolean>;
}

// ---- 适配器共用的小工具 ----

/** 没有映射的键名（ADR 0052 决策 4：不猜测替代路线）。 */
export function unmappedKeyMessage(keyName: string): string {
  return `这台设备上不能按下 ${JSON.stringify(keyName)} 键；请改写这一步，避免依赖这个按键`;
}

/** 键名的比对形式：去掉首尾空白、不分大小写（Midscene 给出的键名大小写不固定）。 */
export function keyNameKey(keyName: string): string {
  return keyName.trim().toLowerCase();
}

/** 新建一个带 capability_unavailable 标记的异常（发命令之前就能判定的失败）。 */
export function capabilityUnavailable(message: string): Error {
  return attachClassification(new Error(message), { errorType: "capability_unavailable", message });
}

/** 新建一个带 engine_error 标记的异常。 */
export function engineFailure(message: string): Error {
  return attachClassification(new Error(message), { errorType: "engine_error", message });
}

/** 能否按实测过的驱动错误文本再归类（并缓存由此得出的能力否定）：只有命令守卫在命令失败后查到会话仍为 RUNNING（标记带
 *  sessionRunningConfirmed）、命令结果已知（engine_error 且不是结果未知）时可以（ADR 0051 决策 4「仍为 RUNNING 时才允许匹配两条
 *  实测过的驱动错误文本」）。会话丢失与结果未知的标记原样传出。会话状态没有确认的一律不再归类：守卫查询会话状态本身失败时只挂
 *  结果已知的 engine_error、不带这项事实（ADR 0052 决策 6）；窗口已关闭的晚到失败守卫不查状态；没经过守卫的异常（生命周期通道
 *  上的命令）没有查过会话状态。 */
export function driverTextMatchAllowed(e: unknown): boolean {
  const mark = readClassification(e);
  return mark !== null && mark.errorType === "engine_error" && mark.sessionRunningConfirmed === true
    && mark.message !== RESULT_UNKNOWN_MESSAGE;
}

// cause 链的查找上限，与 worker/surface.mts 读归类标记时的上限相同，同时防环。
const MAX_CAUSE_DEPTH = 8;

/** 驱动报错的全文：异常及其 cause 链上的名字与消息，用来匹配实测过的驱动错误文本。WebdriverIO 把服务端的错误体放进 message，
 *  个别形态下 message 是对象，这里按 JSON 展开。 */
export function driverErrorText(e: unknown): string {
  const parts: string[] = [];
  let current: unknown = e;
  for (let depth = 0; depth < MAX_CAUSE_DEPTH && current !== null && current !== undefined; depth++) {
    if (typeof current !== "object") {
      parts.push(String(current));
      break;
    }
    const { name, message, cause } = current as { name?: unknown; message?: unknown; cause?: unknown };
    for (const v of [name, message]) {
      if (typeof v === "string") parts.push(v);
      else if (v !== undefined && v !== null) parts.push(JSON.stringify(v));
    }
    current = cause;
  }
  return parts.join("\n");
}

/** 控件树里的一个元素：标签名与解码后的属性。 */
export interface XmlElement {
  tag: string;
  attrs: ReadonlyMap<string, string>;
}

/** 控件树里带层级的一个元素：子元素按文档顺序。 */
export interface XmlNode extends XmlElement {
  children: XmlNode[];
}

// 控件树的词法单元：处理指令（`<?xml ...?>`）、注释、结束标签、开始标签（含自闭合）。开始标签的属性值用引号括起，值里可以出现
// 未转义的 `>`（XML 允许），所以属性逐个匹配、不用 `[^>]*`。文本节点不是单元：两个驱动的控件树都没有文本节点。
const XML_TOKEN = /<\?[\s\S]*?\?>|<!--[\s\S]*?-->|<\/([A-Za-z_][\w.:-]*)\s*>|<([A-Za-z_][\w.:-]*)((?:\s+[^\s=/>]+\s*=\s*(?:"[^"]*"|'[^']*'))*)\s*(\/?)>/g;
const ATTRIBUTE = /([^\s=/>]+)\s*=\s*(?:"([^"]*)"|'([^']*)')/g;
const ENTITY = /&(?:#x([0-9a-fA-F]+)|#([0-9]+)|(amp|lt|gt|quot|apos));/g;
const NAMED_ENTITIES: Readonly<Record<string, string>> = { amp: "&", lt: "<", gt: ">", quot: "\"", apos: "'" };

function decodeXmlEntities(text: string): string {
  return text.replace(ENTITY, (whole, hex: string | undefined, dec: string | undefined, named: string | undefined) => {
    if (named !== undefined) return NAMED_ENTITIES[named];
    const code = hex !== undefined ? Number.parseInt(hex, 16) : Number(dec);
    return Number.isInteger(code) && code >= 0 && code <= 0x10ffff ? String.fromCodePoint(code) : whole;
  });
}

/** 把控件树解析成带层级的元素（根元素列表，通常只有一个）。结束标签弹到同名的最近一个开始标签，没有同名的就忽略：控件树不成对时
 *  仍给出能用的层级，不整体失败。不是 XML（一个元素都没有）时抛出：空结果只表示「这一屏没有可识别的控件」，不能用来掩盖采集到的
 *  是错误页。 */
export function parseXmlTree(xml: string): XmlNode[] {
  const roots: XmlNode[] = [];
  const open: XmlNode[] = [];
  let count = 0;
  for (const m of xml.matchAll(XML_TOKEN)) {
    const [, endTag, startTag, rawAttrs, selfClosing] = m;
    if (endTag !== undefined) {
      const at = open.map((n) => n.tag).lastIndexOf(endTag);
      if (at >= 0) open.length = at;
      continue;
    }
    if (startTag === undefined) continue;  // 处理指令与注释
    const attrs = new Map<string, string>();
    for (const a of (rawAttrs ?? "").matchAll(ATTRIBUTE)) attrs.set(a[1], decodeXmlEntities(a[2] ?? a[3] ?? ""));
    const node: XmlNode = { tag: startTag, attrs, children: [] };
    (open.length > 0 ? open[open.length - 1].children : roots).push(node);
    count++;
    if (selfClosing === "") open.push(node);
  }
  if (count === 0) throw new Error("设备返回的控件树不是可识别的 XML");
  return roots;
}

/** 按文档顺序列出控件树里的全部元素（parseXmlTree 的扁平视图；不是 XML 时同样抛出）。 */
export function scanXmlElements(xml: string): XmlElement[] {
  const elements: XmlElement[] = [];
  const visit = (node: XmlNode): void => {
    elements.push(node);
    for (const child of node.children) visit(child);
  };
  for (const root of parseXmlTree(xml)) visit(root);
  return elements;
}

/** 按文档顺序遍历一个元素及其全部后代。 */
export function* descendantsOf(node: XmlNode): IterableIterator<XmlNode> {
  yield node;
  for (const child of node.children) yield* descendantsOf(child);
}

/** 属性值：缺失或空串都按「控件树里没有」记为 null（ADR 0051 决策 8 的控件摘要字段）。 */
export function attrOrNull(el: XmlElement, name: string): string | null {
  const v = el.attrs.get(name);
  return v === undefined || v === "" ? null : v;
}

/** 把抽取到的控件收成控件摘要：按上限截断，total 是截断前的总数。 */
export function toControls(items: ControlItem[]): Controls {
  if (items.length <= CONTROLS_MAX_ITEMS) return { items, total: items.length, truncated: false };
  return { items: items.slice(0, CONTROLS_MAX_ITEMS), total: items.length, truncated: true };
}

/** 控件是否可识别：类型之外至少有 id、文本或无障碍标识之一。 */
export function identifiable(item: ControlItem): boolean {
  return item.id !== null || item.text !== null || item.a11y_id !== null;
}

// ---- 选择适配器 ----

/** 适配器清单的一项：驱动名与按会话新建实例的工厂。 */
export interface AdapterEntry {
  readonly automationName: string;
  create(): DeviceAdapter;
}

/** 按会话回报的 automationName 选适配器（设备侧接缝的 AdapterRegistry 端口）：不分大小写比对，每次选择新建一个实例，没有
 *  对应的返回 null（接缝据此记执行前失败）。清单里驱动名重复是装配错误，构造时即抛出。 */
export function adapterRegistry(entries: readonly AdapterEntry[]): { select(automationName: string): DeviceAdapter | null } {
  const byName = new Map<string, AdapterEntry>();
  for (const entry of entries) {
    const key = keyNameKey(entry.automationName);
    if (byName.has(key)) throw new Error(`适配器清单里驱动名 ${entry.automationName} 重复`);
    byName.set(key, entry);
  }
  return {
    select(automationName: string): DeviceAdapter | null {
      return byName.get(keyNameKey(automationName))?.create() ?? null;
    },
  };
}

// 编译期核对：选择结果可以直接当设备侧接缝的 AdapterRegistry 端口用（选出的完整面是端口 DriverAdapter 的子类型）。
type _RegistryIsPort = ReturnType<typeof adapterRegistry> extends AdapterRegistry ? true : never;
const _registryIsPort: _RegistryIsPort = true;
void _registryIsPort;

// ---- 界面实现 ----

/** 长按没有给出时长时的缺省时长（毫秒）。iOS 的 touchAndHold 必须带时长，两个平台统一在这里补上；改它须同步命令契约快照。 */
export const LONG_PRESS_DEFAULT_MS = 800;
/** 「滚到顶 / 底 / 最左 / 最右」时连发的最大幅度滚动次数，对应 Midscene 对这类滚动「快速连滚若干次」的约定。 */
export const SCROLL_TO_EDGE_GESTURES = 5;

const EDGE_SCROLLS: Readonly<Record<string, ScrollDirection>> = {
  scrollToBottom: "down",
  scrollToTop: "up",
  scrollToRight: "right",
  scrollToLeft: "left",
};
const SCROLL_DIRECTIONS: readonly string[] = ["up", "down", "left", "right"];

type ScrollParam = Parameters<ScrollInputPrimitives["scroll"]>[0];
type TypeTextOptions = Parameters<KeyboardInputPrimitives["typeText"]>[1];

/** Midscene 动作参数里的目标元素（LocateResultElement）取中心点；没有目标时为 null。 */
function locatePoint(target: unknown): Point | null {
  const center = (target as { center?: unknown } | null | undefined)?.center;
  if (Array.isArray(center) && typeof center[0] === "number" && typeof center[1] === "number") return { x: center[0], y: center[1] };
  return null;
}

const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

/** 从 base64 的 PNG 截图里读像素尺寸（IHDR 块的宽与高，紧跟在 8 字节签名与块头之后）。 */
export function pngSize(base64: string): { width: number; height: number } {
  const head = Buffer.from(base64.slice(0, 44), "base64");
  if (head.length < 24 || !head.subarray(0, 8).equals(PNG_SIGNATURE) || head.toString("latin1", 12, 16) !== "IHDR") {
    throw new Error("设备返回的截图不是 PNG 图像");
  }
  return { width: head.readUInt32BE(16), height: head.readUInt32BE(20) };
}

const PLATFORM_LABELS: Readonly<Record<Device, string>> = { android: "Android", ios: "iOS" };

export interface AppiumInterfaceConfig {
  /** 命令守卫代理。 */
  driver: Browser;
  adapter: DeviceAdapter;
  scale: number;
  inputContext: InputContext | null;
  /** AppiumSession.withWebContext（只用到它）。 */
  session: Pick<AppiumSession, "withWebContext">;
  /** 诊断日志的出口（收起键盘的原语报错这类不直接定判定的失败写在这里）。 */
  log: (line: string) => void;
}

/** 收起键盘的原语报错时的日志行（按路线措辞）。随后还要核键盘是否仍在、仍在才让这一步失败，所以这里只记报错，不预先断言对判定的影响。 */
function keyboardNotHiddenLogLine(e: unknown, origin: "input" | "action"): string {
  const where = origin === "input" ? "输入后收起键盘" : "「收起键盘」动作";
  return `worker: ${where}的收起命令报错：${errorText(e)}`;
}

// 适配器的收起键盘原语在「界面上没有收起控件」时抛出的异常带这个标记（iOS 走自己定位控件的路线，ADR 0052 决策 4），界面实现据它把
// 失败原因写成「没有这样的控件」而不是「点了没收起」。
const NO_DISMISS_CONTROL = Symbol.for("gherkai.noDismissControl");

/** 构造「界面上没有收起键盘的控件」的异常（适配器用）。 */
export function noDismissControlError(message: string): Error {
  return Object.assign(new Error(message), { [NO_DISMISS_CONTROL]: true });
}

export function isNoDismissControlError(e: unknown): boolean {
  return e !== null && typeof e === "object" && (e as Record<symbol, unknown>)[NO_DISMISS_CONTROL] === true;
}

/** 「收起键盘」动作执行后键盘仍在时交给模型的失败原因（产品语言，ADR 0052 决策 7）：按平台与失败形态分写——iOS 的动作只点纯收起语义的
 *  控件，没有这样的控件时说清并指出用例可以怎么改（iOS 上收起键盘只能走应用或系统浏览器提供的途径，一条都没有的输入框谁都收不起），
 *  改法写成「改写用例后重新运行、本次不再换别的方式」：真机上模型会把改法当成当场可试的替代路线（自己按 Return、点空白）再多花一轮；
 *  点了控件键盘仍在、或 Android 的系统命令没收起，就只说发生了什么。都以同一前缀开头，让这一步快速、明确地失败，免得模型反复重规划。 */
export const KEYBOARD_NOT_DISMISSED_PREFIX = "键盘仍然显示：";
const REMOVE_STEP_ADVICE = "这一步无法按用例的写法完成；若下一步的目标没有被键盘遮住，去掉用例里的「收起键盘」即可";
export function keyboardNotDismissedMessage(device: Device, cause: "no_control" | "not_dismissed"): string {
  if (device === "android") return `${KEYBOARD_NOT_DISMISSED_PREFIX}系统的收起键盘命令没有收起这台设备上的键盘，${REMOVE_STEP_ADVICE}`;
  if (cause === "no_control") {
    return `${KEYBOARD_NOT_DISMISSED_PREFIX}收起键盘的动作只点键盘上的 Done / 完成键或键盘上方工具栏里的 Done，这台设备上当前的输入框没有这样的控件，`
      + `${REMOVE_STEP_ADVICE}；若这个输入框靠 Return 键或点击空白处收起，把用例改写成「按下 Return」或「点击空白处」后重新运行，本次不再换别的方式尝试`;
  }
  return `${KEYBOARD_NOT_DISMISSED_PREFIX}已点击键盘的收起控件（Done / 完成）但键盘没有收起（或点击没有成功），${REMOVE_STEP_ADVICE}`;
}

/** 「收起键盘」动作的名字与给模型看的说明（ADR 0052 决策 7）。说明写明用途与边界：用例要求收起、或键盘遮住下一步要操作的元素时用；
 *  它不是返回键，不会离开当前界面。iOS 补一句它只点纯收起语义的控件、不按 Return、不点空白处（决策 4），要那样做时模型用 KeyboardPress
 *  或 Tap；Android 走系统的收起命令，不涉及 Done 这类控件。 */
export const DISMISS_KEYBOARD_ACTION = "DismissKeyboard";
const INPUT_ACTION = "Input";

/** Input 动作 autoDismissKeyboard 参数给模型的说明（ADR 0052 决策 7 路线 ①，替换 SDK 的「用户要求时才给」——真机上模型从不因那句给出
 *  这个参数，而是把收键盘另规划成一步）：只在用例要求输入后收起键盘时给 true，并说明平台行为与失败后果，让模型把「输入 … 后收起键盘」
 *  规划成一个动作。 */
export function autoDismissKeyboardDescription(device: Device): string {
  const when = "Set it to true only when the test step asks to dismiss, hide or collapse the keyboard right after typing; leave it unset " +
    "when the step does not mention the keyboard. ";
  if (device === "android") return `${when}On Android the system hides the keyboard; if it is still shown afterwards the action fails with the reason.`;
  return `${when}On iOS this taps the keyboard's Done key or the Done button in the toolbar above the keyboard; if the device offers no such ` +
    "control, or the keyboard is still shown afterwards, the action fails with the reason. It never presses Return and never taps a blank area.";
}

/** 把 SDK 定义的 Input 动作的 autoDismissKeyboard 参数说明换成上面那句，其余（名字、call、样例）原样保留。SDK 的参数形态变了（没有这个
 *  参数、或参数不再是对象）就抛出：说明没替换上，模型会按 SDK 原说明从不给这个参数，不能静默放过。 */
function withAutoDismissDescription(action: DeviceAction, device: Device): DeviceAction {
  const schema = action.paramSchema;
  if (!(schema instanceof z.ZodObject) || !("autoDismissKeyboard" in schema.shape)) {
    throw new Error("Midscene 的 Input 动作参数里没有 autoDismissKeyboard，收起键盘的参数说明无处替换：先核对 SDK 的动作定义再调整");
  }
  return { ...action, paramSchema: schema.extend({ autoDismissKeyboard: z.boolean().optional().describe(autoDismissKeyboardDescription(device)) }) };
}

export function dismissKeyboardDescription(device: Device): string {
  const common =
    "Dismiss (hide) the on-screen soft keyboard and stay on the current screen. Use it when the test step asks to dismiss, hide or " +
    "collapse the keyboard, or when the keyboard covers the element you need to interact with next. It does not press Back or Home and " +
    "never leaves the current screen.";
  if (device === "android") return `${common} On Android it asks the system to hide the keyboard.`;
  return `${common} On iOS it only taps a dedicated dismiss control (a Done key on the keyboard, or the Done button in the toolbar ` +
    "above it); it never presses Return and never taps a blank area. If the step asks to press Return or to tap outside the field, " +
    "use KeyboardPress or Tap instead.";
}

/** Midscene 的界面实现：截图、尺寸与动作集（ADR 0052 决策 7）。 */
export class AppiumInterface extends AbstractInterface {
  interfaceType = "appium-webdriver";
  // AbstractInterface 把这些声明为可选的抽象成员，子类显式声明为不提供。url 不提供：设备上读地址以能力探测为前提、由接缝的
  // 快照采集负责（ADR 0052 决策 5），不能让 SDK 在报告或规划里自行调用。
  cacheFeatureForPoint = undefined;
  rectMatchesCacheFeature = undefined;
  getUITree = undefined;
  beforeInvokeAction = undefined;
  afterInvokeAction = undefined;
  getElementsNodeTree = undefined;
  evaluateJavaScript = undefined;
  url = undefined;

  private readonly adapter: DeviceAdapter;
  private readonly ctx: PrimitiveContext;
  private readonly log: (line: string) => void;
  /** 最近一张截图的像素尺寸。Midscene 每轮规划先取尺寸再截图，尺寸取上一轮的截图即可，不为它另截一张。 */
  private lastSize: { width: number; height: number } | null = null;
  private actions: DeviceAction[] | null = null;

  constructor(cfg: AppiumInterfaceConfig) {
    super();
    this.adapter = cfg.adapter;
    this.log = cfg.log;
    const { driver, scale, inputContext, session } = cfg;
    this.ctx = { driver, scale, inputContext, withWebContext: (fn) => session.withWebContext(driver, fn) };
  }

  describe(): string {
    return `${PLATFORM_LABELS[this.adapter.device]} 设备（${this.adapter.automationName}）`;
  }

  async screenshotBase64(): Promise<string> {
    const shot = await this.ctx.driver.takeScreenshot();
    this.lastSize = pngSize(shot);
    return `data:image/png;base64,${shot}`;
  }

  async size(): Promise<{ width: number; height: number }> {
    if (this.lastSize === null) this.lastSize = pngSize(await this.ctx.driver.takeScreenshot());
    return { ...this.lastSize };
  }

  actionSpace(): DeviceAction[] {
    if (this.actions !== null) return this.actions;
    const { adapter, ctx } = this;
    const { home, back } = adapter.systemButtons;
    const inputs: InputPrimitives = {
      pointer: {
        tap: (p) => adapter.tap(ctx, p),
        longPress: (p, opts) => adapter.longPress(ctx, p, opts?.duration ?? LONG_PRESS_DEFAULT_MS),
      },
      keyboard: {
        typeText: (value, opts) => this.typeText(value, opts),
        keyboardPress: async (keyName, opts) => {
          await this.focus(opts?.target);
          await adapter.keyboardPress(ctx, keyName);
        },
        clearInput: async (target) => {
          await this.focus(target);
          await adapter.clearInput(ctx);
        },
      },
      scroll: { scroll: (param) => this.scroll(param) },
      system: back === null
        ? { homeButton: () => home.press(ctx) }
        : { homeButton: () => home.press(ctx), backButton: () => back.press(ctx) },
    };
    const systemActions: SystemInputActionOptions = back === null
      ? { homeButton: home.action }
      : { homeButton: home.action, backButton: back.action };
    this.actions = [
      // Input 动作的 autoDismissKeyboard 参数说明换成「用例要求输入后收起键盘时给」（ADR 0052 决策 7 路线 ①）
      ...defineActionsFromInputPrimitives(inputs, { size: () => this.size(), includeSwipe: false, systemActions })
        .map((action) => action.name === INPUT_ACTION ? withAutoDismissDescription(action, this.adapter.device) : action),
      // 「收起键盘」动作（ADR 0052 决策 7 路线 ②）：两平台同一条原语。用例把「收起键盘」写成单独一步、或键盘遮住下一步目标而用例没写时，
      // 模型用它；没有它只能借返回键或点键盘上的按钮去凑（Android 有退出当前界面的风险，iOS 原生应用上收不起）。
      defineAction({
        name: DISMISS_KEYBOARD_ACTION,
        description: dismissKeyboardDescription(this.adapter.device),
        call: async () => { await this.hideKeyboard("action"); },
      }),
    ];
    return this.actions;
  }

  async destroy(): Promise<void> {
    // 会话由设备侧接缝的终结收尾，这里没有要释放的东西。
  }

  /** 有目标元素时先点它取得焦点。 */
  private async focus(target: unknown): Promise<void> {
    const p = locatePoint(target);
    if (p !== null) await this.adapter.tap(this.ctx, p);
  }

  /** Input 动作：有目标元素时先点它取得焦点（设备上没有焦点的输入框收不到输入），替换语义下再清空，然后输入；只要求取得焦点时
   *  不输入。清空与否的语义与 Midscene 的网页实现一致：只在有目标元素时清空。Midscene 传来的 autoDismissKeyboard 恰为 true 时，
   *  输入完成后收起键盘一次并核键盘是否仍在（参数说明已改为「用例要求时才给」，给了即是用例的要求）；为 false 或没有给时不收。 */
  private async typeText(value: string, opts: TypeTextOptions): Promise<void> {
    const target = locatePoint(opts?.target);
    if (target !== null) await this.adapter.tap(this.ctx, target);
    if (opts?.focusOnly) return;
    if (target !== null && opts?.replace !== false) await this.adapter.clearInput(this.ctx);
    if (value !== "") await this.adapter.typeText(this.ctx, value);
    if (opts?.autoDismissKeyboard === true) await this.hideKeyboard("input");
  }

  /** 收起键盘（ADR 0052 决策 7）：两条路线同一口径——Input 动作带 autoDismissKeyboard 为 true（参数说明只让模型在用例要求时给）与模型显式
   *  调用的「收起键盘」动作，都要快速明确地失败：原语之后核一次键盘是否仍显示（点了收起控件但没收起，或驱动报成功而键盘仍在），仍在即抛出
   *  产品语言的原因，让 Midscene 结束这一步而不是反复重规划；核不出来（只读命令失败）按未知：原语失败则抛，原语成功不抛。原语报错先记一行
   *  日志（措辞按路线）。经守卫发出的命令若遇到会话丢失或结果未知，守卫已把它记在本次执行窗口的判定上（并中止当前 act），这里的处置不会
   *  掩盖它。 */
  private async hideKeyboard(origin: "input" | "action"): Promise<void> {
    let failure: unknown = null;
    try {
      await this.adapter.hideKeyboard(this.ctx);
    } catch (e) {
      failure = e;
      this.log(keyboardNotHiddenLogLine(e, origin));
    }
    let shown: boolean | null = null;
    try {
      shown = await this.adapter.keyboardShown(this.ctx);
    } catch {
      shown = null;  // 核不出来：按未知处理
    }
    if (shown === true || (shown === null && failure !== null)) {
      throw new Error(keyboardNotDismissedMessage(this.adapter.device, isNoDismissControlError(failure) ? "no_control" : "not_dismissed"));
    }
  }

  /** Scroll 动作：单次滚动按方向与距离；滚到边缘时连发若干次最大幅度（距离取整屏）的滚动。 */
  private async scroll(param: ScrollParam): Promise<void> {
    const screen = await this.size();
    const type = param.scrollType ?? "singleAction";
    const edge = EDGE_SCROLLS[type];
    if (edge !== undefined) {
      const distance = edge === "up" || edge === "down" ? screen.height : screen.width;
      for (let i = 0; i < SCROLL_TO_EDGE_GESTURES; i++) await this.adapter.scroll(this.ctx, { direction: edge, distance, screen });
      return;
    }
    if (type !== "singleAction") throw new Error(`不支持的滚动方式：${JSON.stringify(type)}`);
    const direction = param.direction ?? "down";
    if (!SCROLL_DIRECTIONS.includes(direction)) throw new Error(`不支持的滚动方向：${JSON.stringify(direction)}`);
    const distance = typeof param.distance === "number" && param.distance > 0 ? param.distance : null;
    await this.adapter.scroll(this.ctx, { direction, distance, screen });
  }
}

/** 构造界面实现前的核对（都是装配错误，正常执行不会触发）：平台与驱动一致、比例为正数、iOS 带输入上下文。没有给日志出口时
 *  不记日志。 */
export function createAppiumInterface(args: {
  driver: Browser; adapter: DeviceAdapter; session: Pick<AppiumSession, "withWebContext">; device: Device; scale: number;
  inputContext: InputContext | null; log?: (line: string) => void;
}): AppiumInterface {
  const { adapter, device, scale, inputContext } = args;
  if (adapter.device !== device) {
    throw new Error(`设备回报的自动化驱动 ${adapter.automationName} 与测试目标的平台 ${PLATFORM_LABELS[device]} 不符`);
  }
  if (!Number.isFinite(scale) || scale <= 0) throw new Error(`坐标比例 ${scale} 不是正数，无法换算手势坐标`);
  if (device === "ios" && inputContext !== "web" && inputContext !== "native") {
    throw new Error("iOS 设备的界面实现需要能力探测给出的输入上下文");
  }
  return new AppiumInterface({ driver: args.driver, adapter, scale, inputContext, session: args.session, log: args.log ?? (() => {}) });
}

/** 设备 Agent 的构造参数：设备侧接缝 AgentFactory 端口的参数，适配器取完整面，另加能力探测给出的 iOS 输入上下文。 */
export interface DeviceAgentArgs {
  /** 命令守卫代理。 */
  driver: Browser;
  adapter: DeviceAdapter;
  session: Pick<AppiumSession, "withWebContext">;
  device: Device;
  /** 能力探测得到的坐标比例。 */
  scale: number;
  /** 能力探测得到的 iOS 输入上下文；Android 为 null。 */
  inputContext: InputContext | null;
  /** 已含重规划上限的构造项（设备侧接缝的 deviceAgentOpts 给出，ADR 0044 决策 2）。 */
  opts: AgentOpt;
}

/** 设备 Agent 的构造处（设备侧接缝的 AgentFactory 端口）：new Agent(界面实现, 构造项)。重规划上限只在接缝读一次、经构造项传入，
 *  这里不再读 env；设备上它必须有限（ADR 0052 决策 6 的 ⑨），缺失或非正整数是装配错误。log 是交给界面实现的诊断日志出口，必须
 *  由装配方给出：收起键盘的原语报错只写在这里（判定由随后核键盘是否仍在决定），漏接时这类报错不留下任何记录。 */
export function createDeviceAgentFactory(options: { log: (line: string) => void }): { create(args: DeviceAgentArgs): Agent } {
  const { log } = options;
  return {
    create(args: DeviceAgentArgs): Agent {
      const limit = args.opts.replanningCycleLimit;
      if (typeof limit !== "number" || !Number.isSafeInteger(limit) || limit <= 0) {
        throw new Error(`设备 Agent 的构造项缺少有限的重规划上限（replanningCycleLimit 为 ${String(limit)}）`);
      }
      return new Agent(createAppiumInterface({ ...args, log }), args.opts);
    },
  };
}
