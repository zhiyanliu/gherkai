// evidence 单测（ADR 0042 决策一/二/六，对称 Nova 的 fixture 映射测试）：
// ① 引擎映射对**真产物裁成的 fixture**（sdkVersion 1.9.8 的 ReportActionDump，两个 execution：Act 与 Boolean）
//    ——格式漂移在升 @midscene/web 后跑测试时变红（决策六第 2 道防线）；
// ② 截图：路径由 id + 扩展名拼、`after-calling` 优先、按 id 去重、上界 K/M；
// ③ scenario 键派生（确定性 + 不二次撞名）；
// ④ best-effort（决策二）：落盘/上传抛 → step_done 照发、无 evidence ref、status 不变。
// 纯逻辑 + 本地临时目录，不起浏览器、不连 AWS。跑：npm test。
import { test } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

import {
  buildEvidence, scenarioKey, evidenceFile, screenshotsDir, executionsLength,
  stepEvidenceRef, EVIDENCE_SCHEMA_VERSION,
  type EvidenceDoc, type EvidenceUploader,
} from "./evidence.mjs";

// ---- 夹具与工具 ----

const FIXTURE = JSON.parse(
  fs.readFileSync(new URL("./fixtures/midscene_dump.json", import.meta.url), "utf-8"),
) as { executions: unknown[] };

const RUN_DIR = "/tmp/run/midscene-run";  // 只参与拼路径，不落盘（映射是纯函数）
const STEP = { index: 2, keyword: "Then", text: "页面上出现『订单提交成功』字样" };

// 截图 uri：local 档上传器就是这么拼的（file:// + 绝对路径），这里同形以便断言路径本身。
function fileRef(p: string): string {
  return `file://${p}`;
}

function build(over: Partial<Parameters<typeof buildEvidence>[0]> = {}): EvidenceDoc {
  return buildEvidence({
    scopeId: "features/order.feature:6",
    scenarioId: "features/order.feature:12",
    step: STEP,
    status: "passed",
    message: null,
    executions: [],
    prompt: "页面上出现『订单提交成功』字样",
    votes: [],
    url: "https://shop.example.com/cart",
    error: null,
    runDir: RUN_DIR,
    refFor: fileRef,
    ...over,
  });
}

// 合成 task：只带映射用到的字段（结构类型即契约）。shot=id → 该 task 的「动作前」截图；after=id → recorder 的「动作后」截图。
function task(o: {
  type?: string; subType?: string; param?: unknown; thought?: string; output?: unknown;
  errorMessage?: string; shot?: string; after?: string; ext?: string;
} = {}): unknown {
  const mk = (id: string) => ({ type: "midscene_screenshot_ref", id, mimeType: o.ext === "png" ? "image/png" : "image/jpeg" });
  return {
    type: o.type ?? "Planning", subType: o.subType ?? "Plan", param: o.param, thought: o.thought,
    output: o.output, errorMessage: o.errorMessage,
    uiContext: o.shot ? { screenshot: mk(o.shot) } : undefined,
    recorder: o.after ? [{ type: "screenshot", timing: "after-calling", screenshot: mk(o.after) }] : undefined,
  };
}
const exec = (...tasks: unknown[]) => ({ name: "Act - x", tasks });

const shotPath = (id: string, ext = "jpeg") => path.join(RUN_DIR, "report", "screenshots", `${id}.${ext}`);

// ---- ① 引擎映射（真产物 fixture）----

