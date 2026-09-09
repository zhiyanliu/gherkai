// run-scope worker 单测（ADR 0024/0014/0028）——派发分支 + 投票多数票数学 + 网络瞬时分类。
// 跑：npm test（node --import tsx --test "src/**/*.test.mts"）。
// 与 Nova 引擎 test_argument.py / test_transient_network.py 对称：纯逻辑、注 fake agent、不连 AWS。
//
// 事件经注入的 fake sink 收集（ADR 0024 I/O 边缘可注入接口：emit 从模块级 fd 写改为参数注入的 EventSink，
// 使测试可注 fake、无需真写 fd 再读回——顺带补上 emit 此前"模块级、无法打桩"的缺口）。testSink 作 sink 参数
// 传进 runStep/runScenario；events() 读本测试起点之后新收集的事件（beforeEach 记偏移，隔离各测试）。
import { test, beforeEach } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { spawn } from "node:child_process";  // 自述入口的 stdout 完整性只能真跑子进程验（见文件末那条）

const _events: any[] = [];
const testSink = { emit: async (e: unknown) => { _events.push(e); } };  // 注入进 runStep/runScenario
let readOffset = 0;

beforeEach(() => { readOffset = _events.length; });  // 记下本测试起点，只读其后新增的事件

function events(): any[] {
  return _events.slice(readOffset);  // 从本测试起点读增量（对齐旧"按偏移读"隔离语义）
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
  // run-scope.mts 无入口守卫、也不在顶层跑 main（入口是 bin.mts，ADR 0037 决策 3）→ import 只拿具名导出。
  return await import("./run-scope.mjs");
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

// ---- AWS SDK v3 服务端瞬时（AgentCore 起会话节流/5xx，ADR 0028，对称 Nova ClientError 细分）----
test("isTransientNetwork: AWS 节流 name（ThrottlingException 等）→ true", async () => {
  const { isTransientNetwork } = await importMod();
  for (const name of ["ThrottlingException", "TooManyRequestsException", "SlowDown", "ServiceUnavailable"]) {
    assert.equal(isTransientNetwork({ name }), true, name);
  }
});

test("isTransientNetwork: AWS 5xx $metadata.httpStatusCode → true", async () => {
  const { isTransientNetwork } = await importMod();
  for (const httpStatusCode of [500, 502, 503, 504]) {
    assert.equal(isTransientNetwork({ $metadata: { httpStatusCode } }), true, String(httpStatusCode));
  }
});

test("isTransientNetwork: AWS $retryable.throttling → true", async () => {
  const { isTransientNetwork } = await importMod();
  assert.equal(isTransientNetwork({ $retryable: { throttling: true } }), true);
});

test("isTransientNetwork: AWS 永久错（ValidationException / 4xx）→ false", async () => {
  const { isTransientNetwork } = await importMod();
  assert.equal(isTransientNetwork({ name: "ValidationException", $metadata: { httpStatusCode: 400 } }), false);
  assert.equal(isTransientNetwork({ name: "AccessDeniedException", $metadata: { httpStatusCode: 403 } }), false);
});

test("isTransientNetwork: AgentCore 起会话节流错在 cause 链里（穿透包装）→ true", async () => {
  // 对称 Nova：底层 AWS 节流错被外层包裹，遍历 cause 链须穿透命中
  const { isTransientNetwork } = await importMod();
  const outer: any = new Error("Failed to start browser session");
  outer.cause = { name: "ThrottlingException", $metadata: { httpStatusCode: 429 } };
  assert.equal(isTransientNetwork(outer), true);
});

// ---- Playwright "has been closed" 按阶段判定（对称 Nova TargetClosedError，ADR 0028）----
test('isTransientNetwork: "has been closed" 仅建连阶段（connecting=true）→ true', async () => {
  const { isTransientNetwork } = await importMod();
  const err = new Error("Target page, context or browser has been closed");
  assert.equal(isTransientNetwork(err, true), true);   // 建连阶段：认作瞬时→重试
});

test('isTransientNetwork: "has been closed" 默认/act 中途（connecting=false）→ false', async () => {
  const { isTransientNetwork } = await importMod();
  const err = new Error("Target page, context or browser has been closed");
  assert.equal(isTransientNetwork(err), false);        // 默认不认——守「拿不准→不归 network」铁律
  assert.equal(isTransientNetwork(err, false), false);
});

test("isTransientNetwork: connecting=true 不放宽真永久错（ValidationException）→ 仍 false", async () => {
  // connecting 只额外认 "has been closed"，不是放宽一切
  const { isTransientNetwork } = await importMod();
  assert.equal(isTransientNetwork({ name: "ValidationException", $metadata: { httpStatusCode: 400 } }, true), false);
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
  const r = await runStep(agent, fakePage, "sc:0", step("Given", '打开 "https://example.com"'), 1, testSink);
  assert.equal(r, "passed");
  assert.deepEqual(calls, []);  // 不浪费 AI
  const ev = events().find((e) => e.type === "step_done");
  assert.equal(ev.status, "passed");
  assert.equal(ev.votes, undefined);  // 确定性导航无 votes
});

test("runStep: When 自然语言 → 走 aiAct、passed、无 votes", async () => {
  const { runStep } = await importMod();
  const { agent, calls } = fakeAgent();
  const r = await runStep(agent, fakePage, "sc:0", step("When", '"搜索 OpenAI"'), 1, testSink);
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
  const r = await runStep(agent, fakePage, "sc:0", step("Then", '"对吗"'), 1, testSink);
  assert.equal(r, "passed");
  assert.equal(calls.length, 1);
  const ev = events().find((e) => e.type === "step_done");
  assert.deepEqual(ev.votes, { yes: 1, total: 1 });
});

test("runStep: Then votesN=3 取 2/3 多数 → passed", async () => {
  const { runStep } = await importMod();
  const { agent } = fakeAgent([true, false, true]);
  const r = await runStep(agent, fakePage, "sc:0", step("Then", '"对吗"'), 3, testSink);
  assert.equal(r, "passed");  // yes=2 > 3/2=1.5
  assert.deepEqual(events().find((e) => e.type === "step_done").votes, { yes: 2, total: 3 });
});

test("runStep: Then votesN=3 仅 1/3 → failed/assertion_failed", async () => {
  const { runStep } = await importMod();
  const { agent } = fakeAgent([true, false, false]);
  const r = await runStep(agent, fakePage, "sc:0", step("Then", '"对吗"'), 3, testSink);
  assert.equal(r, "failed");  // yes=1 不 > 1.5
  const ev = events().find((e) => e.type === "step_done");
  assert.equal(ev.status, "failed");
  assert.equal(ev.errorType, "assertion_failed");
});

test("runStep: Then votesN=2 平票 1/2 → failed（yes>1 不成立，平票算失败）", async () => {
  const { runStep } = await importMod();
  const { agent } = fakeAgent([true, false]);
  const r = await runStep(agent, fakePage, "sc:0", step("Then", '"对吗"'), 2, testSink);
  assert.equal(r, "failed");  // yes=1 不 > 2/2=1 —— 偶数平票算失败（ADR 0028 已记的有意设计）
});

// ---- act 中途网络瞬时失败 → error + network_error（ADR 0028 act 中途分类，对称 Nova）----
test("runStep: aiAct 抛网络瞬时异常 → error/network_error（仅分类、不重试）", async () => {
  const { runStep } = await importMod();
  const agent = { aiAct: async () => { const e: any = new Error("reset"); e.code = "ECONNRESET"; throw e; } } as any;
  const r = await runStep(agent, fakePage, "sc:0", step("When", '"做事"'), 1, testSink);
  assert.equal(r, "error");
  const ev = events().find((e) => e.type === "step_done");
  assert.equal(ev.status, "error");
  assert.equal(ev.errorType, "network_error");
});

test("runStep: aiAct 抛非网络异常 → error/engine_error", async () => {
  const { runStep } = await importMod();
  const agent = { aiAct: async () => { throw new Error("AI boom"); } } as any;
  const r = await runStep(agent, fakePage, "sc:0", step("When", '"做事"'), 1, testSink);
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
  const statuses = await runScenario(agent, fakePage, "sc:0", steps, 1,
    { snapshotReport: async () => {} } as any, { mtime: -1 }, testSink);  // 抢传 no-op（这些 fake agent 无 reportFile、抢传跳过）
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
  const statuses = await runScenario(agent, fakePage, "sc:0", steps, 1,
    { snapshotReport: async () => {} } as any, { mtime: -1 }, testSink);  // 抢传 no-op（这些 fake agent 无 reportFile、抢传跳过）
  assert.deepEqual(statuses, ["passed", "passed"]);
  assert.equal(events().filter((e) => e.type === "step_skipped").length, 0);
});

test("runScenario: failed 不触发短路（判据锁 error，非 failed）", async () => {
  // failed 是业务结论、环境没坏，后续步该照跑——只有 error（执行故障）才短路。
  const { runScenario } = await importMod();
  const { agent } = fakeAgent([false, true]);  // 第一个 Then failed，第二个 Then passed
  const steps = [step("Then", '"对吗A"', 0), step("Then", '"对吗B"', 1)];
  const statuses = await runScenario(agent, fakePage, "sc:0", steps, 1,
    { snapshotReport: async () => {} } as any, { mtime: -1 }, testSink);  // 抢传 no-op（这些 fake agent 无 reportFile、抢传跳过）
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
  await runStep(agent, fakePage, "sc:0", step("Then", '"对吗"'), 3, testSink);
  const ev = events().find((e) => e.type === "step_done");
  assert.deepEqual(ev.cost, { tokens: 600 });  // 100+200+300，非旧逻辑的 300
});

test("runStep: 连续两 step token 各算各的增量（不双计前一 step）", async () => {
  const { runStep } = await importMod();
  const agent = costAgent([100, 200]);  // step1 用 100，step2 用 200（累积 executions 不清）
  await runStep(agent, fakePage, "sc:0", step("When", '"做事1"', 0), 1, testSink);
  const ev1 = events().find((e) => e.type === "step_done");
  assert.deepEqual(ev1.cost, { tokens: 100 });
  await runStep(agent, fakePage, "sc:0", step("When", '"做事2"', 1), 1, testSink);
  // 第二 step 只算增量 200，不把 step1 的 100 双计进来
  const ev2 = events().reverse().find((e) => e.type === "step_done" && e.stepIndex === 1);
  assert.deepEqual(ev2.cost, { tokens: 200 });
});


// ---- act 边界抢传（ADR 0029，为 Fargate 预演）：runScenario 每 step_done 后 snapshot report + mtime 去重 + 空窗跳过 ----
// fail=true：snapshotReport 抛错（模拟上传失败）——验 worker 层 try/catch 吞错、best-effort 不打断主流程。
function spyUploader(fail = false) {
  const snaps: string[] = [];
  return {
    snaps,
    uploader: {
      snapshotReport: async (p: string) => { snaps.push(p); if (fail) throw new Error("snapshot boom"); },
    } as any,
  };
}

test("runScenario: 每变化 step 后抢传 report（snapshot overwrite）", async () => {
  const { runScenario } = await importMod();
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "snaptest-"));
  const rf = path.join(dir, "report.html");
  fs.writeFileSync(rf, "v0");
  // fake agent：每 aiAct 改一次 reportFile 内容+mtime（模拟 SDK 增量写），reportFile 从首个 act 起有值
  let i = 0;
  const agent = {
    get reportFile() { return i > 0 ? rf : undefined; },  // 空窗：首个 act 前 undefined
    aiAct: async () => { i++; fs.writeFileSync(rf, "v" + i); const t = Date.now() / 1000 + i; fs.utimesSync(rf, t, t); },
  } as any;
  const { snaps, uploader } = spyUploader();
  const steps = [step("When", '"a"', 0), step("When", '"b"', 1)];
  await runScenario(agent, fakePage, "sc:0", steps, 1, uploader, { mtime: -1 }, testSink);
  assert.equal(snaps.length, 2, "两个 AI step 各抢传一次（report 每步都变）");
  assert.ok(snaps.every((p) => p === rf), "抢传的都是同一 reportFile（overwrite 同 key）");
});

