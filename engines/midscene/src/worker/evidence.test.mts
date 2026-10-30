// evidence 单测（ADR 0042 决策一/二/六，对称 Nova 的 fixture 映射测试）：
// ① 引擎映射对**真产物裁成的 fixture**（sdkVersion 1.9.8 的 ReportActionDump，两个 execution：Act 与 Boolean）
//    ——格式漂移在升 @midscene/web 后运行测试时变红（决策六第 2 道防线）；
// ② 截图：路径由 id + 扩展名拼、`after-calling` 优先、按 id 去重、上界 K/M；
// ③ scenario 键派生（确定性 + 不二次撞名）；
// ④ best-effort（决策二）：落盘/上传抛 → step_done 照发、无 evidence ref、status 不变；不传 logFn 时失败日志的缺省出口
//    写出前脱敏（ADR 0035 决策 5）；
// ⑤ 截图字节的时机（决策一「上传时机分两类」）：引用到的截图路径随 ref 一起回传，runStep 在 step_done
//    **emit 之后**才交给上传器的后台队列（顺序反了就等于把字节压回判定前面）；
// ⑥ 设备目标的例外（ADR 0051 决策 8；ADR 0042 决策一）：界面快照的键落到 evidence 顶层，确定性与导航 step 在
//    failed / error 时也产（acts 为空数组）、passed 不产，原始控件树的 URI 由 refFor 算出、文件随截图一起回传入队；
//    桌面快照不带设备键，桌面 evidence 与引入快照之前逐字节一致。
// 纯逻辑 + 本地临时目录，不起浏览器、不连 AWS。运行：npm test。
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
import type { Snapshot } from "./surface.mjs";

// ---- 夹具与工具 ----

const FIXTURE = JSON.parse(
  fs.readFileSync(new URL("./fixtures/midscene_dump.json", import.meta.url), "utf-8"),
) as { executions: unknown[] };

const RUN_DIR = "/tmp/run/midscene-run";  // 只参与拼路径，不落盘（映射是纯函数）
const STEP = { index: 2, keyword: "Then", text: "页面上出现『订单提交成功』字样" };
// 桌面接缝给的快照：只有地址两键（AI step 末的 page.url()），不带 step_kind，evidence 因此不加设备键。
const DESKTOP_SNAP: Snapshot = { url: "https://shop.example.com/cart", url_missing: null };

// 截图 uri：本机后端上传器就是这么拼的（file:// + 绝对路径），这里写法相同以便断言路径本身。
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
    snapshot: DESKTOP_SNAP,
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

test("映射：act 的 frames 逐 task 一条，actions 名取 type/subType，args 是 param 原样", () => {
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
  assert.ok(th[0]?.startsWith("The user instruction is to click"));   // Plan：推理在 output.thought（实际运行核出）
  assert.equal(th[1], null);                                           // Locate：空串 → null
  assert.equal(th[2], null);                                           // Tap：无
  assert.ok(th[3]?.startsWith("The user's instruction was to click"));
  assert.ok(doc.acts[1].frames[0].thought?.includes("订单提交成功"));    // Boolean：task.thought
});