test("映射：fixture 两个 execution → 两个 act，文档骨架按 schema 填齐", () => {
  const doc = build({ executions: FIXTURE.executions, status: "failed", message: "AI 断言未过多数票（0/1）：…", votes: [null, false] });
  assert.equal(doc.schema_version, EVIDENCE_SCHEMA_VERSION);
  assert.equal(doc.engine, "midscene");
  assert.equal(doc.scope_id, "features/order.feature:6");
  assert.equal(doc.scenario_id, "features/order.feature:12");
  assert.equal(doc.step_index, 2);
  assert.deepEqual(doc.step, { keyword: "Then", text: STEP.text });
  assert.equal(doc.status, "failed");
  assert.equal(doc.message, "AI 断言未过多数票（0/1）：…");
  assert.equal(doc.acts.length, 2);
  assert.deepEqual(doc.acts.map((a) => a.index), [0, 1]);
  // prompt 取 worker 自己构造的指令，**不取** execution.name（那是 SDK 展示名「Act - …」/「Boolean - …」）
  assert.ok(doc.acts.every((a) => a.prompt === STEP.text));
  assert.ok(doc.acts.every((a) => a.url === "https://shop.example.com/cart"));
  assert.ok(doc.acts.every((a) => a.time_worked_s === null));  // Midscene 恒 null（per-task timing 是另一种量）
  assert.deepEqual(doc.acts.map((a) => a.vote), [null, false]);  // 动作 act 无票；断言 act 那一票
});

test("映射：act 的 frames 逐 task 一条，actions 名 = type/subType，args = param 原样", () => {
  const doc = build({ executions: FIXTURE.executions });
  const actNames = doc.acts[0].frames.map((f) => f.actions.map((a) => a.name).join(","));
  assert.deepEqual(actNames, ["Planning/Plan", "Planning/Locate", "Action Space/Tap", "Planning/Plan"]);
  assert.deepEqual(doc.acts[1].frames.map((f) => f.actions[0].name), ["Insight/Boolean"]);
  // args 原样透传（内部键随 SDK、不属本契约）
  assert.deepEqual(doc.acts[1].frames[0].actions[0].args, { domIncluded: false, dataDemand: "页面上出现『订单提交成功』字样" });
  assert.equal((doc.acts[0].frames[1].actions[0].args as any).prompt, "提交订单 button");
  // 逐 frame URL 仅 Nova 有；Midscene 恒 null
  assert.ok(doc.acts.every((a) => a.frames.every((f) => f.url === null)));
});

test("映射：thought 按值判——Insight/Boolean 取 task.thought，Planning/Plan 回落 output.thought，Locate 空串 / Tap 无 → null", () => {
  const doc = build({ executions: FIXTURE.executions });
  const th = doc.acts[0].frames.map((f) => f.thought);
  assert.ok(th[0]?.startsWith("The user instruction is to click"));   // Plan：推理在 output.thought（真跑核出）
  assert.equal(th[1], null);                                           // Locate：空串 → null
  assert.equal(th[2], null);                                           // Tap：无
  assert.ok(th[3]?.startsWith("The user's instruction was to click"));
  assert.ok(doc.acts[1].frames[0].thought?.includes("订单提交成功"));    // Boolean：task.thought
});

test("映射：result = 末个 task 的 output（Boolean 的 output 即那一票的布尔）", () => {
  const doc = build({ executions: FIXTURE.executions });
  assert.equal(doc.acts[1].result, true);
  // Act 的末 task 是 Planning/Plan，其 output 原样（含 actions/log/thought）
  assert.deepEqual((doc.acts[0].result as any).actions, []);
  assert.ok(typeof (doc.acts[0].result as any).thought === "string");
});

test("映射：output=false 不被 ?? 吞成 null（判否那一票的 result 必须是 false）", () => {
  const doc = build({ executions: [exec(task({ type: "Insight", subType: "Boolean", output: false, thought: "no" }))] });
  assert.equal(doc.acts[0].result, false);
});

test("映射：error = 首个非空 errorMessage；无 errorMessage 时末个 act 兜住抛出的异常", () => {
  const boom = exec(task({ subType: "Plan" }), task({ subType: "Locate", errorMessage: "Element not found" }), task({ errorMessage: "后一个不该被取" }));
  const doc = build({ status: "error", executions: [exec(task()), boom], error: "ActError: timeout", votes: [] });
  assert.equal(doc.acts[1].error, "Element not found", "首个非空 errorMessage 优先于抛出的异常文本");
  assert.equal(doc.acts[0].error, null, "非末 act 且自身无 errorMessage → null（不把异常抄给已跑完的前一票）");
  // 全无 errorMessage 时：只有**末** act 兜住抛出的异常（抛的那一刻正在跑的就是它）
  const doc2 = build({ status: "error", executions: [exec(task()), exec(task())], error: "ActError: timeout" });
  assert.deepEqual(doc2.acts.map((a) => a.error), [null, "ActError: timeout"]);
});

