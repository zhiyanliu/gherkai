// 应用启停的单测（ADR 0051 决策 9、14；ADR 0052 决策 3「应用启停」块）。运行：npx tsx --test src/device/app.test.mts。
//
// 两层：存在性检查与预签名用真的 S3Client，只把网络层换成本地的请求处理器（离线、不连 AWS），这样 HeadObject 的错误形态与
// 预签名地址的形态都是 SDK 的真实行为，不是 fake 自己说了算；预签名的签名值另按 SigV4 规范在测试里独立复算一遍。启动与重启
// 用记录调用序列的假 driver。
import { test } from "node:test";
import assert from "node:assert";
import { createHash, createHmac } from "node:crypto";
import { Readable } from "node:stream";
import { S3Client } from "@aws-sdk/client-s3";
import {
  APP_LAUNCH_SELF_EXIT_MESSAGE, APP_OBJECT_FORBIDDEN_MESSAGE, APP_OBJECT_MISSING_MESSAGE, APP_RESTART_SELF_EXIT_MESSAGE, APP_STATE,
  appHandle, checkAppObject, launchApp, presignAppObject, s3AppObjectStore, type AppControl, type AppObjectStore,
} from "./app.mjs";
import { APP_PRESIGN_EXPIRES_S, LAUNCH_SAMPLE_COUNT, LAUNCH_SAMPLE_INTERVAL_MS } from "./limits.mjs";
import { attachClassification, readClassification } from "../worker/surface.mjs";
import { redactSecrets } from "../lib/redact.mjs";

const LOC = { bucket: "gherkai-artifacts-123456789012-us-west-2", key: "apps/9f2c/shop-debug (1).apk" };
const FAKE_CREDS = { accessKeyId: "AKIDEXAMPLE", secretAccessKey: "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY" };

interface SeenRequest { method: string; hostname: string; path: string; abortSignal?: unknown }

/** 真的 S3Client，网络层换成本地处理器：返回给定状态码的空响应，并记下发出的请求。 */
function offlineClient(statusCode: number, seen: SeenRequest[] = []): S3Client {
  return new S3Client({
    region: "us-west-2",
    maxAttempts: 1,
    credentials: FAKE_CREDS,
    requestHandler: {
      handle: async (req: { method: string; hostname: string; path: string }, opts?: { abortSignal?: unknown }) => {
        seen.push({ method: req.method, hostname: req.hostname, path: req.path, abortSignal: opts?.abortSignal });
        return { response: { statusCode, headers: {}, body: Readable.from([]) } };
      },
    } as never,
  });
}

// ---- 存在性检查（建会话前，ADR 0051 决策 9）----

test("存在性检查：对象存在时放行（返回 null），发出的是对应用键的 HEAD", async () => {
  const seen: SeenRequest[] = [];
  const store = s3AppObjectStore({ client: offlineClient(200, seen) });
  assert.equal(await checkAppObject(store, LOC, AbortSignal.timeout(5_000)), null);
  assert.equal(seen.length, 1);
  assert.equal(seen[0].method, "HEAD");
  assert.equal(decodeURIComponent(seen[0].path), `/${LOC.key}`);
});

test("存在性检查：404 记 precheck_failed，消息是 ADR 原文「安装包已不在存储桶里，请重新提交」", async () => {
  const store = s3AppObjectStore({ client: offlineClient(404) });
  assert.deepEqual(await checkAppObject(store, LOC, AbortSignal.timeout(5_000)), {
    errorType: "precheck_failed", message: "安装包已不在存储桶里，请重新提交",
  });
  assert.equal(APP_OBJECT_MISSING_MESSAGE, "安装包已不在存储桶里，请重新提交");
});

test("存在性检查：403 同样记 precheck_failed，消息与 404 不同、说明是权限问题", async () => {
  const store = s3AppObjectStore({ client: offlineClient(403) });
  const got = await checkAppObject(store, LOC, AbortSignal.timeout(5_000));
  assert.deepEqual(got, { errorType: "precheck_failed", message: APP_OBJECT_FORBIDDEN_MESSAGE });
  assert.notEqual(APP_OBJECT_FORBIDDEN_MESSAGE, APP_OBJECT_MISSING_MESSAGE);
  assert.match(APP_OBJECT_FORBIDDEN_MESSAGE, /权限/);
});

test("存在性检查：404 与 403 之外的失败不归类，原样抛给调用方（不当作缺失或无权）", async () => {
  const store = s3AppObjectStore({ client: offlineClient(500) });
  await assert.rejects(checkAppObject(store, LOC, AbortSignal.timeout(5_000)));
});

