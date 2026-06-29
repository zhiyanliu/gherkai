// 确定性注册表单测（ADR 0022）——node:test via tsx，不连 AWS、不起浏览器。
// 跑：node --import tsx --test worker/deterministic.test.ts
import { test, beforeEach } from "node:test";
import assert from "node:assert";
import {
  deterministic,
  match,
  _clear,
  DeterministicConflict,
  DeterministicAssertion,
} from "./deterministic.ts";

beforeEach(() => _clear());

test("注册并命中，返回 handler + 具名组", () => {
  const calls: Array<Record<string, string>> = [];
  deterministic('页面地址匹配 "(?<pattern>.+)"', (_ctx, groups) => {
    calls.push(groups);
  });
  const hit = match('页面地址匹配 "/wiki/OpenAI"');
  assert.ok(hit, "应命中");
  assert.deepEqual(hit!.groups, { pattern: "/wiki/OpenAI" });
});

test("未命中返回 null（走 AI catch-all）", () => {
  deterministic('页面地址匹配 "(?<pattern>.+)"', () => {});
  assert.equal(match("搜索 OpenAI"), null);
});

test("命中多条 → DeterministicConflict（ADR 0022：最多一条）", () => {
  deterministic("地址(?<a>.+)", () => {});
  deterministic("(?<b>地址.+)", () => {});
  assert.throws(() => match("地址匹配 x"), DeterministicConflict);
});

test("handler 抛 DeterministicAssertion 可被识别为 failed", () => {
  deterministic("必假", () => {
    throw new DeterministicAssertion("故意失败");
  });
  const hit = match("必假");
  assert.ok(hit);
  assert.throws(() => hit!.handler({ page: {} as any }, hit!.groups), DeterministicAssertion);
});

test("无具名组 → groups 为空对象", () => {
  deterministic("固定文本", () => {});
  const hit = match("固定文本");
  assert.deepEqual(hit!.groups, {});
});
