// 界面实现的动作集（ADR 0052 决策 3、7）：两平台都注册「收起键盘」动作，调适配器的收起键盘原语；失败是尽力动作、只记一行日志。
// 运行：node --import tsx --test。
import { test } from "node:test";
import assert from "node:assert";
import { AppiumInterface, DISMISS_KEYBOARD_ACTION } from "./interface.mjs";
import { createUiAutomator2Adapter } from "./adapters/uiautomator2.mjs";
import { createXcuitestAdapter } from "./adapters/xcuitest.mjs";

/** 只记录调用的假驱动：hideKeyboard 可按需抛出。 */
function fakeDriver(opts: { hideFails?: boolean } = {}) {
  const calls: string[] = [];
  return {
    calls,
    hideKeyboard: async () => { calls.push("hideKeyboard"); if (opts.hideFails) throw new Error("WebDriverError: cannot hide keyboard"); },
    execute: async (cmd: string) => { calls.push(`execute:${cmd}`); },
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

for (const [label, adapter] of [
  ["Android", createUiAutomator2Adapter({ foregroundPoll: { attempts: 1, intervalMs: 0 } })],
  ["iOS", createXcuitestAdapter()],
] as const) {
  test(`${label}：动作集含「收起键盘」动作，调用即发一条 hideKeyboard，系统按键动作照常在`, async () => {
    const driver = fakeDriver();
    const logs: string[] = [];
    const actions = iface(adapter, driver, logs).actionSpace();
    const names = actions.map((a) => a.name);
    assert.ok(names.includes(DISMISS_KEYBOARD_ACTION), names.join(","));
    assert.ok(names.includes(adapter.systemButtons.home.action.name), names.join(","));
    if (adapter.systemButtons.back) assert.ok(names.includes(adapter.systemButtons.back.action.name));
    const dismiss = actions.find((a) => a.name === DISMISS_KEYBOARD_ACTION)!;
    assert.match(dismiss.description, /keyboard/i);
    assert.ok(!dismiss.paramSchema, "无参数");
    await dismiss.call(undefined as never);
    assert.deepEqual(driver.calls, ["hideKeyboard"]);
    assert.deepEqual(logs, []);
  });

  test(`${label}：「收起键盘」动作失败只记一行日志、不抛出`, async () => {
    const driver = fakeDriver({ hideFails: true });
    const logs: string[] = [];
    const dismiss = iface(adapter, driver, logs).actionSpace().find((a) => a.name === DISMISS_KEYBOARD_ACTION)!;
    await dismiss.call(undefined as never);
    assert.equal(logs.length, 1);
    assert.match(logs[0], /^worker: 「收起键盘」动作未能收起软键盘（不影响这一步的判定）：/);
  });
}
