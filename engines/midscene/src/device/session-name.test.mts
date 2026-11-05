// 会话名编码的单测（ADR 0051 决策 3；桌面请求名的长度上限见决策 4）。运行：npx tsx --test src/device/session-name.test.mts。
// 期望值里的哈希是用 shasum 另算后写死的字面量，不经被测模块复算，防止「哈希了编码段或截断后的串」这类错与实现一起漂。
import { test } from "node:test";
import assert from "node:assert";
import {
  AGENTCORE_SESSION_NAME_MAX, DEVICE_FARM_SESSION_NAME_MAX, RUN_ID_ENV, encode, runIdFromEnv, scopeHash,
} from "./session-name.mjs";

const RUN = "20260629T141207Z-a3f9c1";
const CHECKOUT_HASH = "c7761e58969f7edd";                    // sha256("checkout") 的前 16 位
const CJK_SCOPE = "登录 流程/a~b:c";
const CJK_HASH = "ab5bc226428ff117";                         // sha256(UTF-8 "登录 流程/a~b:c") 的前 16 位
const CJK_ENCODED = "%E7%99%BB%E5%BD%95%20%E6%B5%81%E7%A8%8B%2Fa%7Eb%3Ac";

// 测试内按段位取段：编码段不含冒号，取最后一个冒号之后的部分；RUN 不含冒号，按冒号切开后第三段是 scope 哈希。
const segmentOf = (name: string): string => name.slice(name.lastIndexOf(":") + 1);
const hashOf = (name: string): string => name.split(":")[2]!;

test("格式与段序：gherkai、run_id、scope 哈希、尝试序号、scope_id 编码，冒号分隔", () => {
  assert.equal(encode(RUN, "checkout", 1), `gherkai:${RUN}:${CHECKOUT_HASH}:1:checkout`);
  assert.equal(encode(RUN, "checkout", 0), `gherkai:${RUN}:${CHECKOUT_HASH}:0:checkout`);
  assert.equal(encode(RUN, "checkout", 27), `gherkai:${RUN}:${CHECKOUT_HASH}:27:checkout`);
});

test("scope 哈希：完整 scope_id 按 UTF-8 求 SHA-256，取前 16 位小写十六进制", () => {
  assert.equal(scopeHash("checkout"), CHECKOUT_HASH);
  assert.equal(scopeHash(CJK_SCOPE), CJK_HASH);
  assert.match(scopeHash(CJK_SCOPE), /^[0-9a-f]{16}$/);
  assert.equal(encode(RUN, CJK_SCOPE, 2), `gherkai:${RUN}:${CJK_HASH}:2:${CJK_ENCODED}`);
});

test("百分号编码：A-Z a-z 0-9 . _ - 原样保留，其余字符按 UTF-8 字节编成大写 %XX", () => {
  const seg = (scopeId: string) => segmentOf(encode(RUN, scopeId, 1));
  assert.equal(seg("AZaz09._-"), "AZaz09._-");
  // encodeURIComponent 放行的 ! ' ( ) * ~ 在这里一律编码；冒号与百分号本身也编码，编码段因此不含分隔符
  assert.equal(seg("!'()*~"), "%21%27%28%29%2A%7E");
  assert.equal(seg("a:b%c d+e/f"), "a%3Ab%25c%20d%2Be%2Ff");
  assert.equal(seg("é"), "%C3%A9");
  assert.equal(seg("😀"), "%F0%9F%98%80");                    // 四字节字符（JS 里是代理对）按码点整体编码
  assert.equal(seg(CJK_SCOPE), CJK_ENCODED);
});

test("长度上限：缺省 256，桌面请求名用 100", () => {
  assert.equal(DEVICE_FARM_SESSION_NAME_MAX, 256);
  assert.equal(AGENTCORE_SESSION_NAME_MAX, 100);
  const long = "s".repeat(400);
  assert.equal(encode(RUN, long, 1).length, 256);
  assert.equal(encode(RUN, long, 1, { maxLength: AGENTCORE_SESSION_NAME_MAX }).length, 100);
});

test("超长只截最后一段：其余四段原样保留，编码段是完整编码的前缀", () => {
  const long = "scope-".repeat(80);
  for (const maxLength of [DEVICE_FARM_SESSION_NAME_MAX, AGENTCORE_SESSION_NAME_MAX]) {
    const name = encode(RUN, long, 3, { maxLength });
    const head = `gherkai:${RUN}:${scopeHash(long)}:3:`;
    assert.ok(name.startsWith(head), name);
    assert.equal(name.length, maxLength);
    assert.ok(long.startsWith(name.slice(head.length)));
  }
  // 恰好等于上限时不截
  const head = `gherkai:${RUN}:${scopeHash("x")}:1:`;
  const exact = "a".repeat(AGENTCORE_SESSION_NAME_MAX - head.length);
  assert.equal(encode(RUN, exact, 1, { maxLength: AGENTCORE_SESSION_NAME_MAX }).length, AGENTCORE_SESSION_NAME_MAX);
  assert.ok(encode(RUN, exact, 1, { maxLength: AGENTCORE_SESSION_NAME_MAX }).endsWith(`:${exact}`));
});

