// lib/event-bounds.mts 的单测：发出事件之前对说明与设备描述的截断（ADR 0024「字段语义」节「单条事件的大小」条）。
// 运行：npm test（node --import tsx --test "src/**/*.test.mts"）。
//
// 规则由跨语言夹具 engines/fixtures/event-truncation-cases.json 锁住，Nova 的 lib/event_bounds.py 的测试读同一个文件、逐条相等；
// 本文件另核对按真实上限的边界、事件出口的两种通道与 message 截断时写进 worker 日志的完整文字。
import { test } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import {
  DEVICE_FIELD_MAX_BYTES, MESSAGE_MAX_BYTES, boundEvent, boundText, truncateUtf8,
} from "../lib/event-bounds.mjs";
import { EventSink } from "../lib/event-sink.mjs";
import { redactSecrets } from "../lib/redact.mjs";

const FIXTURE = JSON.parse(fs.readFileSync(
  path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../fixtures/event-truncation-cases.json"), "utf-8")) as {
  limits: { message_bytes: number; device_field_bytes: number };
  texts: Array<{ input: unknown; max: number; expected: string }>;
  events: Array<{ input: Record<string, unknown>; expected: Record<string, unknown> }>;
};

const size = (s: string): number => Buffer.byteLength(s, "utf-8");
const noLog = (msg: string): void => { throw new Error(`说明没有超出上限，不该写日志：${msg}`); };
function logs(): { lines: string[]; log: (m: string) => void } {
  const lines: string[] = [];
  return { lines, log: (m) => { lines.push(m); } };
}

// ---- 跨语言夹具 ----
test("两侧常量与夹具的 limits 相同", () => {
  assert.deepEqual(FIXTURE.limits, { message_bytes: MESSAGE_MAX_BYTES, device_field_bytes: DEVICE_FIELD_MAX_BYTES });
});

test("boundText: 跨语言夹具逐条相等，结果不超上限、再脱敏一次不变", () => {
  assert.ok(FIXTURE.texts.length > 0);
  for (const c of FIXTURE.texts) {
    const got = boundText(c.input, c.max);
    assert.equal(got, c.expected, `输入 ${JSON.stringify(c.input)}，上限 ${c.max}`);
    assert.ok(size(got) <= c.max, JSON.stringify(c));
    assert.equal(redactSecrets(got), got, "出口对整行再脱敏一次不会把它加长");
  }
});

test("boundEvent: 跨语言夹具逐条相等，传入的事件不被改动", () => {
  assert.ok(FIXTURE.events.length > 0);
  for (const c of FIXTURE.events) {
    const before = JSON.stringify(c.input);
    assert.deepStrictEqual(boundEvent(c.input, noLog), c.expected, JSON.stringify(c.input));
    assert.equal(JSON.stringify(c.input), before);
  }
});

// ---- 按真实上限的边界 ----
test("message 恰好等于上限：原样保留、不写日志", () => {
  const msg = "x".repeat(MESSAGE_MAX_BYTES);
  assert.equal(boundEvent({ type: "step_done", message: msg }, noLog).message, msg);
});

test("message 超出一个字节：截到上限，完整文字写一行日志", () => {
  const msg = "x".repeat(MESSAGE_MAX_BYTES + 1);
  const { lines, log } = logs();
  const out = boundEvent({ type: "step_done", scenarioId: "f:3", stepIndex: 2, message: msg }, log);
  assert.equal(out.message, "x".repeat(MESSAGE_MAX_BYTES));
  assert.equal(lines.length, 1);
  assert.ok(lines[0].endsWith(msg));
  assert.ok(lines[0].includes("scenario f:3 的 step 2 的说明长 8193 字节"), lines[0].slice(0, 80));
});

test("多字节字符压在 8192 字节的边界上：整个字符舍去，不出半个字符", () => {
  for (const [tail, kept] of [["汉", MESSAGE_MAX_BYTES - 2], ["😀", MESSAGE_MAX_BYTES - 3], ["é", MESSAGE_MAX_BYTES - 1]] as const) {
    const out = boundEvent({ type: "scope_done", scopeId: "s", message: "x".repeat(kept) + tail + "尾" }, () => {}).message as string;
    assert.equal(out, "x".repeat(kept), `末尾字符 ${tail}`);
    assert.ok(size(out) <= MESSAGE_MAX_BYTES);
  }
});

test("凭据跨过 8192 字节的边界：先脱敏再截断，口令片段不出 worker；日志里的完整文字同样已脱敏", () => {
  const secret = "https://admin:hunter2hunter2@h.example/login";
  const head = "x".repeat(MESSAGE_MAX_BYTES - 20);
  const { lines, log } = logs();
  const out = boundEvent({ type: "step_done", message: head + secret }, log).message as string;
  assert.ok(!out.includes("admin") && !out.includes("hunter2"), out.slice(-40));
  assert.equal(out, (head + redactSecrets(secret)).slice(0, MESSAGE_MAX_BYTES));
  assert.ok(!lines[0].includes("hunter2") && lines[0].includes(redactSecrets(secret)));
});

test("原文超出上限、脱敏之后恰好等于上限：按脱敏之后的长度判断，原样（已脱敏）发出、不写日志", () => {
  const secret = "https://admin:hunter2hunter2@h/";  // 脱敏之后短 17 字节
  const msg = "x".repeat(MESSAGE_MAX_BYTES - size(redactSecrets(secret))) + secret;
  assert.equal(size(msg), MESSAGE_MAX_BYTES + 17);
  const out = boundEvent({ type: "step_done", scenarioId: "f:1", stepIndex: 0, message: msg }, noLog).message as string;
  assert.equal(out, redactSecrets(msg));
  assert.equal(size(out), MESSAGE_MAX_BYTES);
});

test("原文恰好等于上限、脱敏之后超出：截断，日志写一行，行尾是脱敏之后的全文", () => {
  const tail = "?X-Amz-Signature=a";  // 脱敏之后长 2 字节
  const msg = "x".repeat(MESSAGE_MAX_BYTES - tail.length) + tail;
  assert.equal(size(msg), MESSAGE_MAX_BYTES);
  const { lines, log } = logs();
  const out = boundEvent({ type: "scope_done", scopeId: "s", message: msg }, log).message as string;
  assert.equal(out, msg.slice(0, -"=a".length), "退到 `=` 之前，出口补回 `***` 时不超限");
  assert.equal(lines.length, 1);
  assert.ok(lines[0].endsWith(redactSecrets(msg)), lines[0].slice(-40));
  assert.ok(lines[0].includes(`scope s 的说明长 ${MESSAGE_MAX_BYTES + 2} 字节`), lines[0].slice(0, 80));
});

test("截断点正好落在 `X-Amz-Signature=` 之后：截断改为退到 `=` 之前，出口补回 `***` 之后不再超限", () => {
  const head = "x".repeat(MESSAGE_MAX_BYTES - "?X-Amz-Signature=".length);
  const out = boundText(`${head}?X-Amz-Signature=sig&a=1`, MESSAGE_MAX_BYTES);
  assert.equal(out, `${head}?X-Amz-Signature`);
  assert.ok(size(redactSecrets(out)) <= MESSAGE_MAX_BYTES);
});

test("message 不是字符串：先转成字符串再截断", () => {
  const { lines, log } = logs();
  const out = boundEvent({ type: "step_done", message: { toString: () => "原因".repeat(2000) } }, log).message;
  assert.equal(out, "原因".repeat(1365), "再多一个字就是 8193 字节");
  assert.equal(size(out as string), 8190);
  assert.equal(lines.length, 1);
  assert.equal(boundEvent({ type: "scope_done", message: { a: 1 } }, noLog).message, "[object Object]");
});

test("设备的型号与系统版本各截到 255 字节，unit 等别的字段不动", () => {
  const ev = { type: "session_opened", scopeId: "s", sessionId: "arn", name: "n", origin: "created",
    device: { platform: "android", model: "机".repeat(100), osVersion: "1".repeat(256), unit: "u".repeat(300) } };
  const device = boundEvent(ev, noLog).device as Record<string, string>;
  assert.equal(device.model, "机".repeat(85));
  assert.equal(size(device.model), DEVICE_FIELD_MAX_BYTES);
  assert.equal(device.osVersion, "1".repeat(DEVICE_FIELD_MAX_BYTES));
  assert.equal(device.unit, "u".repeat(300));
  assert.equal(ev.device.model, "机".repeat(100), "传入的事件不被改动");
  const exact = { ...ev, device: { ...ev.device, model: "m".repeat(DEVICE_FIELD_MAX_BYTES) } };
  assert.equal((boundEvent(exact, noLog).device as Record<string, string>).model, "m".repeat(DEVICE_FIELD_MAX_BYTES));
});

test("truncateUtf8: 退到字符起始字节；孤立的代理码元按 U+FFFD 计", () => {
  assert.deepEqual(truncateUtf8("ab汉", 4), { bytes: Buffer.from("ab"), truncated: true });
  assert.deepEqual(truncateUtf8("ab汉", 5), { bytes: Buffer.from("ab汉"), truncated: false });
  assert.equal(truncateUtf8("a\ud800", 4).bytes.toString("utf-8"), "a�");
});

// ---- 事件出口：两种通道同一规则 ----
function longStepDone(): Record<string, unknown> {
  return { type: "step_done", scenarioId: "f:1", stepIndex: 0, status: "failed", errorType: "assertion_failed",
    votes: { yes: 0, total: 1 }, message: "断言未过：" + "长".repeat(4000) };
}

test("fd 态：发出的 message 不超上限、其余字段不变，完整文字写一行日志，传入的事件不变", async () => {
  const file = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "evbound-")), "events.jsonl");
  const fd = fs.openSync(file, "w+");
  const saved = process.env.EVENTS_FD;
  process.env.EVENTS_FD = String(fd);
  try {
    const { lines, log } = logs();
    const ev = longStepDone();
    await EventSink.fromEnv(log).emit(ev);
    const sent = JSON.parse(fs.readFileSync(file, "utf-8").trim());
    assert.ok(size(sent.message) <= MESSAGE_MAX_BYTES && sent.message.startsWith("断言未过：长长"));
    const { message: _m, ...rest } = sent;
    const { message: _o, ...restIn } = ev;
    assert.deepEqual(rest, restIn);
    assert.ok(size(ev.message as string) > MESSAGE_MAX_BYTES, "传入的事件不被改动");
    assert.equal(lines.length, 1);
    assert.ok(lines[0].endsWith(ev.message as string));
  } finally {
    if (saved === undefined) delete process.env.EVENTS_FD; else process.env.EVENTS_FD = saved;
  }
});

