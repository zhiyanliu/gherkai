// 驱动适配器的命令契约快照与失败归类（ADR 0052 决策 4、8；ADR 0048 决策 7；ADR 0051 决策 4、8），以及界面实现把 Midscene 的
// 动作翻成适配器原语的方式（ADR 0052 决策 7）。运行：npx tsx --test src/device/adapters/adapters.contract.test.mts。
//
// 快照在 fixtures/<适配器>.commands.json：每个用例给出原语名（call）、输入（input）、原语执行时的上下文（context：坐标比例与 iOS
// 的输入上下文）、假 driver 的应答（responses，可缺），以及适配器经 driver 发出的命令序列（commands：方法名与参数；在网页上下文
// 里发出的命令收在 withWebContext 下）。改动任何原语发出的命令都必须显式改快照，本测试不自动重写它（ADR 0052 决策 8）。
// 同一份用例也是 ADR 0052 决策 8 的真机重新探测工具的对照基准：按用例在真实会话里执行原语，再与这里的命令序列比对。
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import type { Browser } from "webdriverio";
import type { AgentOpt } from "@midscene/core";
import type { DeviceAction } from "@midscene/core/device";
import { attachClassification, readClassification } from "../../worker/surface.mjs";
import { RESULT_UNKNOWN_MESSAGE, createCommandGuard } from "../guard.mjs";
import { CONTROLS_MAX_ITEMS } from "../limits.mjs";
import {
  AppiumInterface, LONG_PRESS_DEFAULT_MS, SCROLL_TO_EDGE_GESTURES, adapterRegistry, createAppiumInterface, deviceAgentFactory,
  driverTextMatchAllowed, unmappedKeyMessage, type DeviceAdapter, type InputContext, type PrimitiveContext,
} from "../interface.mjs";
import {
  APP_DID_NOT_HANDLE_ADDRESS_MESSAGE, FOREGROUND_NOT_APP_MESSAGE, UIAUTOMATOR2, createUiAutomator2Adapter,
  extractAndroidControls, undeliverableAddressChars, uiautomator2Entry,
} from "./uiautomator2.mjs";
import {
  DEEP_LINK_UNSUPPORTED_MESSAGE, READ_ONLY_MOBILE_COMMANDS as IOS_READ_ONLY, XCUITEST, activeAppInfo, createXcuitestAdapter,
  deviceScreenInfo, extractIosControls, xcuitestEntry,
} from "./xcuitest.mjs";
import { READ_ONLY_MOBILE_COMMANDS as ANDROID_READ_ONLY } from "./uiautomator2.mjs";

const FIXTURES = path.join(import.meta.dirname, "fixtures");
const W3C_ELEMENT_KEY = "element-6066-11e4-a52f-4f735466cecf";
const FOREGROUND_POLL = { attempts: 3, intervalMs: 250 };

// ---- 假 driver：记录每条命令，按用例给的应答返回 ----

type Recorded = { method: string; args: unknown[] } | { withWebContext: Recorded[] };

interface Recorder {
  driver: Browser;
  commands: Recorded[];
  sleeps: number[];
  ctx(scale: number, inputContext: InputContext | null): PrimitiveContext;
  sleep(ms: number): Promise<void>;
}

/** responses 的每个值是按调用次序给出的应答；Error 实例表示这一次调用抛出它。 */
function recorder(responses: Record<string, unknown[]> = {}): Recorder {
  const root: Recorded[] = [];
  let current = root;
  const sleeps: number[] = [];
  const queues = new Map(Object.entries(responses).map(([k, v]) => [k, [...v]]));
  const defaults: Record<string, () => unknown> = {
    getActiveElement: () => ({ [W3C_ELEMENT_KEY]: "active-1" }),
  };
  const driver = new Proxy({}, {
    get(_t, prop) {
      if (typeof prop !== "string" || prop === "then") return undefined;
      return async (...args: unknown[]) => {
        current.push({ method: prop, args: JSON.parse(JSON.stringify(args)) as unknown[] });
        const queue = queues.get(prop);
        if (queue && queue.length > 0) {
          const next = queue.shift();
          if (next instanceof Error) throw next;
          return next;
        }
        return defaults[prop]?.();
      };
    },
  }) as unknown as Browser;
  return {
    driver,
    commands: root,
    sleeps,
    ctx: (scale, inputContext) => ({
      driver, scale, inputContext,
      async withWebContext<T>(fn: () => Promise<T> | T): Promise<T> {
        const inner: Recorded[] = [];
        const outer = current;
        outer.push({ withWebContext: inner });
        current = inner;
        try { return await fn(); } finally { current = outer; }
      },
    }),
    sleep: async (ms) => { sleeps.push(ms); },
  };
}

function flatten(commands: Recorded[]): Array<{ method: string; args: unknown[] }> {
  return commands.flatMap((c) => ("withWebContext" in c ? flatten(c.withWebContext) : [c]));
}

// ---- 快照用例 ----

