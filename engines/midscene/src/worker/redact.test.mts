// 凭据脱敏三条规则的单测（Midscene worker 的那份实现，ADR 0035 决策 5；0051 决策 11）。运行：npm test。
// 用例表只有一份：engines/fixtures/redaction-cases.json，与 core、Nova 三份实现各自读它、逐条断言。本实现只收字符串，故没有 None 那一条。
// 文件后半是出口级用例：规则由用例表守，出口级用例守的是 worker 自己写 stderr 的几处出口与设备目标的两处写盘出口（原始控件树、device-session.json）都接上了规则。
import { test } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { MASK, SECRET_MASK, redactSecrets } from "../lib/redact.mjs";

const FIXTURE = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../fixtures/redaction-cases.json");
const CASES = (JSON.parse(fs.readFileSync(FIXTURE, "utf8")) as { cases: Array<[string, string]> }).cases;

test("redactSecrets：跨语言用例表逐条通过", () => {
  assert.ok(CASES.length > 10);
  for (const [input, expected] of CASES) {
    assert.equal(redactSecrets(input), expected, `输入 ${JSON.stringify(input)}`);
  }
});

test("MASK 是 ***@、SECRET_MASK 是 ***", () => {
  assert.equal(MASK, "***@");
  assert.equal(SECRET_MASK, "***");
});

test("redactSecrets：同一个正则对象连续调用不残留 lastIndex（全局标志的常见陷阱）", () => {
  // 全局正则若误用 test / exec，会在调用之间记住位置、下一次漏掉匹配；replace 不受影响，这里锁住它。
  for (let i = 0; i < 3; i++) {
    assert.equal(redactSecrets("https://u1:p1@h.example/?gherkai_tunnel_token=t"), "https://***@h.example/?gherkai_tunnel_token=***");
  }
});

test("redactSecrets：已序列化的整行仍能解析，字段值里的凭据被换掉", () => {
  const line = JSON.stringify({ type: "step_done", message: "页面停在 https://u1:p1@h.example/x 未跳转",
    url: "https://h/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=abc", ep: "https://x.amazonaws.com/remote-endpoint/tok123/wd/hub" });
  const out = redactSecrets(line);
  assert.ok(!out.includes("u1:p1@") && !out.includes("=abc") && !out.includes("tok123"));
  assert.deepEqual(JSON.parse(out), { type: "step_done", message: "页面停在 https://***@h.example/x 未跳转",
    url: "https://h/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=***", ep: "https://x.amazonaws.com/remote-endpoint/***/wd/hub" });
});

test("redactSecrets：匹配停在引号处，不跨字段吞掉内容", () => {
  // 前一个字段的地址不带 @、后一个字段里有 @
  const line = '{"url":"https://h.example","who":"x@y"}';
  assert.equal(redactSecrets(line), line);
});


// ---- 出口级用例（ADR 0051 决策 11、0035 决策 5）----
// worker 自己写 stderr 的五处出口：run-scope 的 log()、bin 的 worker fatal 行、ArtifactUploader 的缺省 logFn、loadUserSteps 的
// 缺省 logFn、evidence 的缺省 logFn（运行期用例在 evidence.test.mts）；出口集合恰为这五处由 stderr-outlets.test.mts 的静态差集守。
// 设备目标另有两处写盘出口：原始控件树（page source）与 device-session.json。样本取用例表里输入与期望不同的那些条目
// （即带凭据的输入）：出口写出的文字要含期望的脱敏结果、不含原始输入。事件行与 evidence 写盘两处出口由 event-sink 与 evidence
// 各自的测试守。
const SECRET_CASES = CASES.filter(([input, expected]) => input !== expected);

