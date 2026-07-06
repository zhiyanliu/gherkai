// ArtifactUploader 单测（ADR 0029 第一期，对称 Nova 的 test_artifact_upload.py）：
// 整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-op 报 file://。mock S3 client（不连真 AWS）。
// 跑：node --import tsx --test worker/artifact-upload.test.ts（已接入 npm test 的 worker/*.test.ts）。
//
// 重点护 ADR 0029：key 镜像 run 树、ref 逐字一致、两级时机（reportRef 实时传不删 / flush 传剩余+全成功删整目录）、
// 整目录传不按文件挑（抗 SDK 升级）、失败护栏（reportRef 抛 / 剩余吞但不删目录）、no-op 报 file://。
import { test } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { ArtifactUploader } from "../lib/artifact-upload.mjs";

// 塞 mock S3 client（记录 send 的 key；failKeys 里的 key 抛错），绕过真 aws-sdk。返回纯 key 数组（老测试直接
// deepEqual 用）。send 的第二参 options（含 abortSignal）另记到 client.sendOpts 上，供超时 plumbing 断言读
// （uploadOne 给 send 传 { abortSignal: AbortSignal.timeout(...) }，mock 曾丢弃第二参 → 漏传也照绿，绿≠对 CLAUDE.md）。
function withMockClient(u: ArtifactUploader, opts: { failKeys?: string[] } = {}): string[] {
  const keys: string[] = [];
  const sendOpts: any[] = [];
  (u as any).client = {
    sendOpts,  // 新测试经 (u as any).client.sendOpts 读第二参，不污染返回的 keys 数组（deepEqual 友好）
    send: async (cmd: any, options?: any) => {
      keys.push(cmd.input.Key);
      sendOpts.push(options);
      if ((opts.failKeys ?? []).includes(cmd.input.Key)) throw new Error("s3 fail");
      return {};
    },
  };
  return keys;
}

function tmproot(): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), "artup-"));
}

// ---- no-op（无 ARTIFACT_S3_BUCKET）：报 file://、不上传、不删、flush 是 no-op ----
test("no-op reports file:// and does not touch local", async () => {
  const root = tmproot();
  const f = path.join(root, "midscene-run", "report", "x.html");
  fs.mkdirSync(path.dirname(f), { recursive: true });
  fs.writeFileSync(f, "html");
  delete process.env.ARTIFACT_S3_BUCKET;
  const u = ArtifactUploader.fromEnv();
  assert.equal(u.enabled, false);
  assert.equal(await u.toReportRef(f), `file://${f}`);  // 裸拼 file://（与 Nova 对称、保旧行为）
  await u.flushAndCleanup(path.join(root, "midscene-run"));
  assert.ok(fs.existsSync(f));  // no-op 不碰本地
});

// ---- toReportRef：实时传（不删）、key 镜像 run 树、ref 逐字一致 ----
test("toReportRef uploads realtime, key mirrors tree, ref matches key, no delete", async () => {
  const root = tmproot();
  const runDir = path.join(root, "reports", "rid");
  const rep = path.join(runDir, "midscene-run", "report");
  fs.mkdirSync(rep, { recursive: true });
  const f = path.join(rep, "x.html");
  fs.writeFileSync(f, "html");
  const u = new (ArtifactUploader as any)("bkt", "reports/rid/", runDir);
  const keys = withMockClient(u);
  const ref = await u.toReportRef(f);
  const expectedKey = "reports/rid/midscene-run/report/x.html";
  assert.deepEqual(keys, [expectedKey]);            // 实时传、key 镜像 run 树
  assert.equal(ref, `s3://bkt/${expectedKey}`);     // ref 与 key 逐字一致（0029 主验）
  assert.ok(fs.existsSync(f));                       // 实时传**不删**（留到 flush）
});

