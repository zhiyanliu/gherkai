// 一行有界原因文本的边界单测（ADR 0042 决策一映射表 `act.error` / 决策三 `step_done.message`）。
// 运行：npm test（node --import tsx --test "src/**/*.test.mts"）。
//
// 主路径（多行超长 → 首个非空行 + 折叠空白 + 封顶）在 run-scope.test.mts 与 evidence.test.mts 各锁住一条，
// 这里锁住的是那两条照不出的抛出物形态与截断边界，逐条对称 Nova 侧 `_error_text` 的同名断言——两引擎同形
// 是 ADR 0042 的要求（同一份 feature 在两侧运行，「原因」不该一侧一行、另一侧上千字符），退回
// `${name}: ${message}` 的朴素写法时这些语义要有一条变红。
import { test } from "node:test";
import assert from "node:assert";
import { errorText, oneLineError } from "./error-text.mjs";

test("errorText: message 为空 → 只留类型（不留悬着的冒号）", () => {
  assert.equal(errorText(Object.assign(new Error(""), { name: "TimeoutError" })), "TimeoutError");
});

test("errorText: 不是 Error 的抛出物（字符串 / 裸对象）→ 整体压成一行", () => {
  assert.equal(errorText("boom"), "boom");
  assert.equal(errorText("boom\n第二行细节"), "boom");            // 没有 name 也照压一行
  assert.equal(errorText({ toString: () => "plain object" }), "plain object");
});

test("errorText: null / undefined → \"Error\"（message 字段不留空）", () => {
  assert.equal(errorText(null), "Error");
  assert.equal(errorText(undefined), "Error");
});

test("errorText: 超长 message 截到上界，类型前缀不占额度（同 Nova 的 first[:300]）", () => {
  assert.equal(errorText(new Error("x".repeat(500))).length, "Error: ".length + 300);
});

test("oneLineError: 截断按码点——非 BMP 字符压在边界上也不会被切成孤立代理项", () => {
  // 按码元截（String.prototype.slice）时第 300 个码元正好是代理对的前半：切出的孤立代理项会一路传到
  // core，落 jobs/*.json 与报告页时 utf-8 编码直接抛，该 job 的判定明细/报告整体写不下去。
  const got = oneLineError("x".repeat(299) + "😀" + "尾巴");
  assert.equal([...got].length, 300, "上界按码点算");
  assert.ok(got.endsWith("😀"), `边界上的字符要么整个留、要么整个丢：${JSON.stringify(got.slice(-3))}`);
  assert.equal(Buffer.from(got, "utf8").toString("utf8"), got, "须能无损 utf-8 编码（孤立代理项在这里现形）");
});
