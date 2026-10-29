// 隧道会话预热（ADR 0051 决策 13；ADR 0035「边界与不变量」）——Midscene worker 侧。运行：npm test。
// 纯逻辑部分（三种可见结果的归因、有界重试）用假 page 覆盖；主入口的完整性判据用真子进程验（建会话之前即拒、零 AWS）。
// 真边界（AgentCore 浏览器上 Set-Cookie 真写进 cookie 库、业务请求真带上）在跳板机上真实执行核对。
import { test } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import * as W from "../lib/tunnel-warmup.mjs";

const FIXTURE = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../fixtures/tunnel-warmup.json");
const WARMUP_URL = "https://t.ngrok-free.app/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=" + "a".repeat(32);

test("边缘契约常量与跨语言 fixture 一致（runtime、Nova、Midscene 三方同值）", () => {
  const fx = JSON.parse(fs.readFileSync(FIXTURE, "utf8"));
  assert.deepEqual([W.WARMUP_PATH, W.CHECK_PATH, W.TOKEN_PARAM, W.COOKIE_NAME], [fx.warmup_path, fx.check_path, fx.token_param, fx.cookie_name]);
  assert.deepEqual({ ...W.WARMUP_TITLES }, fx.titles);
  assert.deepEqual({ ...W.WARMUP_MARKERS }, fx.markers);
  assert.deepEqual([W.SESSION_WARMUP_URL_ENV, W.EXTRA_HTTP_HEADERS_ENV, W.SESSION_WARMUP_KEY], [fx.env.warmup_url, fx.env.extra_http_headers, fx.capability_key]);
  // 四条产品语言的消息也同源：两个 worker 对同一种失败给同一句话（排障文档只写一遍）
  assert.equal(Object.keys(fx.messages).length, 4);  // fixture 多出一句而 worker 没跟上时在这里红
  assert.equal(W.INCOMPLETE_DEFINITION_MESSAGE, fx.messages.incomplete_definition);
  assert.equal(W.WARMUP_AUTH_REQUIRED_MESSAGE, fx.messages.auth_required);
  assert.equal(W.WARMUP_DENIED_MESSAGE, fx.messages.denied);
  assert.equal(W.warmupErrorMessage(3, "原因"), fx.messages.error_template.replace("{attempts}", "3").replace("{reason}", "原因"));
});

/** 每次 goto 按序给出一个结果（数字状态码 / null / Error 实例）；title 按序给出，最后一个值一直保持。 */
function fakePage(statuses: Array<number | null | Error>, titles: string[]) {
  const gotos: string[] = [];
  const page: W.WarmupPage = {
    async goto(url) {
      gotos.push(url);
      const s = statuses.shift();
      if (s instanceof Error) throw s;
      return s === null || s === undefined ? null : { status: () => s };
    },
    async title() {
      return titles.length > 1 ? titles.shift()! : (titles[0] ?? "");
    },
  };
  return { page, gotos };
}

function deps() {
  let t = 0;
  return { log: () => {}, sleep: async () => {}, now: () => (t += 5000) };  // 假时钟每读一次前进 5 秒：等标记的 10 秒预算两次就到
}

test("READY 标记即就绪：预热恰一次导航，随即离开预热页（令牌不留在当前地址）", async () => {
  const { page, gotos } = fakePage([200], ["gherkai-tunnel-warmup", W.WARMUP_TITLES.ready]);
  assert.equal(await W.warmupSession(page, WARMUP_URL, deps()), null);
  assert.deepEqual(gotos, [WARMUP_URL, "about:blank"]);
});

test("离开预热页失败只记日志：会话已换到 cookie，判定不受影响", async () => {
  const { page, gotos } = fakePage([200, new Error("reset")], ["gherkai-tunnel-warmup", W.WARMUP_TITLES.ready]);
  const lines: string[] = [];
  assert.equal(await W.warmupSession(page, WARMUP_URL, { ...deps(), log: (l) => lines.push(l) }), null);
  assert.deepEqual(gotos, [WARMUP_URL, "about:blank"]);
  assert.ok(lines.some((l) => l.includes("could not be left")));
});