interface ContractCase {
  name: string;
  call: string;
  context?: { scale?: number; inputContext?: InputContext | null };
  input?: Record<string, unknown>;
  responses?: Record<string, unknown[]>;
  commands: Recorded[];
}

interface ContractFixture {
  automationName: string;
  cases: ContractCase[];
}

function loadFixture(name: string): ContractFixture {
  return JSON.parse(fs.readFileSync(path.join(FIXTURES, `${name}.commands.json`), "utf-8")) as ContractFixture;
}

const PRIMITIVES = ["tap", "longPress", "scroll", "typeText", "keyboardPress", "clearInput", "home", "back", "deepLink"] as const;

async function runCase(make: (rec: Recorder) => DeviceAdapter, c: ContractCase): Promise<Recorded[]> {
  const rec = recorder(c.responses);
  const adapter = make(rec);
  const ctx = rec.ctx(c.context?.scale ?? 1, c.context?.inputContext ?? null);
  const i = (c.input ?? {}) as Record<string, any>;
  switch (c.call) {
    case "tap": await adapter.tap(ctx, i.point); break;
    case "longPress": await adapter.longPress(ctx, i.point, i.durationMs); break;
    case "scroll": await adapter.scroll(ctx, { direction: i.direction, distance: i.distance ?? null, screen: i.screen }); break;
    case "typeText": await adapter.typeText(ctx, i.text); break;
    case "keyboardPress": await adapter.keyboardPress(ctx, i.keyName); break;
    case "clearInput": await adapter.clearInput(ctx); break;
    case "home": await adapter.systemButtons.home.press(ctx); break;
    case "back": {
      const back = adapter.systemButtons.back;
      assert.ok(back !== null, `${c.name}：这个适配器没有返回键`);
      await back.press(ctx);
      break;
    }
    case "deepLink": await adapter.deepLink(rec.driver, i.address, i.appId ?? null); break;
    default: throw new Error(`快照里的原语名 ${JSON.stringify(c.call)} 不在 ${PRIMITIVES.join("、")} 之中`);
  }
  return rec.commands;
}

const ADAPTERS: Array<{ fixture: string; make: (rec: Recorder) => DeviceAdapter; primitives: readonly string[] }> = [
  {
    fixture: "uiautomator2",
    make: (rec) => createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL, sleep: (ms) => rec.sleep(ms) }),
    primitives: PRIMITIVES,
  },
  { fixture: "xcuitest", make: () => createXcuitestAdapter(), primitives: PRIMITIVES.filter((p) => p !== "back") },
];

for (const { fixture, make, primitives } of ADAPTERS) {
  test(`${fixture}：每个原语发出的命令与快照完全一致`, async () => {
    const doc = loadFixture(fixture);
    assert.equal(doc.automationName, make(recorder()).automationName);
    for (const c of doc.cases) {
      const actual = await runCase(make, c);
      assert.deepEqual(actual, c.commands, `${c.name}：实际发出 ${JSON.stringify(actual)}`);
    }
  });

  test(`${fixture}：快照覆盖了适配器的每个原语`, () => {
    const covered = new Set(loadFixture(fixture).cases.map((c) => c.call));
    const missing = primitives.filter((p) => !covered.has(p));
    assert.deepEqual(missing, [], `快照缺少这些原语的用例：${missing.join("、")}`);
  });
}

test("Android：输入只发 mobile: type，全程不用 W3C 指针或键盘动作", async () => {
  const doc = loadFixture("uiautomator2");
  const typing = doc.cases.filter((c) => c.call === "typeText");
  assert.ok(typing.length > 0);
  for (const c of typing) {
    assert.deepEqual(flatten(c.commands).map((x) => x.args[0]), ["mobile: type"], c.name);
  }
  const all = flatten(doc.cases.flatMap((c) => c.commands));
  assert.deepEqual([...new Set(all.map((x) => x.method))].sort(), ["execute", "getCurrentPackage"]);
  const clear = doc.cases.find((c) => c.call === "clearInput")!;
  assert.ok(flatten(clear.commands).every((x) => JSON.stringify(x.args) === JSON.stringify(["mobile: pressKey", { keycode: 67 }])));
});

test("iOS：不发旧版 POST /keys、不用 W3C 指针拖动，pressButton 只出现在主屏键", async () => {
  const doc = loadFixture("xcuitest");
  for (const c of doc.cases) {
    const cmds = flatten(c.commands);
    for (const x of cmds) {
      assert.ok(!["keys", "sendKeys", "performActions", "releaseActions", "touchAction"].includes(x.method), `${c.name}：${x.method}`);
      if (x.method === "execute") {
        assert.notEqual(x.args[0], "mobile: dragFromToForDuration", c.name);
        if (x.args[0] === "mobile: pressButton") assert.equal(c.call, "home", c.name);
      }
    }
  }
  const typing = doc.cases.filter((c) => c.call === "typeText" || c.call === "keyboardPress" || c.call === "clearInput");
  for (const c of typing) {
    assert.deepEqual(flatten(c.commands).map((x) => x.method), ["getActiveElement", "elementSendKeys"], c.name);
  }
  assert.equal(createXcuitestAdapter().systemButtons.back, null, "iOS 没有系统返回键");
});

