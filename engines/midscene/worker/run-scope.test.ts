// run-scope worker 单测（ADR 0024/0014/0028）——派发分支 + 投票多数票数学 + 网络瞬时分类。
// 跑：node --import tsx --test worker/run-scope.test.ts（已接入 npm test）。
// 与 Nova 腿 test_argument.py / test_transient_network.py 对称：纯逻辑、注 fake agent、不连 AWS。
//
// emit 走 EVENTS_FD（run-scope.ts:73）：测试把它指向临时文件，跑完读回断言事件序列。
import { test, beforeEach } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

// EVENTS_FD 在模块加载时固化（const），故 import 前设好、全程同一 fd、不截断（截断不重置写偏移会留 NUL 空洞）。
// 隔离靠"按偏移读增量"：每个测试只解析自上次读以来 emit 新追加的内容。
const evFile = path.join(os.tmpdir(), `ev-runstep-${process.pid}.jsonl`);
const evFd = fs.openSync(evFile, "w+");
process.env.EVENTS_FD = String(evFd);
let readOffset = 0;

beforeEach(() => { readOffset = fs.fstatSync(evFd).size; });  // 记下本测试起点，只读其后追加的事件
process.on("exit", () => { try { fs.closeSync(evFd); } catch {} try { fs.unlinkSync(evFile); } catch {} });

function events(): any[] {
  const size = fs.fstatSync(evFd).size;
  if (size <= readOffset) return [];
  const buf = Buffer.alloc(size - readOffset);
  fs.readSync(evFd, buf, 0, buf.length, readOffset);  // 从本测试起点读增量
  return buf.toString("utf-8").trim().split("\n").filter(Boolean).map((l) => JSON.parse(l));
}

// fake agent：aiBoolean 按预设布尔序列逐票回；aiAct 记录被调。无 _unstableLogContent → lastCost 返 undefined。
function fakeAgent(boolSeq: boolean[] = []) {
  let i = 0;
  const calls: string[] = [];
  return {
    agent: {
      aiBoolean: async (_instr: string) => { calls.push("aiBoolean"); return boolSeq[i++] ?? false; },
      aiAct: async (_instr: string) => { calls.push("aiAct"); },
    } as any,
    calls,
  };
}
const fakePage = { goto: async () => {} } as any;

async function importMod() {
  // run-scope.ts main 守卫确保 import 不触发 main；具名导出经 tsx CJS interop 在测试文件可用。
  return await import("./run-scope.ts");
}

function step(keyword: string, text: string, index = 0): any {
  return { index, keyword, text };
}

// ---- isTransientNetwork：白名单 + cause 链 + ENOTFOUND/EAI_AGAIN（对称 Nova test_transient_network）----
test("isTransientNetwork: ECONNRESET/ETIMEDOUT 等瞬时码 → true", async () => {
  const { isTransientNetwork } = await importMod();
  for (const code of ["ECONNRESET", "ECONNREFUSED", "ETIMEDOUT", "EPIPE", "EAI_AGAIN", "ECONNABORTED"]) {
    assert.equal(isTransientNetwork({ code }), true, code);
  }
});

test("isTransientNetwork: ENOTFOUND(DNS 永久) → false（对齐 Nova EAI_NONAME）", async () => {
  const { isTransientNetwork } = await importMod();
  assert.equal(isTransientNetwork({ code: "ENOTFOUND" }), false);
});

test("isTransientNetwork: 非网络 → false", async () => {
  const { isTransientNetwork } = await importMod();
  assert.equal(isTransientNetwork(new Error("plain")), false);
  assert.equal(isTransientNetwork({ code: "EACCES" }), false);
});

test("isTransientNetwork: 遍历 cause 链识别底层瞬时", async () => {
  const { isTransientNetwork } = await importMod();
  const outer: any = new Error("wrapped");
  outer.cause = { code: "ECONNRESET" };
  assert.equal(isTransientNetwork(outer), true);
});

// ---- aggregate：error > failed > passed ----
test("aggregate 优先级 error>failed>passed", async () => {
  const { aggregate } = await importMod();
  assert.equal(aggregate(["passed", "passed"]), "passed");
  assert.equal(aggregate(["passed", "failed"]), "failed");
  assert.equal(aggregate(["failed", "error"]), "error");
});