// ---- flushAndCleanup：传剩余（跳过已传）+ 全成功删整目录（整目录传、不按文件挑）----
test("flush uploads rest, skips uploaded, deletes whole dir", async () => {
  const root = tmproot();
  const runDir = path.join(root, "reports", "rid");
  const msDir = path.join(runDir, "midscene-run");
  const rep = path.join(msDir, "report");
  fs.mkdirSync(rep, { recursive: true });
  const html = path.join(rep, "x.html"); fs.writeFileSync(html, "html");   // reportRef 文件（实时传）
  const logDir = path.join(msDir, "log"); fs.mkdirSync(logDir);
  const log = path.join(logDir, "ai-call.log"); fs.writeFileSync(log, "log");  // 剩余（flush 传，非产物也传）
  const u = new (ArtifactUploader as any)("bkt", "reports/rid/", runDir);
  const keys = withMockClient(u);
  await u.toReportRef(html);           // 实时传 html
  await u.flushAndCleanup(msDir);
  // html 只传一次（实时；flush 跳过）；log 由 flush 传（整目录、不按文件挑）
  assert.equal(keys.filter((k) => k.endsWith("report/x.html")).length, 1);
  assert.ok(keys.includes("reports/rid/midscene-run/log/ai-call.log"));
  assert.ok(!fs.existsSync(msDir));  // 全成功 → 整目录删（本地零残留，含 log/）
});

// ---- 幂等：已成功传的文件再调 toReportRef → 不重传（对称 Nova，ADR 0029 review #4）----
test("toReportRef idempotent, no re-upload", async () => {
  const root = tmproot();
  const runDir = path.join(root, "reports", "rid");
  const rep = path.join(runDir, "midscene-run", "report");
  fs.mkdirSync(rep, { recursive: true });
  const f = path.join(rep, "x.html");
  fs.writeFileSync(f, "html");
  const u = new (ArtifactUploader as any)("bkt", "reports/rid/", runDir);
  const keys = withMockClient(u);
  const ref1 = await u.toReportRef(f);  // 首次真传
  const ref2 = await u.toReportRef(f);  // 再调：幂等短路
  assert.equal(ref1, ref2);
  assert.equal(keys.length, 1, "已传文件再调不应重复 upload");
});

// ---- reportRef 实时传失败 → 抛（可观测），本地不删 ----
test("toReportRef upload failure raises and keeps local", async () => {
  const root = tmproot();
  const runDir = path.join(root, "reports", "rid");
  const f = path.join(runDir, "midscene-run", "report", "x.html");
  fs.mkdirSync(path.dirname(f), { recursive: true });
  fs.writeFileSync(f, "html");
  const u = new (ArtifactUploader as any)("bkt", "reports/rid/", runDir);
  withMockClient(u, { failKeys: ["reports/rid/midscene-run/report/x.html"] });
  await assert.rejects(() => u.toReportRef(f), /s3 fail/);
  assert.ok(fs.existsSync(f));  // 失败不删
});

// ---- 剩余 flush 失败 → 吞掉，但整目录不删（护栏：产物不丢）----
test("flush failure swallowed but dir kept", async () => {
  const root = tmproot();
  const runDir = path.join(root, "reports", "rid");
  const msDir = path.join(runDir, "midscene-run");
  const rep = path.join(msDir, "report");
  fs.mkdirSync(rep, { recursive: true });
  const html = path.join(rep, "x.html"); fs.writeFileSync(html, "html");
  const logDir = path.join(msDir, "log"); fs.mkdirSync(logDir);
  const log = path.join(logDir, "ai.log"); fs.writeFileSync(log, "log");
  const u = new (ArtifactUploader as any)("bkt", "reports/rid/", runDir);
  withMockClient(u, { failKeys: ["reports/rid/midscene-run/log/ai.log"] });  // 剩余 log 上传失败
  await u.toReportRef(html);            // 实时传 html（成功）
  await u.flushAndCleanup(msDir);        // 传 log 失败 → 吞掉、不抛
  assert.ok(fs.existsSync(msDir));       // 整目录保留（产物不丢）
  assert.ok(fs.existsSync(html) && fs.existsSync(log));
});