test("iOS：坐标为截图像素除以探测得到的比例", async () => {
  const rec = recorder();
  const adapter = createXcuitestAdapter();
  await adapter.tap(rec.ctx(3, null), { x: 900, y: 1500 });
  await adapter.tap(rec.ctx(2, null), { x: 900, y: 1500 });
  assert.deepEqual(rec.commands, [
    { method: "execute", args: ["mobile: tap", { x: 300, y: 500 }] },
    { method: "execute", args: ["mobile: tap", { x: 450, y: 750 }] },
  ]);
});

// ---- 未映射的键 ----

test("未映射的键名记 capability_unavailable，不发任何命令", async () => {
  const cases: Array<[DeviceAdapter, InputContext | null, string]> = [
    [createXcuitestAdapter(), "native", "Tab"],
    [createXcuitestAdapter(), "web", "Escape"],
    [createXcuitestAdapter(), "native", "Control+A"],
    [createXcuitestAdapter(), "native", "Home"],
    [createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL }), null, "Control+A"],
    [createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL }), null, "F13"],
  ];
  for (const [adapter, inputContext, key] of cases) {
    const rec = recorder();
    await assert.rejects(adapter.keyboardPress(rec.ctx(adapter.automationName === XCUITEST ? 3 : 1, inputContext), key), (e) => {
      assert.deepEqual(readClassification(e), { errorType: "capability_unavailable", message: unmappedKeyMessage(key) });
      return true;
    });
    assert.deepEqual(rec.commands, [], `${adapter.automationName} ${key}`);
  }
});

test("iOS 的输入原语需要能力探测给出的输入上下文", async () => {
  const rec = recorder();
  await assert.rejects(createXcuitestAdapter().typeText(rec.ctx(3, null), "x"), /输入上下文/);
  assert.deepEqual(rec.commands, []);
});

// ---- DeepLink：Android ----

test("Android：地址按 RFC 3986 字符集校验，; ' ( ) 与非 URI 字符在发命令前拒绝", async () => {
  // { } 实测逐字送达，但不在 RFC 3986 字符集内，目前按字符集拒收（是否放行待 ADR 0048 决策 7 定，定了须同步改这里与适配器）。
  for (const bad of [";", "'", "(", ")", " ", "|", "<", ">", "\"", "{", "}", "\\", "^", "`", "é", "中"]) {
    const address = `myshop://cart?x=a${bad}b`;
    assert.deepEqual(undeliverableAddressChars(address), [bad], JSON.stringify(bad));
    const rec = recorder();
    const adapter = createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL, sleep: rec.sleep });
    await assert.rejects(adapter.deepLink(rec.driver, address, "com.example.shop"), (e) => {
      const mark = readClassification(e);
      assert.equal(mark?.errorType, "capability_unavailable");
      assert.match(mark!.message, /百分号编码/);
      assert.ok(mark!.message.includes(JSON.stringify(bad)), mark!.message);
      return true;
    });
    assert.deepEqual(rec.commands, [], "校验不过时不发命令");
  }
  // 网页目标经同一条驱动路径传地址，同样校验
  const rec = recorder();
  await assert.rejects(createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL }).deepLink(rec.driver, "https://a.example/(x)", null),
    (e) => readClassification(e)?.errorType === "capability_unavailable");
  assert.deepEqual(rec.commands, []);
  // 多个违规字符按出现顺序各列一次
  assert.deepEqual(undeliverableAddressChars("x://a;b(c);d e"), [";", "(", ")", " "]);
});

test("Android：实测逐字送达的字符与已百分号编码的字符放行", async () => {
  const address = "myshop://p/a-b_c.d~e?q=+%20%E4%B8%AD&[x]=1#f!*$,@:/?=";
  assert.deepEqual(undeliverableAddressChars(address), []);
  const rec = recorder({ getCurrentPackage: ["com.example.shop"] });
  await createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL, sleep: rec.sleep }).deepLink(rec.driver, address, "com.example.shop");
  assert.deepEqual(flatten(rec.commands)[0], { method: "execute", args: ["mobile: deepLink", { url: address, package: "com.example.shop" }] });
});

test("Android：应用未处理该地址记 capability_unavailable，不核对前台包名", async () => {
  const driverError = Object.assign(new Error("An unknown server-side error occurred: Unable to resolve Intent { act=VIEW dat=myshop://x }"),
    { name: "unknown error" });
  const rec = recorder({ execute: [driverError] });
  await assert.rejects(
    createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL, sleep: rec.sleep }).deepLink(rec.driver, "myshop://x", "com.example.shop"),
    (e) => {
      assert.equal(e, driverError, "归类挂在驱动原来的异常上，日志仍能看到驱动的报错");
      assert.deepEqual(readClassification(e), { errorType: "capability_unavailable", message: APP_DID_NOT_HANDLE_ADDRESS_MESSAGE });
      return true;
    });
  assert.deepEqual(flatten(rec.commands).map((x) => x.method), ["execute"]);
});