async function captureStderr(fn: () => unknown): Promise<string> {
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

function assertRedactedOutput(out: string, input: string, expected: string): void {
  assert.ok(out.includes(expected), `应写出脱敏后的 ${JSON.stringify(expected)}，实际 ${JSON.stringify(out)}`);
  assert.ok(!out.includes(input), `不应写出原始输入 ${JSON.stringify(input)}，实际 ${JSON.stringify(out)}`);
}

test("出口：用例表里带凭据的样本足够覆盖三条规则", () => {
  // 防止样本被筛空后出口用例全部空转
  assert.ok(SECRET_CASES.some(([i]) => i.includes("@")), "userinfo 样本");
  assert.ok(SECRET_CASES.some(([i]) => /X-Amz-Signature=/i.test(i)), "签名参数样本");
  assert.ok(SECRET_CASES.some(([i]) => i.includes("/remote-endpoint/")), "设备端点样本");
});

test("出口：run-scope 的 log() 写 stderr 前经 redactSecrets（经 interruptSnapshot 的缺省诊断出口）", async () => {
  const { interruptSnapshot } = await import("./run-scope.mjs");
  for (const [input, expected] of SECRET_CASES) {
    const uploader = { snapshotReport: async (_p: string) => { throw new Error(input); } };
    const out = await captureStderr(() => interruptSnapshot(uploader, "report.html"));
    assert.ok(out.startsWith("worker: "), `该经 log() 写出一行：${JSON.stringify(out)}`);
    assertRedactedOutput(out, input, expected);
  }
});

test("出口：ArtifactUploader 的缺省 logFn 写 stderr 前经 redactSecrets", async () => {
  const { ArtifactUploader } = await import("../lib/artifact-upload.mjs");
  const saved = process.env.ARTIFACT_S3_BUCKET;
  delete process.env.ARTIFACT_S3_BUCKET;  // 只要一个上传器实例取它的缺省 logFn；不注入落点即不上传
  try {
    const uploader = ArtifactUploader.fromEnv();
    for (const [input, expected] of SECRET_CASES) {
      const out = await captureStderr(() => uploader.logFn(`worker: 证据截图上传失败：${input}`));
      assertRedactedOutput(out, input, expected);
    }
  } finally {
    if (saved !== undefined) process.env.ARTIFACT_S3_BUCKET = saved;
  }
});

test("出口：loadUserSteps 的缺省 logFn 写 stderr 前经 redactSecrets（目录路径里带设备端点令牌与签名参数）", async () => {
  const { loadUserSteps } = await import("./user-steps.mjs");
  // 目录路径取用例表里设备端点样本的路径部分，末段再接一个带隧道令牌参数的样本的末段（文件系统允许 ? 与 &）
  const [endpointSample] = SECRET_CASES.find(([i]) => i.includes("/remote-endpoint/") && i.startsWith("https://"))!;
  const [querySample] = SECRET_CASES.find(([i]) => /^https:\/\/[^ ]*\?[^ ]*&gherkai_tunnel_token=/.test(i))!;
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "gherkai-redact-steps-"));
  const stepsDir = path.join(root, new URL(endpointSample).pathname, querySample.slice(querySample.lastIndexOf("/") + 1));
  fs.mkdirSync(stepsDir, { recursive: true });
  fs.writeFileSync(path.join(stepsDir, "a.mts"), "");
  let registered = 0;
  try {
    const out = await captureStderr(() => loadUserSteps({ stepsDir, importer: async () => { registered++; }, size: () => registered }));
    assert.ok(out.includes("worker: "), `该写出加载行：${JSON.stringify(out)}`);
    assertRedactedOutput(out, stepsDir, redactSecrets(stepsDir));
    assert.ok(out.includes(`/remote-endpoint/${SECRET_MASK}`) && out.includes(`gherkai_tunnel_token=${SECRET_MASK}`), out);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("出口：bin 的 worker fatal 行经 redactSecrets（真入口子进程，启动期失败的异常文本带凭据）", async () => {
  // 启动期失败取 GHERKAI_STEPS_DIR 指向不存在的目录：异常文本原样带着这个值。样本按行拼接，各行互不影响脱敏结果（前提先核）。
  const raw = SECRET_CASES.map(([i]) => i).join("\n");
  const want = SECRET_CASES.map(([, e]) => e).join("\n");
  assert.equal(redactSecrets(raw), want);
  const bin = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "bin.mts");
  const proc = spawn(process.execPath, ["--import", import.meta.resolve("tsx"), bin], {
    stdio: ["ignore", "pipe", "pipe"], env: { ...process.env, GHERKAI_STEPS_DIR: raw },
  });
  const err: Buffer[] = [];
  proc.stderr.on("data", (c) => err.push(c));
  const code: number = await new Promise((r) => proc.on("close", r));
  const out = Buffer.concat(err).toString("utf-8");
  assert.equal(code, 1, out);
  assert.ok(out.includes("worker fatal: "), out);
  assert.ok(out.includes(want), `fatal 行该含脱敏后的样本：${JSON.stringify(out)}`);
  for (const [input] of SECRET_CASES) assert.ok(!out.includes(input), `不应写出原始输入 ${JSON.stringify(input)}`);
});

test("出口：原始控件树写盘经 redactSecrets，写出的内容即脱敏结果", async () => {
  const { writePageSourceFile } = await import("../device/surface.mjs");
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "gherkai-redact-page-source-"));
  try {
    SECRET_CASES.forEach(([input, expected], i) => {
      const file = path.join(dir, `step-${i}.xml`);
      assert.deepEqual(writePageSourceFile(file, input), { truncated: false });
      assert.equal(fs.readFileSync(file, "utf-8"), expected, `输入 ${JSON.stringify(input)}`);
    });
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test("出口：原始控件树先脱敏再按 1 MiB 截断，截断点上的凭据不留片段，多字节字符不被切断", async () => {
  const { writePageSourceFile } = await import("../device/surface.mjs");
  const { PAGE_SOURCE_MAX_BYTES } = await import("../device/limits.mjs");
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "gherkai-redact-page-source-"));
  try {
    // userinfo 跨过截断点：先截断会留下没有 @ 的「https://user:supersec」，脱敏规则认不出，口令片段就进了文件
    const secret = "https://user:supersecretpassword@h.example/login";
    const head = "<a>" + "x".repeat(PAGE_SOURCE_MAX_BYTES - 3 - 20);
    const boundary = path.join(dir, "boundary.xml");
    assert.deepEqual(writePageSourceFile(boundary, `${head}${secret}"/></a>`), { truncated: true });
    const written = fs.readFileSync(boundary);
    assert.ok(written.length <= PAGE_SOURCE_MAX_BYTES, String(written.length));
    const text = written.toString("utf-8");
    assert.ok(!text.includes("user:") && !text.includes("supersec"), text.slice(-40));
    assert.ok(text.endsWith(redactSecrets(secret).slice(0, 20)), text.slice(-40));

    // 截断点落在三字节字符中间：退到字符起点，不写出半个字符
    const wide = path.join(dir, "wide.xml");
    assert.deepEqual(writePageSourceFile(wide, "<a>" + "控".repeat(PAGE_SOURCE_MAX_BYTES / 3 + 10) + "</a>"), { truncated: true });
    const bytes = fs.readFileSync(wide);
    assert.ok(bytes.length <= PAGE_SOURCE_MAX_BYTES && bytes.length > PAGE_SOURCE_MAX_BYTES - 3, String(bytes.length));
    assert.ok(!bytes.toString("utf-8").includes("\ufffd"));
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test("出口：device-session.json 整份经 redactSecrets（换台原因与执行前失败消息里带凭据）", async () => {
  const { writeDeviceSessionFile } = await import("../device/device-session.mjs");
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "gherkai-redact-device-session-"));
  try {
    for (const [input, expected] of SECRET_CASES) {
      const file = writeDeviceSessionFile(dir, {
        target: { device: "android", ui_kind: "web", app_id: null },
        session: null,
        replaced_sessions: [{ arn: "arn:aws:devicefarm:us-west-2:123456789012:session:p/r/1", name: "gherkai:r:s:1:x", reason: input }],
        automation_name: null,
        probe: null,
        timings: {
          acquire_started_at: null, session_created_at: null, session_running_at: null, appium_connected_at: null,
          probe_done_at: null, ready_at: null, warmup_done_at: null, released_at: null,
        },
        acquire_failure: { error_type: "precheck_failed", message: input },
        release_failed: false,
      });
      const text = fs.readFileSync(file, "utf-8");
      const doc = JSON.parse(text);
      assert.equal(doc.acquire_failure.message, expected, `输入 ${JSON.stringify(input)}`);
      assert.equal(doc.replaced_sessions[0].reason, expected, `输入 ${JSON.stringify(input)}`);
    }
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