test("映射：抛错早于任何 execution 落账 → 仍留一条只带 error 的 act（frames 空是 SDK 事实）", () => {
  const doc = build({ status: "error", executions: [], error: "TargetClosedError: closed", votes: [] });
  assert.equal(doc.acts.length, 1);
  assert.deepEqual(doc.acts[0].frames, []);
  assert.equal(doc.acts[0].error, "TargetClosedError: closed");
  assert.equal(doc.acts[0].prompt, STEP.text);
});

test("映射：容缺——execution 缺 tasks / task 缺全部字段都不抛", () => {
  const doc = build({ executions: [{}, { tasks: [{}] }, null] });
  assert.equal(doc.acts.length, 3);
  assert.deepEqual(doc.acts[0].frames, []);
  assert.deepEqual(doc.acts[1].frames, [{ url: null, thought: null, actions: [], screenshot: null }]);
  assert.equal(doc.acts[2].result, null);
});

// ---- ② 截图：路径、after-calling 优先、去重、上界 ----

test("截图：路径 = <run 目录>/report/screenshots/<id>.<扩展名>，jpeg / png 各按其 mime", () => {
  assert.equal(screenshotsDir(RUN_DIR), path.join(RUN_DIR, "report", "screenshots"));
  const jpg = build({ executions: [exec(task({ shot: "aaa" }))] });
  assert.equal(jpg.acts[0].frames[0].screenshot, fileRef(shotPath("aaa")));
  const png = build({ executions: [exec(task({ shot: "bbb", ext: "png" }))] });
  assert.equal(png.acts[0].frames[0].screenshot, fileRef(shotPath("bbb", "png")));
});

test("截图：内存态对象的 extension getter 优先于 mimeType 回落", () => {
  const shot = { id: "ccc", extension: "jpeg", mimeType: "image/png" };  // 两者矛盾时以 extension 为准
  const doc = build({ executions: [{ tasks: [{ type: "Planning", subType: "Plan", uiContext: { screenshot: shot } }] }] });
  assert.equal(doc.acts[0].frames[0].screenshot, fileRef(shotPath("ccc")));
});

test("截图：优先 recorder 的 after-calling（动作后），无则回落 uiContext（动作前）", () => {
  // 同一 task 两张都有 → 取 after-calling 那张
  const both = build({ executions: [exec(task({ shot: "before", after: "after" }))] });
  assert.equal(both.acts[0].frames[0].screenshot, fileRef(shotPath("after")));
  // 只有 uiContext（真产物里 Planning/Locate 就是这样）→ 回落
  const only = build({ executions: [exec(task({ shot: "before" }))] });
  assert.equal(only.acts[0].frames[0].screenshot, fileRef(shotPath("before")));
  // 两者都无 → null（容缺，不拼假路径）
  const none = build({ executions: [exec(task())] });
  assert.equal(none.acts[0].frames[0].screenshot, null);
  // 真产物：Act 末 frame 的 after-calling 与其 uiContext 是**不同**两张，取前者
  const real = build({ executions: FIXTURE.executions });
  assert.equal(real.acts[0].frames[3].screenshot, fileRef(shotPath("c1b23df2-e0ea-435c-9e1e-7bf0b6dbeb9c")));
});

test("截图：同一张跨 task 共享 → 多个 frame 指同一 uri、只算一次额度", () => {
  const calls: string[] = [];
  const doc = build({
    status: "failed",
    // 三个 task 共享同一张截图：首个含 thought、第二个出错、末个是末帧 → 三格都被选中
    executions: [exec(task({ shot: "same", thought: "t" }), task({ shot: "same", errorMessage: "boom" }), task({ shot: "same" }))],
    refFor: (p) => { calls.push(p); return fileRef(p); },
  });
  const uris = doc.acts[0].frames.map((f) => f.screenshot);
  assert.deepEqual(uris, [fileRef(shotPath("same")), fileRef(shotPath("same")), fileRef(shotPath("same"))]);
  assert.equal(calls.length, 1, "按截图 id 去重后计：同一张只算一次");
});

