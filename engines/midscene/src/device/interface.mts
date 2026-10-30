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
//   - AppiumInterface 与 deviceAgentFactory：继承 Midscene 的 AbstractInterface（决策 7）。截图在原生上下文（决策 6：step 前核对与
//     复原核对保证 AI 步开始与结束时会话都在原生上下文，所以截图前不再读当前上下文），尺寸取截图的像素尺寸；动作集只经
//     defineActionsFromInputPrimitives 定义，includeSwipe 关、系统动作显式给出（Android 返回与主屏、iOS 只有主屏）；原语全部经
//     适配器下发，命令经构造时传入的 driver（命令守卫代理）发出。设备 Agent 在这里构造。
//
// 不做：按系统版本或机型分支（决策 1）——本模块与适配器都不读系统版本与机型，坐标比例与 iOS 的输入上下文是能力探测的结论，
// 由构造方传入（决策 5）；不在运行期试错换路线，每个原语只有一条路线（决策 4，被拒方案「运行期试错、失败再回落」）。
// 命令失败时的会话状态核对不在这里：经守卫代理发出的命令失败时，守卫已先查会话状态并在异常上挂好归类（ADR 0051 决策 4
// 「会话丢失的判定靠查状态」）。会话丢失与结果未知的标记原样传出；守卫确认会话仍在运行、结果已知的 engine_error 可按驱动
// 文本再归类（判定见 driverTextMatchAllowed）。
import { Agent } from "@midscene/core/agent";
import {
  AbstractInterface, defineActionsFromInputPrimitives,
  type DeviceAction, type InputPrimitives, type KeyboardInputPrimitives, type ScrollInputPrimitives, type SystemInputActionConfig,
  type SystemInputActionOptions,
} from "@midscene/core/device";
import type { AgentOpt } from "@midscene/core";
import type { Browser } from "webdriverio";
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

/** 能否按实测过的驱动错误文本再归类：异常没有标记，或命令守卫已核对会话仍在运行、命令结果已知（engine_error 且不是结果未知）。
 *  会话丢失与结果未知的标记原样传出（ADR 0051 决策 4：仍为 RUNNING 时才允许匹配两条实测过的驱动错误文本）。守卫查询会话状态
 *  本身失败时不据此判会话丢失、同样挂结果已知的 engine_error（ADR 0052 决策 6），这里与守卫一致。 */
export function driverTextMatchAllowed(e: unknown): boolean {
  const mark = readClassification(e);
  return mark === null || (mark.errorType === "engine_error" && mark.message !== RESULT_UNKNOWN_MESSAGE);
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

// 开始标签（含自闭合）：属性值用引号括起，值里可以出现未转义的 `>`（XML 允许），所以属性逐个匹配、不用 `[^>]*`。
// 处理指令（`<?xml ...?>`）、注释与结束标签都不以字母开头，不会匹配。
const START_TAG = /<([A-Za-z_][\w.:-]*)((?:\s+[^\s=/>]+\s*=\s*(?:"[^"]*"|'[^']*'))*)\s*\/?>/g;
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

/** 按文档顺序列出控件树里的全部元素。不是 XML（一个元素都没有）时抛出：空列表只表示「这一屏没有可识别的控件」，不能用来
 *  掩盖采集到的是错误页。 */
export function scanXmlElements(xml: string): XmlElement[] {
  const elements: XmlElement[] = [];
  for (const m of xml.matchAll(START_TAG)) {
    const attrs = new Map<string, string>();
    for (const a of (m[2] ?? "").matchAll(ATTRIBUTE)) attrs.set(a[1], decodeXmlEntities(a[2] ?? a[3] ?? ""));
    elements.push({ tag: m[1], attrs });
  }
  if (elements.length === 0) throw new Error("设备返回的控件树不是可识别的 XML");
  return elements;
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
  scrollToBottom: "down", untilBottom: "down",
  scrollToTop: "up", untilTop: "up",
  scrollToRight: "right", untilRight: "right",
  scrollToLeft: "left", untilLeft: "left",
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
  /** 最近一张截图的像素尺寸。Midscene 每轮规划先取尺寸再截图，尺寸取上一轮的截图即可，不为它另截一张。 */
  private lastSize: { width: number; height: number } | null = null;
  private actions: DeviceAction[] | null = null;

  constructor(cfg: AppiumInterfaceConfig) {
    super();
    this.adapter = cfg.adapter;
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
    this.actions = defineActionsFromInputPrimitives(inputs, { size: () => this.size(), includeSwipe: false, systemActions });
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
   *  不输入。清空与否的语义与 Midscene 的网页实现一致：只在有目标元素时清空。Midscene 传来的 autoDismissKeyboard 目前不处理：
   *  驱动适配器没有收起键盘的原语。 */
  private async typeText(value: string, opts: TypeTextOptions): Promise<void> {
    const target = locatePoint(opts?.target);
    if (target !== null) await this.adapter.tap(this.ctx, target);
    if (opts?.focusOnly) return;
    if (target !== null && opts?.replace !== false) await this.adapter.clearInput(this.ctx);
    if (value !== "") await this.adapter.typeText(this.ctx, value);
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
    if (type !== "singleAction" && type !== "once") throw new Error(`不支持的滚动方式：${JSON.stringify(type)}`);
    const direction = param.direction ?? "down";
    if (!SCROLL_DIRECTIONS.includes(direction)) throw new Error(`不支持的滚动方向：${JSON.stringify(direction)}`);
    const distance = typeof param.distance === "number" && param.distance > 0 ? param.distance : null;
    await this.adapter.scroll(this.ctx, { direction, distance, screen });
  }
}

/** 构造界面实现前的核对（都是装配错误，正常执行不会触发）：平台与驱动一致、比例为正数、iOS 带输入上下文。 */
export function createAppiumInterface(args: {
  driver: Browser; adapter: DeviceAdapter; session: Pick<AppiumSession, "withWebContext">; device: Device; scale: number;
  inputContext: InputContext | null;
}): AppiumInterface {
  const { adapter, device, scale, inputContext } = args;
  if (adapter.device !== device) {
    throw new Error(`设备回报的自动化驱动 ${adapter.automationName} 与测试目标的平台 ${PLATFORM_LABELS[device]} 不符`);
  }
  if (!Number.isFinite(scale) || scale <= 0) throw new Error(`坐标比例 ${scale} 不是正数，无法换算手势坐标`);
  if (device === "ios" && inputContext !== "web" && inputContext !== "native") {
    throw new Error("iOS 设备的界面实现需要能力探测给出的输入上下文");
  }
  return new AppiumInterface({ driver: args.driver, adapter, scale, inputContext, session: args.session });
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
 *  这里不再读 env；设备上它必须有限（ADR 0052 决策 6 的 ⑨），缺失或非正整数是装配错误。 */
export const deviceAgentFactory = {
  create(args: DeviceAgentArgs): Agent {
    const limit = args.opts.replanningCycleLimit;
    if (typeof limit !== "number" || !Number.isSafeInteger(limit) || limit <= 0) {
      throw new Error(`设备 Agent 的构造项缺少有限的重规划上限（replanningCycleLimit 为 ${String(limit)}）`);
    }
    return new Agent(createAppiumInterface(args), args.opts);
  },
};
