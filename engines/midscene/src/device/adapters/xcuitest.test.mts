// XCUITest 适配器的收起键盘原语（ADR 0052 决策 4）：从原生控件树里选收起控件（键盘子树里收起语义的键，或紧贴键盘上方工具栏里的
// 收起按钮），经类链查询取句柄后点击元素，多个句柄按矩形核对。夹具是四份真机控件树：Safari 与示例应用在 iOS 18.6 / 26.3.1 上键盘
// 显示时采集（fixtures/ios*-keyboard.xml）。运行：node --import tsx --test。
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";
import assert from "node:assert";
import {
  ACCESSORY_DISMISS_BUTTON_QUERY, ACCESSORY_TOOLBAR_MAX_GAP, DISMISS_CONTROL_AMBIGUOUS_MESSAGE, DISMISS_CONTROL_VANISHED_MESSAGE,
  IOS_DISMISS_KEY_LABELS, KEYBOARD_DISMISS_KEY_QUERY, NO_DISMISS_CONTROL_MESSAGE, createXcuitestAdapter, findDismissControl,
} from "./xcuitest.mjs";
import { isNoDismissControlError, type PrimitiveContext } from "../interface.mjs";

const FIXTURES = path.join(import.meta.dirname, "fixtures");
const tree = (name: string): string => fs.readFileSync(path.join(FIXTURES, name), "utf-8");
const REF = "element-6066-11e4-a52e-4f735466cecf";

// ---- 合成控件树的小工具 ----
type Rect = { x: number; y: number; width: number; height: number };
const attrs = (r: Rect, extra = ""): string => `x="${r.x}" y="${r.y}" width="${r.width}" height="${r.height}" ${extra}`;
const app = (...children: string[]): string =>
  `<AppiumAUT><XCUIElementTypeApplication type="XCUIElementTypeApplication" ${attrs({ x: 0, y: 0, width: 390, height: 844 }, 'visible="true"')}>`
  + children.join("") + "</XCUIElementTypeApplication></AppiumAUT>";
const window = (visible: boolean, ...children: string[]): string =>
  `<XCUIElementTypeWindow type="XCUIElementTypeWindow" ${attrs({ x: 0, y: 0, width: 390, height: 844 }, `visible="${visible}"`)}>${children.join("")}</XCUIElementTypeWindow>`;
const KEYBOARD_RECT: Rect = { x: 0, y: 553, width: 390, height: 234 };
const keyboard = (keys: string, rect: Rect = KEYBOARD_RECT, visible = true): string =>
  `<XCUIElementTypeKeyboard type="XCUIElementTypeKeyboard" ${attrs(rect, `visible="${visible}"`)}>${keys}</XCUIElementTypeKeyboard>`;
const key = (type: "Key" | "Button", label: string, rect: Rect, visible = true): string =>
  `<XCUIElementType${type} type="XCUIElementType${type}" name="${label}" label="${label}" ${attrs(rect, `visible="${visible}" enabled="true"`)}/>`;
const toolbar = (rect: Rect, buttons: string, visible = true): string =>
  `<XCUIElementTypeToolbar type="XCUIElementTypeToolbar" name="Toolbar" ${attrs(rect, `visible="${visible}"`)}>${buttons}</XCUIElementTypeToolbar>`;
const button = (label: string, rect: Rect, opts: { enabled?: boolean; visible?: boolean; type?: string } = {}): string =>
  `<XCUIElementType${opts.type ?? "Button"} type="XCUIElementType${opts.type ?? "Button"}" name="${label}" label="${label}" `
  + `${attrs(rect, `visible="${opts.visible ?? true}" enabled="${opts.enabled ?? true}"`)}/>`;
const SEARCH_KEY = key("Button", "search", { x: 292, y: 722, width: 98, height: 47 });
const DONE_RECT: Rect = { x: 324, y: 509, width: 66, height: 44 };
const TOOLBAR_RECT: Rect = { x: 0, y: 509, width: 390, height: 44 };

test("Safari：两代 iOS 上都选到键盘上方工具栏里的 Done；键盘自身的回车键面是 search，不算收起键", () => {
  assert.deepEqual(findDismissControl(tree("ios18-safari-keyboard.xml")),
    { route: "toolbar", label: "Done", rect: { x: 324, y: 509, width: 66, height: 44 } });
  assert.deepEqual(findDismissControl(tree("ios26-safari-keyboard.xml")),
    { route: "toolbar", label: "Done", rect: { x: 341, y: 513, width: 40, height: 38 } });
});

