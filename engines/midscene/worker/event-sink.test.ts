// EventSink 单测（Midscene，ADR 0024 I/O 边缘可注入接口第一期）：subprocess 态写 EVENTS_FD fd + 回落 + 保序。
// 此前 emit 内联在 run-scope（模块级、无法打桩、只能真写 fd 1），无测试覆盖。跑：node --import tsx --test。
import { test } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { EventSink } from "../lib/event-sink.mjs";

// 造临时文件当 EVENTS_FD 目标，emit 后读回断言。返回 { fd, read() }。
function fdSink(): { sink: EventSink; read: () => string } {
  const f = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "evsink-")), "events.jsonl");
  const fd = fs.openSync(f, "w+");
  process.env.EVENTS_FD = String(fd);
  return { sink: EventSink.fromEnv(), read: () => fs.readFileSync(f, "utf-8") };
}

test("emit writes JSON lines to injected EVENTS_FD, order preserved", async () => {
  const { sink, read } = fdSink();
  await sink.emit({ type: "scope_started", scopeId: "s:0" });
  await sink.emit({ type: "scope_done", scopeId: "s:0" });
  const types = read().trim().split("\n").map((l) => JSON.parse(l).type);
  assert.deepEqual(types, ["scope_started", "scope_done"]);  // 两行、顺序保持（同步 writeSync 保序）
  delete process.env.EVENTS_FD;
});

test("emit is one JSON object per line (JSON Lines)", async () => {
  const { sink, read } = fdSink();
  await sink.emit({ type: "step_done", votes: { yes: 2, total: 3 } });
  const lines = read().trim().split("\n");
  assert.equal(lines.length, 1);
  assert.deepEqual(JSON.parse(lines[0]).votes, { yes: 2, total: 3 });
  delete process.env.EVENTS_FD;
});

test("fromEnv 回落 fd 1 (stdout) when no EVENTS_FD; emit 不抛", async () => {
  // 无 EVENTS_FD（手动直跑）→ 回落 fd 1=stdout。不做 fd 重定向（会污染 node:test 输出、脆弱）——
  // 断言回落目标**确实是 fd 1**（读内部 fd）——否则改成 fd 2 也照绿（review：回落测试须验目标 fd）。
  // 不真写 stdout（会污染 node:test 输出），只验内部 fd 值 + emit 不抛。
  delete process.env.EVENTS_FD;
  const sink = EventSink.fromEnv();
  assert.equal((sink as any).fd, 1, "无 EVENTS_FD → 回落 fd 1（stdout）");
  await assert.doesNotReject(async () => { await sink.emit({ type: "scope_started" }); });
});

test("EVENTS_SQS_URL 注入 → fromEnv fail-loud throw（不静默走 fd）", () => {
  // SQS 态守卫（Fargate 化未实现，对称 JobSource）：注入 EVENTS_SQS_URL → throw、不静默走 fd/stdout。锁死守卫。
  const saved = process.env.EVENTS_SQS_URL;
  process.env.EVENTS_SQS_URL = "https://sqs.us-east-1.amazonaws.com/x/q.fifo";
  try {
    assert.throws(() => EventSink.fromEnv(), /SQS 态未实现/);
  } finally {
    if (saved === undefined) delete process.env.EVENTS_SQS_URL; else process.env.EVENTS_SQS_URL = saved;
  }
});