test("runScenario: 抢传失败（snapshotReport 抛）被吞、不打断 step 循环（best-effort 不变量）", async () => {
  // 验 run-scope.mts 里 runScenario 的 try{snapshotReport}catch{log} 分工：lib 抛→worker 吞、继续跑完剩余 step。
  // 若有人误删该 catch 或改 rethrow，本测试会红（抢传失败会打断 step 循环、statuses 不全）。
  const { runScenario } = await importMod();
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "snapfail-"));
  const rf = path.join(dir, "report.html");
  let i = 0;
  const agent = {
    get reportFile() { return rf; },  // 恒有 reportFile → 每 step 都试抢传
    aiAct: async () => { i++; fs.writeFileSync(rf, "v" + i); const t = Date.now() / 1000 + i; fs.utimesSync(rf, t, t); },
  } as any;
  const { snaps, uploader } = spyUploader(true);  // snapshotReport 每次抛
  const steps = [step("When", '"a"', 0), step("When", '"b"', 1), step("When", '"c"', 2)];
  const statuses = await runScenario(agent, fakePage, "sc:0", steps, 1, uploader, { mtime: -1 }, testSink);
  // 抢传每步都抛，但被吞：三步全跑完、全 passed（statuses 完整），抢传也每步都试过（snaps 三次）
  assert.deepEqual(statuses, ["passed", "passed", "passed"], "抢传失败不影响 step 执行结果");
  assert.equal(snaps.length, 3, "每步都试了抢传（虽都抛，被吞后继续）");
});

