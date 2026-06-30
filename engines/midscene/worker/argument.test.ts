// step argument（DataTable/DocString）拼接单测（ADR 0024/0025）。
// 跑：node --import tsx --test worker/argument.test.ts
// 与 Nova 引擎 worker/test_argument.py **对称**——同一拼法、同一断言，保两个引擎同一 feature 行为一致。
import { test } from "node:test";
import assert from "node:assert";
import { argumentText, unquote, buildInstruction } from "./argument.ts";

// ---- dataTable → markdown 表格 ----
test("dataTable 拼回 markdown 表格", () => {
  const arg = { kind: "dataTable", rows: [["字段", "值"], ["用户名", "alice"], ["邮箱", "a@t.com"]] };
  assert.equal(argumentText(arg), "| 字段 | 值 |\n| 用户名 | alice |\n| 邮箱 | a@t.com |");
});

test("dataTable 空 rows → 空串", () => {
  assert.equal(argumentText({ kind: "dataTable", rows: [] }), "");
});

// ---- docString → 原样多行 ----
test("docString 原样", () => {
  assert.equal(argumentText({ kind: "docString", content: "第一行\n第二行" }), "第一行\n第二行");
});

// ---- 无 argument / 未知 kind ----
test("无 argument / 未知 kind → 空串", () => {
  assert.equal(argumentText(null), "");
  assert.equal(argumentText(undefined), "");
  assert.equal(argumentText({}), "");
  assert.equal(argumentText({ kind: "weird" }), "");
});

// ---- buildInstruction：自然语言 + 参数拼接（去引号）----
test("buildInstruction 接上 dataTable", () => {
  const arg = { kind: "dataTable", rows: [["字段", "值"], ["用户名", "alice"]] };
  assert.equal(buildInstruction('"填写注册表单"', arg), "填写注册表单\n| 字段 | 值 |\n| 用户名 | alice |");
});

test("buildInstruction 无参数 → 仅去引号（行为不变）", () => {
  assert.equal(buildInstruction('"搜索 OpenAI"', null), "搜索 OpenAI");
});

test("buildInstruction 接上 docString", () => {
  const arg = { kind: "docString", content: "很满意\n但要暗色模式" };
  assert.equal(buildInstruction("在反馈框填入以下内容", arg), "在反馈框填入以下内容\n很满意\n但要暗色模式");
});

// ---- 边界：cell 含 | / 换行（与 Nova 同规则清洗，保表格结构）----
test("cell 含 | 转义", () => {
  assert.equal(argumentText({ kind: "dataTable", rows: [["a|b", "c"]] }), "| a\\|b | c |");
});

test("cell 含换行压成空格", () => {
  assert.equal(argumentText({ kind: "dataTable", rows: [["第一行\n第二行", "x"]] }), "| 第一行 第二行 | x |");
});

// ---- unquote 边界：只剥 ASCII 空白（BOM 不剥，与 Nova 对称）----
test("unquote 仅剥外层成对引号", () => {
  assert.equal(unquote('"abc"'), "abc");
  assert.equal(unquote("abc"), "abc");          // 无引号原样
  assert.equal(unquote('"abc'), '"abc');         // 不成对原样
});

test("unquote 只剥 ASCII 空白、不剥 BOM（对称 Nova）", () => {
  assert.equal(unquote('"login"﻿'), '"login"﻿');  // 尾 BOM 不剥 → 外引号不成对 → 原样
  assert.equal(unquote('  "搜索"  '), "搜索");                 // ASCII 空白正常剥 + 去引号
});
