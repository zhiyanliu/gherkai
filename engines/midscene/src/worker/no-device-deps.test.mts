// 设备依赖不进桌面路径与能力自述（ADR 0052 决策 3「设备模块动态加载」），以及由设备限值常量推出的值（ADR 0049 决策 4、5；
// ADR 0051 决策 2、5）与设备依赖的分类和版本锁定（ADR 0052 决策 7）。运行：node --import tsx --test。
//
// **真起子进程**：「没有加载」只能在真实进程里观察。in-process import 会被本测试自己的 import 污染；读源码里的 import 行
// 又看不到传递依赖与动态 import。做法是经 `--import` 预加载一个记录钩子：resolve 钩子记下每次成功解析的父模块、
// specifier 与结果 URL，进程退出时再补记 CommonJS 缓存里的文件（CommonJS 包内部的 require 不经过 ESM 钩子）。
// 钩子文件由本测试写进临时目录、用完即删，不入库。每条子进程断言都带正向对照（记录里必须出现该路径必经的模块），
// 否则钩子失效时「没有加载」的断言会空过。
//
// 桌面 job 的子进程把 AWS 端点指向本机一个已关闭的端口、凭证给假值：建连在本机就被拒绝，不产生任何 AWS 调用，
// 按建连重试耗尽以网络专用退出码 80 结束（ADR 0028）。这个退出码同时证明 job 确实走进了桌面建连路径。
import { test } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as net from "node:net";
import * as os from "node:os";
import * as path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";
import {
  deviceGraceSeconds, busyBackoffMs, MAX_SESSION_S, SESSION_CAP_S, FARGATE_STOP_TIMEOUT_CAP_S, DEVICE_WARMUP_ATTEMPTS,
} from "../device/limits.mjs";
import { WARMUP_ATTEMPTS } from "../lib/tunnel-warmup.mjs";
import { UPLOAD_TIMEOUT_MS } from "../lib/artifact-upload.mjs";
import { MIN_GRACE_MARGIN_MS, QUEUE_DRAIN_EXIT_MS, WORKER_TARGETS, minGraceSeconds } from "./run-scope.mjs";

const PKG_DIR = path.resolve(import.meta.dirname, "..", "..");
const BIN = path.join(PKG_DIR, "src", "bin.mts");
const LIMITS = path.join(PKG_DIR, "src", "device", "limits.mts");
const SESSION_NAME = path.join(PKG_DIR, "src", "device", "session-name.mts");
const DEVICE_DIRS = [path.join(PKG_DIR, "src", "device"), path.join(PKG_DIR, "dist", "device")];
// 设备专属的两个包：webdriverio（Appium 客户端）与 Device Farm SDK。各自的子路径与 node_modules 下的实体文件都算加载。
const DEVICE_PACKAGES = ["webdriverio", "@aws-sdk/client-device-farm"];
// 零 SDK、桌面路径也用的设备模块：限值常量与会话名编码（ADR 0051 决策 4 要求桌面请求带同格式会话名）
const SHARED_DEVICE_MODULES = /^(limits|session-name)\.m[tj]s$/;

interface Resolved { parent: string | null; specifier: string | null; url: string }

const HOOK_SOURCE = `
import * as fs from "node:fs";
let out;
export function initialize(data) { out = data.out; }
export async function resolve(specifier, context, next) {
  const result = await next(specifier, context);
  fs.appendFileSync(out, JSON.stringify({ parent: context.parentURL ?? null, specifier, url: result.url }) + "\\n");
  return result;
}
`;

function registerSource(hookUrl: string, out: string): string {
  return `
import { register, createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import * as fs from "node:fs";
register(${JSON.stringify(hookUrl)}, { data: { out: ${JSON.stringify(out)} } });
const require = createRequire(import.meta.url);
process.on("exit", () => {
  for (const file of Object.keys(require.cache)) {
    fs.appendFileSync(${JSON.stringify(out)}, JSON.stringify({ parent: null, specifier: null, url: pathToFileURL(file).href }) + "\\n");
  }
});
`;
}

