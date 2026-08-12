// JobSource 单测（Midscene，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 到 EOF、切首行 JSON。
// 此前内联在 run-scope main（JSON.parse((await readStdin()).split("\n")[0])），无测试覆盖。跑：node --import tsx --test。
import { test } from "node:test";
import assert from "node:assert";
import { Readable } from "node:stream";
import { JobSource } from "../lib/job-source.mjs";

// 用一个 Readable 假冒 process.stdin（for await 可迭代），跑完恢复。
async function withStdin<T>(content: string, fn: () => Promise<T>): Promise<T> {
  const saved = Object.getOwnPropertyDescriptor(process, "stdin");
  Object.defineProperty(process, "stdin", { value: Readable.from([Buffer.from(content, "utf-8")]), configurable: true });
  try {
    return await fn();
  } finally {
    if (saved) Object.defineProperty(process, "stdin", saved);
  }
}

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