// ---- runStep 派发分支 ----
test("runStep: Given 含引号 URL → 走 page.goto、passed、无 AI 调用", async () => {
  const { runStep } = await importMod();
  const { agent, calls } = fakeAgent();
  const r = await runStep(agent, fakePage, "sc:0", step("Given", '打开 "https://example.com"'), 1);
  assert.equal(r, "passed");
  assert.deepEqual(calls, []);  // 不浪费 AI
  const ev = events().find((e) => e.type === "step_done");
  assert.equal(ev.status, "passed");
  assert.equal(ev.votes, undefined);  // 确定性导航无 votes
});

test("runStep: When 自然语言 → 走 aiAct、passed、无 votes", async () => {
  const { runStep } = await importMod();
  const { agent, calls } = fakeAgent();
  const r = await runStep(agent, fakePage, "sc:0", step("When", '"搜索 OpenAI"'), 1);
  assert.equal(r, "passed");
  assert.deepEqual(calls, ["aiAct"]);
  const ev = events().find((e) => e.type === "step_done");
  assert.equal(ev.status, "passed");
  assert.equal(ev.votes, undefined);  // 动作步无 votes（core 据此知非 AI 断言）
});

// ---- 投票多数票数学（ADR 0014 抖动治理的判定边界）----
test("runStep: Then votesN=1 单票 yes → passed，带 votes{1,1}", async () => {
  const { runStep } = await importMod();
  const { agent, calls } = fakeAgent([true]);
  const r = await runStep(agent, fakePage, "sc:0", step("Then", '"对吗"'), 1);
  assert.equal(r, "passed");
  assert.equal(calls.length, 1);
  const ev = events().find((e) => e.type === "step_done");
  assert.deepEqual(ev.votes, { yes: 1, total: 1 });
});

test("runStep: Then votesN=3 取 2/3 多数 → passed", async () => {
  const { runStep } = await importMod();
  const { agent } = fakeAgent([true, false, true]);
  const r = await runStep(agent, fakePage, "sc:0", step("Then", '"对吗"'), 3);
  assert.equal(r, "passed");  // yes=2 > 3/2=1.5
  assert.deepEqual(events().find((e) => e.type === "step_done").votes, { yes: 2, total: 3 });
});

test("runStep: Then votesN=3 仅 1/3 → failed/assertion_failed", async () => {
  const { runStep } = await importMod();
  const { agent } = fakeAgent([true, false, false]);
  const r = await runStep(agent, fakePage, "sc:0", step("Then", '"对吗"'), 3);
  assert.equal(r, "failed");  // yes=1 不 > 1.5
  const ev = events().find((e) => e.type === "step_done");
  assert.equal(ev.status, "failed");
  assert.equal(ev.errorType, "assertion_failed");
});

test("runStep: Then votesN=2 平票 1/2 → failed（yes>1 不成立，平票算失败）", async () => {
  const { runStep } = await importMod();
  const { agent } = fakeAgent([true, false]);
  const r = await runStep(agent, fakePage, "sc:0", step("Then", '"对吗"'), 2);
  assert.equal(r, "failed");  // yes=1 不 > 2/2=1 —— 偶数平票算失败（ADR 0028 已记的有意设计）
});

// ---- act 中途网络瞬时失败 → error + network_error（本会话刚加的分类，对称 Nova）----
test("runStep: aiAct 抛网络瞬时异常 → error/network_error（仅分类、不重试）", async () => {
  const { runStep } = await importMod();
  const agent = { aiAct: async () => { const e: any = new Error("reset"); e.code = "ECONNRESET"; throw e; } } as any;
  const r = await runStep(agent, fakePage, "sc:0", step("When", '"做事"'), 1);
  assert.equal(r, "error");
  const ev = events().find((e) => e.type === "step_done");
  assert.equal(ev.status, "error");
  assert.equal(ev.errorType, "network_error");
});

test("runStep: aiAct 抛非网络异常 → error/engine_error", async () => {
  const { runStep } = await importMod();
  const agent = { aiAct: async () => { throw new Error("AI boom"); } } as any;
  const r = await runStep(agent, fakePage, "sc:0", step("When", '"做事"'), 1);
  assert.equal(r, "error");
  assert.equal(events().find((e) => e.type === "step_done").errorType, "engine_error");
});

// ---- scope 内 step 短路（ADR 0031 决定六 / 0028，对称 Nova test_run_step）----
// fake agent：aiAct 抛异常模拟 step error；记 aiAct/aiBoolean 调用数（验证短路后不再调）。
function shortcircuitAgent(navRaises: Error) {
  let aiActCalls = 0;
  let aiBooleanCalls = 0;
  const agent = {
    aiAct: async () => { aiActCalls++; throw navRaises; },  // 上游动作抛错 → step error
    aiBoolean: async () => { aiBooleanCalls++; return true; },
  } as any;
  return { agent, counts: () => ({ aiActCalls, aiBooleanCalls }) };
}