/** 在记录钩子下起一个子进程，返回退出码、输出与全部解析记录。 */
async function runRecorded(
  args: string[], opts: { env?: Record<string, string>; stdin?: string; cwd?: string } = {},
): Promise<{ code: number | null; out: string; err: string; records: Resolved[] }> {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "gherkai-no-device-deps-"));
  try {
    const out = path.join(dir, "resolved.jsonl");
    fs.writeFileSync(out, "");
    const hook = path.join(dir, "record-hook.mjs");
    fs.writeFileSync(hook, HOOK_SOURCE);
    const reg = path.join(dir, "record-register.mjs");
    fs.writeFileSync(reg, registerSource(pathToFileURL(hook).href, out));
    const env = opts.env ?? sandboxEnv(dir);
    const proc = spawn(process.execPath, ["--import", pathToFileURL(reg).href, "--import", import.meta.resolve("tsx"), ...args],
      { env, cwd: opts.cwd ?? dir, stdio: ["pipe", "pipe", "pipe"] });
    let stdout = ""; let stderr = "";
    proc.stdout.on("data", (d) => { stdout += d.toString(); });
    proc.stderr.on("data", (d) => { stderr += d.toString(); });
    const code: number | null = await new Promise((resolve) => {
      proc.on("close", resolve);
      proc.stdin.end(opts.stdin ?? "");
    });
    const records = fs.readFileSync(out, "utf-8").split("\n").filter(Boolean).map((l) => JSON.parse(l) as Resolved);
    return { code, out: stdout, err: stderr, records };
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

/** 与宿主隔离的环境：不继承宿主的 AWS 凭证、配置文件与 HOME，模型与 steps 覆盖也一律不带。 */
function sandboxEnv(dir: string, extra: Record<string, string> = {}): Record<string, string> {
  const env: Record<string, string> = {};
  for (const k of ["PATH", "TMPDIR", "LANG", "LC_ALL"]) if (process.env[k] !== undefined) env[k] = process.env[k]!;
  env["HOME"] = dir;
  env["AWS_CONFIG_FILE"] = path.join(dir, "aws-config-absent");
  env["AWS_SHARED_CREDENTIALS_FILE"] = path.join(dir, "aws-credentials-absent");
  env["AWS_EC2_METADATA_DISABLED"] = "true";
  env["MIDSCENE_RUN_DIR"] = path.join(dir, "midscene-run");
  return { ...env, ...extra };
}

function filePath(url: string): string | null {
  return url.startsWith("file:") ? fileURLToPath(url) : null;
}

/** 记录里属于设备专属依赖的条目：两个设备包，以及 src/device 与 dist/device 下 limits 与 session-name 之外的模块。 */
function deviceLoads(records: Resolved[]): string[] {
  const hits = new Set<string>();
  for (const r of records) {
    for (const pkg of DEVICE_PACKAGES) {
      const bySpecifier = r.specifier === pkg || (r.specifier?.startsWith(`${pkg}/`) ?? false);
      if (bySpecifier || r.url.includes(`/node_modules/${pkg}/`)) hits.add(`${pkg}: ${r.url}`);
    }
    const file = filePath(r.url);
    if (file === null) continue;
    for (const dir of DEVICE_DIRS) {
      if (file.startsWith(dir + path.sep) && !SHARED_DEVICE_MODULES.test(path.relative(dir, file))) hits.add(r.url);
    }
  }
  return [...hits].sort();
}

function loaded(records: Resolved[], predicate: (url: string) => boolean): boolean {
  return records.some((r) => predicate(r.url));
}

const isRunScope = (url: string) => filePath(url) === path.join(PKG_DIR, "src", "worker", "run-scope.mts");
const isMidsceneWeb = (url: string) => url.includes("/node_modules/@midscene/web/");

async function closedPort(): Promise<number> {
  const server = net.createServer();
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const { port } = server.address() as net.AddressInfo;
  await new Promise<void>((resolve) => server.close(() => resolve()));
  return port;
}

test("--capabilities 不加载 webdriverio、Device Farm SDK，以及 limits 与 session-name 之外的设备模块（ADR 0052 决策 3）", async () => {
  const { code, out, err, records } = await runRecorded([BIN, "--capabilities"]);
  assert.equal(code, 0, err.slice(-800));
  const caps = JSON.parse(out);
  assert.equal(caps.engine, "midscene");
  // 正向对照：自述路径必经 run-scope 与 Midscene 网页 SDK，记录里没有它们说明钩子没生效
  assert.ok(loaded(records, isRunScope) && loaded(records, isMidsceneWeb), `记录钩子没有记到自述路径的模块（共 ${records.length} 条）`);
  assert.deepEqual(deviceLoads(records), []);
  // 设备目标的会话上限只能来自 limits（ADR 0049 决策 4）；桌面条目不带这个键
  for (const t of caps.targets as Array<{ device: string; max_session_s?: number }>) {
    if (t.device === "desktop") assert.equal(t.max_session_s, undefined);
    else assert.equal(t.max_session_s, MAX_SESSION_S, `${t.device} 的 max_session_s 应由设备限值常量推出`);
  }
});

test("桌面 job 走到建连也不加载设备依赖：建连在本机被拒、按重试耗尽以 80 退出（ADR 0052 决策 3、ADR 0028）", { timeout: 120_000 }, async () => {
  const fixture = path.resolve(PKG_DIR, "..", "fixtures", "job-lines.json");
  const job = { ...JSON.parse(fs.readFileSync(fixture, "utf-8")).jobs.desktop, engine: "midscene" };
  assert.equal(job.target.device, "desktop");
  const port = await closedPort();
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "gherkai-no-device-deps-env-"));
  try {
    const env = sandboxEnv(dir, {
      AWS_REGION: "us-east-1",
      AWS_ACCESS_KEY_ID: "test-access-key",
      AWS_SECRET_ACCESS_KEY: "test-secret-key",
      AWS_ENDPOINT_URL: `http://127.0.0.1:${port}`,
      RUN_ID: "20260629T141207Z-a3f9c1",  // 桌面请求的会话名带本次运行的编号（ADR 0051 决策 4），缺失即构造期报错
    });
    const { code, err, records } = await runRecorded([BIN], { env, stdin: JSON.stringify(job) + "\n", cwd: dir });
    // 80 只在建连重试耗尽时出现：证明请求打到了本机关闭的端口（没有去 AWS），也证明 job 进入了桌面建连路径
    assert.equal(code, 80, err.slice(-1500));
    assert.match(err, new RegExp(`ECONNREFUSED 127\\.0\\.0\\.1:${port}`), err.slice(-1500));
    assert.ok(loaded(records, isRunScope) && loaded(records, isMidsceneWeb), `记录钩子没有记到桌面路径的模块（共 ${records.length} 条）`);
    assert.deepEqual(deviceLoads(records), []);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

// 桌面路径可以加载的两个设备模块（SHARED_DEVICE_MODULES）各自的加载闭包也须零 SDK，豁免才不会成为缺口
for (const [name, file, why] of [
  ["limits", LIMITS, "能力自述与收尾下限只 import 它"],
  ["session-name", SESSION_NAME, "桌面路径在每次建会话前调用它"],
] as const) test(`${name} 自身的加载闭包只含本包源码，不含任何 node_modules 里的包（${why}）`, async () => {
  const moduleUrl = pathToFileURL(file).href;
  const { code, err, records } = await runRecorded(["--input-type=module", "-e", `await import(${JSON.stringify(moduleUrl)});`]);
  assert.equal(code, 0, err.slice(-800));
  // 从该模块出发沿「父模块到被解析模块」的边求闭包；钩子与 tsx 自身的加载不在其中
  const edges = new Map<string, Set<string>>();
  for (const r of records) {
    if (r.parent === null) continue;
    if (!edges.has(r.parent)) edges.set(r.parent, new Set());
    edges.get(r.parent)!.add(r.url);
  }
  const closure = new Set<string>([moduleUrl]);
  const queue = [moduleUrl];
  while (queue.length) for (const next of edges.get(queue.shift()!) ?? []) if (!closure.has(next)) { closure.add(next); queue.push(next); }
  // 正向对照：模块自己的那次解析必须被记到
  assert.ok(records.some((r) => r.url === moduleUrl), `记录钩子没有记到 ${name} 的解析（共 ${records.length} 条）`);
  const outside = [...closure].filter((u) => !u.startsWith("node:") && !(filePath(u)?.startsWith(path.join(PKG_DIR, "src") + path.sep) ?? false));
  assert.deepEqual(outside, [], `${name} 的加载闭包里出现了本包源码之外的模块`);
});

test("限值常量推出的值：max_session_s 为 9000 减 120 即 8880；设备收尾之和 63.5 秒，取两条路径较大者仍为 63.5（ADR 0049 决策 4、5）", () => {
  assert.equal(SESSION_CAP_S, 9000);
  assert.equal(FARGATE_STOP_TIMEOUT_CAP_S, 120);
  assert.equal(MAX_SESSION_S, SESSION_CAP_S - FARGATE_STOP_TIMEOUT_CAP_S);
  assert.equal(MAX_SESSION_S, 8880);
  const device = deviceGraceSeconds({ uploadMs: UPLOAD_TIMEOUT_MS, queueDrainExitMs: QUEUE_DRAIN_EXIT_MS, marginMs: MIN_GRACE_MARGIN_MS });
  assert.equal(device, 63.5);
  // 桌面路径之和是 31；能力自述取两条路径的较大者、不相加（ADR 0051 决策 5）
  assert.equal(Math.max(minGraceSeconds(), device), 63.5);
  assert.ok(device < FARGATE_STOP_TIMEOUT_CAP_S, "设备收尾之和必须低于 Fargate 停止宽限的硬上限");
  for (const t of WORKER_TARGETS) if (t.device !== "desktop") assert.equal(t.max_session_s, MAX_SESSION_S);
});

test("繁忙等待的重列间隔按 5、10、20 秒递增并封顶 30 秒；设备预热次数与桌面共用同一常量（ADR 0051 决策 3、ADR 0052 决策 6）", () => {
  assert.deepEqual([0, 1, 2, 3, 4, 10].map(busyBackoffMs), [5_000, 10_000, 20_000, 30_000, 30_000, 30_000]);
  assert.equal(DEVICE_WARMUP_ATTEMPTS, WARMUP_ATTEMPTS);
});

test("设备依赖进 dependencies、按验证过的版本精确锁定，锁文件与 package.json 同步（ADR 0052 决策 7）", () => {
  const pkg = JSON.parse(fs.readFileSync(path.join(PKG_DIR, "package.json"), "utf-8"));
  const deps = pkg.dependencies as Record<string, string>;
  const devDeps = (pkg.devDependencies ?? {}) as Record<string, string>;
  // 发行的包与云端基础镜像只装 dependencies：设备模块在执行期加载 Device Farm SDK，留在 devDependencies 会在使用方环境缺失
  assert.ok("@aws-sdk/client-device-farm" in deps, "@aws-sdk/client-device-farm 应在 dependencies");
  assert.ok(!("@aws-sdk/client-device-farm" in devDeps), "@aws-sdk/client-device-farm 不应再在 devDependencies");
  const exact = /^\d+\.\d+\.\d+$/;
  // @midscene/core 与 @midscene/web 锁同一版本（ADR 0042 决策六的 SDK 版本锁定）
  assert.match(deps["@midscene/core"] ?? "", exact);
  assert.equal(deps["@midscene/core"], deps["@midscene/web"]);
  // webdriverio 的超时、重试与连接池共享结论都依据 10.0.2 的源码行为，升级须先过真机验收（ADR 0052 决策 7、8）
  assert.equal(deps["webdriverio"], "10.0.2");
  const lock = JSON.parse(fs.readFileSync(path.join(PKG_DIR, "package-lock.json"), "utf-8"));
  assert.deepEqual(lock.packages[""].dependencies, deps);
  assert.deepEqual(lock.packages[""].devDependencies ?? {}, devDeps);
  assert.notEqual(lock.packages["node_modules/@aws-sdk/client-device-farm"]?.dev, true, "锁文件里 Device Farm SDK 仍被标为开发依赖");
  assert.equal(lock.packages["node_modules/@midscene/core"]?.version, deps["@midscene/core"]);
  assert.equal(lock.packages["node_modules/webdriverio"]?.version, "10.0.2");
  // WebdriverIO 日志掩码装在 @wdio/logger 的模块级状态上，设备模块直接 import 它（ADR 0051 决策 11）：显式声明并精确锁定，
  // 版本与 webdriver 10.0.2 依赖的一致，锁文件里 webdriver 与 webdriverio 下不另嵌一份，两边才解析到同一个模块实例（ADR 0052 决策 7）
  assert.equal(deps["@wdio/logger"], "10.0.0");
  assert.ok(!("@wdio/logger" in devDeps), "@wdio/logger 不应在 devDependencies");
  assert.equal(lock.packages["node_modules/webdriver"]?.dependencies?.["@wdio/logger"], deps["@wdio/logger"]);
  assert.equal(lock.packages["node_modules/@wdio/logger"]?.version, deps["@wdio/logger"]);
  assert.notEqual(lock.packages["node_modules/@wdio/logger"]?.dev, true, "锁文件里 @wdio/logger 被标为开发依赖");
  for (const owner of ["webdriver", "webdriverio"]) {
    assert.equal(lock.packages[`node_modules/${owner}/node_modules/@wdio/logger`], undefined, `${owner} 下另嵌了一份 @wdio/logger`);
  }
});