test("Android：网页目标上的同一报错不归应用未处理，原样抛出", async () => {
  const driverError = new Error("Unable to resolve Intent");
  const rec = recorder({ execute: [driverError] });
  await assert.rejects(createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL }).deepLink(rec.driver, "https://a.example/", null), (e) => {
    assert.equal(e, driverError);
    assert.equal(readClassification(e), null);
    return true;
  });
});

test("Android：命令成功后前台始终不是被测应用记 engine_error，轮询有界", async () => {
  const rec = recorder({ getCurrentPackage: ["com.android.chrome", "com.android.chrome", "com.android.chrome", "com.example.shop"] });
  await assert.rejects(
    createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL, sleep: rec.sleep }).deepLink(rec.driver, "myshop://x", "com.example.shop"),
    (e) => {
      assert.deepEqual(readClassification(e), { errorType: "engine_error", message: FOREGROUND_NOT_APP_MESSAGE });
      return true;
    });
  assert.deepEqual(flatten(rec.commands).map((x) => x.method), ["execute", "getCurrentPackage", "getCurrentPackage", "getCurrentPackage"]);
  assert.deepEqual(rec.sleeps, [250, 250], "第一次核对不等待，之后每次间隔一次");
});

test("Android：前台在轮询期间切到被测应用即成功", async () => {
  const rec = recorder({ getCurrentPackage: ["com.android.launcher3", "com.example.shop"] });
  await createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL, sleep: rec.sleep }).deepLink(rec.driver, "myshop://x", "com.example.shop");
  assert.deepEqual(flatten(rec.commands).map((x) => x.method), ["execute", "getCurrentPackage", "getCurrentPackage"]);
  assert.deepEqual(rec.sleeps, [250]);
});

test("Android：前台轮询参数必须是正整数次与非负间隔", () => {
  assert.throws(() => createUiAutomator2Adapter({ foregroundPoll: { attempts: 0, intervalMs: 10 } }), /foregroundPoll/);
  assert.throws(() => createUiAutomator2Adapter({ foregroundPoll: { attempts: 1.5, intervalMs: 10 } }), /foregroundPoll/);
  assert.throws(() => createUiAutomator2Adapter({ foregroundPoll: { attempts: 2, intervalMs: -1 } }), /foregroundPoll/);
});

// ---- DeepLink：iOS ----

const XCODE_SDK_ERROR = "The current Xcode SDK does not support opening of URLs with given application";

test("iOS：首次遇到不支持打开地址记 capability_unavailable 并缓存到本会话", async () => {
  const driverError = new Error(`An unknown server-side error occurred while processing the command. Original error: ${XCODE_SDK_ERROR}`);
  const rec = recorder({ execute: [driverError] });
  const adapter = createXcuitestAdapter();
  await assert.rejects(adapter.deepLink(rec.driver, "myapp://a", "com.example.app"), (e) => {
    assert.equal(e, driverError);
    assert.deepEqual(readClassification(e), { errorType: "capability_unavailable", message: DEEP_LINK_UNSUPPORTED_MESSAGE });
    return true;
  });
  await assert.rejects(adapter.deepLink(rec.driver, "myapp://b", "com.example.app"),
    (e) => readClassification(e)?.message === DEEP_LINK_UNSUPPORTED_MESSAGE);
  assert.equal(flatten(rec.commands).length, 1, "缓存之后不再发命令");
  // 结论只属于这一个会话：新会话选出的新适配器照常发命令
  const rec2 = recorder();
  await createXcuitestAdapter().deepLink(rec2.driver, "myapp://a", "com.example.app");
  assert.equal(flatten(rec2.commands).length, 1);
});

test("iOS：其它失败原样抛出，不进缓存", async () => {
  const timeout = Object.assign(new Error("Request timed out!"), { code: "ETIMEDOUT" });
  const rec = recorder({ execute: [timeout] });
  const adapter = createXcuitestAdapter();
  await assert.rejects(adapter.deepLink(rec.driver, "myapp://a", "com.example.app"), (e) => {
    assert.equal(e, timeout);
    assert.equal(readClassification(e), null);
    return true;
  });
  await adapter.deepLink(rec.driver, "myapp://a", "com.example.app");
  assert.equal(flatten(rec.commands).length, 2);
});