test("401（令牌错）、AUTH REQUIRED、DENIED 都是确定性拒绝：precheck_failed、不重试，令牌被拒与 cookie 未通过校验各给自己的一句", async () => {
  const cases = [
    [[401], ["gherkai-tunnel-auth-required"], W.WARMUP_AUTH_REQUIRED_MESSAGE],  // 令牌错：预热路径直接 401 页
    [[200], [W.WARMUP_TITLES.auth_required], W.WARMUP_AUTH_REQUIRED_MESSAGE],
    [[200], [W.WARMUP_TITLES.denied], W.WARMUP_DENIED_MESSAGE],  // 会话 cookie 未通过校验：脚本对校验路径得到 401
  ] as const;
  for (const [statuses, titles, message] of cases) {
    const { page, gotos } = fakePage([...statuses], [...titles]);
    const f = await W.warmupSession(page, WARMUP_URL, deps());
    assert.deepEqual(f, { errorType: "precheck_failed", message });
    assert.equal(gotos.length, 1);
  }
});

test("ERROR 标记原地重导航，之后 READY 即就绪", async () => {
  const { page, gotos } = fakePage([200, 200], [W.WARMUP_TITLES.error, W.WARMUP_TITLES.ready]);
  assert.equal(await W.warmupSession(page, WARMUP_URL, deps()), null);
  assert.deepEqual(gotos, [WARMUP_URL, WARMUP_URL, "about:blank"]);
});

test("导航抛网络类异常：吞在有界重试里、不向上抛，耗尽后 engine_error（不进建连重试域、不退 80）", async () => {
  const { page, gotos } = fakePage([Object.assign(new Error("read ECONNRESET"), { code: "ECONNRESET" }), new Error("Timeout"), new Error("x")], [""]);
  const f = await W.warmupSession(page, WARMUP_URL, deps());
  assert.equal(f?.errorType, "engine_error");
  assert.match(f!.message, /已尝试 3 次/);
  assert.equal(gotos.length, 3);
});

test("预算内没有任何标记 → engine_error，消息说明", async () => {
  const { page } = fakePage([200, 200, 200], ["gherkai-tunnel-warmup"]);
  const f = await W.warmupSession(page, WARMUP_URL, deps());
  assert.equal(f?.errorType, "engine_error");
  assert.match(f!.message, /没有给出任何标记/);
  assert.match(f!.message, /响应状态 200，页面标题 gherkai-tunnel-warmup/);
  const f2 = await W.warmupSession(fakePage([null, null, null], [""]).page, WARMUP_URL, deps());  // 没有响应对象、空标题：说「未知」「空」
  assert.match(f2!.message, /响应状态 未知，页面标题 空/);
  assert.doesNotMatch(f2!.message, /null|undefined|""/);
});

test("warmupFailureOutcome：按归因发 scope_done{error}，退出码只随 cleanupFailed（预热失败本身 0、释放失败才 1）", () => {
  const failure: W.WarmupFailure = { errorType: "precheck_failed", message: W.WARMUP_DENIED_MESSAGE };
  const ok = W.warmupFailureOutcome(failure, "s", "sess-1", false);
  assert.deepEqual(ok.event, { type: "scope_done", scopeId: "s", sessionId: "sess-1", status: "error", errorType: "precheck_failed", message: W.WARMUP_DENIED_MESSAGE });
  assert.equal(ok.exitCode, 0);
  const leaked = W.warmupFailureOutcome({ errorType: "engine_error", message: "m" }, "s", null, true);
  assert.equal(leaked.exitCode, 1);
  assert.equal(leaked.event.sessionId, null);
  assert.equal(leaked.event.errorType, "engine_error");
});

test("主入口的完整性判据：有额外请求头、没有预热地址 → 唯一事件 scope_done{precheck_failed}，不建会话、退出码 0（真子进程）", async () => {
  const env: Record<string, string> = {};
  for (const k of ["PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "NODE_OPTIONS"]) if (process.env[k] !== undefined) env[k] = process.env[k]!;
  env["AWS_EC2_METADATA_DISABLED"] = "true";
  env[W.EXTRA_HTTP_HEADERS_ENV] = '{"ngrok-skip-browser-warning": "1"}';
  const job = { schemaVersion: 1, scope: { id: "s", name: "s" }, engine: "midscene", assertionVotes: 1, timeoutS: null,
    target: { device: "desktop", uiKind: "web" }, deviceRequest: null,
    scenarios: [{ id: "f:3", name: "s", steps: [{ index: 0, keyword: "Given", text: "https://x/" }] }] };
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
  assert.equal(events[0].message, W.INCOMPLETE_DEFINITION_MESSAGE);
});
