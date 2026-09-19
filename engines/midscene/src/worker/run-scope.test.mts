// run-scope worker 单测（ADR 0024/0014/0028）——派发分支 + 投票多数票数学 + 网络瞬时分类。
// 运行：npm test（node --import tsx --test "src/**/*.test.mts"）。
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
import { spawn } from "node:child_process";  // 自述入口的 stdout 完整性只能真实运行子进程验（见文件末那条）

const _events: any[] = [];
const testSink = { emit: async (e: unknown) => { _events.push(e); } };  // 注入进 runStep/runScenario
let readOffset = 0;

beforeEach(() => { readOffset = _events.length; });  // 记下本测试起点，只读其后新增的事件

function events(): any[] {
  return _events.slice(readOffset);  // 从本测试起点读增量（对齐旧"按偏移读"隔离语义）
}

// fake agent：aiBoolean 按预设布尔序列逐票回；aiAct 记录被调。无 metrics → 累计读 0、增量 0 → step_done 不带 cost。
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
  // run-scope.mts 无入口守卫、也不在顶层执行 main（入口是 bin.mts，ADR 0037 决策 3）→ import 只拿具名导出。
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

// ---- 失败原因压成一行有界文本（ADR 0042 决策一/三，对称 Nova _error_text）----
test("runStep: 多行超长异常 → message 只留首个非空行、折叠空白、有界", async () => {
  // Playwright 异常的 message 惯常是「一句原因 + 多行 call log」，整段进 message 会把 run 的 step 行、
  // explain 的「原因」与判定明细 JSON 撑成一条上千字符的行（下游只折不截）。
  const { runStep } = await importMod();
  const firstLine = "Timeout 30000ms exceeded：等" + "候元素可见".repeat(100);  // 首行本身就超上界
  const err: any = new Error(`\n  ${firstLine}  \n=========== logs ===========\n  navigating to "https://x"\n`);
  err.name = "TimeoutError";
  const agent = { aiAct: async () => { throw err; } } as any;
  assert.equal(await runStep(agent, fakePage, "sc:0", step("When", '"做事"'), 1, testSink), "error");
  const msg = events().find((e) => e.type === "step_done").message as string;
  assert.equal(msg.includes("\n"), false, "原因须是一行");
  assert.equal(msg.includes("logs"), false, "首个非空行之后的 call log 不进 message");
  assert.equal(msg, `TimeoutError: ${firstLine.slice(0, 300)}`);        // 类型 + 首行截 300
  assert.ok(msg.length <= "TimeoutError: ".length + 300, `有界：${msg.length}`);
});

test("runStep: 异常 message 的内部空白折叠成单空格", async () => {
  const { runStep } = await importMod();
  const agent = { aiAct: async () => { throw new Error("locator   resolved \t to  2 elements"); } } as any;
  await runStep(agent, fakePage, "sc:0", step("When", '"做事"'), 1, testSink);
  assert.equal(events().find((e) => e.type === "step_done").message, "Error: locator resolved to 2 elements");
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
  // failed 是业务结论、环境没坏，后续步该照常执行——只有 error（执行故障）才短路。
  const { runScenario } = await importMod();
  const { agent } = fakeAgent([false, true]);  // 第一个 Then failed，第二个 Then passed
  const steps = [step("Then", '"对吗A"', 0), step("Then", '"对吗B"', 1)];
  const statuses = await runScenario(agent, fakePage, "sc:0", steps, 1,
    { snapshotReport: async () => {} } as any, { mtime: -1 }, testSink);  // 抢传 no-op（这些 fake agent 无 reportFile、抢传跳过）
  assert.deepEqual(statuses, ["failed", "passed"]);  // failed 不短路，第二步照常执行
  assert.equal(events().filter((e) => e.type === "step_skipped").length, 0);
});