test("会话丢失与结果未知的标记原样传出：不改归类，也不缓存能力否定", async () => {
  // 守卫在会话已不在运行时挂 session_lost；此时驱动文本即使匹配也不能据此归类（ADR 0051 决策 4「先查会话状态」）。
  const lostIos = attachClassification(new Error(XCODE_SDK_ERROR), { errorType: "session_lost", message: "会话丢失" });
  const recIos = recorder({ execute: [lostIos] });
  const ios = createXcuitestAdapter();
  await assert.rejects(ios.deepLink(recIos.driver, "myapp://a", "com.example.app"),
    (e) => e === lostIos && readClassification(e)?.errorType === "session_lost");
  await ios.deepLink(recIos.driver, "myapp://a", "com.example.app");
  assert.equal(flatten(recIos.commands).length, 2, "没有缓存");

  // 结果未知（客户端超时或传输层故障）同样不按驱动文本再归类
  const unknownAndroid = attachClassification(new Error("Unable to resolve Intent"), { errorType: "engine_error", message: RESULT_UNKNOWN_MESSAGE });
  const recAndroid = recorder({ execute: [unknownAndroid] });
  await assert.rejects(createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL }).deepLink(recAndroid.driver, "myshop://x", "com.example.shop"),
    (e) => e === unknownAndroid && readClassification(e)?.message === RESULT_UNKNOWN_MESSAGE);
});

test("能否按驱动文本再归类：没有标记，或守卫确认会话仍在运行、结果已知的 engine_error", () => {
  const plain = new Error("x");
  assert.equal(driverTextMatchAllowed(plain), true);
  assert.equal(driverTextMatchAllowed(attachClassification(new Error("x"), { errorType: "engine_error", message: "设备命令执行失败：x" })), true);
  assert.equal(driverTextMatchAllowed(attachClassification(new Error("x"), { errorType: "engine_error", message: RESULT_UNKNOWN_MESSAGE })), false);
  assert.equal(driverTextMatchAllowed(attachClassification(new Error("x"), { errorType: "session_lost", message: "会话丢失" })), false);
  assert.equal(driverTextMatchAllowed(attachClassification(new Error("x"), { errorType: "capability_unavailable", message: "y" })), false);
});

// 经真实命令守卫发出 DeepLink：守卫给每个失败都挂标记，适配器在会话仍在运行时仍须按实测过的驱动错误文本归类。
const IOS_DRIVER_ERROR = (): Error => Object.assign(
  new Error(`An unknown server-side error occurred while processing the command. Original error: ${XCODE_SDK_ERROR}`), { name: "unknown error" });
const ANDROID_DRIVER_ERROR = (): Error => Object.assign(
  new Error("An unknown server-side error occurred: Unable to resolve Intent { act=VIEW dat=myshop://x }"), { name: "unknown error" });

/** 一个打开了执行窗口的命令守卫：执行实例是记录命令的假 driver，会话状态查询恒返回 status。 */
function guarded(adapter: DeviceAdapter, responses: Record<string, unknown[]>, status: string) {
  const rec = recorder(responses);
  const guard = createCommandGuard({ exec: rec.driver, adapter, sessionStatus: async () => status });
  guard.openWindow(new AbortController());
  return { rec, driver: guard.driver };
}

test("经命令守卫：会话仍在运行时 DeepLink 的两条驱动报错照常归 capability_unavailable，iOS 缓存到本会话", async () => {
  const ios = createXcuitestAdapter();
  const g = guarded(ios, { execute: [IOS_DRIVER_ERROR()] }, "RUNNING");
  await assert.rejects(ios.deepLink(g.driver, "myapp://a", "com.example.app"), (e) => {
    assert.deepEqual(readClassification(e), { errorType: "capability_unavailable", message: DEEP_LINK_UNSUPPORTED_MESSAGE });
    return true;
  });
  await assert.rejects(ios.deepLink(g.driver, "myapp://b", "com.example.app"),
    (e) => readClassification(e)?.message === DEEP_LINK_UNSUPPORTED_MESSAGE);
  assert.equal(flatten(g.rec.commands).length, 1, "缓存之后不再发命令");

  const android = createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL });
  const ga = guarded(android, { execute: [ANDROID_DRIVER_ERROR()] }, "RUNNING");
  await assert.rejects(android.deepLink(ga.driver, "myshop://x", "com.example.shop"), (e) => {
    assert.deepEqual(readClassification(e), { errorType: "capability_unavailable", message: APP_DID_NOT_HANDLE_ADDRESS_MESSAGE });
    return true;
  });
  assert.deepEqual(flatten(ga.rec.commands).map((x) => x.method), ["execute"], "不核对前台包名");
});

test("经命令守卫：会话已不在运行时同样的驱动报错归 session_lost，iOS 不缓存", async () => {
  const ios = createXcuitestAdapter();
  const g = guarded(ios, { execute: [IOS_DRIVER_ERROR()] }, "COMPLETED");
  await assert.rejects(ios.deepLink(g.driver, "myapp://a", "com.example.app"),
    (e) => readClassification(e)?.errorType === "session_lost");
  const rec = recorder();
  await ios.deepLink(rec.driver, "myapp://a", "com.example.app");
  assert.equal(flatten(rec.commands).length, 1, "没有缓存能力否定");

  const android = createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL });
  const ga = guarded(android, { execute: [ANDROID_DRIVER_ERROR()] }, "COMPLETED");
  await assert.rejects(android.deepLink(ga.driver, "myshop://x", "com.example.shop"),
    (e) => readClassification(e)?.errorType === "session_lost");
});