test("runScenario: reportFile 空窗（首步未置）→ 跳过抢传", async () => {
  const { runScenario } = await importMod();
  const agent = {
    reportFile: undefined,  // 全程无 reportFile（如纯确定性步、AI 未产 report）
    aiAct: async () => {},
  } as any;
  const { snaps, uploader } = spyUploader();
  await runScenario(agent, fakePage, "sc:0", [step("When", '"a"', 0)], 1, uploader, { mtime: -1 }, testSink);
  assert.equal(snaps.length, 0, "reportFile 空 → 不抢传");
});

test("runScenario: report mtime 不变（确定性步不写 report）→ 不重复抢传", async () => {
  const { runScenario } = await importMod();
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "snaptest2-"));
  const rf = path.join(dir, "report.html");
  fs.writeFileSync(rf, "fixed");
  const t = Date.now() / 1000; fs.utimesSync(rf, t, t);  // mtime 固定、不再变
  const agent = { reportFile: rf, aiAct: async () => {} } as any;  // aiAct 不改 report（mtime 不变）
  const { snaps, uploader } = spyUploader();
  const steps = [step("When", '"a"', 0), step("When", '"b"', 1)];
  await runScenario(agent, fakePage, "sc:0", steps, 1, uploader, { mtime: -1 }, testSink);
  assert.equal(snaps.length, 1, "首步抢传一次；第二步 mtime 未变 → 去重跳过");
});