test("截图上界：passed → 每 act 只留末帧一张", () => {
  const doc = build({
    status: "passed",
    executions: [exec(task({ shot: "s0", thought: "t" }), task({ shot: "s1" }), task({ shot: "s2" }))],
  });
  assert.deepEqual(doc.acts[0].frames.map((f) => f.screenshot), [null, null, fileRef(shotPath("s2"))]);
});

test("截图上界：failed / error → 每 act 最多三张（末帧、首个含 thought 的帧、出错帧）", () => {
  const doc = build({
    status: "failed",
    executions: [exec(
      task({ shot: "s0" }),
      task({ shot: "s1", thought: "首个含 thought" }),
      task({ shot: "s2", thought: "第二个含 thought（不该被选）" }),
      task({ shot: "s3", errorMessage: "出错帧" }),
      task({ shot: "s4" }),
      task({ shot: "s5" }),                                  // 末帧
    )],
  });
  const picked = doc.acts[0].frames.map((f, i) => (f.screenshot === null ? null : i));
  assert.deepEqual(picked, [null, 1, null, 3, null, 5], "只选首个 thought 帧 / 出错帧 / 末帧");
  assert.equal(doc.acts[0].frames.filter((f) => f.screenshot !== null).length, 3);
  // 文本不受限：全部 frame 的 thought / actions 都在
  assert.equal(doc.acts[0].frames.length, 6);
  assert.equal(doc.acts[0].frames[2].thought, "第二个含 thought（不该被选）");
});

test("截图上界：每 step 总数封顶（超出的 frame 只丢 screenshot、thought 照留）", () => {
  // 5 个 act × 3 张互不相同 = 15 张候选 → 只有前 12 张拿到 uri
  const acts = Array.from({ length: 5 }, (_, a) => exec(
    task({ shot: `a${a}-0`, thought: "t" }),
    task({ shot: `a${a}-1`, errorMessage: "boom" }),
    task({ shot: `a${a}-2` }),
  ));
  const doc = build({ status: "error", executions: acts, error: null });
  const withShot = doc.acts.flatMap((a) => a.frames.filter((f) => f.screenshot !== null));
  assert.equal(withShot.length, 12);
  assert.equal(new Set(withShot.map((f) => f.screenshot)).size, 12, "12 张互不相同（去重后计）");
  // 预算耗尽落在最后一个 act 上，但它的 thought 仍在
  assert.deepEqual(doc.acts[4].frames.map((f) => f.screenshot), [null, null, null]);
  assert.equal(doc.acts[4].frames[0].thought, "t");
});

// ---- ③ scenario 键与落点 ----

test("scenario 键：由 id 派生（转义分隔符 + 尾附短哈希）、确定性", () => {
  const k = scenarioKey("features/login.feature:12");
  assert.match(k, /^features_login\.feature_12-[0-9a-f]{8}$/);
  assert.equal(k, scenarioKey("features/login.feature:12"), "同一 id 恒得同一键");
  assert.ok(!k.includes("/") && !k.includes(":"), "键要能当单个目录名");
});

test("scenario 键：转义后可读部分相同的两条 id 仍不撞名（哈希兜住）", () => {
  const a = scenarioKey("features/login.feature:12");
  const b = scenarioKey("features:login.feature:12");   // 转义后 slug 与 a 相同
  assert.equal(a.split("-")[0], b.split("-")[0]);
  assert.notEqual(a, b, "撞名的表现是证据静默互相覆盖，必须由哈希区分");
  assert.notEqual(scenarioKey("features/login.feature:12"), scenarioKey("features/login.feature:13"));
  // Outline 的 example 行、超长 uri（slug 被截断）都不撞
  assert.notEqual(scenarioKey("f.feature:12:20"), scenarioKey("f.feature:12:21"));
  const long = "features/" + "x".repeat(200) + ".feature:";
  assert.notEqual(scenarioKey(long + "12"), scenarioKey(long + "13"));
  assert.ok(scenarioKey(long + "12").length < 100, "键要短到能当路径分量");
});

