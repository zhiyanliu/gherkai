// 确定性注册表单测（ADR 0022）——node:test via tsx，不连 AWS、不起浏览器。
// 运行：npm test（node --import tsx --test "src/**/*.test.mts"）
import { test, beforeEach } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { ADDRESS_PATTERN } from "./deterministic.steps.mjs";  // 内建导航条目的模式（import 副作用注册的条目被 beforeEach 清掉）
import type { Keyword } from "./deterministic.mjs";
import {
  deterministic,
  match,
  matchBatch,
  _clear,
  DeterministicConflict,
  DeterministicAssertion,
  DeterministicKeywordMismatch,
  listRegistry,
} from "./deterministic.mjs";

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
    { pattern: '页面地址匹配 "(?<p>.+)"', description: "断言 URL", example: 'Then 页面地址匹配 "/x"', keywords: ["Given", "When", "Then"] },
  ]);  // 缺省接受全部关键字
});

test("keywords 声明：封闭集合、非空、不重复，自述按规范顺序（ADR 0050 决策 1）", () => {
  deterministic("仅 Then", () => {}, { description: "x", example: "y", keywords: ["Then"] });
  deterministic("先 When 后 Given", () => {}, { description: "x", example: "y", keywords: ["When", "Given"] });
  assert.deepEqual(listRegistry().map((e) => e.keywords), [["Then"], ["Given", "When"]]);
  assert.throws(() => deterministic("a", () => {}, { description: "x", example: "y", keywords: [] }), /不能为空/);
  assert.throws(() => deterministic("b", () => {}, { description: "x", example: "y", keywords: ["And" as any] }), /未知取值/);
  assert.throws(() => deterministic("c", () => {}, { description: "x", example: "y", keywords: ["Then", "Then"] }), /重复/);
});

test("match 在命中后核对关键字：不符 → DeterministicKeywordMismatch；不传关键字不核对（兼容）", () => {
  deterministic("仅给定", () => {}, { description: "x", example: "y", keywords: ["Given"] });
  assert.ok(match("仅给定", "Given"));
  assert.ok(match("仅给定"));
  assert.throws(() => match("仅给定", "Then"), (e: any) =>
    e instanceof DeterministicKeywordMismatch && /只在 Given 下有意义/.test(e.message) && /当前关键字是 Then/.test(e.message)
    && e.pattern === "仅给定" && JSON.stringify(e.keywords) === JSON.stringify(["Given"]));
});

test("matchBatch 的每项可带关键字：命中但不符 → keyword_mismatch；裸字符串不核对", () => {
  deterministic("仅给定", () => {}, { description: "x", example: "y", keywords: ["Given"] });
  const got = matchBatch([{ keyword: "Given", text: "仅给定" }, { keyword: "Then", text: "仅给定" },
    { keyword: "Then", text: "没命中" }, "仅给定"]);
  assert.deepEqual(got[0], { pattern: "仅给定", description: "x" });
  assert.deepEqual(got[1], { keyword_mismatch: "仅给定", keywords: ["Given"] });
  assert.equal(got[2], null);
  assert.deepEqual(got[3], { pattern: "仅给定", description: "x" });
});


test("matchBatch：命中/未命中/冲突结构化返回（ADR 0036 决策 4，冲突不抛）", () => {
  deterministic('页面地址匹配 "(?<p>[^"]+)"', () => {}, { description: "断言 URL", example: "Then …" });
  deterministic("地址(?<a>.+)", () => {}, { description: "x", example: "y" });
  const got = matchBatch(['页面地址匹配 "x"', "无关文本", "地址什么的"]);
  assert.deepEqual(got[0], { conflict: ['页面地址匹配 "(?<p>[^"]+)"', "地址(?<a>.+)"] });
  assert.equal(got[1], null);
  assert.deepEqual(got[2], { pattern: "地址(?<a>.+)", description: "x" });
});

test("内建导航模式的跨语言对拍：engines/fixtures 的用例集在 JS 侧给出相同的命中与 url 组（ADR 0020 第 3 条）", () => {
  // 用例集只有一份（engines/fixtures/navigation-address-cases.json），Nova 侧的 test_deterministic.py 读同一个文件。
  const file = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../fixtures/navigation-address-cases.json");
  const { cases } = JSON.parse(fs.readFileSync(file, "utf8")) as { cases: Array<{ text: string; hit: boolean; url?: string }> };
  assert.ok(cases.length >= 10);
  const re = new RegExp(ADDRESS_PATTERN);
  for (const c of cases) {
    const m = re.exec(c.text);
    assert.equal(m !== null, c.hit, JSON.stringify(c));
    if (m) assert.equal(m.groups?.url, c.url, JSON.stringify(c));
  }
});

test("注册表语义的跨语言对拍：同一组注册输入，清单的 keywords 与 matchBatch 对探针的回答与 Nova 侧一致（ADR 0050 决策 1、0022 冲突规则）", () => {
  // 夹具的 pattern 用 Python 具名组写法，这里换成 JS 方言；<NAV> 代入内建导航的 ADDRESS_PATTERN。
  const file = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../fixtures/navigation-address-cases.json");
  const reg = JSON.parse(fs.readFileSync(file, "utf8")).registry as {
    entries: Array<{ pattern: string; description: string; example: string; keywords?: Keyword[] }>;
    expected_keywords: string[][];
    probes: Array<{ keyword?: string; text: string; expect: unknown }>;
  };
  const sub = (v: unknown): unknown => {
    if (typeof v === "string") return v === "<NAV>" ? ADDRESS_PATTERN : v.replace(/\(\?P</g, "(?<");
    if (Array.isArray(v)) return v.map(sub);
    if (v && typeof v === "object") return Object.fromEntries(Object.entries(v).map(([k, x]) => [k, sub(x)]));
    return v;
  };
  _clear();
  for (const e of reg.entries) {
    deterministic(sub(e.pattern) as string, () => {}, { description: e.description, example: e.example, keywords: e.keywords });
  }
  assert.deepEqual(listRegistry().map((e) => e.keywords), reg.expected_keywords);
  for (const p of reg.probes) {
    const item = "keyword" in p ? { keyword: p.keyword, text: p.text } : p.text;
    assert.deepEqual(matchBatch([item]), [sub(p.expect)], JSON.stringify(p));
  }
});