// ---- fromEnv：读注入 env，runDir = MIDSCENE_RUN_DIR 父级 ----
test("fromEnv enabled when bucket set, runDir = MIDSCENE_RUN_DIR parent", () => {
  const root = tmproot();
  const runDir = path.join(root, "reports", "rid", "midscene-run");
  process.env.ARTIFACT_S3_BUCKET = "bkt";
  process.env.ARTIFACT_S3_PREFIX = "reports/rid/";
  process.env.MIDSCENE_RUN_DIR = runDir;
  const u = ArtifactUploader.fromEnv();
  assert.equal(u.enabled, true);
  assert.equal((u as any).bucket, "bkt");
  assert.equal((u as any).runDir, path.dirname(runDir));  // run 树根 = MIDSCENE_RUN_DIR 父级
  delete process.env.ARTIFACT_S3_BUCKET;
  delete process.env.ARTIFACT_S3_PREFIX;
  delete process.env.MIDSCENE_RUN_DIR;
});


// ---- snapshotReport（act 边界抢传，ADR 0029 为 Fargate 预演）：overwrite 同 key、不记 uploaded、不删目录 ----
test("snapshotReport overwrites same key, does not touch uploaded ledger", async () => {
  const root = tmproot();
  const runDir = path.join(root, "reports", "rid");
  const rep = path.join(runDir, "midscene-run", "report");
  fs.mkdirSync(rep, { recursive: true });
  const f = path.join(rep, "report.html");
  fs.writeFileSync(f, "html-v1");
  const u = new (ArtifactUploader as any)("bkt", "reports/rid/", runDir);
  const keys = withMockClient(u);
  const K = "reports/rid/midscene-run/report/report.html";
  // 连抢 3 次（模拟每 step_done 抢传增量增长的 report）→ 同 key overwrite 3 次
  await u.snapshotReport(f);
  await u.snapshotReport(f);
  await u.snapshotReport(f);
  assert.deepEqual(keys, [K, K, K]);  // 绕幂等守卫、同 key overwrite（非短路）
  // 不记 uploaded → 随后 toReportRef 仍真传权威终版（第 4 次同 key）、且返回 s3:// ref
  const ref = await u.toReportRef(f);
  assert.equal(ref, `s3://bkt/${K}`);
  assert.equal(keys.length, 4, "snapshot 不记 uploaded → toReportRef 不被短路、仍传一次");
});

test("snapshotReport keeps dir (never rmSync)", async () => {
  const root = tmproot();
  const runDir = path.join(root, "reports", "rid");
  const msDir = path.join(runDir, "midscene-run");
  const rep = path.join(msDir, "report");
  fs.mkdirSync(rep, { recursive: true });
  const f = path.join(rep, "report.html"); fs.writeFileSync(f, "html");
  const u = new (ArtifactUploader as any)("bkt", "reports/rid/", runDir);
  withMockClient(u);
  await u.snapshotReport(f);
  assert.ok(fs.existsSync(msDir));  // 抢传绝不删目录（不误删在写的 report）
  assert.ok(fs.existsSync(f));
});

test("snapshotReport no-op when not enabled", async () => {
  const root = tmproot();
  const f = path.join(root, "report.html"); fs.writeFileSync(f, "html");
  delete process.env.ARTIFACT_S3_BUCKET;
  const u = ArtifactUploader.fromEnv();  // 无 bucket → no-op
  assert.equal(u.enabled, false);
  const keys = withMockClient(u);
  await u.snapshotReport(f);  // 不上传、不抛
  assert.deepEqual(keys, []);
});

test("snapshotReport raises on upload failure (worker swallows)", async () => {
  const root = tmproot();
  const runDir = path.join(root, "reports", "rid");
  const rep = path.join(runDir, "midscene-run", "report");
  fs.mkdirSync(rep, { recursive: true });
  const f = path.join(rep, "report.html"); fs.writeFileSync(f, "html");
  const u = new (ArtifactUploader as any)("bkt", "reports/rid/", runDir);
  withMockClient(u, { failKeys: ["reports/rid/midscene-run/report/report.html"] });
  await assert.rejects(() => u.snapshotReport(f), /s3 fail/);  // 原样抛（lib 纯净、交 worker 吞）
});


