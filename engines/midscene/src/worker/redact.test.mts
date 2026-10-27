// 凭据脱敏三条规则的单测（Midscene worker 的那份实现，ADR 0035 决策 5；0051 决策 11）。运行：npm test。
// 用例表只有一份：engines/fixtures/redaction-cases.json，与 core、Nova 三份实现各自读它、逐条断言。本实现只收字符串，故没有 None 那一条。
import { test } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { MASK, SECRET_MASK, redactSecrets } from "../lib/redact.mjs";

const FIXTURE = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../fixtures/redaction-cases.json");
const CASES = (JSON.parse(fs.readFileSync(FIXTURE, "utf8")) as { cases: Array<[string, string]> }).cases;

test("redactSecrets：跨语言用例表逐条通过", () => {
  assert.ok(CASES.length > 10);
  for (const [input, expected] of CASES) {
    assert.equal(redactSecrets(input), expected, `输入 ${JSON.stringify(input)}`);
  }
});

test("MASK 是 ***@、SECRET_MASK 是 ***", () => {
  assert.equal(MASK, "***@");
  assert.equal(SECRET_MASK, "***");
});

test("redactSecrets：同一个正则对象连续调用不残留 lastIndex（全局标志的常见陷阱）", () => {
  // 全局正则若误用 test / exec，会在调用之间记住位置、下一次漏掉匹配；replace 不受影响，这里锁住它。
  for (let i = 0; i < 3; i++) {
    assert.equal(redactSecrets("https://u1:p1@h.example/?gherkai_tunnel_token=t"), "https://***@h.example/?gherkai_tunnel_token=***");
  }
});

test("redactSecrets：已序列化的整行仍能解析，字段值里的凭据被换掉", () => {
  const line = JSON.stringify({ type: "step_done", message: "页面停在 https://u1:p1@h.example/x 未跳转",
    url: "https://h/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=abc", ep: "https://x.amazonaws.com/remote-endpoint/tok123/wd/hub" });
  const out = redactSecrets(line);
  assert.ok(!out.includes("u1:p1@") && !out.includes("=abc") && !out.includes("tok123"));
  assert.deepEqual(JSON.parse(out), { type: "step_done", message: "页面停在 https://***@h.example/x 未跳转",
    url: "https://h/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=***", ep: "https://x.amazonaws.com/remote-endpoint/***/wd/hub" });
});

test("redactSecrets：匹配停在引号处，不跨字段吞掉内容", () => {
  // 前一个字段的地址不带 @、后一个字段里有 @
  const line = '{"url":"https://h.example","who":"x@y"}';
  assert.equal(redactSecrets(line), line);
});
