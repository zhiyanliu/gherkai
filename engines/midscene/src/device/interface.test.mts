// 界面实现的动作集（ADR 0052 决策 3、7）：两平台都注册「收起键盘」动作，调适配器的收起键盘原语（Android 一条驱动命令，iOS 读控件树、
// 经类链查询取句柄后点击元素）；动作之后核键盘是否仍在。另有接缝模块控件树解析的用例。运行：node --import tsx --test。
import { test } from "node:test";
import assert from "node:assert";
import { AppiumInterface, DISMISS_KEYBOARD_ACTION, keyboardNotDismissedMessage, parseXmlTree, scanXmlElements } from "./interface.mjs";
import { createUiAutomator2Adapter } from "./adapters/uiautomator2.mjs";
import { KEYBOARD_DISMISS_KEY_QUERY, createXcuitestAdapter } from "./adapters/xcuitest.mjs";

// 键盘里有 done 键的控件树（iOS 假驱动的 getPageSource 应答）
const KEYBOARD_DONE_TREE =
  '<AppiumAUT><XCUIElementTypeApplication type="XCUIElementTypeApplication" x="0" y="0" width="375" height="812" visible="true">' +
  '<XCUIElementTypeKeyboard type="XCUIElementTypeKeyboard" x="0" y="521" width="375" height="233" visible="true">' +
  '<XCUIElementTypeButton type="XCUIElementTypeButton" name="Return" label="done" x="281" y="690" width="94" height="46" visible="true" enabled="true"/>' +
  "</XCUIElementTypeKeyboard></XCUIElementTypeApplication></AppiumAUT>";

/** 只记录调用的假驱动：收起键盘路线里最后一条有副作用的命令（Android 的 hideKeyboard、iOS 的 elementClick）可按需抛出。 */
function fakeDriver(opts: { hideFails?: boolean; keyboardStays?: boolean } = {}) {
  const calls: string[] = [];
  const fail = () => { if (opts.hideFails) throw new Error("WebDriverError: cannot hide keyboard"); };
  return {
    calls,
    hideKeyboard: async () => { calls.push("hideKeyboard"); fail(); },
    getPageSource: async () => { calls.push("getPageSource"); return KEYBOARD_DONE_TREE; },
    findElements: async (using: string, query: string) => {
      calls.push(`findElements:${using}:${query === KEYBOARD_DISMISS_KEY_QUERY ? "keyboard" : "other"}`);
      return [{ "element-6066-11e4-a52e-4f735466cecf": "key-1" }];
    },
    getElementRect: async () => { calls.push("getElementRect"); return { x: 0, y: 0, width: 0, height: 0 }; },
    elementClick: async (id: string) => { calls.push(`elementClick:${id}`); fail(); },
    execute: async (cmd: string) => { calls.push(`execute:${cmd}`); },
    isKeyboardShown: async () => { calls.push("isKeyboardShown"); return opts.keyboardStays ?? false; },
    takeScreenshot: async () => "",
  };
}

function iface(adapter: any, driver: any, logs: string[]) {
  return new AppiumInterface({
    driver, adapter, scale: 1, inputContext: null,
    session: { withWebContext: async (_d: unknown, fn: (d: unknown) => Promise<unknown>) => fn(driver) } as any,
    log: (line) => { logs.push(line); },
  });
}

for (const [label, adapter, hideCalls] of [
  ["Android", createUiAutomator2Adapter({ foregroundPoll: { attempts: 1, intervalMs: 0 } }), ["hideKeyboard"]],
  ["iOS", createXcuitestAdapter(), ["getPageSource", "findElements:-ios class chain:keyboard", "elementClick:key-1"]],
] as const) {
  test(`${label}：动作集含「收起键盘」动作，调用即走一次收起键盘路线并核键盘是否仍在，系统按键动作照常在`, async () => {
    const driver = fakeDriver();
    const logs: string[] = [];
    const actions = iface(adapter, driver, logs).actionSpace();
    const names = actions.map((a) => a.name);
    assert.ok(names.includes(DISMISS_KEYBOARD_ACTION), names.join(","));
    assert.ok(names.includes(adapter.systemButtons.home.action.name), names.join(","));
    if (adapter.systemButtons.back) assert.ok(names.includes(adapter.systemButtons.back.action.name));
    const dismiss = actions.find((a) => a.name === DISMISS_KEYBOARD_ACTION)!;
    assert.match(dismiss.description, /keyboard/i);
    // 说明按平台分写：iOS 说明只点收起控件、不按 Return；Android 不提 Done 这类控件
    assert.equal(/never presses Return/.test(dismiss.description), label === "iOS", dismiss.description);
    assert.equal(/Done/.test(dismiss.description), label === "iOS", dismiss.description);
    assert.ok(!dismiss.paramSchema, "无参数");
    await dismiss.call(undefined as never);
    assert.deepEqual(driver.calls, [...hideCalls, "isKeyboardShown"]);
    assert.deepEqual(logs, []);
  });

  test(`${label}：「收起键盘」动作：命令报错但键盘已不在时只记一行日志、不抛出；键盘仍在时抛出产品语言的原因`, async () => {
    const driver = fakeDriver({ hideFails: true });
    const logs: string[] = [];
    const dismiss = iface(adapter, driver, logs).actionSpace().find((a) => a.name === DISMISS_KEYBOARD_ACTION)!;
    await dismiss.call(undefined as never);
    assert.equal(logs.length, 1);
    assert.match(logs[0], /^worker: 「收起键盘」动作的收起命令报错：/);
    const stays = iface(adapter, fakeDriver({ keyboardStays: true }), []).actionSpace().find((a) => a.name === DISMISS_KEYBOARD_ACTION)!;
    await assert.rejects(stays.call(undefined as never),
      (e: Error) => e.message === keyboardNotDismissedMessage(label === "iOS" ? "ios" : "android", "not_dismissed"));
  });
}

test("parseXmlTree：层级、自闭合、处理指令与注释、不成对的结束标签、实体解码；scanXmlElements 是它的文档顺序扁平视图", () => {
  const xml = `<?xml version="1.0"?><!-- 注释 --><root a="1"><a x="&lt;&gt;" /><b><c label='q&quot;'></c></zzz></b><d/></root>`;
  const roots = parseXmlTree(xml);
  assert.equal(roots.length, 1);
  const root = roots[0];
  assert.deepEqual(root.children.map((n) => n.tag), ["a", "b", "d"]);
  assert.deepEqual(root.children[1].children.map((n) => n.tag), ["c"]);
  assert.equal(root.children[0].attrs.get("x"), "<>");
  assert.equal(root.children[1].children[0].attrs.get("label"), 'q"');
  assert.deepEqual(scanXmlElements(xml).map((e) => e.tag), ["root", "a", "b", "c", "d"]);
  assert.throws(() => parseXmlTree("not xml"), /不是可识别的 XML/);
  assert.throws(() => scanXmlElements("<?xml version=\"1.0\"?>"), /不是可识别的 XML/);
});