// ---- snapshotLogs（scenario 边界抢传 log，ADR 0029「第四级」）：多文件 + mtime 去重 + 总预算 + 逐文件吞失败 ----
// 建一个 log 目录、塞若干 .log 文件，给定 mtime。返回 { logDir, mk(name, content, mtimeSec) }。
function mkLogDir(): { logDir: string; runDir: string; mk: (name: string, content: string, mtimeSec: number) => string } {
  const root = tmproot();
  const runDir = path.join(root, "reports", "rid");
  const logDir = path.join(runDir, "midscene-run", "log");
  fs.mkdirSync(logDir, { recursive: true });
  const mk = (name: string, content: string, mtimeSec: number) => {
    const p = path.join(logDir, name);
    fs.writeFileSync(p, content);
    fs.utimesSync(p, mtimeSec, mtimeSec);
    return p;
  };
  return { logDir, runDir, mk };
}

test("snapshotLogs uploads all log files, keys mirror tree, overwrites same key (bypass uploaded)", async () => {
  const { logDir, runDir, mk } = mkLogDir();
  mk("ai-call.log", "a", 1000);
  mk("planning.log", "b", 1000);
  const u = new (ArtifactUploader as any)("bkt", "reports/rid/", runDir);
  const keys = withMockClient(u);
  const seen = new Map<string, number>();
  await u.snapshotLogs(logDir, seen, 5000);
  assert.deepEqual(
    keys.sort(),
    ["reports/rid/midscene-run/log/ai-call.log", "reports/rid/midscene-run/log/planning.log"],
  );
  // 不记 uploaded → scope 末 flush 仍会传（这里验 uploaded 账本没被污染）
  assert.equal((u as any).uploaded.size, 0, "snapshotLogs 不记 uploaded");
  // 目录仍在（绝不 rmSync）
  assert.ok(fs.existsSync(logDir));
});

test("snapshotLogs mtime 去重：未变文件不重传，变了才重传", async () => {
  const { logDir, runDir, mk } = mkLogDir();
  const p = mk("ai-call.log", "v1", 1000);
  const u = new (ArtifactUploader as any)("bkt", "reports/rid/", runDir);
  const keys = withMockClient(u);
  const seen = new Map<string, number>();
  await u.snapshotLogs(logDir, seen, 5000);       // 首次传
  await u.snapshotLogs(logDir, seen, 5000);       // mtime 未变 → 跳过
  assert.equal(keys.length, 1, "第二次 mtime 未变 → 去重跳过");
  // log 增长（append）+ mtime 变 → 重传
  fs.writeFileSync(p, "v1-and-more");
  fs.utimesSync(p, 2000, 2000);
  await u.snapshotLogs(logDir, seen, 5000);
  assert.equal(keys.length, 2, "mtime 变 → 重传一次（overwrite 同 key）");
  assert.ok(keys.every((k) => k === "reports/rid/midscene-run/log/ai-call.log"));
});

test("snapshotLogs 逐文件吞失败：某 log 传失败不饿死其余、失败的不记 seen（下轮重试）", async () => {
  const { logDir, runDir, mk } = mkLogDir();
  mk("good.log", "g", 1000);
  mk("bad.log", "b", 1000);
  const u = new (ArtifactUploader as any)("bkt", "reports/rid/", runDir);
  const keys = withMockClient(u, { failKeys: ["reports/rid/midscene-run/log/bad.log"] });
  const seen = new Map<string, number>();
  await u.snapshotLogs(logDir, seen, 5000);  // bad 抛、good 照传（不整体抛）
  assert.ok(keys.includes("reports/rid/midscene-run/log/good.log"), "good 照传");
  assert.ok(keys.includes("reports/rid/midscene-run/log/bad.log"), "bad 尝试过");
  // good 记 seen、bad 没记 → 下轮 good 跳过、bad 重试
  const before = keys.length;
  await u.snapshotLogs(logDir, seen, 5000);
  const retried = keys.slice(before);
  assert.deepEqual(retried, ["reports/rid/midscene-run/log/bad.log"], "下轮只重试失败的 bad，good 已 seen 跳过");
});