test("映射：result 取末个 task 的 output（Boolean 的 output 即那一票的布尔）", () => {
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

test("映射：error 取首个非空 errorMessage；无 errorMessage 时末个 act 兜住抛出的异常", () => {
  const boom = exec(task({ subType: "Plan" }), task({ subType: "Locate", errorMessage: "Element not found" }), task({ errorMessage: "后一个不该被取" }));
  const doc = build({ status: "error", executions: [exec(task()), boom], error: "ActError: timeout", votes: [] });
  assert.equal(doc.acts[1].error, "Element not found", "首个非空 errorMessage 优先于抛出的异常文本");
  assert.equal(doc.acts[0].error, null, "非末 act 且自身无 errorMessage → null（不把异常抄给已完成的前一票）");
  // 全无 errorMessage 时：只有**末** act 兜住抛出的异常（抛的那一刻正在运行的就是它）
  const doc2 = build({ status: "error", executions: [exec(task()), exec(task())], error: "ActError: timeout" });
  assert.deepEqual(doc2.acts.map((a) => a.error), [null, "ActError: timeout"]);
});

test("映射：多行超长 errorMessage 压成一行有界文本（与 step_done.message 格式相同）", () => {
  // SDK 的 errorMessage 与抛出异常的 message 同源（Playwright 的「一句原因 + 多行 call log」），act.error
  // 无论从哪条来源填，形状都必须一样——否则 explain / 报告页的「原因」会因来源不同而一行 / 上千字符不定。
  const firstLine = "Element not found：等" + "候元素可见".repeat(100);  // 首行本身就超上界
  const raw = `\n  ${firstLine}  \n=========== logs ===========\n  waiting for locator("#x")\n`;
  const doc = build({ status: "error", executions: [exec(task({ errorMessage: raw }))], error: "TimeoutError: x", votes: [] });
  const got = doc.acts[0].error as string;
  assert.equal(got.includes("\n"), false, "原因须是一行");
  assert.equal(got.includes("logs"), false, "首个非空行之后的 call log 不进 error");
  assert.equal(got, firstLine.slice(0, 300));
  // 「出错帧」判据同一函数：压行不改变「这一帧算不算出错」
  assert.deepEqual(doc.acts[0].frames.length, 1);
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

test("截图：路径是 <run 目录>/report/screenshots/<id>.<扩展名>，jpeg / png 各按其 mime", () => {
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
  // 5 个 act 各 3 张互不相同的截图、共 15 张候选 → 只有前 12 张拿到 uri
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

// 本机后端上传器的行为形状：refFor / toReportRef 都报 file://，记录调用以分辨「传了字节」（即时）、
// 「只算 ref」与「入了后台队列」（截图字节）。queued 收平铺后的路径，order 记跨调用的相对次序。
function spyUploader(opts: { failUpload?: boolean } = {}) {
  const uploaded: string[] = [];
  const refs: string[] = [];
  const queued: string[] = [];
  const order: string[] = [];
  const uploader: EvidenceUploader = {
    toReportRef: async (p) => {
      if (opts.failUpload) throw new Error("s3 fail");
      uploaded.push(p);
      order.push("toReportRef");
      return fileRef(p);
    },
    refFor: (p) => { refs.push(p); return fileRef(p); },
    enqueue: (paths) => { queued.push(...paths); order.push("enqueue"); },
  };
  return { uploader, uploaded, refs, queued, order };
}

const fixtureAgent = { dump: { executions: FIXTURE.executions } };

test("stepEvidenceRef：落盘到落点 + 经 toReportRef 即时上传拿 ref；截图只算 ref 不上传", async () => {
  const runDir = tmpRun();
  const { uploader, uploaded, refs, queued } = spyUploader();
  const produced = await stepEvidenceRef(
    { runDir, scopeId: "features/order.feature:6", uploader, logFn: () => {} },
    {
      scenarioId: "features/order.feature:12", step: STEP, status: "failed",
      message: "AI 断言未过多数票（0/1）：…", agent: fixtureAgent, execFrom: 1, snapshot: DESKTOP_SNAP,
      prompt: STEP.text, votes: [false], error: null,
    },
  );
  const file = evidenceFile(runDir, "features/order.feature:12", 2);
  assert.equal(produced?.ref, fileRef(file));
  assert.deepEqual(uploaded, [file], "evidence.json 即时上传（它的 ref 要随 step_done 走）");
  assert.ok(refs.every((p) => p.includes(path.join("report", "screenshots"))), "截图只算 ref、不进上传");
  assert.ok(refs.length > 0);
  // 引用到的截图路径随 ref 一起回传（ADR 0042 决策一）：**与 refFor 被调的那几张逐字一致**——本模块自己
  // 不入队（那是 emit 之后的事），但「json 里引用了谁」必须原样交出去，否则调用方无从入队、URI 就悬空。
  assert.deepEqual(produced?.screenshots, refs);
  assert.deepEqual(queued, [], "stepEvidenceRef 自己绝不入队（入队排在 step_done emit 之后）");
  const doc = JSON.parse(fs.readFileSync(file, "utf-8")) as EvidenceDoc;
  assert.equal(doc.acts.length, 1, "execFrom=1 只切出本 step 新增的那个 execution");
  assert.equal(doc.acts[0].vote, false);
  assert.equal(doc.acts[0].url, "https://shop.example.com/cart");
  assert.ok(doc.acts[0].frames[0].thought?.includes("订单提交成功"));
  assert.equal(doc.status, "failed");
});

test("stepEvidenceRef：无 hook（--no-report 方式 / 无产物落点）→ 直接不产", async () => {
  const produced = await stepEvidenceRef(undefined, {
    scenarioId: "s:1", step: STEP, status: "passed", message: null, agent: fixtureAgent,
    execFrom: 0, snapshot: DESKTOP_SNAP, prompt: STEP.text, votes: [], error: null,
  });
  assert.equal(produced, null);
});

test("stepEvidenceRef（桌面）：本 step 没调过 AI（无新 execution 且无指令）→ 不产，failed / error 也不产", async () => {
  const runDir = tmpRun();
  const { uploader, uploaded } = spyUploader();
  for (const status of ["passed", "failed", "error"]) {
    const produced = await stepEvidenceRef({ runDir, scopeId: "sc", uploader }, {
      scenarioId: "s:1", step: { index: 0, keyword: "Given", text: '打开 "https://x/"' }, status,
      message: status === "passed" ? null : "boom", agent: fixtureAgent, execFrom: 2,
      snapshot: { url: null, url_missing: null }, prompt: null, votes: [], error: status === "error" ? "E: boom" : null,
    });
    assert.equal(produced, null, `桌面确定性 / 导航 step 照旧不产（${status}）`);
  }
  assert.deepEqual(uploaded, []);
  assert.ok(!fs.existsSync(path.join(runDir, "evidence")), "确定性 / 导航 step 不留空证据目录");
});

test("stepEvidenceRef：落盘的 evidence.json 里隧道凭据已脱敏（ADR 0035 决策 5），仍是合法 JSON", async () => {
  // step 文本、AI 指令、页面地址、thought、消息都带凭据内嵌的地址：写出的文件里 userinfo 段一律换成 ***。
  const cred = "https://u1:p1@h.example/";
  const runDir = tmpRun();
  const { uploader } = spyUploader();
  const agent = { dump: { executions: [exec(task({ type: "Insight", subType: "Boolean", output: false,
    thought: `已打开 ${cred}home`, shot: "s1" }))] } };
  const produced = await stepEvidenceRef({ runDir, scopeId: "sc", uploader, logFn: () => {} }, {
    scenarioId: "s:1", step: { index: 0, keyword: "Then", text: `页面 ${cred}home 显示欢迎语` }, status: "failed",
    message: `页面停在 ${cred}home 未跳转`, agent, execFrom: 0, snapshot: { url: `${cred}home`, url_missing: null },
    prompt: `确认 ${cred}home 已加载`, votes: [false], error: null,
  });
  assert.notEqual(produced, null);
  const raw = fs.readFileSync(evidenceFile(runDir, "s:1", 0), "utf-8");
  assert.ok(!raw.includes("u1:p1@"), "凭据不该出现在 evidence.json 里");
  assert.ok(raw.includes("***@"));
  const doc = JSON.parse(raw) as EvidenceDoc;
  assert.equal(doc.step.text, "页面 https://***@h.example/home 显示欢迎语");
  assert.equal(doc.message, "页面停在 https://***@h.example/home 未跳转");
  assert.equal(doc.acts[0].prompt, "确认 https://***@h.example/home 已加载");
  assert.equal(doc.acts[0].url, "https://***@h.example/home");
  assert.equal(doc.acts[0].frames[0].thought, "已打开 https://***@h.example/home");
});

test("stepEvidenceRef：落盘失败 → 日志一行 + 返 null，绝不抛", async () => {
  // runDir 指到一个**文件**上 → mkdir 必失败（真失败，不打桩）
  const bogus = fs.mkdtempSync(path.join(os.tmpdir(), "evid-"));
  const asFile = path.join(bogus, "not-a-dir");
  fs.writeFileSync(asFile, "x");
  const { uploader, uploaded } = spyUploader();
  const logs: string[] = [];
  const produced = await stepEvidenceRef({ runDir: asFile, scopeId: "sc", uploader, logFn: (m) => logs.push(m) }, {
    scenarioId: "s:1", step: STEP, status: "failed", message: null, agent: fixtureAgent,
    execFrom: 1, snapshot: DESKTOP_SNAP, prompt: STEP.text, votes: [false], error: null,
  });
  assert.equal(produced, null);
  assert.deepEqual(uploaded, []);
  assert.equal(logs.length, 1, "失败只一行日志");
  assert.ok(logs[0].includes("证据"));
});

test("stepEvidenceRef：上传失败 → 同样吞成 null（toReportRef 的失败即抛契约不动）", async () => {
  const runDir = tmpRun();
  const { uploader } = spyUploader({ failUpload: true });
  const logs: string[] = [];
  const produced = await stepEvidenceRef({ runDir, scopeId: "sc", uploader, logFn: (m) => logs.push(m) }, {
    scenarioId: "s:1", step: STEP, status: "failed", message: null, agent: fixtureAgent,
    execFrom: 1, snapshot: DESKTOP_SNAP, prompt: STEP.text, votes: [false], error: null,
  });
  assert.equal(produced, null);
  assert.equal(logs.length, 1);
  assert.ok(fs.existsSync(evidenceFile(runDir, "s:1", 2)), "json 已落盘（本地仍留证据，scope 末整目录 flush 兜）");
});

// 缺省日志出口（不传 logFn）写出前脱敏（ADR 0035 决策 5）：失败日志带着异常文本，上传出错时它可能含预签名地址或设备端点令牌。
// 样本取跨语言用例表里输入与期望不同的条目，写出的文字要含期望的脱敏结果、不含原始输入。
const REDACTION_CASES = (JSON.parse(
  fs.readFileSync(new URL("../../../fixtures/redaction-cases.json", import.meta.url), "utf-8"),
) as { cases: Array<[string, string]> }).cases.filter(([input, expected]) => input !== expected);

async function captureStderr(fn: () => Promise<unknown>): Promise<string> {
  const chunks: string[] = [];
  const original = process.stderr.write;
  process.stderr.write = ((chunk: string | Uint8Array) => {
    chunks.push(typeof chunk === "string" ? chunk : Buffer.from(chunk).toString("utf-8"));
    return true;
  }) as typeof process.stderr.write;
  try {
    await fn();
  } finally {
    process.stderr.write = original;
  }
  return chunks.join("");
}

test("stepEvidenceRef：不传 logFn 时缺省写 stderr，失败日志里的凭据在写出前脱敏", async () => {
  assert.ok(REDACTION_CASES.length > 5, "用例表里带凭据的样本不该被筛空");
  for (const [secret, masked] of REDACTION_CASES) {
    const runDir = tmpRun();
    const uploader: EvidenceUploader = {
      toReportRef: async () => { throw new Error(`上传 ${secret} 失败`); },
      refFor: fileRef,
      enqueue: () => {},
    };
    let produced: unknown = undefined;
    const out = await captureStderr(async () => {
      produced = await stepEvidenceRef({ runDir, scopeId: "sc", uploader }, {
        scenarioId: "s:1", step: STEP, status: "failed", message: null, agent: fixtureAgent,
        execFrom: 1, snapshot: DESKTOP_SNAP, prompt: STEP.text, votes: [false], error: null,
      });
    });
    assert.equal(produced, null);
    assert.equal(out.split("\n").filter((l) => l !== "").length, 1, "失败只一行日志");
    assert.ok(out.includes("证据") && out.includes(masked), `应写出脱敏后的 ${JSON.stringify(masked)}，实际 ${JSON.stringify(out)}`);
    assert.ok(!out.includes(secret), `不应写出原始输入 ${JSON.stringify(secret)}，实际 ${JSON.stringify(out)}`);
  }
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

/** runStep 的第一个参数是界面接缝对象（ADR 0052 决策 2）：这里用真实的桌面实现，只换掉 AgentCore 控制面与 CDP 建连两处外部边界，
 *  桌面 evidence 因此经与生产相同的接缝路径产出（逐字节不变的前提）。 */
async function desktopSeam(agent: any, page: any = stepPage): Promise<any> {
  const { createDesktopSurface } = await import("./surface-desktop.mjs");
  const target = { device: "desktop", uiKind: "web" };
  const p = { evaluate: async () => undefined, ...page };
  const ctx = { pages: () => [p], newPage: async () => p, addInitScript: async () => {}, setExtraHTTPHeaders: async () => {} };
  const browser = { contexts: () => [ctx], newContext: async () => ctx, close: async () => {} };
  const surface = createDesktopSurface({
    job: { schemaVersion: 1, scope: { id: "sc", name: "sc" }, engine: "midscene", assertionVotes: 1, timeoutS: null, target, deviceRequest: null },
    emit: async () => {}, log: () => {}, agentOpts: {}, uploader: {} as any, artifactRoot: undefined, requestFinalization: () => {},
  } as any, {
    client: { send: async () => ({ sessionId: "sess-1", streams: { automationStream: { streamEndpoint: "wss://agentcore.test/1" } } }) } as any,
    signCdpUpgrade: async () => ({}), connectOverCDP: async () => browser as any,
    createAgent: () => agent, runId: "20260629T141207Z-a3f9c1",
  });
  const acquired = await surface.acquire();
  assert.ok(acquired.ready, "桌面接缝应就绪");
  return { surface, agent: acquired.agent, target, sessionLost: null };
}

test("runStep：AI 断言 step 的 step_done 带 kind=evidence 的 step 级 ref（Midscene 首条）", async () => {
  const { runStep } = await importRunScope();
  const runDir = tmpRun();
  const { uploader } = spyUploader();
  const { events, sink } = collector();
  const { agent } = dumpAgent([false]);
  const status = await runStep(await desktopSeam(agent), "features/order.feature:12",
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
  const status = await runStep(await desktopSeam(agent), "s:1", { index: 0, keyword: "Then", text: "对吗" }, 3, sink,
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
  await runStep(await desktopSeam(agent), "s:1", { index: 1, keyword: "When", text: "点击提交" }, 1, sink,
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
  const status = await runStep(await desktopSeam(agent), "s:1", { index: 0, keyword: "When", text: "点击提交" }, 1, sink,
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
  const status = await runStep(await desktopSeam(agent), "s:1", { index: 0, keyword: "Then", text: "对吗" }, 1, sink,
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
  const status = await runStep(await desktopSeam(agent), "s:1", { index: 0, keyword: "Then", text: "对吗" }, 1, sink,
    { runDir, scopeId: "sc", uploader, logFn: () => {} });
  assert.equal(status, "passed");
  const done = events.find((e) => e.type === "step_done");
  assert.equal(done.status, "passed");
  assert.equal(done.errorType, undefined, "上传失败不该被归成 network_error / engine_error");
  assert.equal(done.reportRefs, undefined);
});

test("runStep：不注入 evidence（--no-report 方式）→ 事件与此前逐字一致，无 reportRefs", async () => {
  const { runStep } = await importRunScope();
  const { events, sink } = collector();
  const { agent } = dumpAgent([true]);
  const status = await runStep(await desktopSeam(agent), "s:1", { index: 0, keyword: "Then", text: "对吗" }, 1, sink);
  assert.equal(status, "passed");
  const done = events.find((e) => e.type === "step_done");
  assert.equal(done.reportRefs, undefined);
});

// ---- ⑤ 截图字节的时机（ADR 0042 决策一「上传时机分两类」）----
// 锁住「emit 先、入队后」这个顺序契约：入队排在 emit 之前，等于把 K × 票数次 PutObject 又压回判定前面
// （判定要等队列排到才发得出），正是决策一要避免的那件事；顺序只在真实调用序里看得见，故用同一个 order 数组
// 记 sink.emit 与上传器三个方法的相对次序。
test("runStep：截图字节在 step_done emit **之后**才入队，且入的正是 json 里引用的那几张", async () => {
  const { runStep } = await importRunScope();
  const runDir = tmpRun();
  const order: string[] = [];
  const queued: string[] = [];
  const uploader: EvidenceUploader = {
    toReportRef: async (p) => { order.push("上传 evidence.json"); return fileRef(p); },
    refFor: (p) => fileRef(p),
    enqueue: (paths) => { order.push("截图入队"); queued.push(...paths); },
  };
  const events: any[] = [];
  const sink = { emit: async (e: any) => { events.push(e); order.push(`emit:${e.type}`); } };
  const { agent } = dumpAgent([false]);
  await runStep(await desktopSeam(agent), "s:1", { index: 0, keyword: "Then", text: "对吗" }, 1, sink,
    { runDir, scopeId: "sc", uploader, logFn: () => {} });
  assert.deepEqual(order, [
    "emit:step_started", "上传 evidence.json", "emit:step_done", "截图入队",
  ], "evidence.json 即时传拿 ref → 发 step_done → 才把截图交后台队列");
  // 入队的与 json 里写的 URI 同一批（否则 json 里的 URI 悬空、或传了没人引用的字节）
  const doc = JSON.parse(fs.readFileSync(evidenceFile(runDir, "s:1", 0), "utf-8")) as EvidenceDoc;
  const inDoc = doc.acts.flatMap((a) => a.frames.map((f) => f.screenshot)).filter((u) => u !== null);
  assert.ok(inDoc.length > 0, "本 step 的 evidence 确实引用了截图");
  assert.deepEqual(queued.map(fileRef), inDoc);
});

test("runStep：本 step 的 evidence 没引用任何截图 → 不入队（不给队列塞空批）", async () => {
  const { runStep } = await importRunScope();
  const runDir = tmpRun();
  const { uploader, queued } = spyUploader();
  const { events, sink } = collector();
  // 新 execution 的 task 不带截图（如 SDK 未落盘 / 无 screenshot id）→ json 里 screenshot 全 null
  const { agent } = dumpAgent([true], () => exec(task({ thought: "想了想" })));
  await runStep(await desktopSeam(agent), "s:1", { index: 0, keyword: "Then", text: "对吗" }, 1, sink,
    { runDir, scopeId: "sc", uploader, logFn: () => {} });
  assert.equal(events.find((e) => e.type === "step_done").reportRefs[0].kind, "evidence");
  assert.deepEqual(queued, []);
});

test("runStep：URL 导航 step（不调 AI）→ 不产 evidence", async () => {
  const { runStep } = await importRunScope();
  const runDir = tmpRun();
  const { uploader, uploaded } = spyUploader();
  const { events, sink } = collector();
  const { agent } = dumpAgent();
  await runStep(await desktopSeam(agent), "s:1", { index: 0, keyword: "Given", text: '"https://shop.example.com/"' }, 1, sink,
    { runDir, scopeId: "sc", uploader, logFn: () => {} });
  const done = events.find((e) => e.type === "step_done");
  assert.equal(done.status, "passed");
  assert.equal(done.reportRefs, undefined);
  assert.deepEqual(uploaded, []);
});

test("runStep：AI step 末页面已关（page.url() 抛）→ evidence 的 url 记 null，其余证据照产、判定不变", async () => {
  const { runStep } = await importRunScope();
  const runDir = tmpRun();
  const { uploader } = spyUploader();
  const { events, sink } = collector();
  const { agent } = dumpAgent([false]);
  const closedPage = { url: () => { throw new Error("Target page, context or browser has been closed"); }, goto: async () => {} };
  const status = await runStep(await desktopSeam(agent, closedPage), "s:1", { index: 2, keyword: "Then", text: STEP.text }, 1, sink,
    { runDir, scopeId: "sc", uploader, logFn: () => {} });
  assert.equal(status, "failed", "读不到地址不改判定");
  const done = events.find((e) => e.type === "step_done");
  assert.equal(done.errorType, "assertion_failed");
  assert.equal(done.reportRefs[0].kind, "evidence");
  const doc = JSON.parse(fs.readFileSync(evidenceFile(runDir, "s:1", 2), "utf-8")) as EvidenceDoc;
  assert.equal(doc.acts[0].url, null);
  assert.ok(doc.acts[0].frames.length > 0, "地址缺了不影响其余证据");
});

// ---- ⑥ 设备目标的例外与桌面不变（ADR 0051 决策 8；ADR 0042 决策一）----
// 快照由界面接缝在 step 末采好交进来（evidence 保持纯映射、不发 WebDriver 命令，ADR 0052 决策 7）：快照带 step_kind
// 即设备实现给的，evidence 才加设备键；桌面快照只有地址两键，桌面 evidence 必须与引入快照之前逐字节一致。

// 引入快照之前的实现对下面这份输入写出的 evidence.json 原文（`<RUN_DIR>` 处是本次的产物落点根）。桌面路径的消费方
// （explain、报告页、使用方脚本）按这份字节形态读，任何新键、键序变化或格式变化都会让本用例变红。
const DESKTOP_GOLDEN = `{
  "schema_version": 1,
  "engine": "midscene",
  "scope_id": "features/order.feature:6",
  "scenario_id": "features/order.feature:12",
  "step_index": 2,
  "step": {
    "keyword": "Then",
    "text": "页面显示成功"
  },
  "status": "failed",
  "message": "AI 断言未过多数票（0/1）：页面显示成功",
  "acts": [
    {
      "index": 0,
      "prompt": "页面显示成功",
      "vote": false,
      "url": "https://shop.example.com/cart",
      "frames": [
        {
          "url": null,
          "thought": "先看看",
          "actions": [
            {
              "name": "Planning/Plan",
              "args": null
            }
          ],
          "screenshot": "file://<RUN_DIR>/report/screenshots/s0.jpeg"
        },
        {
          "url": null,
          "thought": null,
          "actions": [
            {
              "name": "Action Space/Tap",
              "args": {
                "x": 1
              }
            }
          ],
          "screenshot": "file://<RUN_DIR>/report/screenshots/s1.jpeg"
        }
      ],
      "result": null,
      "error": "boom",
      "time_worked_s": null
    }
  ]
}`;

// 产出 DESKTOP_GOLDEN 的那份输入：前一个 step 留下一个 execution，本 step 一票断言、两个 task（含 thought、出错帧与「动作后」截图）。
function goldenInput(over: { snapshot?: Snapshot }) {
  const agent = { dump: { executions: [
    { name: "old", tasks: [] },
    exec(
      task({ type: "Planning", subType: "Plan", thought: "先看看", shot: "s0" }),
      task({ type: "Action Space", subType: "Tap", param: { x: 1 }, errorMessage: "boom\nmore", after: "s1" }),
    ),
  ] } };
  const base = {
    scenarioId: "features/order.feature:12", step: { index: 2, keyword: "Then", text: "页面显示成功" }, status: "failed",
    message: "AI 断言未过多数票（0/1）：页面显示成功", agent, execFrom: 1,
    prompt: "页面显示成功", votes: [false], error: null,
  };
  return { ...base, snapshot: over.snapshot ?? DESKTOP_SNAP };
}

async function goldenBytes(over: { snapshot?: Snapshot }): Promise<string> {
  const runDir = tmpRun();
  const { uploader } = spyUploader();
  const produced = await stepEvidenceRef({ runDir, scopeId: "features/order.feature:6", uploader, logFn: () => {} }, goldenInput(over));
  assert.notEqual(produced, null);
  return fs.readFileSync(evidenceFile(runDir, "features/order.feature:12", 2), "utf-8").split(runDir).join("<RUN_DIR>");
}

test("桌面不变：桌面快照写出的 evidence.json 与引入快照之前逐字节一致", async () => {
  assert.equal(await goldenBytes({ snapshot: DESKTOP_SNAP }), DESKTOP_GOLDEN);
});

test("桌面不变：真产物 fixture 上，桌面 evidence 的顶层键与 act 键都与引入快照之前相同，不出现任何设备键", () => {
  const doc = build({ executions: FIXTURE.executions, status: "failed", votes: [null, false] });
  assert.deepEqual(Object.keys(doc), [
    "schema_version", "engine", "scope_id", "scenario_id", "step_index", "step", "status", "message", "acts",
  ]);
  for (const a of doc.acts) {
    assert.deepEqual(Object.keys(a), ["index", "prompt", "vote", "url", "frames", "result", "error", "time_worked_s"]);
  }
  // 桌面快照即便带着 url_missing 也不写顶层地址键：地址只进各 act（ADR 0042 映射表 act.url）
  const missing = build({ snapshot: { url: null, url_missing: "error" }, executions: FIXTURE.executions });
  assert.ok(!("url" in missing) && !("url_missing" in missing) && !("step_kind" in missing));
});

// 设备快照：网页目标的 AI step（读到地址、passed，不采控件）。
const DEVICE_AI_SNAP: Snapshot = { step_kind: "ai", url: "https://m.example.com/list", url_missing: null };
const PAGE_SOURCE = path.join(RUN_DIR, "device", "page-source-3.xml");
// 设备快照：failed / error 的 step 带控件摘要与原始控件树。
function failedDeviceSnap(over: Partial<Snapshot> = {}): Snapshot {
  return {
    step_kind: "ai", url: null, url_missing: "no_web_context",
    controls: { items: [{ type: "Button", id: "login", text: "登录", a11y_id: "btn-login" }], total: 250, truncated: true },
    controls_missing: null,
    page_source_path: PAGE_SOURCE,
    page_source_truncated: true,
    ...over,
  };
}

test("快照落位（设备 AI step、passed）：step_kind 与顶层 url / url_missing 落位，各 act 的 url 取快照地址，不采控件即无控件键", () => {
  const doc = build({ snapshot: DEVICE_AI_SNAP, executions: FIXTURE.executions, status: "passed" });
  assert.deepEqual(Object.keys(doc), [
    "schema_version", "engine", "scope_id", "scenario_id", "step_index", "step", "status", "message",
    "step_kind", "url", "url_missing", "acts",
  ]);
  assert.equal(doc.step_kind, "ai");
  assert.equal(doc.url, "https://m.example.com/list");
  assert.equal(doc.url_missing, null);
  assert.ok(doc.acts.length > 0 && doc.acts.every((a) => a.url === "https://m.example.com/list"));
});

test("快照落位（设备 failed / error）：controls 与 page_source 两组键落位，page_source 是 refFor 算出的 URI", () => {
  const refs: string[] = [];
  const doc = build({
    snapshot: failedDeviceSnap(), executions: FIXTURE.executions, status: "failed", votes: [null, false],
    refFor: (p) => { refs.push(p); return `s3://bkt/run/${path.basename(p)}`; },
  });
  assert.deepEqual(Object.keys(doc), [
    "schema_version", "engine", "scope_id", "scenario_id", "step_index", "step", "status", "message",
    "step_kind", "url", "url_missing", "controls", "controls_missing", "page_source", "page_source_truncated", "acts",
  ]);
  assert.equal(doc.url, null);
  assert.equal(doc.url_missing, "no_web_context");
  assert.ok(doc.acts.every((a) => a.url === null), "没有可用网页上下文时各 act 的 url 同为 null");
  assert.deepEqual(doc.controls, {
    items: [{ type: "Button", id: "login", text: "登录", a11y_id: "btn-login" }], total: 250, truncated: true,
  });
  assert.equal(doc.controls_missing, null);
  assert.equal(doc.page_source, "s3://bkt/run/page-source-3.xml");
  assert.equal(doc.page_source_truncated, true);
  assert.equal(refs[refs.length - 1], PAGE_SOURCE, "原始控件树的 URI 经同一个 refFor 算出（字节随后入队）");
});

test("快照落位：控件摘要每项只写 schema 的四个键，缺的记 null（适配器多带的字段不进 evidence）", () => {
  const snap = failedDeviceSnap({
    controls: { items: [{ type: "TextView", id: null, text: "欢迎", a11y_id: null, bounds: "[0,0][1,1]" } as never], total: 1, truncated: false },
  });
  const doc = build({ snapshot: snap, status: "error", error: "E: x" });
  assert.deepEqual(doc.controls?.items, [{ type: "TextView", id: null, text: "欢迎", a11y_id: null }]);
});

test("快照落位：采集失败时 controls 为 null 并给 controls_missing，原始控件树没取到时 page_source 为 null", () => {
  const doc = build({
    snapshot: failedDeviceSnap({ controls: null, controls_missing: "timeout", page_source_path: null, page_source_truncated: false }),
    status: "error", error: "E: x",
  });
  assert.equal(doc.controls, null);
  assert.equal(doc.controls_missing, "timeout");
  assert.equal(doc.page_source, null);
  assert.equal(doc.page_source_truncated, false);
});

test("快照落位：应用目标的 url 为 null、url_missing 为 not_applicable", () => {
  const doc = build({ snapshot: { step_kind: "ai", url: null, url_missing: "not_applicable" }, executions: FIXTURE.executions });
  assert.equal(doc.url, null);
  assert.equal(doc.url_missing, "not_applicable");
});

test("原始控件树不占截图额度：截图已用满每 step 上限时 page_source 仍有 URI", () => {
  const calls: string[] = [];
  const acts = Array.from({ length: 5 }, (_, a) => exec(
    task({ shot: `a${a}-0`, thought: "t" }), task({ shot: `a${a}-1`, errorMessage: "boom" }), task({ shot: `a${a}-2` }),
  ));
  const doc = build({
    snapshot: failedDeviceSnap(), status: "error", executions: acts,
    refFor: (p) => { calls.push(p); return fileRef(p); },
  });
  assert.equal(doc.acts.flatMap((a) => a.frames).filter((f) => f.screenshot !== null).length, 12);
  assert.equal(doc.page_source, fileRef(PAGE_SOURCE));
  assert.equal(calls.length, 13, "12 张截图 + 1 份原始控件树");
});

test("确定性 / 导航 step（设备）：acts 恒为空数组，抛出的异常只进 message、不补一条 error act", () => {
  for (const kind of ["deterministic", "navigation"] as const) {
    const doc = build({
      snapshot: failedDeviceSnap({ step_kind: kind }), status: "error", message: "E: boom",
      // 起点标记读失败时切片可能带进历史 execution：这类 step 不调 AI，一律不映射
      executions: [exec(task({ shot: "old", thought: "历史" }))], prompt: null, error: "E: boom",
    });
    assert.equal(doc.step_kind, kind);
    assert.deepEqual(doc.acts, []);
    assert.equal(doc.message, "E: boom");
  }
});

test("stepEvidenceRef（设备）：确定性与导航 step 在 failed / error 时产 acts:[] 的 evidence，passed 不产", async () => {
  const runDir = tmpRun();
  const { uploader, uploaded } = spyUploader();
  const cases = [
    { kind: "deterministic", status: "failed", index: 0 },
    { kind: "deterministic", status: "error", index: 1 },
    { kind: "navigation", status: "error", index: 2 },
    { kind: "navigation", status: "failed", index: 3 },
  ] as const;
  for (const c of cases) {
    const produced = await stepEvidenceRef({ runDir, scopeId: "sc", uploader, logFn: () => {} }, {
      scenarioId: "s:1", step: { index: c.index, keyword: "When", text: "x" }, status: c.status,
      message: "原因", agent: fixtureAgent, execFrom: 2,
      snapshot: failedDeviceSnap({ step_kind: c.kind }), prompt: null, votes: [], error: c.status === "error" ? "E: x" : null,
    });
    assert.notEqual(produced, null, `${c.kind} ${c.status} 要产 evidence`);
    const doc = JSON.parse(fs.readFileSync(evidenceFile(runDir, "s:1", c.index), "utf-8")) as EvidenceDoc;
    assert.equal(doc.step_kind, c.kind);
    assert.equal(doc.status, c.status);
    assert.equal(doc.message, "原因");
    assert.deepEqual(doc.acts, []);
  }
  assert.equal(uploaded.length, cases.length);
  // passed 的确定性 / 导航 step 不产（设备快照此时不带控件键）
  for (const kind of ["deterministic", "navigation"] as const) {
    const produced = await stepEvidenceRef({ runDir, scopeId: "sc", uploader }, {
      scenarioId: "s:2", step: { index: 0, keyword: "Given", text: "x" }, status: "passed", message: null,
      agent: fixtureAgent, execFrom: 2, snapshot: { step_kind: kind, url: null, url_missing: "not_applicable" },
      prompt: null, votes: [], error: null,
    });
    assert.equal(produced, null, `${kind} passed 不产`);
  }
  assert.ok(!fs.existsSync(path.dirname(evidenceFile(runDir, "s:2", 0))), "passed 的确定性 / 导航 step 不留证据目录");
});

test("stepEvidenceRef（设备）：AI step 各状态都产并带 step_kind", async () => {
  const runDir = tmpRun();
  const { uploader } = spyUploader();
  for (const [i, status] of (["passed", "failed", "error"] as const).entries()) {
    const produced = await stepEvidenceRef({ runDir, scopeId: "sc", uploader, logFn: () => {} }, {
      scenarioId: "s:1", step: { index: i, keyword: "Then", text: "对吗" }, status, message: null,
      agent: fixtureAgent, execFrom: 1, snapshot: status === "passed" ? DEVICE_AI_SNAP : failedDeviceSnap(),
      prompt: "对吗", votes: [status === "passed"], error: status === "error" ? "E: x" : null,
    });
    assert.notEqual(produced, null);
    const doc = JSON.parse(fs.readFileSync(evidenceFile(runDir, "s:1", i), "utf-8")) as EvidenceDoc;
    assert.equal(doc.step_kind, "ai");
    assert.equal(doc.acts.length, 1);
  }
});

test("stepEvidenceRef（设备）：AI step 在 step 前核对失败、没调 AI 时同样产（acts 为空数组），已写盘的原始控件树被引用并回传", async () => {
  const runDir = tmpRun();
  const { uploader, uploaded, refs } = spyUploader();
  const pageSource = path.join(runDir, "device", "page-source-1.xml");
  const produced = await stepEvidenceRef({ runDir, scopeId: "sc", uploader, logFn: () => {} }, {
    scenarioId: "s:1", step: { index: 4, keyword: "When", text: "点一下" }, status: "error", message: "未能切回原生界面",
    agent: fixtureAgent, execFrom: FIXTURE.executions.length,
    snapshot: failedDeviceSnap({ page_source_path: pageSource }), prompt: null, votes: [], error: null,
  });
  assert.notEqual(produced, null, "设备上 AI step 一律产（ADR 0052 决策 2 第 4 步）");
  assert.equal(uploaded.length, 1);
  assert.deepEqual(produced?.screenshots, [pageSource], "没有截图，只有原始控件树随 evidence 回传入队");
  assert.deepEqual(refs, [pageSource]);
  const doc = JSON.parse(fs.readFileSync(evidenceFile(runDir, "s:1", 4), "utf-8")) as EvidenceDoc;
  assert.equal(doc.step_kind, "ai");
  assert.equal(doc.status, "error");
  assert.equal(doc.message, "未能切回原生界面");
  assert.deepEqual(doc.acts, [], "本 step 没调 AI、也没有抛出的异常，不补只带 error 的 act");
  assert.equal(doc.page_source, fileRef(pageSource));
});

test("stepEvidenceRef（设备）：原始控件树的文件随截图一起回传给调用方入队，本模块自己不入队", async () => {
  const runDir = tmpRun();
  const { uploader, refs, queued } = spyUploader();
  const pageSource = path.join(runDir, "device", "page-source-0.xml");
  const produced = await stepEvidenceRef({ runDir, scopeId: "sc", uploader, logFn: () => {} }, {
    scenarioId: "s:1", step: STEP, status: "failed", message: null, agent: fixtureAgent, execFrom: 1,
    snapshot: failedDeviceSnap({ page_source_path: pageSource }), prompt: STEP.text, votes: [false], error: null,
  });
  assert.notEqual(produced, null);
  assert.deepEqual(produced?.screenshots, refs, "回传的正是算过 URI 的那几份文件");
  assert.equal(produced?.screenshots[produced.screenshots.length - 1], pageSource);
  assert.ok(produced!.screenshots.length > 1, "截图在前、原始控件树在后");
  assert.deepEqual(queued, [], "入队排在 step_done emit 之后，由调用方做");
  const doc = JSON.parse(fs.readFileSync(evidenceFile(runDir, "s:1", 2), "utf-8")) as EvidenceDoc;
  assert.equal(doc.page_source, fileRef(pageSource));
});

test("stepEvidenceRef（设备）：控件文本与地址里的签名与令牌在写盘前脱敏，含 XML 实体转义形态", async () => {
  const runDir = tmpRun();
  const { uploader } = spyUploader();
  const signed = "https://b/k?X-Amz-Date=1&amp;X-Amz-Signature=abc&amp;X-Amz-Expires=9";
  const tokenUrl = "https://h.example/x?a=1&gherkai_tunnel_token=tok123&b=2";
  const produced = await stepEvidenceRef({ runDir, scopeId: "sc", uploader, logFn: () => {} }, {
    scenarioId: "s:1", step: { index: 0, keyword: "When", text: "x" }, status: "error", message: "E: x",
    agent: fixtureAgent, execFrom: 2, prompt: null, votes: [], error: "E: x",
    snapshot: failedDeviceSnap({
      step_kind: "deterministic", url: tokenUrl, url_missing: null,
      controls: { items: [{ type: "WebView", id: null, text: signed, a11y_id: null }], total: 1, truncated: false },
    }),
  });
  assert.notEqual(produced, null);
  const raw = fs.readFileSync(evidenceFile(runDir, "s:1", 0), "utf-8");
  assert.ok(!raw.includes("abc") && !raw.includes("tok123"), "签名与令牌不进 evidence.json");
  const doc = JSON.parse(raw) as EvidenceDoc;
  assert.equal(doc.url, "https://h.example/x?a=1&gherkai_tunnel_token=***&b=2");
  assert.equal(doc.controls?.items[0].text, "https://b/k?X-Amz-Date=1&amp;X-Amz-Signature=***&amp;X-Amz-Expires=9");
});