// ---- token 成本：多票断言按增量合计全 N 票（修 lastCost 只算最后一票的欠计）----
// fake agent：metrics 是**累计快照**（对齐 SDK 语义：自 agent 建起只增不清）——每次 aiBoolean/aiAct 把本次 token 累加进去。
function costAgent(perCallTokens: number[]) {
  let totalTokens = 0;
  let i = 0;
  return {
    aiBoolean: async () => { totalTokens += perCallTokens[i++] ?? 0; return true; },
    aiAct: async () => { totalTokens += perCallTokens[i++] ?? 0; },
    get metrics() { return { totalTokens }; },
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
  const agent = costAgent([100, 200]);  // step1 用 100，step2 用 200（metrics 累计不清零）
  await runStep(agent, fakePage, "sc:0", step("When", '"做事1"', 0), 1, testSink);
  const ev1 = events().find((e) => e.type === "step_done");
  assert.deepEqual(ev1.cost, { tokens: 100 });
  await runStep(agent, fakePage, "sc:0", step("When", '"做事2"', 1), 1, testSink);
  // 第二 step 只算增量 200，不把 step1 的 100 双计进来
  const ev2 = events().reverse().find((e) => e.type === "step_done" && e.stepIndex === 1);
  assert.deepEqual(ev2.cost, { tokens: 200 });
});


// ---- PlaywrightAgent 构造项：forceChromeSelectRendering 必须显式关 ----
// SDK 1.10.0 起这项默认开，注入样式那步在 CDP 远连的 AgentCore 云端浏览器上会 "Execution context was
// destroyed"、每 run 往 stderr 打一段报错栈；功能面我们用不到 → 钉死显式 false（默认值回来了这条会红）。
test("agentOpts: forceChromeSelectRendering 显式 false（CDP 远连浏览器上它只是噪声）", async () => {
  const saved = process.env.AWS_REGION;
  process.env.AWS_REGION = "us-east-1";  // agentOpts 里的 modelConfig() 会求 region（缺则 fail-loud）
  try {
    const { agentOpts } = await importMod();
    assert.equal(agentOpts().forceChromeSelectRendering, false);
  } finally {
    if (saved === undefined) delete process.env.AWS_REGION; else process.env.AWS_REGION = saved;
  }
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
  // 验 run-scope.mts 里 runScenario 的 try{snapshotReport}catch{log} 分工：lib 抛→worker 吞、继续运行完剩余 step。
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
  // 抢传每步都抛，但被吞：三步全部运行完、全 passed（statuses 完整），抢传也每步都试过（snaps 三次）
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
  assert.ok(logs.some((m) => m.includes("引擎原生报告未能在中断退出前上传")), "失败被 log（吞、不抛）");
});


// ---- shutdownSequence（SIGTERM 收尾序列，ADR 0024 会话释放优先铁律）：锁住 cleanup 先于抢传/排空的顺序不变量 ----
// 造带 order 记录的 spy deps；断言 cleanup 排在 snapshotReport 与截图队列排空之前（会话释放优先，那两件
// best-effort、不延迟它）。drained=false 模拟「预算内没排空」→ 该记一行。
function shutdownSpy(opts: {
  cleanupFailed?: boolean; reportFile?: string | null; inflight?: boolean; drained?: boolean;
} = {}) {
  const order: string[] = [];
  const logs: string[] = [];
  const drainBudgets: number[] = [];
  // 用 "reportFile" in opts 区分「未传→默认有 report」vs「显式传 null→空窗」（?? 对 null 也回退、会吞掉空窗意图）
  const rf = "reportFile" in opts ? opts.reportFile : "/tmp/run/report.html";
  const deps = {
    inflightPending: () => opts.inflight ?? false,
    settleMs: 1,
    sleep: async (_ms: number) => { order.push("sleep"); },
    cleanup: async () => { order.push("cleanup"); },
    uploader: {
      snapshotReport: async (_p: string) => { order.push("snapshot"); },
      drain: async (ms: number) => { order.push("drain"); drainBudgets.push(ms); return opts.drained ?? true; },
    },
    reportFile: () => rf,
    getCleanupFailed: () => opts.cleanupFailed ?? false,
    logFn: (m: string) => { logs.push(m); },
  };
  return { order, logs, drainBudgets, deps };
}

test("shutdownSequence: cleanup 先于中断抢传（会话释放优先铁律，ADR 0024）", async () => {
  const { shutdownSequence } = await importMod();
  const { order, deps } = shutdownSpy();
  const code = await shutdownSequence(deps);
  // 核心不变量：会话释放（cleanup）必须排在抢传（snapshot）与截图队列排空（drain）之前——退化网络下这两件
  // 各自挂满预算，也不该延迟会话释放。
  assert.deepEqual(order, ["cleanup", "snapshot", "drain"], "顺序须 cleanup→snapshot→drain，绝不可颠倒");
  assert.equal(code, 0, "cleanup 未失败 → 退 0");
});