test("存在性检查：调用方的截止信号原样交到 SDK 的网络层（中止由网络层执行，单次调用的上界因此由调用方给出）", async () => {
  const seen: SeenRequest[] = [];
  const store = s3AppObjectStore({ client: offlineClient(200, seen) });
  const deadline = AbortSignal.timeout(5_000);
  await checkAppObject(store, LOC, deadline);
  assert.equal(seen[0].abortSignal, deadline);
});

test("存在性检查：截止信号已中止时网络层没有响应，原样抛出（不当作缺失或无权）", async () => {
  const client = new S3Client({
    region: "us-west-2", maxAttempts: 1, credentials: FAKE_CREDS,
    requestHandler: {
      handle: async (_req: unknown, opts?: { abortSignal?: AbortSignal }) => {
        if (opts?.abortSignal?.aborted) throw Object.assign(new Error("Request aborted"), { name: "AbortError" });
        return { response: { statusCode: 200, headers: {}, body: Readable.from([]) } };
      },
    } as never,
  });
  const aborted = new AbortController();
  aborted.abort();
  await assert.rejects(checkAppObject(s3AppObjectStore({ client }), LOC, aborted.signal), /aborted/i);
});

// ---- 预签名（newSession 前，ADR 0051 决策 9）----

/** RFC 3986 的严格编码（SigV4 规范的 UriEncode）：只有 A-Z a-z 0-9 - . _ ~ 不编码。 */
function uriEncode(s: string): string {
  return encodeURIComponent(s).replace(/[!'()*]/g, (c) => `%${c.charCodeAt(0).toString(16).toUpperCase()}`);
}

/** 按 SigV4 规范（查询串签名形态）独立复算签名，不经 SDK 的签名器。 */
function recomputeSignature(url: URL, secretAccessKey: string): string {
  const params = [...url.searchParams.entries()].filter(([k]) => k !== "X-Amz-Signature");
  const canonicalQuery = params.map(([k, v]) => [uriEncode(k), uriEncode(v)] as const)
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)).map(([k, v]) => `${k}=${v}`).join("&");
  const signedHeaders = url.searchParams.get("X-Amz-SignedHeaders")!;
  assert.equal(signedHeaders, "host");
  const canonicalRequest = ["GET", url.pathname, canonicalQuery, `host:${url.host}`, "", signedHeaders, "UNSIGNED-PAYLOAD"].join("\n");
  const amzDate = url.searchParams.get("X-Amz-Date")!;
  const [, date, region, service] = url.searchParams.get("X-Amz-Credential")!.split("/");
  const scope = `${date}/${region}/${service}/aws4_request`;
  const stringToSign = ["AWS4-HMAC-SHA256", amzDate, scope, createHash("sha256").update(canonicalRequest).digest("hex")].join("\n");
  const hmac = (key: string | Buffer, data: string) => createHmac("sha256", key).update(data).digest();
  const signingKey = hmac(hmac(hmac(hmac(`AWS4${secretAccessKey}`, date), region), service), "aws4_request");
  return createHmac("sha256", signingKey).update(stringToSign).digest("hex");
}

test("预签名：GET 应用键，有效期取 limits 的 3600 秒，只签 host，不发任何请求", async () => {
  const seen: SeenRequest[] = [];
  const store = s3AppObjectStore({ client: offlineClient(200, seen) });
  const url = new URL(await presignAppObject(store, LOC));
  assert.equal(seen.length, 0, "预签名是本地计算，不发请求");
  assert.equal(url.protocol, "https:");
  assert.equal(url.hostname, `${LOC.bucket}.s3.us-west-2.amazonaws.com`);
  assert.equal(decodeURIComponent(url.pathname), `/${LOC.key}`);
  assert.equal(APP_PRESIGN_EXPIRES_S, 3600);
  assert.equal(url.searchParams.get("X-Amz-Expires"), String(APP_PRESIGN_EXPIRES_S));
  assert.equal(url.searchParams.get("X-Amz-Algorithm"), "AWS4-HMAC-SHA256");
  assert.equal(url.searchParams.get("X-Amz-SignedHeaders"), "host");
  assert.match(url.searchParams.get("X-Amz-Credential")!, /^AKIDEXAMPLE\/\d{8}\/us-west-2\/s3\/aws4_request$/);
  assert.match(url.searchParams.get("X-Amz-Signature")!, /^[0-9a-f]{64}$/);
});

test("预签名：签名值与按 SigV4 规范独立复算的结果一致（载荷记 UNSIGNED-PAYLOAD，下载方不必带任何额外请求头）", async () => {
  const store = s3AppObjectStore({ client: offlineClient(200) });
  const url = new URL(await presignAppObject(store, LOC));
  assert.equal(url.searchParams.get("X-Amz-Signature"), recomputeSignature(url, FAKE_CREDS.secretAccessKey));
});

