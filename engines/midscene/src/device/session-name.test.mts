// 会话名编解码的单测（ADR 0051 决策 3；桌面请求名的长度上限见决策 4）。运行：npx tsx --test src/device/session-name.test.mts。
// 期望值里的哈希是用 shasum 另算后写死的字面量，不经被测模块复算，防止「哈希了编码段或截断后的串」这类错与实现一起漂。
import { test } from "node:test";
import assert from "node:assert";
import {
  AGENTCORE_SESSION_NAME_MAX, DEVICE_FARM_SESSION_NAME_MAX, RUN_ID_ENV, decode, encode, matches, runIdFromEnv, scopeHash,
} from "./session-name.mjs";

const RUN = "20260629T141207Z-a3f9c1";
const CHECKOUT_HASH = "c7761e58969f7edd";                    // sha256("checkout") 的前 16 位
const CJK_SCOPE = "登录 流程/a~b:c";
const CJK_HASH = "ab5bc226428ff117";                         // sha256(UTF-8 "登录 流程/a~b:c") 的前 16 位
const CJK_ENCODED = "%E7%99%BB%E5%BD%95%20%E6%B5%81%E7%A8%8B%2Fa%7Eb%3Ac";

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
  const seg = (scopeId: string) => decode(encode(RUN, scopeId, 1))!.scopeIdSegment;
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
    const segment = decode(name)!.scopeIdSegment;
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
  assert.equal(decode(na)!.scopeIdSegment, decode(nb)!.scopeIdSegment);  // 截断后编码段相同
  assert.notEqual(decode(na)!.scopeHash, decode(nb)!.scopeHash);          // 哈希仍能区分
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

test("按整名相等匹配：同 run 同 scope 的任一尝试都认，前缀、加尾巴、改大小写都不认", () => {
  const name = encode(RUN, CJK_SCOPE, 4);
  assert.equal(matches(name, RUN, CJK_SCOPE), true);
  assert.equal(matches(encode(RUN, CJK_SCOPE, 0), RUN, CJK_SCOPE), true);
  assert.equal(matches(name.slice(0, -1), RUN, CJK_SCOPE), false);
  assert.equal(matches(`${name}x`, RUN, CJK_SCOPE), false);
  assert.equal(matches(name.toLowerCase(), RUN, CJK_SCOPE), false);
  assert.equal(matches(name.replace(CJK_HASH, CJK_HASH.toUpperCase()), RUN, CJK_SCOPE), false);
  assert.equal(matches(name.replace(":4:", ":04:"), RUN, CJK_SCOPE), false);   // 尝试序号不是规范写法
  assert.equal(matches(`gherkai:${RUN}:${CJK_HASH}:4:`, RUN, CJK_SCOPE), false); // 只靠哈希段相同不算
});

test("指定尝试序号时只认这一次尝试的名字", () => {
  const name = encode(RUN, "checkout", 2);
  assert.equal(matches(name, RUN, "checkout", { attempt: 2 }), true);
  assert.equal(matches(name, RUN, "checkout", { attempt: 3 }), false);
});

test("匹配用的长度上限须与编码时一致：被截断的名字换个上限重算就不相等", () => {
  const long = "s".repeat(400);
  const desktop = encode(RUN, long, 1, { maxLength: AGENTCORE_SESSION_NAME_MAX });
  assert.equal(matches(desktop, RUN, long, { maxLength: AGENTCORE_SESSION_NAME_MAX }), true);
  assert.equal(matches(desktop, RUN, long), false);
  // 没被截断的名字与上限无关
  const short = encode(RUN, "checkout", 1, { maxLength: AGENTCORE_SESSION_NAME_MAX });
  assert.equal(matches(short, RUN, "checkout"), true);
});

test("同一 run 内不同 scope 不互认，不同 run 的同一 scope 也不互认", () => {
  assert.equal(matches(encode(RUN, "checkout", 1), RUN, "login"), false);
  assert.equal(matches(encode(RUN, "login", 1), RUN, "checkout"), false);
  assert.equal(matches(encode(RUN, "checkout", 1), "20260629T141207Z-ffffff", "checkout"), false);
  // 前缀相同、截断后编码段相同的两个长 scope：哈希不同，不互认
  const a = "x".repeat(300) + "-a";
  const b = "x".repeat(300) + "-b";
  assert.equal(matches(encode(RUN, a, 1), RUN, b), false);
  assert.equal(matches(encode(RUN, b, 1), RUN, a), false);
});

test("decode：拆出各段；不是本规则生成的名字返回 null", () => {
  assert.deepEqual(decode(encode(RUN, CJK_SCOPE, 12)),
    { runId: RUN, scopeHash: CJK_HASH, attempt: 12, scopeIdSegment: CJK_ENCODED });
  for (const foreign of [
    "worker", "spike06-android-1730000000000", "", "gherkai:", `gherkai:${RUN}`,
    `gherkai:${RUN}:${CHECKOUT_HASH}:1`,                         // 缺编码段的分隔符
    `gherkai:${RUN}:${CHECKOUT_HASH.slice(0, 15)}:1:checkout`,   // 哈希不足 16 位
    `gherkai:${RUN}:${CHECKOUT_HASH.toUpperCase()}:1:checkout`,  // 哈希须小写
    `gherkai:${RUN}:${CHECKOUT_HASH}:x:checkout`,                // 尝试序号非数字
    `gherkai:${RUN}:${CHECKOUT_HASH}:01:checkout`,               // 尝试序号带前导零
    `gherkai::${CHECKOUT_HASH}:1:checkout`,                      // run_id 为空
    `gherkai:${RUN}:${CHECKOUT_HASH}:1:check out`,               // 编码段含未编码字符
    `Gherkai:${RUN}:${CHECKOUT_HASH}:1:checkout`,
  ]) {
    assert.equal(decode(foreign), null, foreign);
    assert.equal(matches(foreign, RUN, "checkout"), false, foreign);
  }
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