test("截断按完整字符的编码单元进行，不切开 %XX，截后的编码段仍能解码成 scope_id 的前缀", () => {
  const scopeId = "流程".repeat(60);                             // 每个字符编码成 9 个字符
  for (const maxLength of [DEVICE_FARM_SESSION_NAME_MAX, AGENTCORE_SESSION_NAME_MAX]) {
    const name = encode(RUN, scopeId, 1, { maxLength });
    const segment = segmentOf(name);
    assert.ok(name.length <= maxLength && name.length > maxLength - 9, `${name.length}`);
    assert.equal(segment.length % 9, 0);
    assert.ok(scopeId.startsWith(decodeURIComponent(segment)));
  }
  // 截断点落在一个四字节字符中间时整字符舍去
  const head = `gherkai:${RUN}:${scopeHash("ab😀")}:1:`;
  assert.equal(encode(RUN, "ab😀", 1, { maxLength: head.length + 5 }), `${head}ab`);
});

test("哈希始终取完整 scope_id：截断只影响编码段", () => {
  const a = "x".repeat(300) + "-a";
  const b = "x".repeat(300) + "-b";
  const na = encode(RUN, a, 1);
  const nb = encode(RUN, b, 1);
  assert.equal(segmentOf(na), segmentOf(nb));                  // 截断后编码段相同
  assert.equal(hashOf(na), scopeHash(a));
  assert.notEqual(hashOf(na), hashOf(nb));                     // 哈希仍能区分
  assert.notEqual(na, nb);
});

test("固定四段放不下时报错，不截其余四段", () => {
  const longRun = "r".repeat(120);
  assert.throws(() => encode(longRun, "checkout", 1, { maxLength: AGENTCORE_SESSION_NAME_MAX }), /会话名/);
  // 固定四段恰好占满上限时编码段为空，仍可用
  const head = `gherkai:${RUN}:${CHECKOUT_HASH}:1:`;
  assert.equal(encode(RUN, "checkout", 1, { maxLength: head.length }), head);
});

test("参数校验：run_id 为空、尝试序号不是非负整数、上限不是正整数都报错", () => {
  assert.throws(() => encode("", "checkout", 1));
  for (const bad of [-1, 1.5, Number.NaN, Number.POSITIVE_INFINITY]) assert.throws(() => encode(RUN, "checkout", bad), `${bad}`);
  for (const bad of [0, -5, 2.5]) assert.throws(() => encode(RUN, "checkout", 1, { maxLength: bad }), `${bad}`);
});

test("长度上限不同时，被截断的名字不相等；没被截断的名字与上限无关", () => {
  const long = "s".repeat(400);
  assert.notEqual(encode(RUN, long, 1, { maxLength: AGENTCORE_SESSION_NAME_MAX }), encode(RUN, long, 1));
  assert.equal(encode(RUN, "checkout", 1, { maxLength: AGENTCORE_SESSION_NAME_MAX }), encode(RUN, "checkout", 1));
});

test("同一 run 内不同 scope 的名字不同，不同 run 的同一 scope 名字也不同", () => {
  assert.notEqual(encode(RUN, "checkout", 1), encode(RUN, "login", 1));
  assert.notEqual(encode(RUN, "checkout", 1), encode("20260629T141207Z-ffffff", "checkout", 1));
  // 前缀相同、截断后编码段相同的两个长 scope 名字不同，见上「哈希始终取完整 scope_id」一条
});

test(`runIdFromEnv：读 ${RUN_ID_ENV}；缺失或为空时报错，消息说明原因与处置、不带内部指代`, () => {
  assert.equal(RUN_ID_ENV, "RUN_ID");
  assert.equal(runIdFromEnv({ RUN_ID: RUN }), RUN);
  for (const env of [{}, { RUN_ID: "" }]) {
    assert.throws(() => runIdFromEnv(env), (err: unknown) => {
      assert.ok(err instanceof Error);
      assert.match(err.message, /RUN_ID/);
      assert.match(err.message, /命名/);
      assert.doesNotMatch(err.message, /ADR|决策|session-name|runIdFromEnv/);
      return true;
    });
  }
});

test("runIdFromEnv：缺省读 process.env", () => {
  const saved = process.env.RUN_ID;
  try {
    process.env.RUN_ID = "run-from-env";
    assert.equal(runIdFromEnv(), "run-from-env");
    delete process.env.RUN_ID;
    assert.throws(() => runIdFromEnv(), /RUN_ID/);
  } finally {
    if (saved === undefined) delete process.env.RUN_ID; else process.env.RUN_ID = saved;
  }
});
