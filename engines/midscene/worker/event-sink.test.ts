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

test("DDB 态：EVENTS_DDB_TABLE 注入 → emit = PutItem(PK=run_id#scope_id, SK=自增 seq, body)", async () => {
  // DDB 态（Fargate 化，ADR 0024）：mock DynamoDBClient send（塞 client、不连真 AWS——对称 artifact-upload.test 惯例）。
  const saved = { t: process.env.EVENTS_DDB_TABLE, r: process.env.RUN_ID, s: process.env.SCOPE_ID };
  process.env.EVENTS_DDB_TABLE = "ev";
  process.env.RUN_ID = "run-1";
  process.env.SCOPE_ID = "browse";
  try {
    const sink = EventSink.fromEnv();
    const items: any[] = [];
    (sink as any).client = { send: async (cmd: any) => { items.push(cmd.input); return {}; } };  // 绕惰性建
    await sink.emit({ type: "scope_started", scopeId: "browse" });
    await sink.emit({ type: "scope_done", scopeId: "browse" });
    // 两条、PK=run_id#scope_id、SK 自增 1/2、body 原样 json line（DDB attribute 形态 {S}/{N}）
    assert.deepEqual(items.map((i) => i.Item.pk.S), ["run-1#browse", "run-1#browse"]);
    assert.deepEqual(items.map((i) => i.Item.seq.N), ["1", "2"]);
    assert.equal(JSON.parse(items[0].Item.body.S).type, "scope_started");
    assert.equal(JSON.parse(items[1].Item.body.S).type, "scope_done");
    assert.equal(items[0].TableName, "ev");
    // expires_at = now+7d（epoch 秒 {N}，DDB TTL，ADR 0033）：范围断言避时钟脆
    const now = Math.floor(Date.now() / 1000);
    const ttl7d = 7 * 24 * 60 * 60;
    for (const i of items) {
      const exp = Number(i.Item.expires_at.N);
      assert.ok(exp >= now + ttl7d - 60 && exp <= now + ttl7d + 60, `expires_at ${exp} 应在 now+7d 附近`);
    }
  } finally {
    for (const [k, v] of [["EVENTS_DDB_TABLE", saved.t], ["RUN_ID", saved.r], ["SCOPE_ID", saved.s]] as const) {
      if (v === undefined) delete process.env[k]; else process.env[k] = v;
    }
  }
});

test("空串 EVENTS_DDB_TABLE 当作未注入（|| undefined）→ 走 fd 态（回落 fd 1）", () => {
  const saved = process.env.EVENTS_DDB_TABLE;
  process.env.EVENTS_DDB_TABLE = "";
  delete process.env.EVENTS_FD;
  try {
    assert.equal((EventSink.fromEnv() as any).fd, 1, "空串 → 未注入 → fd 态回落 fd 1");
  } finally {
    if (saved === undefined) delete process.env.EVENTS_DDB_TABLE; else process.env.EVENTS_DDB_TABLE = saved;
  }
});