test("scenario 键：非 ASCII 标题/路径不进键（仍靠哈希唯一）", () => {
  const k = scenarioKey("features/登录.feature:12");
  assert.match(k, /^[A-Za-z0-9._-]+$/);
  assert.notEqual(k, scenarioKey("features/注册.feature:12"));
});

test("落点：<run 目录>/evidence/<scenario 键>/step-<n>/evidence.json", () => {
  const p = evidenceFile(RUN_DIR, "features/login.feature:12", 3);
  assert.equal(path.dirname(p).endsWith(path.join("step-3")), true);
  assert.equal(path.basename(p), "evidence.json");
  assert.equal(p, path.join(RUN_DIR, "evidence", scenarioKey("features/login.feature:12"), "step-3", "evidence.json"));
});

// ---- executionsLength（step 起点标记）----

test("executionsLength：读 agent.dump.executions；读不到 / getter 抛 → 0（不让记起点冒泡）", () => {
  assert.equal(executionsLength({ dump: { executions: [1, 2, 3] } }), 3);
  assert.equal(executionsLength({}), 0);
  assert.equal(executionsLength(undefined), 0);
  assert.equal(executionsLength({ dump: { executions: "不是数组" } }), 0);
  assert.equal(executionsLength({ get dump(): any { throw new Error("boom"); } }), 0);
});

// ---- stepEvidenceRef：落盘 + 上传 + best-effort ----

function tmpRun(): string {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), "evid-"));
  return path.join(d, "midscene-run");
}

// local 档上传器的行为形状：refFor / toReportRef 都报 file://，记录调用以分辨「传了字节」与「只算 ref」。
function spyUploader(opts: { failUpload?: boolean } = {}) {
  const uploaded: string[] = [];
  const refs: string[] = [];
  const uploader: EvidenceUploader = {
    toReportRef: async (p) => {
      if (opts.failUpload) throw new Error("s3 fail");
      uploaded.push(p);
      return fileRef(p);
    },
    refFor: (p) => { refs.push(p); return fileRef(p); },
  };
  return { uploader, uploaded, refs };
}

const fixtureAgent = { dump: { executions: FIXTURE.executions } };
const urlPage = { url: () => "https://shop.example.com/cart" };

test("stepEvidenceRef：落盘到落点 + 经 toReportRef 即时上传拿 ref；截图只算 ref 不上传", async () => {
  const runDir = tmpRun();
  const { uploader, uploaded, refs } = spyUploader();
  const ref = await stepEvidenceRef(
    { runDir, scopeId: "features/order.feature:6", uploader, logFn: () => {} },
    {
      scenarioId: "features/order.feature:12", step: STEP, status: "failed",
      message: "AI 断言未过多数票（0/1）：…", agent: fixtureAgent, execFrom: 1, page: urlPage,
      prompt: STEP.text, votes: [false], error: null,
    },
  );
  const file = evidenceFile(runDir, "features/order.feature:12", 2);
  assert.equal(ref, fileRef(file));
  assert.deepEqual(uploaded, [file], "evidence.json 即时上传（它的 ref 要随 step_done 走）");
  assert.ok(refs.every((p) => p.includes(path.join("report", "screenshots"))), "截图只算 ref、不进上传");
  assert.ok(refs.length > 0);
  const doc = JSON.parse(fs.readFileSync(file, "utf-8")) as EvidenceDoc;
  assert.equal(doc.acts.length, 1, "execFrom=1 只切出本 step 新增的那个 execution");
  assert.equal(doc.acts[0].vote, false);
  assert.equal(doc.acts[0].url, "https://shop.example.com/cart");
  assert.ok(doc.acts[0].frames[0].thought?.includes("订单提交成功"));
  assert.equal(doc.status, "failed");
});

test("stepEvidenceRef：无 hook（--no-report 档 / 无产物落点）→ 直接不产", async () => {
  const ref = await stepEvidenceRef(undefined, {
    scenarioId: "s:1", step: STEP, status: "passed", message: null, agent: fixtureAgent,
    execFrom: 0, page: urlPage, prompt: STEP.text, votes: [], error: null,
  });
  assert.equal(ref, null);
});