test("示例应用：键盘里只有键面为 return 的回车键、没有工具栏，两代 iOS 上都没有收起控件", () => {
  for (const name of ["ios18-sample-app-keyboard.xml", "ios26-sample-app-keyboard.xml"]) {
    const src = tree(name);
    assert.ok(src.includes('name="Return" label="return"'), name);
    assert.equal(findDismissControl(src), null, name);
  }
});

test("键盘里的回车键面配成 done 时选键盘路线（键盘路线优先于工具栏）；键面只比对 label、只忽略大小写——与类链查询的 ==[c] 同口径", () => {
  const sample = tree("ios18-sample-app-keyboard.xml");
  const relabel = (label: string): string => sample.replace('name="Return" label="return"', `name="Return" label="${label}"`);
  assert.deepEqual(findDismissControl(relabel("DONE")), { route: "keyboard", label: "DONE", rect: { x: 281, y: 690, width: 94, height: 46 } });
  assert.equal(findDismissControl(relabel(" Done ")), null, "带首尾空白的 label 查询查不到，树上也不选");
  assert.equal(findDismissControl(sample.replace('name="Return" label="return"', 'name="Done" label=""')), null, "label 为空不回落到 name");
  const both = app(window(false, toolbar(TOOLBAR_RECT, button("Done", DONE_RECT))),
    window(true, keyboard(key("Button", "完成", { x: 292, y: 722, width: 98, height: 47 }))));
  assert.deepEqual(findDismissControl(both), { route: "keyboard", label: "完成", rect: { x: 292, y: 722, width: 98, height: 47 } });
});

test("键盘不在树里、不可见或零尺寸：没有东西要收", () => {
  assert.equal(findDismissControl(app(window(true, button("Done", DONE_RECT)))), "no_keyboard");
  assert.equal(findDismissControl(app(window(true, keyboard(SEARCH_KEY, KEYBOARD_RECT, false)))), "no_keyboard");
  assert.equal(findDismissControl(app(window(true, keyboard(SEARCH_KEY, { ...KEYBOARD_RECT, height: 0 })))), "no_keyboard");
});

test("工具栏要紧贴键盘上方且可用：离得太远、在键盘之下、水平不重叠、不可见的工具栏都不算；不可用、不可见、非按钮的 Done 不算", () => {
  const kb = window(true, keyboard(SEARCH_KEY));
  const withToolbar = (rect: Rect, done = button("Done", DONE_RECT), visible = true): string => app(window(false, toolbar(rect, done, visible)), kb);
  assert.ok(findDismissControl(withToolbar(TOOLBAR_RECT)) !== null, "紧贴");
  assert.ok(findDismissControl(withToolbar({ ...TOOLBAR_RECT, y: 553 - 44 - ACCESSORY_TOOLBAR_MAX_GAP })) !== null, "间距恰为上限");
  assert.equal(findDismissControl(withToolbar({ ...TOOLBAR_RECT, y: 553 - 44 - ACCESSORY_TOOLBAR_MAX_GAP - 1 })), null, "超过上限");
  assert.equal(findDismissControl(withToolbar({ ...TOOLBAR_RECT, y: 800 })), null, "在键盘之下");
  assert.equal(findDismissControl(withToolbar({ ...TOOLBAR_RECT, x: 390 })), null, "水平不重叠");
  assert.equal(findDismissControl(withToolbar(TOOLBAR_RECT, button("Done", DONE_RECT), false)), null, "工具栏不可见");
  assert.equal(findDismissControl(withToolbar(TOOLBAR_RECT, button("Done", DONE_RECT, { enabled: false }))), null, "按钮不可用");
  assert.equal(findDismissControl(withToolbar(TOOLBAR_RECT, button("Done", DONE_RECT, { visible: false }))), null, "按钮不可见");
  assert.equal(findDismissControl(withToolbar(TOOLBAR_RECT, button("Done", DONE_RECT, { type: "StaticText" }))), null, "不是按钮");
  assert.equal(findDismissControl(withToolbar(TOOLBAR_RECT, button("Next", DONE_RECT))), null, "标签不是收起语义");
  assert.deepEqual(findDismissControl(withToolbar(TOOLBAR_RECT, button("Previous", { x: 0, y: 509, width: 48, height: 44 }) + button("隐藏键盘", DONE_RECT))),
    { route: "toolbar", label: "隐藏键盘", rect: DONE_RECT });
});

test("标签表只含纯收起语义，两条类链查询都带全部标签、各限定在键盘子树与工具栏子树", () => {
  for (const l of IOS_DISMISS_KEY_LABELS) {
    assert.ok(!/^(return|search|go|next|send|join|换行|搜索|前往|发送|下一项)$/i.test(l), l);
    for (const q of [KEYBOARD_DISMISS_KEY_QUERY, ACCESSORY_DISMISS_BUTTON_QUERY]) assert.ok(q.includes(`label ==[c] ${JSON.stringify(l)}`), `${q} ${l}`);
  }
  assert.ok(KEYBOARD_DISMISS_KEY_QUERY.startsWith("**/XCUIElementTypeKeyboard/**/*[`"));
  assert.ok(ACCESSORY_DISMISS_BUTTON_QUERY.startsWith("**/XCUIElementTypeToolbar/**/XCUIElementTypeButton[`"));
});

