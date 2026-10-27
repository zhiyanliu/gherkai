// 建会话前的自检（ADR 0049 决策 7；0048 决策 3、4）：对称 Nova 的 test_precheck.py。运行：node --import tsx --test。
import { test } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { precheckJob, precheckSchema, precheckTarget, targetLabel } from "../lib/precheck.mjs";
import { JOB_SCHEMA_VERSION } from "../lib/job-source.mjs";
import { WORKER_TARGETS } from "./run-scope.mjs";

const DEVICE_TARGETS = [{ device: "desktop", ui_kinds: ["web"] }, { device: "android", ui_kinds: ["web", "app"], max_session_s: 8000 }];

test("桌面 job 对真实 WORKER_TARGETS 通过；缺 target 不再当桌面、按版本不一致拒绝", () => {
  assert.equal(precheckTarget({ target: { device: "desktop", uiKind: "web" }, timeoutS: 300 }, WORKER_TARGETS), null);
  assert.equal(precheckTarget({ target: { device: "desktop", uiKind: "web" }, timeoutS: null }, WORKER_TARGETS), null);  // 不超时写 null
  const msg = precheckTarget({}, WORKER_TARGETS);
  assert.ok(msg !== null && msg.includes("没有带测试目标") && msg.includes("同一版本"));
});

test("job 行的结构版本先于目标核对（ADR 0024）：不等于本 worker 认的（含缺键）即拒绝；本 worker 认的值与跨语言 golden 一致", () => {
  assert.equal(precheckSchema({ schemaVersion: JOB_SCHEMA_VERSION }), null);
  assert.ok(precheckSchema({})!.includes("缺失"));
  assert.ok(precheckSchema({ schemaVersion: JOB_SCHEMA_VERSION + 1 })!.includes(`格式版本是 ${JOB_SCHEMA_VERSION + 1}`));
  assert.ok(precheckJob({ schemaVersion: JOB_SCHEMA_VERSION + 1, target: { device: "ios", uiKind: "app" } }, WORKER_TARGETS)!.includes("格式版本"));
  assert.equal(precheckJob({ schemaVersion: JOB_SCHEMA_VERSION, target: { device: "desktop", uiKind: "web" }, timeoutS: null }, WORKER_TARGETS), null);
  const file = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../fixtures/job-lines.json");
  const jobs = JSON.parse(fs.readFileSync(file, "utf-8")).jobs as Record<string, any>;
  for (const job of Object.values(jobs)) assert.equal(job.schemaVersion, JOB_SCHEMA_VERSION);
});

test("设备 job 被当前只声明桌面网页的 worker 拒绝，消息是产品语言", () => {
  const msg = precheckTarget({ target: { device: "ios", uiKind: "app" }, timeoutS: 1500 }, WORKER_TARGETS);
  assert.equal(msg, "这个 worker 不支持在 iOS 应用上执行测试（它支持：桌面网页）。请改用支持该目标的引擎，或使用与命令行工具同版本的 worker 镜像。");
  assert.ok(!msg!.includes("ADR") && !msg!.includes("precheck"));
});

test("墙钟预算超过会话上限被拒绝；等于上限、没带预算、桌面无上限都通过", () => {
  const over = precheckTarget({ target: { device: "android", uiKind: "web" }, timeoutS: 9000 }, DEVICE_TARGETS);
  assert.ok(over !== null && over.includes("墙钟预算 9000 秒超过了 Android 网页的会话上限 8000 秒") && over.includes("--default-job-timeout"));
  assert.equal(precheckTarget({ target: { device: "android", uiKind: "web" }, timeoutS: 8000 }, DEVICE_TARGETS), null);
  assert.equal(precheckTarget({ target: { device: "android", uiKind: "web" } }, DEVICE_TARGETS), null);
  assert.equal(precheckTarget({ target: { device: "desktop", uiKind: "web" }, timeoutS: 1e9 }, DEVICE_TARGETS), null);
});

test("设备受支持但界面类型不受支持也被拒绝（与 Nova 侧对称）", () => {
  const msg = precheckTarget({ target: { device: "android", uiKind: "app" } }, [{ device: "android", ui_kinds: ["web"] }]);
  assert.ok(msg !== null && msg.includes("不支持在 Android 应用上"));
});

test("主入口在建会话之前自检：真子进程喂 android/web 的 job，唯一事件是 scope_done{error, precheck_failed}，退出码 0", async () => {
  const { spawn } = await import("node:child_process");
  const path = await import("node:path");
  const env: Record<string, string> = {};
  for (const k of ["PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "NODE_OPTIONS"]) if (process.env[k] !== undefined) env[k] = process.env[k]!;
  env["AWS_EC2_METADATA_DISABLED"] = "true";
  const job = { schemaVersion: 1, scope: { id: "dev", name: "dev" }, engine: "midscene", assertionVotes: 1, timeoutS: 1500,
    target: { device: "android", uiKind: "web" }, deviceRequest: null,
    scenarios: [{ id: "d.feature:3", name: "s", steps: [{ index: 0, keyword: "Given", text: "https://x/" }] }] };
  const result = await new Promise<{ code: number | null; out: string; err: string }>((resolve) => {
    const proc = spawn(process.execPath, ["--import", import.meta.resolve("tsx"), path.join(import.meta.dirname, "..", "bin.mts")],
      { env, stdio: ["pipe", "pipe", "pipe"] });
    let out = ""; let err = "";
    proc.stdout.on("data", (d) => { out += d.toString(); });
    proc.stderr.on("data", (d) => { err += d.toString(); });
    proc.on("close", (code) => resolve({ code, out, err }));
    proc.stdin.end(JSON.stringify(job) + "\n");
  });
  assert.equal(result.code, 0, result.err.slice(-800));
  const events = result.out.split("\n").filter((l) => l.startsWith("{") && l.includes('"type"')).map((l) => JSON.parse(l));
  assert.deepEqual(events.map((e) => e.type), ["scope_done"], result.err.slice(-500));
  assert.equal(events[0].status, "error");
  assert.equal(events[0].errorType, "precheck_failed");
  assert.ok(String(events[0].message).includes("不支持在 Android 网页上"));
});

test("目标名称与命令行工具同一口径", () => {
  assert.equal(targetLabel("desktop", "web"), "桌面网页");
  assert.equal(targetLabel("android", "app"), "Android 应用");
  assert.equal(targetLabel("ios", "web"), "iOS 网页");
});