test("stepEvidenceRef：本 step 没调过 AI（无新 execution 且无指令）→ 不产", async () => {
  const runDir = tmpRun();
  const { uploader, uploaded } = spyUploader();
  const ref = await stepEvidenceRef({ runDir, scopeId: "sc", uploader }, {
    scenarioId: "s:1", step: { index: 0, keyword: "Given", text: '打开 "https://x/"' }, status: "passed",
    message: null, agent: fixtureAgent, execFrom: 2, page: urlPage, prompt: null, votes: [], error: null,
  });
  assert.equal(ref, null);
  assert.deepEqual(uploaded, []);
  assert.ok(!fs.existsSync(path.join(runDir, "evidence")), "确定性 / 导航 step 不留空证据目录");
});

test("stepEvidenceRef：page.url() 抛（页面已关）→ url 记 null，其余证据照产", async () => {
  const runDir = tmpRun();
  const { uploader } = spyUploader();
  const ref = await stepEvidenceRef({ runDir, scopeId: "sc", uploader, logFn: () => {} }, {
    scenarioId: "s:1", step: STEP, status: "error", message: "boom", agent: fixtureAgent,
    execFrom: 1, page: { url: () => { throw new Error("closed"); } }, prompt: STEP.text, votes: [], error: "E: boom",
  });
  assert.notEqual(ref, null);
  const doc = JSON.parse(fs.readFileSync(evidenceFile(runDir, "s:1", 2), "utf-8")) as EvidenceDoc;
  assert.equal(doc.acts[0].url, null);
  assert.ok(doc.acts[0].frames.length > 0);
});

test("stepEvidenceRef：落盘失败 → 日志一行 + 返 null，绝不抛", async () => {
  // runDir 指到一个**文件**上 → mkdir 必失败（真失败，不打桩）
  const bogus = fs.mkdtempSync(path.join(os.tmpdir(), "evid-"));
  const asFile = path.join(bogus, "not-a-dir");
  fs.writeFileSync(asFile, "x");
  const { uploader, uploaded } = spyUploader();
  const logs: string[] = [];
  const ref = await stepEvidenceRef({ runDir: asFile, scopeId: "sc", uploader, logFn: (m) => logs.push(m) }, {
    scenarioId: "s:1", step: STEP, status: "failed", message: null, agent: fixtureAgent,
    execFrom: 1, page: urlPage, prompt: STEP.text, votes: [false], error: null,
  });
  assert.equal(ref, null);
  assert.deepEqual(uploaded, []);
  assert.equal(logs.length, 1, "失败只一行日志");
  assert.ok(logs[0].includes("证据"));
});

test("stepEvidenceRef：上传失败 → 同样吞成 null（toReportRef 的失败即抛契约不动）", async () => {
  const runDir = tmpRun();
  const { uploader } = spyUploader({ failUpload: true });
  const logs: string[] = [];
  const ref = await stepEvidenceRef({ runDir, scopeId: "sc", uploader, logFn: (m) => logs.push(m) }, {
    scenarioId: "s:1", step: STEP, status: "failed", message: null, agent: fixtureAgent,
    execFrom: 1, page: urlPage, prompt: STEP.text, votes: [false], error: null,
  });
  assert.equal(ref, null);
  assert.equal(logs.length, 1);
  assert.ok(fs.existsSync(evidenceFile(runDir, "s:1", 2)), "json 已落盘（本地仍留证据，scope 末整目录 flush 兜）");
});

// ---- ④ runStep 里的 best-effort 不变量（ADR 0042 决策二）----
// 这几条锁住「evidence 任一环失败都不会改判定、不进 act 异常分类路径」——把 stepEvidenceRef 裸放进 runStep
// 的 try 里，一次上传抖动就会被 catch 归成 network_error / engine_error，把已成的 passed 判定翻掉。

async function importRunScope() {
  return await import("./run-scope.mjs");
}

function collector() {
  const events: any[] = [];
  return { events, sink: { emit: async (e: unknown) => { events.push(e); } } };
}