// ---- 中断兜底抢传（interruptSnapshot，ADR 0029 handler 兜底；对称 Nova test_interrupt_model 把 handler 提出可测）----
// 从 onSignal 提出的可测纯函数：锁住「空窗跳过 / 成功抢传 / 失败吞不抛」——正是 ADR 强调的
// 「Node 能在 handler 里 await 抢传、Nova greenlet 不能」关键不对称，此前是 main() 内闭包、零测试（该对称却漏）。
test("interruptSnapshot: reportFile 空窗（首个 act 前未置）→ 跳过、不调 snapshotReport", async () => {
  const { interruptSnapshot } = await importMod();
  const { snaps, uploader } = spyUploader();
  await interruptSnapshot(uploader, undefined);
  await interruptSnapshot(uploader, null);
  assert.deepEqual(snaps, [], "无 reportFile → 无从抢传");
});

test("interruptSnapshot: 有 reportFile → 抢传该份 report", async () => {
  const { interruptSnapshot } = await importMod();
  const { snaps, uploader } = spyUploader();
  await interruptSnapshot(uploader, "/tmp/run/report.html");
  assert.deepEqual(snaps, ["/tmp/run/report.html"], "读盘上那份增量 report 抢传");
});

test("interruptSnapshot: 抢传失败 → 吞掉、不抛（best-effort，不影响 handler 后续退出流程）", async () => {
  const { interruptSnapshot } = await importMod();
  const { snaps, uploader } = spyUploader(true);  // snapshotReport 抛
  const logs: string[] = [];
  // 不抛才对：若 rethrow，onSignal 的 process.exit 会被跳过、worker 退不干净——本断言锁住 catch 不被误删。
  await interruptSnapshot(uploader, "/tmp/run/report.html", (m) => logs.push(m));
  assert.equal(snaps.length, 1, "试过抢传");
  assert.ok(logs.some((m) => m.includes("中断兜底抢传 report 失败")), "失败被 log（吞、不抛）");
});


// ---- shutdownSequence（SIGTERM 收尾序列，ADR 0024 会话释放优先铁律）：锁住 cleanup 先于抢传的顺序不变量 ----
// 造带 order 记录的 spy deps；断言 cleanup 在 snapshotReport 之前调用（会话释放优先，抢传 best-effort 不延迟它）。
function shutdownSpy(opts: { cleanupFailed?: boolean; reportFile?: string | null; inflight?: boolean } = {}) {
  const order: string[] = [];
  // 用 "reportFile" in opts 区分「未传→默认有 report」vs「显式传 null→空窗」（?? 对 null 也回退、会吞掉空窗意图）
  const rf = "reportFile" in opts ? opts.reportFile : "/tmp/run/report.html";
  const deps = {
    inflightPending: () => opts.inflight ?? false,
    settleMs: 1,
    sleep: async (_ms: number) => { order.push("sleep"); },
    cleanup: async () => { order.push("cleanup"); },
    uploader: { snapshotReport: async (_p: string) => { order.push("snapshot"); } },
    reportFile: () => rf,
    getCleanupFailed: () => opts.cleanupFailed ?? false,
    logFn: () => {},
  };
  return { order, deps };
}