test("预签名：带会话令牌的凭证把令牌放进查询串（同样参与签名）", async () => {
  const client = new S3Client({
    region: "us-west-2", maxAttempts: 1, credentials: { ...FAKE_CREDS, sessionToken: "IQoJb3JpZ2luX2VjEXAMPLE" },
    requestHandler: { handle: async () => { throw new Error("预签名不应发请求"); } } as never,
  });
  const url = new URL(await presignAppObject(s3AppObjectStore({ client }), LOC));
  assert.equal(url.searchParams.get("X-Amz-Security-Token"), "IQoJb3JpZ2luX2VjEXAMPLE");
  assert.equal(url.searchParams.get("X-Amz-Signature"), recomputeSignature(url, FAKE_CREDS.secretAccessKey));
});

test("预签名地址是凭证：经脱敏出口后不剩签名、访问密钥与会话令牌（ADR 0051 决策 11）", async () => {
  const client = new S3Client({
    region: "us-west-2", maxAttempts: 1, credentials: { ...FAKE_CREDS, sessionToken: "IQoJb3JpZ2luX2VjEXAMPLE" },
    requestHandler: { handle: async () => { throw new Error("预签名不应发请求"); } } as never,
  });
  const presigned = await presignAppObject(s3AppObjectStore({ client }), LOC);
  const url = new URL(presigned);
  const masked = redactSecrets(`Request failed: unable to download "${presigned}"`);
  for (const secret of [url.searchParams.get("X-Amz-Signature")!, "IQoJb3JpZ2luX2VjEXAMPLE", FAKE_CREDS.accessKeyId]) {
    assert.ok(presigned.includes(secret) || presigned.includes(encodeURIComponent(secret)), `样本里应有 ${secret}`);
    assert.ok(!masked.includes(secret), `脱敏后仍有 ${secret}`);
  }
  assert.ok(masked.includes("X-Amz-Signature=***"));
});

test("预签名：有效期由 presignAppObject 统一取 limits 常量，交给存储面的就是 3600", async () => {
  const calls: number[] = [];
  const store: AppObjectStore = {
    head: async () => "present",
    presign: async (_loc, expiresS) => { calls.push(expiresS); return "https://example.invalid/app"; },
  };
  assert.equal(await presignAppObject(store, LOC), "https://example.invalid/app");
  assert.deepEqual(calls, [3600]);
});

// ---- 启动与启动采样（ADR 0051 决策 9、14）----

/** 记录调用序列的假 driver：queryAppState 依次返回 states 里的值（用完后保持最后一个），sleep 记进同一序列。 */
function fakeControl(states: number[], opts: { failOn?: string } = {}) {
  const calls: string[] = [];
  let i = 0;
  const maybeFail = (name: string) => {
    if (opts.failOn === name) throw new Error(`${name} 命令失败`);
  };
  const control: AppControl = {
    activateApp: async (appId: string) => { calls.push(`activate:${appId}`); maybeFail("activate"); },
    terminateApp: async (appId: string) => { calls.push(`terminate:${appId}`); maybeFail("terminate"); return true; },
    queryAppState: async (appId: string) => {
      calls.push(`state:${appId}`);
      maybeFail("state");
      const s = states[Math.min(i, states.length - 1)];
      i++;
      return s;
    },
  };
  const sleep = async (ms: number) => { calls.push(`sleep:${ms}`); };
  return { control, calls, sleep };
}

const APP_ID = "com.example.shop";
const SAMPLED = Array.from({ length: LAUNCH_SAMPLE_COUNT }, () => [`sleep:${LAUNCH_SAMPLE_INTERVAL_MS}`, `state:${APP_ID}`]).flat();

test("启动：activateApp 后按 limits 采样 3 次、间隔 1 秒，一直在运行即就绪（返回 null）", async () => {
  assert.equal(LAUNCH_SAMPLE_COUNT, 3);
  assert.equal(LAUNCH_SAMPLE_INTERVAL_MS, 1_000);
  const { control, calls, sleep } = fakeControl([APP_STATE.FOREGROUND]);
  assert.equal(await launchApp(control, APP_ID, { sleep }), null);
  assert.deepEqual(calls, [`activate:${APP_ID}`, ...SAMPLED]);
});