// fake agent：aiBoolean 按预设逐票回，且每次调用往 dump.executions 追加一个 execution（模拟 SDK 记账）。
function dumpAgent(boolSeq: boolean[] = [], newExec: () => unknown = () => exec(task({ shot: "s", thought: "t" }))) {
  const executions: unknown[] = [exec(task())];  // 前一个 step 留下的历史 execution（切片必须把它排除）
  let i = 0;
  return {
    executions,
    agent: {
      dump: { executions },
      aiBoolean: async () => { executions.push(newExec()); return boolSeq[i++] ?? false; },
      aiAct: async () => { executions.push(newExec()); },
    } as any,
  };
}
const stepPage = { url: () => "https://shop.example.com/cart", goto: async () => {} } as any;

test("runStep：AI 断言 step 的 step_done 带 kind=evidence 的 step 级 ref（Midscene 首条）", async () => {
  const { runStep } = await importRunScope();
  const runDir = tmpRun();
  const { uploader } = spyUploader();
  const { events, sink } = collector();
  const { agent } = dumpAgent([false]);
  const status = await runStep(agent, stepPage, "features/order.feature:12",
    { index: 2, keyword: "Then", text: STEP.text }, 1, sink,
    { runDir, scopeId: "features/order.feature:6", uploader, logFn: () => {} });
  assert.equal(status, "failed");
  const done = events.find((e) => e.type === "step_done");
  assert.equal(done.reportRefs.length, 1);
  assert.equal(done.reportRefs[0].kind, "evidence");
  assert.equal(done.reportRefs[0].label, "evidence");
  // 判定字段一个不少
  assert.deepEqual(done.votes, { yes: 0, total: 1 });
  assert.equal(done.errorType, "assertion_failed");
  const doc = JSON.parse(fs.readFileSync(evidenceFile(runDir, "features/order.feature:12", 2), "utf-8")) as EvidenceDoc;
  assert.equal(doc.status, "failed");
  assert.equal(doc.message, done.message);
  assert.equal(doc.acts.length, 1, "只切本 step 新增的 execution（历史那条不算）");
  assert.deepEqual(doc.acts.map((a) => a.vote), [false]);
});

test("runStep：N 票断言 → N 个 act，逐票 vote 落在各自 act 上", async () => {
  const { runStep } = await importRunScope();
  const runDir = tmpRun();
  const { uploader } = spyUploader();
  const { events, sink } = collector();
  const { agent } = dumpAgent([true, false, false]);
  const status = await runStep(agent, stepPage, "s:1", { index: 0, keyword: "Then", text: "对吗" }, 3, sink,
    { runDir, scopeId: "sc", uploader, logFn: () => {} });
  assert.equal(status, "failed");
  const done = events.find((e) => e.type === "step_done");
  assert.deepEqual(done.votes, { yes: 1, total: 3 });
  const doc = JSON.parse(fs.readFileSync(evidenceFile(runDir, "s:1", 0), "utf-8")) as EvidenceDoc;
  assert.deepEqual(doc.acts.map((a) => a.vote), [true, false, false]);
});

test("runStep：AI 动作 step（aiAct）也产 evidence，vote 恒 null", async () => {
  const { runStep } = await importRunScope();
  const runDir = tmpRun();
  const { uploader } = spyUploader();
  const { events, sink } = collector();
  const { agent } = dumpAgent();
  await runStep(agent, stepPage, "s:1", { index: 1, keyword: "When", text: "点击提交" }, 1, sink,
    { runDir, scopeId: "sc", uploader, logFn: () => {} });
  const done = events.find((e) => e.type === "step_done");
  assert.equal(done.status, "passed");
  assert.equal(done.reportRefs[0].kind, "evidence");
  const doc = JSON.parse(fs.readFileSync(evidenceFile(runDir, "s:1", 1), "utf-8")) as EvidenceDoc;
  assert.deepEqual(doc.acts.map((a) => a.vote), [null]);
  assert.equal(doc.status, "passed");
});