test("shutdownSequence: cleanup 先于中断抢传（会话释放优先铁律，ADR 0024）", async () => {
  const { shutdownSequence } = await importMod();
  const { order, deps } = shutdownSpy();
  const code = await shutdownSequence(deps);
  // 核心不变量：会话释放（cleanup）必须排在抢传（snapshot）之前——退化网络下抢传挂也不该延迟会话释放。
  assert.deepEqual(order, ["cleanup", "snapshot"], "顺序须 cleanup→snapshot，绝不可颠倒");
  assert.equal(code, 0, "cleanup 未失败 → 退 0");
});

test("shutdownSequence: 在途窗口兜底 → sleep 在 cleanup 之前", async () => {
  const { shutdownSequence } = await importMod();
  const { order, deps } = shutdownSpy({ inflight: true });
  await shutdownSequence(deps);
  assert.deepEqual(order, ["sleep", "cleanup", "snapshot"], "inflight → 先等在途 settle，再 cleanup，再抢传");
});

test("shutdownSequence: cleanupFailed → 退出码 1（泄漏可观测）", async () => {
  const { shutdownSequence } = await importMod();
  const { deps } = shutdownSpy({ cleanupFailed: true });
  assert.equal(await shutdownSequence(deps), 1, "会话释放失败 → 退 1");
});

test("shutdownSequence: reportFile 空窗 → cleanup 照跑、抢传跳过", async () => {
  const { shutdownSequence } = await importMod();
  const { order, deps } = shutdownSpy({ reportFile: null });
  await shutdownSequence(deps);
  assert.deepEqual(order, ["cleanup"], "无 reportFile：只 cleanup，interruptSnapshot 内部跳过 snapshot");
});


// ---- 自述入口（ADR 0036）的 stdout payload 完整性：真跑子进程 + 真 pipe ----
// **必须真跑**：截断只发生在「真 pipe + 真 process.exit + 真 tsx 非阻塞 fd 1」的组合里，注 fake sink 的单测
// 看不见它（写法看着都对、绿也照绿）。故这条 spawn 真 worker、喂超 64KB（pipe 缓冲）的 payload，断言 stdout
// 是完整可解析 JSON——护住「写完再退」的机制（见 run-scope.mts writeStdoutFlushed 注释里两种失败写法）。
test("--match-steps: 超 64KB payload 经 pipe 完整送出（ADR 0036，不被 exit 截断）", async () => {
  const texts = new Array(2000).fill('页面地址匹配 "/wiki/OpenAI"');  // 命中项，输出 ≈330KB > 64KB
  // spawn 的是**真入口** bin.mts（ADR 0037 决策 3：进程即 worker、bin 装 loader 后调 main）——
  // 截断只发生在「真 pipe + 真 process.exit + 真 tsx 非阻塞 fd 1」的组合里，故必须走入口那条路。
  const proc = spawn(process.execPath, [path.join(import.meta.dirname, "..", "bin.mts"), "--match-steps"],
    { stdio: ["pipe", "pipe", "pipe"] });
  proc.stdin.end(JSON.stringify(texts));
  const out: Buffer[] = [];
  proc.stdout.on("data", (c) => out.push(c));
  const code: number = await new Promise((r) => proc.on("close", r));
  const raw = Buffer.concat(out).toString("utf-8");
  assert.equal(code, 0, `worker 应退 0，stdout ${raw.length} 字符`);
  assert.ok(Buffer.byteLength(raw) > 65536, `payload 须超 pipe 缓冲才有意义，实际 ${Buffer.byteLength(raw)} 字节`);
  const got = JSON.parse(raw);  // 截断时这里抛（rc 仍 0，故只靠退出码守不住）
  assert.equal(got.length, texts.length, "逐条命中结果不该丢");
});


// ---- artifactFlushRoot：非 --no-report 档 → 解析后的 MIDSCENE_RUN_DIR（--no-report 档见 no-artifacts.test.mts）----
test("artifactFlushRoot: 常规档给解析后的 MIDSCENE_RUN_DIR；未设则 undefined（local/无落点 no-op）", async () => {
  const { artifactFlushRoot } = await importMod();
  const prev = process.env.MIDSCENE_RUN_DIR;
  try {
    process.env.MIDSCENE_RUN_DIR = "some/rel/run-dir";
    assert.equal(artifactFlushRoot(), path.resolve("some/rel/run-dir"));
    delete process.env.MIDSCENE_RUN_DIR;
    assert.equal(artifactFlushRoot(), undefined);
  } finally {
    if (prev === undefined) delete process.env.MIDSCENE_RUN_DIR; else process.env.MIDSCENE_RUN_DIR = prev;
  }
});