test("runScenario: 上游 step error 后短路后续、发 step_skipped、不再调 AI", async () => {
  const { runScenario } = await importMod();
  const { agent, counts } = shortcircuitAgent(new Error("SSL boom"));
  const steps = [
    step("When", '"在页面上操作"', 0),   // aiAct 抛错 → error
    step("When", '"再操作"', 1),          // 应被短路（不调 aiAct）
    step("Then", '"页面有预期内容"', 2),   // 应被短路（不调 aiBoolean）
  ];
  const statuses = await runScenario(agent, fakePage, "sc:0", steps, 1);
  // 上游 error 后：只调了 1 次 aiAct（那个失败的），后续 AI 一次没调
  assert.equal(counts().aiActCalls, 1);
  assert.equal(counts().aiBooleanCalls, 0);
  // step 1/2 发 step_skipped（独立事件、无 status）
  const skipped = events().filter((e) => e.type === "step_skipped");
  assert.deepEqual(skipped.map((e) => e.stepIndex), [1, 2]);
  assert.ok(skipped.every((e) => e.status === undefined));
  // 被短路步不进 statuses → scenario 判定由那个 error step 决定
  assert.deepEqual(statuses, ["error"]);
});

test("runScenario: 全 passed 时不短路、无 step_skipped", async () => {
  const { runScenario } = await importMod();
  const { agent } = fakeAgent([true]);  // Then 单票 yes
  const steps = [step("When", '"做事"', 0), step("Then", '"对吗"', 1)];
  const statuses = await runScenario(agent, fakePage, "sc:0", steps, 1);
  assert.deepEqual(statuses, ["passed", "passed"]);
  assert.equal(events().filter((e) => e.type === "step_skipped").length, 0);
});

test("runScenario: failed 不触发短路（判据锁 error，非 failed）", async () => {
  // failed 是业务结论、环境没坏，后续步该照跑——只有 error（执行故障）才短路。
  const { runScenario } = await importMod();
  const { agent } = fakeAgent([false, true]);  // 第一个 Then failed，第二个 Then passed
  const steps = [step("Then", '"对吗A"', 0), step("Then", '"对吗B"', 1)];
  const statuses = await runScenario(agent, fakePage, "sc:0", steps, 1);
  assert.deepEqual(statuses, ["failed", "passed"]);  // failed 不短路，第二步照跑
  assert.equal(events().filter((e) => e.type === "step_skipped").length, 0);
});

// ---- token 成本：多票断言按增量合计全 N 票（修 lastCost 只算最后一票的欠计）----
// fake agent：_unstableLogContent().executions 累积——每次 aiBoolean 追加一个带 usage 的 task。
function costAgent(perCallTokens: number[]) {
  const tasks: any[] = [];
  let i = 0;
  return {
    aiBoolean: async () => { tasks.push({ usage: { total_tokens: perCallTokens[i++] ?? 0 } }); return true; },
    aiAct: async () => { tasks.push({ usage: { total_tokens: perCallTokens[i++] ?? 0 } }); },
    _unstableLogContent: () => ({ executions: [{ tasks }] }),
  } as any;
}

test("runStep: Then votesN=3 token 成本 = 三票之和（不是只算最后一票）", async () => {
  const { runStep } = await importMod();
  const agent = costAgent([100, 200, 300]);  // 三票各 100/200/300
  await runStep(agent, fakePage, "sc:0", step("Then", '"对吗"'), 3);
  const ev = events().find((e) => e.type === "step_done");
  assert.deepEqual(ev.cost, { tokens: 600 });  // 100+200+300，非旧逻辑的 300
});

test("runStep: 连续两 step token 各算各的增量（不双计前一 step）", async () => {
  const { runStep } = await importMod();
  const agent = costAgent([100, 200]);  // step1 用 100，step2 用 200（累积 executions 不清）
  await runStep(agent, fakePage, "sc:0", step("When", '"做事1"', 0), 1);
  const ev1 = events().find((e) => e.type === "step_done");
  assert.deepEqual(ev1.cost, { tokens: 100 });
  await runStep(agent, fakePage, "sc:0", step("When", '"做事2"', 1), 1);
  // 第二 step 只算增量 200，不把 step1 的 100 双计进来
  const ev2 = events().reverse().find((e) => e.type === "step_done" && e.stepIndex === 1);
  assert.deepEqual(ev2.cost, { tokens: 200 });
});