test("runStep：act 抛错 → error/engine_error 照常，evidence 带上 error 与出错前的 frames", async () => {
  const { runStep } = await importRunScope();
  const runDir = tmpRun();
  const { uploader } = spyUploader();
  const { events, sink } = collector();
  const executions: unknown[] = [];
  const agent = {
    dump: { executions },
    aiAct: async () => {
      executions.push(exec(task({ shot: "s0", thought: "想了想" }), task({ shot: "s1", errorMessage: "Element not found" })));
      throw new Error("AI boom");
    },
  } as any;
  const status = await runStep(agent, stepPage, "s:1", { index: 0, keyword: "When", text: "点击提交" }, 1, sink,
    { runDir, scopeId: "sc", uploader, logFn: () => {} });
  assert.equal(status, "error");
  const done = events.find((e) => e.type === "step_done");
  assert.equal(done.errorType, "engine_error");
  assert.equal(done.reportRefs[0].kind, "evidence");
  const doc = JSON.parse(fs.readFileSync(evidenceFile(runDir, "s:1", 0), "utf-8")) as EvidenceDoc;
  assert.equal(doc.status, "error");
  assert.equal(doc.acts[0].error, "Element not found", "task 自带的 errorMessage 优先于抛出的异常文本");
  assert.equal(doc.acts[0].frames.length, 2);
});

test("runStep（best-effort 不变量）：落盘失败 → passed 不变、step_done 无 evidence ref、字段照发", async () => {
  const { runStep } = await importRunScope();
  const bogus = fs.mkdtempSync(path.join(os.tmpdir(), "evid-"));
  const asFile = path.join(bogus, "not-a-dir");
  fs.writeFileSync(asFile, "x");           // runDir 指到文件上 → mkdir 真失败
  const { uploader } = spyUploader();
  const { events, sink } = collector();
  const { agent } = dumpAgent([true]);
  const logs: string[] = [];
  const status = await runStep(agent, stepPage, "s:1", { index: 0, keyword: "Then", text: "对吗" }, 1, sink,
    { runDir: asFile, scopeId: "sc", uploader, logFn: (m) => logs.push(m) });
  assert.equal(status, "passed", "证据失败绝不改判定（否则一次抖动把 passed 翻成 error）");
  const done = events.find((e) => e.type === "step_done");
  assert.equal(done.status, "passed");
  assert.deepEqual(done.votes, { yes: 1, total: 1 });
  assert.equal(done.errorType, undefined);
  assert.equal(done.reportRefs, undefined, "没产出就不留空 reportRefs 键");
  assert.equal(logs.length, 1);
});

test("runStep（best-effort 不变量）：上传失败也不改判定、不走 act 异常分类", async () => {
  const { runStep } = await importRunScope();
  const runDir = tmpRun();
  const { uploader } = spyUploader({ failUpload: true });
  const { events, sink } = collector();
  const { agent } = dumpAgent([true]);
  const status = await runStep(agent, stepPage, "s:1", { index: 0, keyword: "Then", text: "对吗" }, 1, sink,
    { runDir, scopeId: "sc", uploader, logFn: () => {} });
  assert.equal(status, "passed");
  const done = events.find((e) => e.type === "step_done");
  assert.equal(done.status, "passed");
  assert.equal(done.errorType, undefined, "上传失败不该被归成 network_error / engine_error");
  assert.equal(done.reportRefs, undefined);
});

test("runStep：不注入 evidence（--no-report 档）→ 事件与此前逐字一致，无 reportRefs", async () => {
  const { runStep } = await importRunScope();
  const { events, sink } = collector();
  const { agent } = dumpAgent([true]);
  const status = await runStep(agent, stepPage, "s:1", { index: 0, keyword: "Then", text: "对吗" }, 1, sink);
  assert.equal(status, "passed");
  const done = events.find((e) => e.type === "step_done");
  assert.equal(done.reportRefs, undefined);
});

test("runStep：URL 导航 step（不调 AI）→ 不产 evidence", async () => {
  const { runStep } = await importRunScope();
  const runDir = tmpRun();
  const { uploader, uploaded } = spyUploader();
  const { events, sink } = collector();
  const { agent } = dumpAgent();
  await runStep(agent, stepPage, "s:1", { index: 0, keyword: "Given", text: '打开 "https://shop.example.com/"' }, 1, sink,
    { runDir, scopeId: "sc", uploader, logFn: () => {} });
  const done = events.find((e) => e.type === "step_done");
  assert.equal(done.status, "passed");
  assert.equal(done.reportRefs, undefined);
  assert.deepEqual(uploaded, []);
});