// ---- 原语：读树、查元素、点击 ----

function fakeCtx(source: string, refs: unknown, rects: Record<string, unknown> = {}) {
  const calls: string[] = [];
  const driver = {
    getPageSource: async () => { calls.push("getPageSource"); return source; },
    findElements: async (using: string, query: string) => {
      const which = query === KEYBOARD_DISMISS_KEY_QUERY ? "keyboard" : query === ACCESSORY_DISMISS_BUTTON_QUERY ? "toolbar" : "?";
      calls.push(`findElements ${using} ${which}`);
      return refs;
    },
    getElementRect: async (id: string) => { calls.push(`getElementRect ${id}`); return rects[id]; },
    elementClick: async (id: string) => { calls.push(`elementClick ${id}`); },
  };
  const ctx = { driver, scale: 3, inputContext: "native", withWebContext: async (fn: () => unknown) => fn() } as unknown as PrimitiveContext;
  return { calls, ctx };
}

test("hideKeyboard：单个句柄直接点击；多个句柄按矩形核对后点与控件树一致的那个", async () => {
  const adapter = createXcuitestAdapter();
  const one = fakeCtx(tree("ios18-safari-keyboard.xml"), [{ [REF]: "done-1" }]);
  await adapter.hideKeyboard(one.ctx);
  assert.deepEqual(one.calls, ["getPageSource", "findElements -ios class chain toolbar", "elementClick done-1"]);
  const many = fakeCtx(tree("ios18-safari-keyboard.xml"), [{ [REF]: "far-1" }, { ELEMENT: "done-1" }],
    { "far-1": { x: 0, y: 100, width: 60, height: 44 }, "done-1": { x: 324, y: 509, width: 66, height: 44 } });
  await adapter.hideKeyboard(many.ctx);
  assert.deepEqual(many.calls, ["getPageSource", "findElements -ios class chain toolbar", "getElementRect far-1", "getElementRect done-1", "elementClick done-1"]);
  const keyRoute = fakeCtx(tree("ios18-sample-app-keyboard.xml").replace('label="return"', 'label="done"'), [{ [REF]: "key-1" }]);
  await adapter.hideKeyboard(keyRoute.ctx);
  assert.deepEqual(keyRoute.calls, ["getPageSource", "findElements -ios class chain keyboard", "elementClick key-1"]);
});

test("hideKeyboard：没有句柄、句柄都与控件树位置不符、树里没有收起控件各抛出自己的原因且不点击；键盘不在树里则只读树", async () => {
  const adapter = createXcuitestAdapter();
  const none = fakeCtx(tree("ios18-safari-keyboard.xml"), []);
  await assert.rejects(adapter.hideKeyboard(none.ctx), (e: Error) => e.message === DISMISS_CONTROL_VANISHED_MESSAGE);
  const ambiguous = fakeCtx(tree("ios18-safari-keyboard.xml"), [{ [REF]: "a" }, { [REF]: "b" }],
    { a: { x: 0, y: 0, width: 1, height: 1 }, b: { x: 324, y: 509, width: 66, height: 40 } });
  await assert.rejects(adapter.hideKeyboard(ambiguous.ctx), (e: Error) => e.message === DISMISS_CONTROL_AMBIGUOUS_MESSAGE);
  const noControl = fakeCtx(tree("ios26-sample-app-keyboard.xml"), [{ [REF]: "x" }]);
  await assert.rejects(adapter.hideKeyboard(noControl.ctx), (e: Error) => e.message === NO_DISMISS_CONTROL_MESSAGE && isNoDismissControlError(e));
  await assert.rejects(adapter.hideKeyboard(fakeCtx(tree("ios18-safari-keyboard.xml"), []).ctx), (e: Error) => !isNoDismissControlError(e));
  assert.deepEqual(noControl.calls, ["getPageSource"]);
  const noKeyboard = fakeCtx(app(window(true, button("Done", DONE_RECT))), [{ [REF]: "x" }]);
  await adapter.hideKeyboard(noKeyboard.ctx);
  assert.deepEqual(noKeyboard.calls, ["getPageSource"]);
  for (const c of [none, ambiguous, noControl, noKeyboard]) assert.ok(!c.calls.some((x) => x.startsWith("elementClick")));
});