test("DDB 态：PutItem 的 body 里 message 不超上限，scope_done 同样截断", async () => {
  const saved = { t: process.env.EVENTS_DDB_TABLE, r: process.env.RUN_ID, s: process.env.SCOPE_ID };
  process.env.EVENTS_DDB_TABLE = "ev";
  process.env.RUN_ID = "r";
  process.env.SCOPE_ID = "s";
  try {
    const { lines, log } = logs();
    const sink = EventSink.fromEnv(log);
    const bodies: any[] = [];
    (sink as any).client = { send: async (cmd: any) => { bodies.push(JSON.parse(cmd.input.Item.body.S)); return {}; } };
    await sink.emit(longStepDone());
    await sink.emit({ type: "scope_done", scopeId: "s", status: "error", errorType: "engine_error", message: "y".repeat(9000) });
    assert.deepEqual(bodies.map((b) => size(b.message) <= MESSAGE_MAX_BYTES), [true, true]);
    assert.equal(bodies[1].message, "y".repeat(MESSAGE_MAX_BYTES));
    assert.equal(lines.length, 2);
    assert.ok(lines[1].includes("scope s 的说明长 9000 字节"), lines[1].slice(0, 60));
  } finally {
    for (const [k, v] of [["EVENTS_DDB_TABLE", saved.t], ["RUN_ID", saved.r], ["SCOPE_ID", saved.s]] as const) {
      if (v === undefined) delete process.env[k]; else process.env[k] = v;
    }
  }
});

