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
  selectHandler,
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
  const sel = selectHandler(hit!, { device: "desktop", uiKind: "web" });
  assert.equal(sel?.kind, "playwright");
  assert.throws(() => (sel as any).fn({ page: {} as any }, hit!.groups), DeterministicAssertion);
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
    { pattern: '页面地址匹配 "(?<p>.+)"', description: "断言 URL", example: 'Then 页面地址匹配 "/x"', keywords: ["Given", "When", "Then"],
      targets: [{ device: "desktop", ui_kinds: ["web"] }] },  // 缺省接受全部关键字；只有 playwright 句柄 → 桌面网页（ADR 0050 决策 1）
  ]);
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

// ---- 多句柄注册面（ADR 0050 决策 1）：跨语言 fixture、单函数兼容、按目标选句柄、不顺延 ----

const HANDLES_FIXTURE = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../fixtures/deterministic-handles.json");
const META = { description: "d", example: "Given e" };

/** fixture 的 handlers 是协议面方言（snake_case、<fn> 占位）：换成 TS 注册面的形态。 */
function toHandlers(v: unknown): any {
  if (v === "<fn>") return () => {};
  if (v === "<not-a-function>") return 42;
  if (Array.isArray(v)) return v.map(toHandlers);
  if (v && typeof v === "object") {
    return Object.fromEntries(Object.entries(v).map(([k, x]) => [k === "ui_kinds" ? "uiKinds" : k, toHandlers(x)]));
  }
  return v;
}

test("多句柄注册的跨语言对拍：同一组注册输入推出的 targets 与 Nova 侧逐字节一致；非法输入两侧都在注册期失败（ADR 0050 决策 1）", () => {
  const fx = JSON.parse(fs.readFileSync(HANDLES_FIXTURE, "utf8")) as {
    valid: Array<{ name: string; handlers: unknown; targets: unknown }>;
    invalid: Array<{ name: string; handlers: unknown; error_contains: string }>;
  };
  for (const c of fx.valid) {
    _clear();
    deterministic("p", toHandlers(c.handlers), META);
    assert.deepEqual(listRegistry()[0].targets, c.targets, c.name);
  }
  for (const c of fx.invalid) {
    _clear();
    assert.throws(() => deterministic("p", toHandlers(c.handlers), META),
      (e: Error) => e.message.includes(c.error_contains), `${c.name}：消息应含「${c.error_contains}」`);
    assert.equal(listRegistry().length, 0, `${c.name}：注册失败不该留下条目`);
  }
});

test("单函数写法保持有效：targets 恰为 desktop/web，selectHandler(desktop/web) 返回它本身（ADR 0050 决策 1；0049 决策 2）", () => {
  const fn = () => {};
  deterministic("单函数", fn, META);
  assert.deepEqual(listRegistry()[0].targets, [{ device: "desktop", ui_kinds: ["web"] }]);
  const hit = match("单函数")!;
  assert.deepEqual(selectHandler(hit, { device: "desktop", uiKind: "web" }), { kind: "playwright", fn });
  assert.equal(selectHandler(hit, { device: "desktop", uiKind: "app" }), null);  // 桌面只有网页：别的界面类型取不到 playwright 句柄
  assert.equal(selectHandler(hit, { device: "android", uiKind: "web" }), null);
});

test("不顺延红线：命中与目标无关——只写 webdriver 的 A 与写 playwright 的 B 同时命中仍是冲突；只命中 A 时桌面上取不到句柄返回 null、不回落到 B；matchBatch 形态不变", () => {
  deterministic("地址(?<a>.+)", { webdriver: { uiKinds: ["app"], devices: ["android"], handler: () => {} } }, META);
  deterministic("(?<b>地址.+)", () => {}, META);
  assert.throws(() => match("地址匹配 x"), DeterministicConflict);
  _clear();
  deterministic("地址(?<a>.+)", { webdriver: { uiKinds: ["app"], devices: ["android"], handler: () => {} } }, META);
  deterministic("别的(?<b>.+)", () => {}, META);
  const hit = match("地址匹配 x")!;
  assert.equal(selectHandler(hit, { device: "desktop", uiKind: "web" }), null);
  assert.equal(selectHandler(hit, { device: "android", uiKind: "web" }), null);  // 条目只覆盖 android/app
  assert.equal(selectHandler(hit, { device: "ios", uiKind: "app" }), null);
  assert.equal(selectHandler(hit, { device: "android", uiKind: "app" })?.kind, "webdriver");
  assert.deepEqual(matchBatch([{ keyword: "When", text: "地址匹配 x" }]), [{ pattern: "地址(?<a>.+)", description: "d" }]);  // 无 targets 字段
});

test("地址核对的 webdriver 写法：requires web_context 的条目推出 desktop 无前提加 android / ios 带前提；用伪 ctx 调 handler 两向判定（ADR 0050 决策 1、2）", async () => {
  deterministic('页面地址匹配 "(?<pattern>[^"]+)"', {
    playwright: ({ page }, { pattern }) => { if (!new RegExp(pattern).test(page.url())) throw new DeterministicAssertion("地址不匹配"); },
    webdriver: [{ uiKinds: ["web"], requires: ["web_context"], handler: async (ctx, { pattern }) => ctx.withWebContext(async () => {
      const url = await ctx.driver.getUrl();
      if (!new RegExp(pattern).test(url)) throw new DeterministicAssertion(`地址 ${url} 不匹配 ${pattern}`);
    }) }],
  }, { description: "核对当前页面地址", example: 'Then 页面地址匹配 "/wiki/OpenAI"', keywords: ["Then"] });
  assert.deepEqual(listRegistry()[0].targets, [
    { device: "desktop", ui_kinds: ["web"] },
    { device: "android", ui_kinds: ["web"], requires: ["web_context"] },
    { device: "ios", ui_kinds: ["web"], requires: ["web_context"] },
  ]);
  const hit = match('页面地址匹配 "/wiki/OpenAI"', "Then")!;
  const sel = selectHandler(hit, { device: "android", uiKind: "web" });
  assert.equal(sel?.kind, "webdriver");
  assert.deepEqual((sel as any).requires, ["web_context"]);
  assert.equal(selectHandler(hit, { device: "android", uiKind: "app" }), null);
  const entered: string[] = [];
  const ctx = (url: string) => ({
    driver: { getUrl: async () => url } as any, device: { platform: "android", osVersion: "14", scale: 1 }, uiKind: "web", appId: null, app: null,
    log: () => {}, withWebContext: async <T,>(fn: () => Promise<T> | T) => { entered.push("in"); try { return await fn(); } finally { entered.push("out"); } },
  });
  await (sel as any).fn(ctx("https://x.example/wiki/OpenAI"), hit.groups);
  assert.deepEqual(entered, ["in", "out"]);
  await assert.rejects(() => (sel as any).fn(ctx("https://x.example/other"), hit.groups), DeterministicAssertion);
  assert.deepEqual(entered, ["in", "out", "in", "out"]);  // 抛错也切回
});
