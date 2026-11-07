// 设备模块缺省等待的单测。运行：npx tsx --test src/device/sleep.test.mts。
//
// 引用方的单测都注入自己的等待，缺省实现只在这里核：到时结束、信号中止时提前结束且不抛出、已中止的信号立即结束，结束之后信号上
// 不残留监听（应用启动采样等调用方在同一个获取预算信号上多次等待，残留的监听会随等待次数累积）。用真实计时器，等待取短值。
import { test } from "node:test";
import assert from "node:assert";
import { getEventListeners } from "node:events";
import { defaultSleep } from "./sleep.mjs";

test("不带信号：到时结束", async () => {
  const start = performance.now();
  await defaultSleep(30);
  assert.ok(performance.now() - start >= 25, "应等到给定的时长");
});

test("带信号且到时结束：结束之后摘掉信号上的监听", async () => {
  const controller = new AbortController();
  await defaultSleep(10, controller.signal);
  assert.strictEqual(getEventListeners(controller.signal, "abort").length, 0);
});

test("等待中信号中止：提前结束、不抛出，并摘掉监听", async () => {
  const controller = new AbortController();
  const start = performance.now();
  const pending = defaultSleep(10_000, controller.signal);
  assert.strictEqual(getEventListeners(controller.signal, "abort").length, 1, "等待期间应挂着一个中止监听");
  setTimeout(() => controller.abort(new Error("stop")), 10);
  await pending;
  assert.ok(performance.now() - start < 5_000, "中止之后应立即结束，不等满给定的时长");
  assert.strictEqual(getEventListeners(controller.signal, "abort").length, 0);
});

test("信号已中止：立即结束，不挂监听", async () => {
  const controller = new AbortController();
  controller.abort(new Error("stop"));
  const start = performance.now();
  await defaultSleep(10_000, controller.signal);
  assert.ok(performance.now() - start < 5_000);
  assert.strictEqual(getEventListeners(controller.signal, "abort").length, 0);
});