test("启动：任一次采样回到「未运行」即 precheck_failed，消息是 ADR 原文，之后不再采样", async () => {
  const { control, calls, sleep } = fakeControl([APP_STATE.FOREGROUND, APP_STATE.NOT_RUNNING, APP_STATE.FOREGROUND]);
  assert.deepEqual(await launchApp(control, APP_ID, { sleep }), {
    errorType: "precheck_failed", message: "应用启动后立即自行退出，通常是应用带有运行环境检测；请提供关闭检测的测试包",
  });
  assert.equal(APP_LAUNCH_SELF_EXIT_MESSAGE, "应用启动后立即自行退出，通常是应用带有运行环境检测；请提供关闭检测的测试包");
  assert.deepEqual(calls, [`activate:${APP_ID}`, ...SAMPLED.slice(0, 4)]);
});

test("启动：采样读到「未安装」同样算不在运行；后台运行不算自退", async () => {
  const exited = fakeControl([APP_STATE.NOT_INSTALLED]);
  assert.equal((await launchApp(exited.control, APP_ID, { sleep: exited.sleep }))?.errorType, "precheck_failed");
  for (const state of [APP_STATE.BACKGROUND_SUSPENDED, APP_STATE.BACKGROUND]) {
    const bg = fakeControl([state]);
    assert.equal(await launchApp(bg.control, APP_ID, { sleep: bg.sleep }), null, `状态 ${state}`);
  }
});

test("启动：activateApp 或采样命令本身失败不归类，原样抛给调用方（由它先查会话状态）", async () => {
  for (const failOn of ["activate", "state"]) {
    const { control, sleep } = fakeControl([APP_STATE.FOREGROUND], { failOn });
    await assert.rejects(launchApp(control, APP_ID, { sleep }), new RegExp(`${failOn} 命令失败`));
  }
});

// ---- ctx.app.restart()（ADR 0052 决策 3；ADR 0050 决策 2）----

test("重启：terminate → activate → 采样，顺序固定，作用于同一个应用标识", async () => {
  const { control, calls, sleep } = fakeControl([APP_STATE.FOREGROUND]);
  await appHandle(control, APP_ID, { sleep }).restart();
  assert.deepEqual(calls, [`terminate:${APP_ID}`, `activate:${APP_ID}`, ...SAMPLED]);
});

test("重启：采样到自退即抛错，异常带 engine_error 的归类标记（不是 precheck_failed）", async () => {
  const { control, sleep } = fakeControl([APP_STATE.NOT_RUNNING]);
  const err = await appHandle(control, APP_ID, { sleep }).restart().then(() => null, (e: unknown) => e);
  assert.ok(err instanceof Error);
  assert.equal(err.message, APP_RESTART_SELF_EXIT_MESSAGE);
  assert.deepEqual(readClassification(err), { errorType: "engine_error", message: APP_RESTART_SELF_EXIT_MESSAGE });
  assert.notEqual(APP_RESTART_SELF_EXIT_MESSAGE, APP_LAUNCH_SELF_EXIT_MESSAGE);
});

test("重启：terminate 或 activate 失败原样传出（守卫挂的归类随异常保留），不补发、不继续后面的原语", async () => {
  const t = fakeControl([APP_STATE.FOREGROUND], { failOn: "terminate" });
  await assert.rejects(appHandle(t.control, APP_ID, { sleep: t.sleep }).restart(), /terminate 命令失败/);
  assert.deepEqual(t.calls, [`terminate:${APP_ID}`]);
  const a = fakeControl([APP_STATE.FOREGROUND], { failOn: "activate" });
  await assert.rejects(appHandle(a.control, APP_ID, { sleep: a.sleep }).restart(), /activate 命令失败/);
  assert.deepEqual(a.calls, [`terminate:${APP_ID}`, `activate:${APP_ID}`]);
});

test("重启：命令守卫挂在异常上的归类原样传出（同一个异常对象，不改写为自退或别的类别）", async () => {
  for (const failure of [
    { errorType: "session_lost" as const, message: "远程访问会话在执行中途结束" },
    { errorType: "engine_error" as const, message: "设备在等待时间内没有回应，这一步可能已执行也可能未执行" },
  ]) {
    const marked = attachClassification(new Error("guarded command failed"), failure);
    const control: AppControl = {
      activateApp: async () => { throw marked; },
      terminateApp: async () => true,
      queryAppState: async () => APP_STATE.FOREGROUND,
    };
    const err = await appHandle(control, APP_ID, { sleep: async () => {} }).restart().then(() => null, (e: unknown) => e);
    assert.equal(err, marked);
    assert.deepEqual(readClassification(err), failure);
  }
});

test("重启句柄只有 restart 一个方法（ADR 0050 决策 2 的 app 字段）", () => {
  const { control, sleep } = fakeControl([APP_STATE.FOREGROUND]);
  assert.deepEqual(Object.keys(appHandle(control, APP_ID, { sleep })), ["restart"]);
});
