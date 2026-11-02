// 设备限值里读 env 的两个函数：重规划上限的覆盖键（ADR 0044 决策 2；缺省值的依据见 ADR 0052 决策 6）与截图缩放的实验开关（ADR 0052 第 9 节）。
// 运行：npx tsx --test src/device/limits.test.mts。由常量推出的会话上限与收尾之和在 worker/no-device-deps.test.mts 里核对，
// 那里同时守本文件所测模块的加载闭包零 SDK。
import { test } from "node:test";
import assert from "node:assert";
import { DEVICE_REPLANNING_CYCLE_LIMIT, REPLANNING_LIMIT_ENV, SCREENSHOT_SHRINK_ENV, replanningCycleLimit, screenshotShrinkFactor } from "./limits.mjs";

test("覆盖键与 Midscene SDK 自己读的 env 同名，缺省值为 12（ADR 0044 决策 2、ADR 0052 决策 6）", () => {
  assert.equal(REPLANNING_LIMIT_ENV, "MIDSCENE_REPLANNING_CYCLE_LIMIT");
  assert.equal(DEVICE_REPLANNING_CYCLE_LIMIT, 12);
});

test("缺省：env 里没有这个键时取缺省值，别的键不影响取值", () => {
  assert.equal(replanningCycleLimit({}), DEVICE_REPLANNING_CYCLE_LIMIT);
  assert.equal(replanningCycleLimit({ MIDSCENE_MODEL_ID: "us.openai.gpt-6-astra" }), DEVICE_REPLANNING_CYCLE_LIMIT);
});

test("缺省参数读进程 env", () => {
  const saved = process.env[REPLANNING_LIMIT_ENV];
  try {
    delete process.env[REPLANNING_LIMIT_ENV];
    assert.equal(replanningCycleLimit(), DEVICE_REPLANNING_CYCLE_LIMIT);
    process.env[REPLANNING_LIMIT_ENV] = "7";
    assert.equal(replanningCycleLimit(), 7);
    process.env[REPLANNING_LIMIT_ENV] = "0";
    assert.throws(() => replanningCycleLimit(), new RegExp(REPLANNING_LIMIT_ENV));
  } finally {
    if (saved === undefined) delete process.env[REPLANNING_LIMIT_ENV]; else process.env[REPLANNING_LIMIT_ENV] = saved;
  }
});

test("合法：十进制正整数按值生效，首尾空白与前导零按 SDK 的读法忽略", () => {
  for (const [raw, want] of [["1", 1], ["12", 12], ["20", 20], ["100", 100], [" 8 ", 8], ["012", 12]] as const) {
    assert.equal(replanningCycleLimit({ [REPLANNING_LIMIT_ENV]: raw }), want, JSON.stringify(raw));
  }
});

test("非法：空串、零、负数、小数、指数写法、非数字与超出安全整数的值都抛出，消息点名该键并给出原值", () => {
  for (const bad of ["", "   ", "0", "00", "-1", "+5", "1.5", "12.0", "1e3", "0x10", "abc", "12abc", "Infinity", "99999999999999999999"]) {
    assert.throws(() => replanningCycleLimit({ [REPLANNING_LIMIT_ENV]: bad }), (e: unknown) => {
      assert.ok(e instanceof Error, JSON.stringify(bad));
      assert.match(e.message, new RegExp(REPLANNING_LIMIT_ENV), JSON.stringify(bad));
      assert.ok(e.message.includes(JSON.stringify(bad)), `消息应给出原值 ${JSON.stringify(bad)}：${e.message}`);
      // 给使用方看的消息：说清怎么改，不带设计文档编号
      assert.match(e.message, /正整数/);
      assert.doesNotMatch(e.message, /ADR|决策/);
      return true;
    });
  }
});

test("截图缩放实验开关：不设、空串、恰为 1 都返回 undefined（构造项不带这个键）；≥1 的数原样返回；小于 1、非数即抛出并点名该键", () => {
  assert.equal(SCREENSHOT_SHRINK_ENV, "GHERKAI_EXPERIMENT_SCREENSHOT_SHRINK");
  assert.equal(screenshotShrinkFactor({}), undefined);
  assert.equal(screenshotShrinkFactor({ [SCREENSHOT_SHRINK_ENV]: "" }), undefined);
  assert.equal(screenshotShrinkFactor({ [SCREENSHOT_SHRINK_ENV]: " 1 " }), undefined);
  assert.equal(screenshotShrinkFactor({ [SCREENSHOT_SHRINK_ENV]: "2" }), 2);
  assert.equal(screenshotShrinkFactor({ [SCREENSHOT_SHRINK_ENV]: "2.625" }), 2.625);
  for (const bad of ["0.5", "0", "-2", "abc", "Infinity"]) {
    assert.throws(() => screenshotShrinkFactor({ [SCREENSHOT_SHRINK_ENV]: bad }), new RegExp(SCREENSHOT_SHRINK_ENV), bad);
  }
});
