// WebdriverIO 日志凭据掩码的单测（ADR 0051 决策 11）。运行：npm test。
//
// 分三层：
//   - 日志模块同一性：在临时目录里建的最小依赖树上，核对本模块与 webdriver 解析到的 @wdio/logger 分成两份的情况能被识别。
//   - 用例表层：用 engines/fixtures/redaction-cases.json 逐条核对 webdriver logger 写出的文字与 redactSecrets 盖住的范围相同
//     （两边的掩码字面量不同：@wdio/logger 固定写 **MASKED**，且整段换掉「参数名=值」或「/remote-endpoint/令牌」）。
//   - 真实运行层：真 webdriverio 对本机的假 WebDriver 服务建会话，制造 newSession 失败与请求最终失败两种 error 行，
//     核对行里的设备端点令牌与预签名地址的签名都已盖住。这两种行由 @wdio/logger 直接写到 stderr、不经 worker 的日志出口；
//     掩码是否装进了 webdriver 实际使用的那个 logger 实例，这一层直接看输出结果。
import { test } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as http from "node:http";
import * as os from "node:os";
import * as path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import getLogger, { SENSITIVE_DATA_REPLACER } from "@wdio/logger";
import { ENDPOINT_TOKEN, QUERY_SECRET, redactSecrets } from "../lib/redact.mjs";
import {
  WDIO_LOG_LEVEL, WDIO_LOGGER, WDIO_MASKING_PATTERNS, installWdioLogMasking, sameLoggerAsWebdriver, wdioLogMaskingInstalled,
} from "./wdio-log.mjs";

const FIXTURE = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../fixtures/redaction-cases.json");
const CASES = (JSON.parse(fs.readFileSync(FIXTURE, "utf8")) as { cases: Array<[string, string]> }).cases;

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

// webdriver logger 的一行是「时间 级别 名字: 正文」，颜色码在非终端下没有，仍按需剥掉
function logBody(line: string): string {
  const plain = line.replace(/\u001b\[[0-9;]*m/g, "").replace(/\n$/, "");
  const marker = ` ${WDIO_LOGGER}: `;
  const at = plain.indexOf(marker);
  assert.ok(at >= 0, `不像 webdriver logger 的一行：${JSON.stringify(line)}`);
  return plain.slice(at + marker.length);
}

test("日志级别固定为 error（不关到 silent）", () => {
  assert.equal(WDIO_LOG_LEVEL, "error");
});

test("掩码串：两条规则，取自 redact 的同一正则对象，只把开头的捕获组改成非捕获组，标志不变", () => {
  // @wdio/logger 按逗号切分掩码串：切出的条数必须恰好是两条，正则源里有逗号会被静默切碎
  const parts = WDIO_MASKING_PATTERNS.split(/,\s*/);
  assert.deepEqual(parts, [QUERY_SECRET, ENDPOINT_TOKEN].map((re) => `/(?:${re.source.slice(1)}/${re.flags}`));
  for (const re of [QUERY_SECRET, ENDPOINT_TOKEN]) {
    assert.ok(re.source.startsWith("(") && !re.source.startsWith("(?"), `规则开头应是保住前缀的捕获组：${re}`);
    assert.ok(re.flags.includes("g"), `规则要带全局标志，否则一行里只盖第一处：${re}`);
  }
});

test("安装前 webdriver logger 没有这组掩码；安装后有，重复安装不叠加", () => {
  assert.equal(wdioLogMaskingInstalled(), false);
  installWdioLogMasking();
  assert.equal(wdioLogMaskingInstalled(), true);
  installWdioLogMasking();
  const installed = getLogger(WDIO_LOGGER).maskingPatterns ?? [];
  assert.deepEqual(installed.map(String), WDIO_MASKING_PATTERNS.split(/,\s*/));
});

// 在临时目录里按 node_modules 布局建一棵最小依赖树：每个包只有 package.json 与入口文件，解析走 Node 的真实查找规则。
// nested 为真时 webdriver 嵌套在 webdriverio 下、自带一份 @wdio/logger，顶层另有一份别的版本（使用方项目自己装了 9.x 的形态）。
function fakeDependencyTree(nested: boolean): string {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "wdio-log-tree-"));
  const pkg = (dir: string, name: string, version: string) => {
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, "package.json"), JSON.stringify({ name, version, main: "index.cjs" }));
    fs.writeFileSync(path.join(dir, "index.cjs"), "");
  };
  const top = path.join(root, "node_modules");
  pkg(path.join(top, "@wdio", "logger"), "@wdio/logger", nested ? "9.29.1" : "10.0.0");
  pkg(path.join(top, "webdriverio"), "webdriverio", "10.0.2");
  const webdriverDir = nested ? path.join(top, "webdriverio", "node_modules", "webdriver") : path.join(top, "webdriver");
  pkg(webdriverDir, "webdriver", "10.0.2");
  if (nested) pkg(path.join(webdriverDir, "node_modules", "@wdio", "logger"), "@wdio/logger", "10.0.0");
  fs.writeFileSync(path.join(root, "entry.mjs"), "");
  return root;
}

