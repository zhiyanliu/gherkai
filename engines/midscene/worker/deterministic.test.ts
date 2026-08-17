// 确定性注册表单测（ADR 0022）——node:test via tsx，不连 AWS、不起浏览器。
// 跑：node --import tsx --test worker/deterministic.test.ts
import { test, beforeEach } from "node:test";
import assert from "node:assert";
import {
  deterministic,
  match,
  matchBatch,
  _clear,
  DeterministicConflict,
  DeterministicAssertion,
  listRegistry,
} from "./deterministic.ts";

beforeEach(() => _clear());

test("注册并命中，返回 handler + 具名组", () => {
  const calls: Array<Record<string, string>> = [];
  deterministic('页面地址匹配 "(?<pattern>.+)"', (_ctx, groups) => {
    calls.push(groups);
  }, { description: "测试", example: "Then 测试" });
  const hit = match('页面地址匹配 "/wiki/OpenAI"');
  assert.ok(hit, "应命中");
  assert.deepEqual(hit!.groups, { pattern: "/wiki/OpenAI" });
});

test("未命中返回 null（走 AI catch-all）", () => {
  deterministic('页面地址匹配 "(?<pattern>.+)"', () => {}, { description: "测试", example: "Then 测试" });
  assert.equal(match("搜索 OpenAI"), null);
});

test("命中多条 → DeterministicConflict（ADR 0022：最多一条）", () => {
  deterministic("地址(?<a>.+)", () => {}, { description: "测试", example: "Then 测试" });
  deterministic("(?<b>地址.+)", () => {}, { description: "测试", example: "Then 测试" });
  assert.throws(() => match("地址匹配 x"), DeterministicConflict);
});

test("handler 抛 DeterministicAssertion 可被识别为 failed", () => {
  deterministic("必假", () => {
    throw new DeterministicAssertion("故意失败");
  }, { description: "测试", example: "Then 测试" });
  const hit = match("必假");
  assert.ok(hit);
  assert.throws(() => hit!.handler({ page: {} as any }, hit!.groups), DeterministicAssertion);
});

test("无具名组 → groups 为空对象", () => {
  deterministic("固定文本", () => {}, { description: "测试", example: "Then 测试" });
  const hit = match("固定文本");
  assert.deepEqual(hit!.groups, {});
});

test("缺元数据注册 fail-loud（ADR 0036：能力必须可发现）", () => {
  assert.throws(() => deterministic("x", () => {}, undefined as any), /description\/example/);
  assert.throws(() => deterministic("x", () => {}, { description: "", example: "y" }), /description\/example/);
});

test("listRegistry 自述含 pattern/description/example（ADR 0036）", () => {
  deterministic('页面地址匹配 "(?<p>.+)"', () => {}, { description: "断言 URL", example: 'Then 页面地址匹配 "/x"' });
  assert.deepEqual(listRegistry(), [
    { pattern: '页面地址匹配 "(?<p>.+)"', description: "断言 URL", example: 'Then 页面地址匹配 "/x"' },
  ]);
});


test("matchBatch：命中/未命中/冲突结构化返回（ADR 0036 第二期，冲突不抛）", () => {
  deterministic('页面地址匹配 "(?<p>[^"]+)"', () => {}, { description: "断言 URL", example: "Then …" });
  deterministic("地址(?<a>.+)", () => {}, { description: "x", example: "y" });
  const got = matchBatch(['页面地址匹配 "x"', "无关文本", "地址什么的"]);
  assert.deepEqual(got[0], { conflict: ['页面地址匹配 "(?<p>[^"]+)"', "地址(?<a>.+)"] });
  assert.equal(got[1], null);
  assert.deepEqual(got[2], { pattern: "地址(?<a>.+)", description: "x" });
});