test("shutdownSequence: 在途窗口兜底 → sleep 在 cleanup 之前", async () => {
  const { shutdownSequence } = await importMod();
  const { order, deps } = shutdownSpy({ inflight: true });
  await shutdownSequence(deps);
  assert.deepEqual(order, ["sleep", "cleanup", "snapshot", "drain"],
    "inflight → 先等在途 settle，再 cleanup，再抢传，再排空截图队列");
});

test("shutdownSequence: cleanupFailed → 退出码 1（泄漏可观测）", async () => {
  const { shutdownSequence } = await importMod();
  const { deps } = shutdownSpy({ cleanupFailed: true });
  assert.equal(await shutdownSequence(deps), 1, "会话释放失败 → 退 1");
});

test("shutdownSequence: reportFile 空窗 → cleanup 照常执行、抢传跳过", async () => {
  const { shutdownSequence } = await importMod();
  const { order, deps } = shutdownSpy({ reportFile: null });
  await shutdownSequence(deps);
  assert.deepEqual(order, ["cleanup", "drain"],
    "无 reportFile：cleanup 照常执行、interruptSnapshot 内部跳过 snapshot，截图队列照排空");
});


// ---- 截图后台队列的有界排空（drainArtifactQueue，ADR 0042 决策一）----
// 与 interruptSnapshot 同形的收尾小函数：排不空只记一行、绝不抛（收尾路径抛会跳过后面的 exit/flush）。
test("shutdownSequence: 排空截图队列排在会话释放之后，且预算有界（计入 grace）", async () => {
  const { shutdownSequence } = await importMod();
  const { deps, drainBudgets, order } = shutdownSpy();
  await shutdownSequence(deps);
  assert.equal(drainBudgets.length, 1, "只排空一次");
  assert.ok(drainBudgets[0] > 0 && drainBudgets[0] <= 10_000,
    `退出路径的排空预算须有界且小（计入 grace），实为 ${drainBudgets[0]}ms`);
  assert.ok(order.indexOf("drain") > order.indexOf("cleanup"));
});

test("shutdownSequence: 预算内没排空 → 一行日志、退出码不受影响", async () => {
  const { shutdownSequence } = await importMod();
  const { deps, logs } = shutdownSpy({ drained: false });
  const code = await shutdownSequence(deps);
  assert.equal(code, 0, "排不空不是会话泄漏，不该改退出码");
  assert.equal(logs.filter((m) => m.includes("截图")).length, 1, "只一行、且是说截图的");
});

test("drainArtifactQueue: 队列已空（drain 返 true）→ 不记日志", async () => {
  const { drainArtifactQueue } = await importMod();
  const logs: string[] = [];
  await drainArtifactQueue({ drain: async () => true }, 6000, (m) => logs.push(m));
  assert.deepEqual(logs, []);
});

test("drainArtifactQueue: drain 抛（上传器坏了 / 没这个方法）→ 吞掉、只记一行，绝不抛", async () => {
  // 收尾路径上抛 = 跳过后面的 process.exit / flush，比丢几张截图严重得多（best-effort 语义）。
  const { drainArtifactQueue } = await importMod();
  const logs: string[] = [];
  await drainArtifactQueue({ drain: async () => { throw new Error("boom"); } }, 6000, (m) => logs.push(m));
  assert.equal(logs.length, 1);
  assert.ok(logs[0].includes("boom"));
});


// ---- 自述入口（ADR 0036）的 stdout payload 完整性：真实运行子进程 + 真 pipe ----
// **必须真实运行**：截断只发生在「真 pipe + 真 process.exit + 真 tsx 非阻塞 fd 1」的组合里，注 fake sink 的单测
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