// ---- 只读命令与探测用的导出 ----

test("只读 mobile 命令名集合：iOS 为屏幕信息与前台应用查询，Android 没有", () => {
  assert.deepEqual([...IOS_READ_ONLY].sort(), ["mobile: activeAppInfo", "mobile: deviceScreenInfo"]);
  assert.deepEqual([...ANDROID_READ_ONLY], []);
  assert.equal(createXcuitestAdapter().readOnlyMobileCommands, IOS_READ_ONLY);
  assert.equal(createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL }).readOnlyMobileCommands, ANDROID_READ_ONLY);
});

test("deviceScreenInfo 与 activeAppInfo：只发集合里的命令，取不到有效值时为 null", async () => {
  const rec = recorder({ execute: [{ scale: 3, statusBarSize: { width: 390, height: 47 } }, { scale: 0 }, {}, { bundleId: "com.apple.mobilesafari", name: "" }, {}] });
  assert.deepEqual(await deviceScreenInfo(rec.driver), { scale: 3 });
  assert.deepEqual(await deviceScreenInfo(rec.driver), { scale: null });
  assert.deepEqual(await deviceScreenInfo(rec.driver), { scale: null });
  assert.deepEqual(await activeAppInfo(rec.driver), { bundleId: "com.apple.mobilesafari" });
  assert.deepEqual(await activeAppInfo(rec.driver), { bundleId: null });
  for (const c of flatten(rec.commands)) assert.ok(IOS_READ_ONLY.has(c.args[0] as string));
});

// ---- 控件摘要 ----

test("Android 控件摘要：类型取 class、id 取 resource-id、文本取 text、无障碍标识取 content-desc，实体已解码", () => {
  const xml = fs.readFileSync(path.join(FIXTURES, "android-page-source.xml"), "utf-8");
  assert.deepEqual(extractAndroidControls(xml), {
    items: [
      { type: "android.widget.TextView", id: "com.example.shop:id/title", text: "购物车 & 结算", a11y_id: null },
      { type: "android.widget.TextView", id: null, text: "满 100 > 立减", a11y_id: null },
      { type: "android.widget.Button", id: "com.example.shop:id/checkout", text: "去结算", a11y_id: "checkout button" },
      { type: "android.widget.ImageView", id: null, text: null, a11y_id: "商品图片 \"A\" 一二" },
    ],
    total: 4,
    truncated: false,
  });
});

test("iOS 控件摘要：类型取 type、文本取 label 其次 value、无障碍标识取 name，没有 id 属性", () => {
  const xml = fs.readFileSync(path.join(FIXTURES, "ios-page-source.xml"), "utf-8");
  assert.deepEqual(extractIosControls(xml), {
    items: [
      { type: "XCUIElementTypeApplication", id: null, text: "示例商店", a11y_id: "示例商店" },
      { type: "XCUIElementTypeButton", id: null, text: "登录", a11y_id: "login_button" },
      { type: "XCUIElementTypeTextField", id: null, text: "a@b.com", a11y_id: "email_field" },
      { type: "XCUIElementTypeStaticText", id: null, text: "欢迎 <新用户> '回来'", a11y_id: null },
    ],
    total: 4,
    truncated: false,
  });
});

test("控件摘要按上限截断，total 是截断前的总数", () => {
  const n = CONTROLS_MAX_ITEMS + 50;
  const buttons = Array.from({ length: n }, (_, i) => `<android.widget.Button class="android.widget.Button" text="b${i}" />`).join("");
  const got = extractAndroidControls(`<hierarchy>${buttons}</hierarchy>`);
  assert.equal(got.items.length, CONTROLS_MAX_ITEMS);
  assert.equal(got.total, n);
  assert.equal(got.truncated, true);
  assert.equal(got.items[0].text, "b0");
  assert.deepEqual(extractIosControls("<XCUIElementTypeApplication type=\"XCUIElementTypeApplication\" visible=\"true\"/>"),
    { items: [], total: 0, truncated: false }, "采集成功但没有可识别的控件");
});

test("控件树不是 XML 时抽取抛出（由接缝记为采集出错）", () => {
  assert.throws(() => extractAndroidControls("Internal Server Error"));
  assert.throws(() => extractIosControls(""));
  assert.deepEqual(createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL }).extractControls("<hierarchy/>"),
    { items: [], total: 0, truncated: false });
});

// ---- 选择适配器 ----