test("snapshotLogs 总墙钟预算：budgetMs=0 → 一个都不传", async () => {
  const { logDir, runDir, mk } = mkLogDir();
  mk("a.log", "a", 1000);
  mk("b.log", "b", 1000);
  const u = new (ArtifactUploader as any)("bkt", "reports/rid/", runDir);
  const keys = withMockClient(u);
  const seen = new Map<string, number>();
  await u.snapshotLogs(logDir, seen, 0);  // 预算 0 → 循环首行即超 deadline、break
  assert.equal(keys.length, 0, "budgetMs=0 → 放弃全部（best-effort）");
});

test("snapshotLogs no-op when not enabled / log 目录不存在", async () => {
  // no-op：无 bucket
  delete process.env.ARTIFACT_S3_BUCKET;
  const u1 = ArtifactUploader.fromEnv();
  const keys1 = withMockClient(u1);
  await u1.snapshotLogs("/nonexistent/log", new Map(), 5000);
  assert.deepEqual(keys1, []);
  // enabled 但 log 目录不存在 → 直接返回、不抛
  const root = tmproot();
  const runDir = path.join(root, "reports", "rid");
  const u2 = new (ArtifactUploader as any)("bkt", "reports/rid/", runDir);
  const keys2 = withMockClient(u2);
  await u2.snapshotLogs(path.join(runDir, "midscene-run", "log"), new Map(), 5000);
  assert.deepEqual(keys2, [], "log 目录不存在 → no-op");
});

// ---- 上传超时 plumbing（ADR 0029「上传必须套超时」）：uploadOne 给 send 传 AbortSignal，防漏传/写错照绿 ----
test("uploadOne passes an AbortSignal to send (退出时间有界 plumbing)", async () => {
  const root = tmproot();
  const runDir = path.join(root, "reports", "rid");
  const rep = path.join(runDir, "midscene-run", "report");
  fs.mkdirSync(rep, { recursive: true });
  const f = path.join(rep, "report.html"); fs.writeFileSync(f, "html");
  const u = new (ArtifactUploader as any)("bkt", "reports/rid/", runDir);
  withMockClient(u);
  await u.snapshotReport(f);  // 任一走 uploadOne 的路径
  // send 第二参必须含 abortSignal（AbortSignal.timeout 造的），且发起时未 aborted——锁住超时 plumbing 不被误删。
  const opts = (u as any).client.sendOpts[0];
  assert.ok(opts && opts.abortSignal, "send 第二参须含 abortSignal（uploadOne 的超时封顶）");
  assert.equal(opts.abortSignal.aborted, false, "发起上传时 signal 未 aborted");
  assert.equal(typeof opts.abortSignal.addEventListener, "function", "是真 AbortSignal");
});

// ---- budget 中间态（退化网络护栏实际工作点）：传了 k 个后墙钟超预算 → break，只传部分、未传的不进 seen ----
test("snapshotLogs 预算中途耗尽：传部分后 break，未传的仍可下轮重试", async () => {
  const { logDir, runDir, mk } = mkLogDir();
  for (const n of ["a.log", "b.log", "c.log"]) mk(n, n, 1000);
  const u = new (ArtifactUploader as any)("bkt", "reports/rid/", runDir);
  // mock send：每次消耗预算——第 1 个成功后就把墙钟推过 deadline（用可控延迟模拟，不靠真时钟）。
  // 这里用「传满 1 个就让后续 Date.now 越界」不易注入，改测更本质的因果：budgetMs 极小 + 每次 send 真耗时。
  let sent = 0;
  (u as any).client = {
    send: async () => {
      sent++;
      // 阻塞一小段真实时间，使循环顶 Date.now() 在若干次后越过 deadline（deadline 检查在循环顶、uploadOne 前）。
      await new Promise((r) => setTimeout(r, 40));
      return {};
    },
  };
  const seen = new Map<string, number>();
  await u.snapshotLogs(logDir, seen, 50);  // 预算 50ms、每次 send 40ms → 传 1~2 个后循环顶越界 break
  assert.ok(sent >= 1 && sent < 3, `预算中途耗尽应传部分（1~2 个）、非全部，实传 ${sent}`);
  assert.equal(seen.size, sent, "只有真传成功的记 seen，未传的不进 seen（下轮/scope 末 flush 可重试）");
});
