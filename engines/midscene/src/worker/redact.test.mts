// 隧道凭据脱敏的规则单测（Midscene worker 的那份实现，ADR 0035 决策 5）。运行：npm test。
// 同一组用例在三份实现上各有一份：本文件、core/tests/test_redact.py、engines/novaact/tests/test_redact.py。
// 改规则时三处实现与三份用例一起改，输入与期望逐条一致。本实现只收字符串，故没有 None 那一条。
import { test } from "node:test";
import assert from "node:assert";
import { MASK, redactUrlUserinfo } from "../lib/redact.mjs";

// [输入, 期望]。三份用例表逐条相同。
const CASES: Array<[string, string]> = [
  // 凭据内嵌的地址：userinfo 段换成 ***，主机与路径保留
  ["https://u1:p1@h.example/login", "https://***@h.example/login"],
  // 只有用户名（令牌形态）也算 userinfo
  ["https://token@h.example/", "https://***@h.example/"],
  // 没有 @ 的地址原样保留
  ["https://h.example/login", "https://h.example/login"],
  // @ 出现在路径或查询串里，不是 userinfo，不动
  ["https://h.example/users/@alice", "https://h.example/users/@alice"],
  ["https://h.example/?email=a@b.example", "https://h.example/?email=a@b.example"],
  // 一段文字里有多个地址：逐个处理，端口与路径保留
  ["先开 https://u1:p1@a.example/ 再开 http://u2:p2@b.example:8080/x",
    "先开 https://***@a.example/ 再开 http://***@b.example:8080/x"],
  // 已知残余：缺少 scheme:// 的「用户:口令@主机」规则抓不到，保持原样
  ["u1:p1@h.example/login", "u1:p1@h.example/login"],
  // 普通邮箱地址不受影响
  ["联系 alice@example.com", "联系 alice@example.com"],
  // 中文叙述里地址后紧跟全角标点再接邮箱：字符集不含中文与全角标点，不会一路吞到邮箱的 @
  ["打开https://example.com，用admin@corp.com登录", "打开https://example.com，用admin@corp.com登录"],
  // 已知残余：纯 ASCII 逗号把地址与邮箱连写，逗号是合法 userinfo 字符，会误吞到邮箱的 @
  ["https://a.example,x@b.example", "https://***@b.example"],
  ["", ""],
];

test("redactUrlUserinfo：三份相同的用例表逐条通过", () => {
  for (const [input, expected] of CASES) {
    assert.equal(redactUrlUserinfo(input), expected, `输入 ${JSON.stringify(input)}`);
  }
});

test("MASK 是 ***@", () => {
  assert.equal(MASK, "***@");
});

test("redactUrlUserinfo：同一个正则对象连续调用不残留 lastIndex（全局标志的常见陷阱）", () => {
  // 全局正则若误用 test / exec，会在调用之间记住位置、下一次漏掉匹配；replace 不受影响，这里锁住它。
  for (let i = 0; i < 3; i++) {
    assert.equal(redactUrlUserinfo("https://u1:p1@h.example/"), "https://***@h.example/");
  }
});

test("redactUrlUserinfo：已序列化的整行仍能解析，字段值里的凭据被换掉", () => {
  const line = JSON.stringify({ type: "step_done", message: "页面停在 https://u1:p1@h.example/x 未跳转" });
  const out = redactUrlUserinfo(line);
  assert.ok(!out.includes("u1:p1@"));
  assert.deepEqual(JSON.parse(out), { type: "step_done", message: "页面停在 https://***@h.example/x 未跳转" });
});

test("redactUrlUserinfo：匹配停在引号处，不跨字段吞掉内容", () => {
  // 前一个字段的地址不带 @、后一个字段里有 @
  const line = '{"url":"https://h.example","who":"x@y"}';
  assert.equal(redactUrlUserinfo(line), line);
});