test("日志模块同一性：本仓库的依赖树上，本模块与 webdriver 解析到同一份 @wdio/logger", () => {
  assert.equal(sameLoggerAsWebdriver(), true);
});

test("日志模块同一性：两边分成两份时判为不同，安装掩码前即可发现", () => {
  for (const nested of [false, true]) {
    const root = fakeDependencyTree(nested);
    try {
      assert.equal(sameLoggerAsWebdriver(pathToFileURL(path.join(root, "entry.mjs"))), !nested, `nested=${nested}`);
    } finally {
      fs.rmSync(root, { recursive: true, force: true });
    }
  }
});

test("用例表逐条：webdriver logger 写出的文字与 redactSecrets 盖住的范围相同", async () => {
  installWdioLogMasking();
  const logger = getLogger(WDIO_LOGGER);
  // 期望侧：用例表的期望输出里，规则二、三盖过的整段（参数名=*** 与 /remote-endpoint/***）换成 @wdio/logger 的掩码字面量。
  // 实际侧：logger 不收 userinfo 规则，故对它写出的文字再经一次 redactSecrets 补上 userinfo；若 logger 漏盖了签名或令牌，
  // 这一步会把它写成「参数名=***」，与期望侧的整段掩码不等，用例失败。
  const toWdioForm = (s: string) => s.replace(QUERY_SECRET, SENSITIVE_DATA_REPLACER).replace(ENDPOINT_TOKEN, SENSITIVE_DATA_REPLACER);
  let masked = 0;
  for (const [input, expected] of CASES) {
    const out = await captureStderr(() => logger.error(input));
    const body = logBody(out);
    if (body.includes(SENSITIVE_DATA_REPLACER)) masked++;
    assert.equal(redactSecrets(body), toWdioForm(expected), `输入 ${JSON.stringify(input)}`);
  }
  assert.ok(masked >= 10, `用例表里该有足够多的条目被盖住，实际 ${masked} 条`);
});

// ---- 真实运行层 ----

// 假 WebDriver 服务：sessionOk 时 POST /session 建会话成功、其余请求直接断开连接（客户端得到 UND_ERR_SOCKET，相当于会话被外部
// 停止后的请求失败）；否则 POST /session 回 500，错误消息里带着预签名的应用地址（应用下载失败时服务端的报错形态）。
async function fakeWebDriver(opts: { sessionOk: boolean; failureMessage?: string }): Promise<{ port: number; close: () => Promise<void> }> {
  const server = http.createServer((req, res) => {
    req.resume();
    req.on("end", () => {
      const isCreate = req.method === "POST" && (req.url ?? "").endsWith("/session");
      if (isCreate && opts.sessionOk) {
        res.writeHead(200, { "content-type": "application/json" });
        res.end(JSON.stringify({ value: { sessionId: "s1", capabilities: { platformName: "Android" } } }));
      } else if (isCreate) {
        res.writeHead(500, { "content-type": "application/json" });
        res.end(JSON.stringify({ value: { error: "session not created", message: opts.failureMessage ?? "", stacktrace: "" } }));
      } else {
        req.socket.destroy();
      }
    });
  });
  await new Promise<void>((r) => server.listen(0, "127.0.0.1", r));
  const port = (server.address() as { port: number }).port;
  return { port, close: () => new Promise<void>((r) => server.close(() => r())) };
}