// ---- 能力自述 --capabilities（ADR 0036「5.」）：JSON 形状 + min_grace_s 的来路（ADR 0024「引擎自报下限」）----
// **真实运行入口**：组合根消费的就是这条路（spawn worker → 读 stdout 一行 JSON → 拿 min_grace_s 当 grace 下限），
// 且「不建会话、不读 stdin、零费用」只有真实运行才看得见——本测试不喂 stdin、不给 AWS 凭证，照样该退 0。
// 起源码形态的 bin 要有 TS 转译能力：`--import tsx` 传绝对 URL（与 cwd 无关），不靠 Node 原生 type stripping
// （那要 Node ≥22.18，而包只声明 >=22——同 user-steps.test.mts 的真实运行层）。
test("--capabilities: 一个 JSON 对象即退 0；五键含 deterministic_steps/model_id；min_grace_s = 收尾各段预算之和 + 余量，当前 = 31s", async () => {
  const {
    INFLIGHT_SETTLE_MS, STOP_SESSION_BUDGET_MS, BROWSER_CLOSE_BUDGET_MS, QUEUE_DRAIN_EXIT_MS, MIN_GRACE_MARGIN_MS,
  } = await importMod();
  const { UPLOAD_TIMEOUT_MS } = await import("../lib/artifact-upload.mjs");
  // 自报的 model_id 得与实际运行中喂给 SDK 的模型名同源（modelConfig() 的 MIDSCENE_MODEL_NAME），故从那个模块取真值比对、
  // 不在测试里写第二份字面量——写死了就只能证明「自述没变」，证不了「自述 = 实际用的模型」。
  const { MODEL } = await import("../lib/agentcore-sigv4.mjs");
  const proc = spawn(process.execPath, [
    "--import", import.meta.resolve("tsx"), path.join(import.meta.dirname, "..", "bin.mts"), "--capabilities",
  ], { stdio: ["ignore", "pipe", "pipe"] });
  const out: Buffer[] = []; const err: Buffer[] = [];
  proc.stdout.on("data", (c) => out.push(c));
  proc.stderr.on("data", (c) => err.push(c));
  const code: number = await new Promise((r) => proc.on("close", r));
  const raw = Buffer.concat(out).toString("utf-8");
  assert.equal(code, 0, `应退 0，stderr=${Buffer.concat(err).toString("utf-8")}`);
  const got = JSON.parse(raw);
  // 键集恰为五个（ADR 0036「5.」）：多一个键 = 自述契约变了（组合根核 schema_version 的前提），少一个 =
  // 消费侧读到 undefined；清单并入本对象后不再有独立的清单 flag（同 ADR 被拒方案「每个自述项一个独立 flag」）。
  assert.deepEqual(Object.keys(got).sort(),
    ["deterministic_steps", "engine", "min_grace_s", "model_id", "schema_version"], `键集：${raw}`);
  assert.equal(got.schema_version, 1);
  assert.equal(got.engine, "midscene");
  // model_id = 起 job 时交给 Midscene SDK 的那个模型名（ADR 0036「5.」：doctor 据此显示当前模型）。
  assert.equal(typeof got.model_id, "string", `model_id 该是串：${raw}`);
  assert.ok(got.model_id.length > 0, `model_id 不该空：${raw}`);
  assert.equal(got.model_id, MODEL, "自报的模型得就是真交给 SDK 的那个，不是另写的字面量");
  // deterministic_steps = 注册表清单（ADR 0036「2.」，每项 pattern/description/example）。实际运行才照得出「清单
  // 与 min_grace_s 同一份自述里一起给」——内建脚手架的注册副作用只在真进程里发生。
  assert.ok(Array.isArray(got.deterministic_steps) && got.deterministic_steps.length > 0,
    `清单该非空（内建脚手架至少一条）：${raw}`);
  for (const e of got.deterministic_steps) {
    assert.deepEqual(Object.keys(e).sort(), ["description", "example", "pattern"], `清单项形状：${JSON.stringify(e)}`);
    for (const k of ["pattern", "description", "example"]) {
      assert.equal(typeof e[k], "string", `${k} 该是串：${JSON.stringify(e)}`);
      assert.ok(e[k].length > 0, `${k} 不该空：${JSON.stringify(e)}`);
    }
  }
  // 自报值必须**由收尾预算常量算出**（改某段预算、下限自动跟着走；见 run-scope.mts minGraceSeconds 注释）——
  // 故这里复算而不是照抄一个数。**它挡的是漂移、不是写法**：某段预算改了而出口没跟着走即红；改成与今值相等的
  // 字面量 31 仍然绿（那一格靠下面的绝对值断言 + code review 挡）。
  const expected = (INFLIGHT_SETTLE_MS + STOP_SESSION_BUDGET_MS + BROWSER_CLOSE_BUDGET_MS
    + UPLOAD_TIMEOUT_MS + QUEUE_DRAIN_EXIT_MS + MIN_GRACE_MARGIN_MS) / 1000;
  assert.equal(got.min_grace_s, expected, "自报的下限得是那些预算常量的和，不是另写的字面量");
  // 再钉一次绝对值：当前各段预算下就是 31s。它变了意味着 grace 下限变了（ADR 0024 grace 硬约束的红线，
  // 且组合根/task-def stopTimeout 侧的比对结论随之变），要有意识地改、不该被某段预算的顺手调整带偏。
  assert.equal(got.min_grace_s, 31, `当前行为是 31s，实际 ${got.min_grace_s}s`);
});