test("按会话回报的 automationName 选适配器：不分大小写，每次选出新实例，没有对应的为 null", () => {
  const registry = adapterRegistry([uiautomator2Entry({ foregroundPoll: FOREGROUND_POLL }), xcuitestEntry]);
  const a = registry.select("UiAutomator2");
  assert.equal(a?.automationName, UIAUTOMATOR2);
  assert.equal(a?.device, "android");
  assert.equal(registry.select("uiautomator2")?.automationName, UIAUTOMATOR2);
  const i1 = registry.select("XCUITest");
  const i2 = registry.select("xcuitest");
  assert.equal(i1?.device, "ios");
  assert.notEqual(i1, i2, "能力否定的缓存只属于一个会话");
  assert.equal(registry.select("Espresso"), null);
  assert.equal(registry.select(""), null);
  assert.throws(() => adapterRegistry([xcuitestEntry, xcuitestEntry]), /XCUITest/);
});

// ---- 界面实现 ----

// 只有 PNG 签名与 IHDR 块的截图：宽 1080、高 2400（尺寸只从 IHDR 读）
const PNG_1080x2400 = Buffer.from("89504e470d0a1a0a0000000d49484452000004380000096008060000000000000000", "hex").toString("base64");

function iface(adapter: DeviceAdapter, opts: { scale?: number; inputContext?: InputContext | null } = {}) {
  const rec = recorder({ takeScreenshot: Array(10).fill(PNG_1080x2400) });
  const ui = createAppiumInterface({
    driver: rec.driver, adapter, session: { withWebContext: (_d, fn) => rec.ctx(1, null).withWebContext(fn) },
    device: adapter.device, scale: opts.scale ?? 1, inputContext: opts.inputContext ?? null,
  });
  return { rec, ui };
}

function action(ui: AppiumInterface, name: string): DeviceAction {
  const found = ui.actionSpace().find((a) => a.name === name);
  assert.ok(found, `动作集里没有 ${name}`);
  return found;
}

test("动作集：不注册 Swipe；Android 注册返回与主屏，iOS 只注册主屏", () => {
  const android = iface(createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL })).ui.actionSpace().map((a) => a.name);
  const ios = iface(createXcuitestAdapter(), { scale: 3, inputContext: "native" }).ui.actionSpace().map((a) => a.name);
  for (const names of [android, ios]) {
    assert.ok(!names.includes("Swipe"), names.join());
    for (const n of ["Tap", "LongPress", "Input", "ClearInput", "KeyboardPress", "Scroll"]) assert.ok(names.includes(n), n);
    for (const n of ["DoubleClick", "DragAndDrop", "Pinch", "Hover", "RightClick"]) assert.ok(!names.includes(n), n);
  }
  assert.ok(android.includes("AndroidBackButton") && android.includes("AndroidHomeButton"));
  assert.ok(ios.includes("IOSHomeButton"));
  assert.ok(!ios.some((n) => /Back/.test(n)), ios.join());
});

test("截图在原生上下文取一次；尺寸取最近一张截图的像素尺寸，不另截图", async () => {
  const { rec, ui } = iface(createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL }));
  assert.deepEqual(await ui.size(), { width: 1080, height: 2400 });
  assert.equal(await ui.screenshotBase64(), `data:image/png;base64,${PNG_1080x2400}`);
  assert.deepEqual(await ui.size(), { width: 1080, height: 2400 });
  assert.deepEqual(flatten(rec.commands).map((x) => x.method), ["takeScreenshot", "takeScreenshot"]);
});

test("Input 动作：先点目标、按替换语义清空，再输入", async () => {
  const { rec, ui } = iface(createXcuitestAdapter(), { scale: 2, inputContext: "native" });
  await action(ui, "Input").call({ value: "abc", locate: { center: [200, 400], description: "邮箱" } }, {} as never);
  assert.deepEqual(flatten(rec.commands), [
    { method: "execute", args: ["mobile: tap", { x: 100, y: 200 }] },
    { method: "getActiveElement", args: [] },
    { method: "elementSendKeys", args: ["active-1", "\b".repeat(40)] },
    { method: "getActiveElement", args: [] },
    { method: "elementSendKeys", args: ["active-1", "abc"] },
  ]);
  const typeOnly = iface(createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL }));
  await action(typeOnly.ui, "Input").call({ value: "x", mode: "typeOnly", locate: { center: [10, 20], description: "框" } }, {} as never);
  assert.deepEqual(flatten(typeOnly.rec.commands), [
    { method: "execute", args: ["mobile: clickGesture", { x: 10, y: 20 }] },
    { method: "execute", args: ["mobile: type", { text: "x" }] },
  ]);
});

test("LongPress 动作没有给时长时取缺省值", async () => {
  const { rec, ui } = iface(createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL }));
  await action(ui, "LongPress").call({ locate: { center: [10, 20], description: "x" } }, {} as never);
  assert.deepEqual(flatten(rec.commands), [
    { method: "execute", args: ["mobile: longClickGesture", { x: 10, y: 20, duration: LONG_PRESS_DEFAULT_MS }] },
  ]);
});