test("出口对整行的脱敏在截断之后执行：截在 `=` 之后时它会补回 `***`，sink 写出的说明仍在上限之内", async () => {
  const file = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "evbound-")), "events.jsonl");
  const fd = fs.openSync(file, "w+");
  const saved = process.env.EVENTS_FD;
  process.env.EVENTS_FD = String(fd);
  try {
    const head = "x".repeat(MESSAGE_MAX_BYTES - "?X-Amz-Signature=".length);
    await EventSink.fromEnv(() => {}).emit({ type: "step_done", message: `${head}?X-Amz-Signature=sig` });
    assert.ok(size(JSON.parse(fs.readFileSync(file, "utf-8").trim()).message) <= MESSAGE_MAX_BYTES);
  } finally {
    if (saved === undefined) delete process.env.EVENTS_FD; else process.env.EVENTS_FD = saved;
  }
});

test("会话事件：设备型号超长的 session_opened 经事件出口发出时截到 255 字节", async () => {
  const { sessionEventSink } = await import("../device/device-session.mjs");
  const file = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "evbound-")), "events.jsonl");
  const fd = fs.openSync(file, "w+");
  const saved = process.env.EVENTS_FD;
  process.env.EVENTS_FD = String(fd);
  try {
    const out = EventSink.fromEnv(noLog);
    await sessionEventSink("s", (e) => out.emit(e)).opened({
      sessionId: "arn:aws:devicefarm:us-west-2:1:session:p/r/1", name: "gherkai:r:s:1:x", origin: "created",
      device: { platform: "ios", model: "iPhone ".repeat(60), osVersion: "18", unit: null },
    });
    const sent = JSON.parse(fs.readFileSync(file, "utf-8").trim());
    assert.equal(sent.device.model, "iPhone ".repeat(60).slice(0, DEVICE_FIELD_MAX_BYTES));
    assert.equal(sent.device.osVersion, "18");
  } finally {
    if (saved === undefined) delete process.env.EVENTS_FD; else process.env.EVENTS_FD = saved;
  }
});