// ---- 删掉的 flag 不留别名：--list-deterministic（ADR 0036 被拒方案「每个自述项一个独立 flag」）----
// **必须真实运行**：「argv 里的某个 flag 不再被任何分支认领 → 掉进 job 模式」是进程 + argv + stdin 层的真实
// 行为，注 fake 的单测照不出（留个别名照样绿）。留了别名就等于保留第二个非 job 入口，run 前置每加一个自述项
// 就多一次 spawn，正是那条被拒方案的坑。stdin 给 /dev/null（stdio ignore）：job 模式读到空载荷立刻非零退出、
// 不挂在等 stdin 上。
test("--list-deterministic 已删、不留别名：非零退出且 stdout 不吐 JSON 载荷", async () => {
  const proc = spawn(process.execPath, [
    "--import", import.meta.resolve("tsx"), path.join(import.meta.dirname, "..", "bin.mts"), "--list-deterministic",
  ], { stdio: ["ignore", "pipe", "pipe"] });
  const out: Buffer[] = []; const err: Buffer[] = [];
  proc.stdout.on("data", (c) => out.push(c));
  proc.stderr.on("data", (c) => err.push(c));
  const code: number = await new Promise((r) => proc.on("close", r));
  const raw = Buffer.concat(out).toString("utf-8");
  assert.notEqual(code, 0, `该 flag 不该被识别（应掉进 job 模式后失败退出），stdout=${raw}`);
  // 关键断言是「stdout 没有结构化载荷」：还认这个 flag 的 worker 会在这里吐出清单数组或自述对象。
  assert.equal(/[{[]/.test(raw), false, `stdout 不该有 JSON 载荷：${raw}`);
  assert.ok(Buffer.concat(err).length > 0, "该有一行诊断说清为什么退出");
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


// ---- 失败 act 的费用照报（ADR 0024「失败的 act 同样带 cost」）：agent 日志里的 usage 不因抛异常消失 ----
test("runStep: aiAct 抛异常 → error 的 step_done 仍带本 step 的 token 增量", async () => {
  const { runStep } = await importMod();
  let totalTokens = 0;
  const agent = {
    aiAct: async () => { totalTokens += 150; throw new Error("AI boom"); },  // 抛之前调用已发生 → 已折进累计
    aiBoolean: async () => true,
    get metrics() { return { totalTokens }; },
  } as any;
  assert.equal(await runStep(agent, fakePage, "sc:0", step("When", '"做事"'), 1, testSink), "error");
  const ev = events().find((e) => e.type === "step_done");
  assert.equal(ev.status, "error");
  assert.deepEqual(ev.cost, { tokens: 150 });  // 曾整块丢掉 → total_tokens 低报
});


// ---- 模型选择（ADR 0044 决策 2/3）：喂 SDK 的家族键 + MIDSCENE_MODEL_ID 覆盖 + 坏配置在启动期就被挡下 ----
// 家族键这条是纯逻辑（agentOpts 不碰 page/browser），env 那两条**必须真实运行子进程**：MODEL 在模块 import 时定值
// （模块级读 env），同进程里改 process.env 再 import 拿不到新值——「env 真的贯通到自述与 SDK 配置」只有另起
// 一个带 env 的进程才照得出。
test("agentOpts: modelConfig 喂 SDK 的是 MIDSCENE_MODEL_FAMILY（旧的单一家族硬开关不留）", async () => {
  const savedRegion = process.env.AWS_REGION;
  process.env.AWS_REGION = "us-east-1";  // modelConfig() 会求 region（缺则 fail-loud）
  try {
    const { agentOpts } = await importMod();
    const { modelFamily, MODEL } = await import("../lib/agentcore-sigv4.mjs");
    const cfg = agentOpts().modelConfig as Record<string, string>;
    // 家族与模型名同源于 lib/agentcore-sigv4（不在这里写第二份字面量，否则测的只是「没变」而非「同源」）
    assert.equal(cfg.MIDSCENE_MODEL_FAMILY, modelFamily(), "家族得由推断/显式 env 决定");
    assert.equal(cfg.MIDSCENE_MODEL_NAME, MODEL);
    // family 真跟 env 走（不是写死的字面量）：注入一个与默认模型推断值不同的家族，modelConfig 得跟着变
    const savedFamily = process.env.MIDSCENE_MODEL_FAMILY;
    process.env.MIDSCENE_MODEL_FAMILY = "gpt-6";
    try {
      assert.equal((agentOpts().modelConfig as Record<string, string>).MIDSCENE_MODEL_FAMILY, "gpt-6",
                   "写死家族字面量 = 换了模型仍按旧家族驱动（静默劣化）");
    } finally {
      if (savedFamily === undefined) delete process.env.MIDSCENE_MODEL_FAMILY;
      else process.env.MIDSCENE_MODEL_FAMILY = savedFamily;
    }
    // 旧开关只认一个家族（ADR 0044 被拒方案「单一 family 硬编码」）；两者同给还会被 SDK 当双模式冲突。
    assert.ok(!("MIDSCENE_USE_QWEN3_VL" in cfg), `不该再给旧开关：${JSON.stringify(cfg)}`);
  } finally {
    if (savedRegion === undefined) delete process.env.AWS_REGION; else process.env.AWS_REGION = savedRegion;
  }
});

/** 实际运行 bin.mts 的入口，带定制 env（继承当前 env、但把模型那两个键按本条测试的意思显式置好，
 *  免得运行测试的 shell 里已有的覆盖把结论污染）。 */
async function spawnWorker(args: string[], modelEnv: Record<string, string | undefined>) {
  const env: Record<string, string | undefined> = { ...process.env, ...modelEnv };
  for (const [k, v] of Object.entries(modelEnv)) if (v === undefined) delete env[k];
  const proc = spawn(process.execPath, [
    "--import", import.meta.resolve("tsx"), path.join(import.meta.dirname, "..", "bin.mts"), ...args,
  ], { stdio: ["ignore", "pipe", "pipe"], env: env as NodeJS.ProcessEnv });
  const out: Buffer[] = []; const err: Buffer[] = [];
  proc.stdout.on("data", (c) => out.push(c));
  proc.stderr.on("data", (c) => err.push(c));
  const code: number = await new Promise((r) => proc.on("close", r));
  return { code, out: Buffer.concat(out).toString("utf-8"), err: Buffer.concat(err).toString("utf-8") };
}

test("--capabilities: MIDSCENE_MODEL_ID 覆盖时自报的 model_id 跟着变（ADR 0044 决策 2 的覆盖项真生效）", async () => {
  const { DEFAULT_MODEL } = await import("../lib/agentcore-sigv4.mjs");
  const override = "us.openai.gpt-6-astra";  // inference profile 形态，且家族推得出（否则会被启动期校验挡下）
  const { code, out, err } = await spawnWorker(["--capabilities"],
    { MIDSCENE_MODEL_ID: override, MIDSCENE_MODEL_FAMILY: undefined });
  assert.equal(code, 0, `应退 0，stderr=${err}`);
  const got = JSON.parse(out);
  assert.equal(got.model_id, override, "自报得反映 env 覆盖——doctor 正是拿这个键显示当前用哪个模型");
  assert.notEqual(got.model_id, DEFAULT_MODEL, "覆盖了还等于默认 = 这个覆盖项其实没接上");
});

test("模型家族推不出 → worker 启动期即非零退出，连自述入口都被挡下（不等到建了云端浏览器会话才炸）", async () => {
  const { code, out, err } = await spawnWorker(["--capabilities"],
    { MIDSCENE_MODEL_ID: "nonexistent.model-x", MIDSCENE_MODEL_FAMILY: undefined });
  assert.notEqual(code, 0, `坏配置该被拒，stdout=${out}`);
  assert.match(err, /MIDSCENE_MODEL_FAMILY/, `诊断得点名怎么办：${err}`);
  // stdout 无 JSON 载荷 = 校验真的排在入口分派之前（挪到建连时这里会照出一个完整自述对象、rc 也回 0）。
  assert.equal(/[{[]/.test(out), false, `stdout 不该有 JSON 载荷：${out}`);
});