test("Scroll 动作：单次滚动按方向与距离；滚到边缘连发若干次最大幅度的滚动", async () => {
  const android = iface(createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL }));
  await android.ui.screenshotBase64();
  await action(android.ui, "Scroll").call({ direction: "down", scrollType: "singleAction", distance: 720 }, {} as never);
  await action(android.ui, "Scroll").call({ scrollType: "scrollToTop" }, {} as never);
  const gestures = flatten(android.rec.commands).filter((x) => x.method === "execute").map((x) => x.args[1] as Record<string, unknown>);
  assert.deepEqual(gestures.map((g) => [g.direction, g.percent]),
    [["down", 0.5], ...Array(SCROLL_TO_EDGE_GESTURES).fill(["up", 1])]);

  const ios = iface(createXcuitestAdapter(), { scale: 3, inputContext: "native" });
  await ios.ui.screenshotBase64();
  await action(ios.ui, "Scroll").call({ scrollType: "scrollToRight" }, {} as never);
  const swipes = flatten(ios.rec.commands).filter((x) => x.method === "execute");
  assert.deepEqual(swipes, Array(SCROLL_TO_EDGE_GESTURES).fill({ method: "execute", args: ["mobile: swipe", { direction: "left" }] }));
});

test("系统动作经适配器下发：Android 返回键 4、主屏键 3，iOS 主屏经 pressButton", async () => {
  const android = iface(createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL }));
  await action(android.ui, "AndroidBackButton").call({}, {} as never);
  await action(android.ui, "AndroidHomeButton").call({}, {} as never);
  assert.deepEqual(flatten(android.rec.commands).map((x) => x.args[1]), [{ keycode: 4 }, { keycode: 3 }]);
  const ios = iface(createXcuitestAdapter(), { scale: 3, inputContext: "native" });
  await action(ios.ui, "IOSHomeButton").call({}, {} as never);
  assert.deepEqual(flatten(ios.rec.commands), [{ method: "execute", args: ["mobile: pressButton", { name: "home" }] }]);
});

test("界面实现的描述不含系统版本与机型", () => {
  assert.equal(iface(createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL })).ui.describe(), "Android 设备（UiAutomator2）");
  assert.equal(iface(createXcuitestAdapter(), { scale: 3, inputContext: "web" }).ui.describe(), "iOS 设备（XCUITest）");
});

test("构造前提：平台与驱动一致、比例为正数、iOS 带输入上下文", () => {
  const base = { driver: recorder().driver, session: { withWebContext: async <T,>(_d: Browser, fn: () => Promise<T> | T) => fn() } };
  assert.throws(() => createAppiumInterface({ ...base, adapter: createXcuitestAdapter(), device: "android", scale: 1, inputContext: null }),
    /XCUITest/);
  assert.throws(() => createAppiumInterface({ ...base, adapter: createXcuitestAdapter(), device: "ios", scale: 0, inputContext: "web" }),
    /比例/);
  assert.throws(() => createAppiumInterface({ ...base, adapter: createXcuitestAdapter(), device: "ios", scale: 3, inputContext: null }),
    /输入上下文/);
  // 调用方漏传输入上下文（装配没跟上构造参数）时同样在构造期失败，而不是到第一次输入才失败
  assert.throws(() => createAppiumInterface({
    ...base, adapter: createXcuitestAdapter(), device: "ios", scale: 3, inputContext: undefined as unknown as InputContext,
  }), /输入上下文/);
  assert.ok(createAppiumInterface({
    ...base, adapter: createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL }), device: "android", scale: 1, inputContext: null,
  }) instanceof AppiumInterface);
});

test("设备 Agent 的构造项必须带有限的重规划上限", () => {
  const args = {
    driver: recorder().driver, adapter: createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL }),
    session: { withWebContext: async <T,>(_d: Browser, fn: () => Promise<T> | T) => fn() },
    device: "android" as const, scale: 1, inputContext: null,
  };
  for (const opts of [{}, { replanningCycleLimit: 0 }, { replanningCycleLimit: Infinity }, { replanningCycleLimit: 2.5 }] as AgentOpt[]) {
    assert.throws(() => deviceAgentFactory.create({ ...args, opts }), /replanningCycleLimit/, JSON.stringify(opts));
  }
});

test("设备 Agent 可以构造，动作集来自界面实现", async () => {
  const agent = deviceAgentFactory.create({
    driver: recorder().driver, adapter: createUiAutomator2Adapter({ foregroundPoll: FOREGROUND_POLL }),
    session: { withWebContext: async <T,>(_d: Browser, fn: () => Promise<T> | T) => fn() },
    device: "android", scale: 1, inputContext: null, opts: { replanningCycleLimit: 12 } as AgentOpt,
  });
  assert.ok(agent);
  const names = (await agent.getActionSpace()).map((a) => a.name);
  assert.ok(!names.includes("Swipe"), names.join());
  assert.ok(names.includes("AndroidBackButton"), names.join());
});
