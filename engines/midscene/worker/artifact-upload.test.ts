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

// 塞 mock S3 client（记录 send 的 key；failKeys 里的 key 抛错），绕过真 aws-sdk。
function withMockClient(u: ArtifactUploader, opts: { failKeys?: string[] } = {}) {
  const keys: string[] = [];
  (u as any).client = {
    send: async (cmd: any) => {
      keys.push(cmd.input.Key);
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
