// 共享：Midscene → Bedrock/AgentCore 的两套 SigV4 签名场景。
// 被 spike（tsx 直跑）和 bdd step（cucumber ESM）共用。
// 用 .mts 扩展名强制 ESM，绕开 midscene 子工程根的 commonjs 设定。
//
// 两套签名 service code 不同（CONTEXT「AgentCore 浏览器会话」已警示别混）：
//   - 模型连接 → service "bedrock"           （Bedrock /openai/v1 chat-completions）
//   - 浏览器连接（CDP）→ service "bedrock-agentcore"  （AgentCore CDP WebSocket upgrade）
// 配方与失败模式见 ../spikes/midscene-sigv4/SIGV4-FETCH-RECIPE.md + 根 docs/adr/0008。
import { SignatureV4 } from "@aws-sdk/signature-v4";
import { HttpRequest } from "@aws-sdk/protocol-http";
import { Sha256 } from "@aws-crypto/sha256-js";
import { fromNodeProviderChain } from "@aws-sdk/credential-providers";

export const REGION = "us-east-1";
export const HOST = `bedrock-runtime.${REGION}.amazonaws.com`;
export const BASE_URL = `https://${HOST}/openai/v1`;
export const MODEL = "qwen.qwen3-vl-235b-a22b";

// === 模型连接：openai-node v6 的自定义 fetch，逐请求 SigV4 自签（service "bedrock"）===
// 关键：只签最小手建请求 { host, content-type }，绝不签 SDK 整个 header 包（否则 403）。
const modelSigner = new SignatureV4({
  service: "bedrock",
  region: REGION,
  credentials: fromNodeProviderChain(),
  sha256: Sha256,
});

export const sigv4Fetch: typeof fetch = async (input, init = {}) => {
  const urlStr = typeof input === "string" ? input : input.toString();
  const u = new URL(urlStr);
  const body = (init.body as string | undefined) ?? undefined;

  const toSign = new HttpRequest({
    method: (init.method ?? "POST").toUpperCase(),
    protocol: u.protocol,
    hostname: u.hostname,
    path: u.pathname,
    query: Object.fromEntries(u.searchParams),
    headers: { host: u.host, "content-type": "application/json" }, // 只签这两个
    body,
  });
  const signed = await modelSigner.sign(toSign);

  const headers = new Headers(init.headers as HeadersInit | undefined);
  headers.delete("authorization"); // 删掉 openai 的 `Bearer unused`
  headers.delete("content-length"); // 让 undici 重算
  for (const [k, v] of Object.entries(signed.headers)) headers.set(k, v as string);

  return fetch(urlStr, {
    method: toSign.method,
    headers,
    body,
    ...(init.signal ? { signal: init.signal } : {}),
  });
};

// === 浏览器连接（CDP）：为 AgentCore WebSocket upgrade（GET，无 body）签 SigV4（service "bedrock-agentcore"）===
// 产出可作 Playwright connectOverCDP(headers) 的静态头。
export async function signCdpUpgrade(wsUrl: string): Promise<Record<string, string>> {
  const signer = new SignatureV4({
    service: "bedrock-agentcore",
    region: REGION,
    credentials: fromNodeProviderChain(),
    sha256: Sha256,
  });
  const u = new URL(wsUrl.replace(/^wss:\/\//, "https://"));
  const req = new HttpRequest({
    method: "GET",
    protocol: u.protocol,
    hostname: u.hostname,
    path: u.pathname,
    query: Object.fromEntries(u.searchParams),
    headers: { host: u.host },
  });
  const signed = await signer.sign(req);
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(signed.headers)) {
    if (k.toLowerCase() !== "host") out[k] = v as string;
  }
  return out;
}
