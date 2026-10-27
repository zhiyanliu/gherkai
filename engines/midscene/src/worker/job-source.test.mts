// JobSource 单测（Midscene，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 到 EOF、切首行 JSON。
// 此前内联在 run-scope main（JSON.parse((await readStdin()).split("\n")[0])），无测试覆盖。运行：node --import tsx --test。
import { test } from "node:test";
import assert from "node:assert";
import { Readable } from "node:stream";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { JOB_KEYS, JOB_SCHEMA_VERSION, JobSource } from "../lib/job-source.mjs";

// 用一个 Readable 假冒 process.stdin（for await 可迭代），运行结束后恢复。
async function withStdin<T>(content: string, fn: () => Promise<T>): Promise<T> {
  const saved = Object.getOwnPropertyDescriptor(process, "stdin");
  Object.defineProperty(process, "stdin", { value: Readable.from([Buffer.from(content, "utf-8")]), configurable: true });
  try {
    return await fn();
  } finally {
    if (saved) Object.defineProperty(process, "stdin", saved);
  }
}

test("Python 到 TS 的往返（ADR 0048 决策 3）：golden 三种形态的键集合都在 TS 的字段清单之内、且清单里的每个键至少在某份 golden 出现", () => {
  // golden 只有一份（engines/fixtures/job-lines.json，由 core 的 job_to_json 产出、core/tests/test_wire.py 核 Python 侧逐字相等）。
  // TS 侧用**显式写出**的 JOB_KEYS 对照：JobSource 只是 JSON.parse，「解析再序列化」证不了字段契约；删掉清单里的一个字段，这里就红。
  const file = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../fixtures/job-lines.json");
  const jobs = JSON.parse(fs.readFileSync(file, "utf-8")).jobs as Record<string, any>;
  const seen = { top: new Set<string>(), target: new Set<string>(), app: new Set<string>(), deviceRequest: new Set<string>() };
  for (const job of Object.values(jobs)) {
    for (const k of Object.keys(job)) { assert.ok((JOB_KEYS.top as readonly string[]).includes(k), `golden 顶层键 ${k} 不在 TS 清单里`); seen.top.add(k); }
    if (job.target) for (const k of Object.keys(job.target)) { assert.ok((JOB_KEYS.target as readonly string[]).includes(k), `target.${k}`); seen.target.add(k); }
    if (job.target?.app) for (const k of Object.keys(job.target.app)) { assert.ok((JOB_KEYS.app as readonly string[]).includes(k), `app.${k}`); seen.app.add(k); }
    if (job.deviceRequest) for (const k of Object.keys(job.deviceRequest)) { assert.ok((JOB_KEYS.deviceRequest as readonly string[]).includes(k), `deviceRequest.${k}`); seen.deviceRequest.add(k); }
  }
  for (const [section, keys] of Object.entries(JOB_KEYS)) {
    for (const k of keys) assert.ok(seen[section as keyof typeof seen].has(k), `TS 清单里的 ${section}.${k} 没在任何一份 golden 出现（Python 侧没跟上？）`);
  }
  // 键集固定（ADR 0024）：桌面 job 与设备 job 同一组键，无值为 null；每份 golden 的 schemaVersion 都是本 worker 认的值
  for (const job of Object.values(jobs)) {
    assert.deepEqual(Object.keys(job).sort(), [...JOB_KEYS.top].sort());
    assert.equal(job.schemaVersion, JOB_SCHEMA_VERSION);
  }
  assert.equal(jobs["desktop"].timeoutS, null);
  assert.equal(jobs["desktop"].deviceRequest, null);
  assert.deepEqual(jobs["desktop"].target, { device: "desktop", uiKind: "web" });
});

test("read parses first-line JSON from stdin", async () => {
  const line = JSON.stringify({ scope: { id: "s:0", name: "S" }, engine: "midscene", scenarios: [], assertionVotes: 3 }) + "\n";
  const job = await withStdin(line, () => JobSource.fromEnv().read());
  assert.equal(job.scope.id, "s:0");
  assert.equal(job.assertionVotes, 3);
});

test("read reads to EOF then takes only first line (尾随行不干扰)", async () => {
  const stdin = JSON.stringify({ scope: { id: "s:0", name: "S" }, engine: "midscene", scenarios: [] }) + "\n后续噪声行不该被解析\n";
  const job = await withStdin(stdin, () => JobSource.fromEnv().read());
  assert.equal(job.scope.id, "s:0");  // 只解析首行
});

test("S3 态：JOB_S3_URI 注入 → read() = GetObject + 解析首行 JSON（注入 fake client，不连真 AWS）", async () => {
  // S3 态（Fargate 化，ADR 0024）：mock S3 client send（对称 artifact-upload.test 惯例）；验 s3:// URI 解析 + 首行 JSON。
  const saved = process.env.JOB_S3_URI;
  process.env.JOB_S3_URI = "s3://bkt/run-1/jobs/browse.json";
  const captured: any = {};
  const fakeClient = {
    send: async (cmd: any) => {
      captured.Bucket = cmd.input.Bucket;
      captured.Key = cmd.input.Key;
      const line = JSON.stringify({ scope: { id: "browse", name: "B" }, engine: "midscene", scenarios: [], assertionVotes: 3 }) + "\n";
      return { Body: { transformToString: async (_enc: string) => line } };
    },
  };
  try {
    const job = await JobSource.fromEnv().read(fakeClient);
    assert.equal(captured.Bucket, "bkt");
    assert.equal(captured.Key, "run-1/jobs/browse.json");  // s3:// URI 解析正确
    assert.equal(job.scope.id, "browse");
    assert.equal(job.assertionVotes, 3);
  } finally {
    if (saved === undefined) delete process.env.JOB_S3_URI; else process.env.JOB_S3_URI = saved;
  }
});

test("JOB_S3_URI 非 s3:// → throw（配置错、fail-loud）", async () => {
  const saved = process.env.JOB_S3_URI;
  process.env.JOB_S3_URI = "http://not-s3/job.json";
  try {
    await assert.rejects(() => JobSource.fromEnv().read({ send: async () => ({}) }), /s3:\/\//);
  } finally {
    if (saved === undefined) delete process.env.JOB_S3_URI; else process.env.JOB_S3_URI = saved;
  }
});

test("空串 JOB_S3_URI 当作未注入（|| undefined）→ 走 stdin、不误抛", async () => {
  const saved = process.env.JOB_S3_URI;
  process.env.JOB_S3_URI = "";
  try {
    const line = JSON.stringify({ scope: { id: "s:0", name: "S" }, engine: "midscene", scenarios: [] }) + "\n";
    const job = await withStdin(line, () => JobSource.fromEnv().read());
    assert.equal(job.scope.id, "s:0");
  } finally {
    if (saved === undefined) delete process.env.JOB_S3_URI; else process.env.JOB_S3_URI = saved;
  }
});

test("s3://bucket（无 key 段）→ fail-loud（对称 Nova：放行会静默算错 bucket/key）", async () => {
  const saved = process.env.JOB_S3_URI;
  try {
    process.env.JOB_S3_URI = "s3://only-bucket";
    await assert.rejects(() => JobSource.fromEnv().read(), /缺 key 段/);
  } finally {
    if (saved === undefined) delete process.env.JOB_S3_URI; else process.env.JOB_S3_URI = saved;
  }
});