// 样本取用例表：设备端点那条的路径给 hub 路径，预签名地址那条（带 Credential 与 Signature）放进服务端的报错消息
const [ENDPOINT_SAMPLE] = CASES.find(([i]) => i.includes("/remote-endpoint/") && i.endsWith("/wd/hub/session"))!;
const ENDPOINT_PATH = new URL(ENDPOINT_SAMPLE).pathname.replace(/\/session$/, "");
const ENDPOINT_SECRET = ENDPOINT_PATH.split("/")[2]!;
const [PRESIGNED_SAMPLE] = CASES.find(([i]) => i.includes("X-Amz-Credential=") && i.includes("X-Amz-Signature="))!;
const PRESIGNED_SECRETS = [...PRESIGNED_SAMPLE.matchAll(QUERY_SECRET)].map((m) => m[0].slice(m[1]!.length));

test("真实运行：newSession 失败与请求最终失败的 error 行里，端点令牌与预签名签名都被盖住", async () => {
  installWdioLogMasking();
  assert.ok(ENDPOINT_SECRET.length > 0 && PRESIGNED_SECRETS.length >= 2 && PRESIGNED_SECRETS.every((s) => s.length > 0));
  const { remote } = await import("webdriverio");
  const base = { protocol: "http", hostname: "127.0.0.1", path: ENDPOINT_PATH, logLevel: WDIO_LOG_LEVEL,
                 connectionRetryCount: 0, connectionRetryTimeout: 5000 } as const;

  // ① newSession 失败：服务端报错消息带预签名地址，webdriver 在抛出前记下错误
  const refused = await fakeWebDriver({ sessionOk: false, failureMessage: `Problem downloading app from url ${PRESIGNED_SAMPLE}: 403` });
  const createOut = await captureStderr(async () => {
    await assert.rejects(remote({ ...base, port: refused.port, capabilities: { platformName: "Android", "appium:app": PRESIGNED_SAMPLE } }));
  });
  await refused.close();

  // ② 请求最终失败：会话已建、之后的请求被断开，webdriver 先记一条带整条端点地址的 error 再抛出
  const dropping = await fakeWebDriver({ sessionOk: true });
  const requestOut = await captureStderr(async () => {
    const browser = await remote({ ...base, port: dropping.port, capabilities: { platformName: "Android" } });
    await assert.rejects(browser.deleteSession());
  });
  await dropping.close();

  for (const [name, out] of [["newSession", createOut], ["deleteSession", requestOut]] as const) {
    assert.ok(out.includes(` ${WDIO_LOGGER}: `), `${name} 该有 webdriver 的 error 行：${JSON.stringify(out)}`);
    assert.ok(out.includes(SENSITIVE_DATA_REPLACER), `${name} 的 error 行该带掩码：${JSON.stringify(out)}`);
    assert.ok(!out.includes(ENDPOINT_SECRET), `${name} 的 error 行不应有端点令牌：${JSON.stringify(out)}`);
    for (const secret of PRESIGNED_SECRETS) assert.ok(!out.includes(secret), `${name} 的 error 行不应有签名参数值 ${secret}`);
  }
  assert.ok(createOut.includes("X-Amz-Date="), "非凭证的预签名参数保留明文，便于诊断过期一类问题");
});
