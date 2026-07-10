// 共享：Midscene → Bedrock/AgentCore 的两套 SigV4 签名场景。
// 被 spike（tsx 直跑）和 worker（run-scope）共用。
// 用 .mts 扩展名强制 ESM，绕开 midscene 子工程根的 commonjs 设定。
//
// 两套签名 service code 不同（CONTEXT「AgentCore 浏览器会话」已警示别混）：
//   - 模型连接 → service "bedrock"           （Bedrock /openai/v1 chat-completions）
//   - 浏览器连接（CDP）→ service "bedrock-agentcore"  （AgentCore CDP WebSocket upgrade）
// 配方与失败模式见 ../spikes/SIGV4-FETCH-RECIPE.md + 根 docs/adr/0008。
import { SignatureV4 } from "@aws-sdk/signature-v4";
import { HttpRequest } from "@aws-sdk/protocol-http";
import { Sha256 } from "@aws-crypto/sha256-js";
import { fromNodeProviderChain } from "@aws-sdk/credential-providers";

// region 读 AWS_REGION（ADR 0033 / 0016 决策 C：Midscene region 全可配，不再硬编码 us-east-1）——与本引擎 I/O 边缘
// （EventSink/JobSource/ArtifactUploader 的 process.env.AWS_REGION）同源，使组合根注入的 region 真正贯通到 AgentCore/
// Bedrock 模型连接（此前硬编码 east、只贯通一半）。
//
// **惰性校验、非模块级 throw**（关键，别学 GlobalConfigManager import 时求值的反模式）：region 读取/校验下沉到真正
// 要连 AgentCore/Bedrock 的入口（getRegion/getBaseUrl/两个 signer/BedrockAgentCoreClient），使**纯逻辑测试**（run-scope
// 的派发/投票/网络分类，不连 AWS）import 本模块时不被 region 缺失误伤。undefined → fail-loud（对齐 Nova
// region=None→NoRegionError；组合根 resolve_region 落实后经 env 注入；spike 直跑须 AWS_REGION=... 前缀）。
export function getRegion(): string {
  const r = process.env.AWS_REGION;
  if (!r) throw new Error("Midscene worker: AWS_REGION 未设——AgentCore/Bedrock 连接需显式 region（ADR 0033/0016 决策 C）");
  return r;
}
export function getBaseUrl(): string {
  return `https://bedrock-runtime.${getRegion()}.amazonaws.com/openai/v1`;
}
export const MODEL = "qwen.qwen3-vl-235b-a22b";

// === 模型连接：openai-node v6 的自定义 fetch，逐请求 SigV4 自签（service "bedrock"）===
// 关键：只签最小手建请求 { host, content-type }，绝不签 SDK 整个 header 包（否则 403）。
// signer 惰性建（首次发请求时，getRegion() 在此 fail-loud）——非模块级单例，避免 import 即求值 region。
let _modelSigner: SignatureV4 | undefined;
function modelSigner_(): SignatureV4 {
  if (!_modelSigner) {
    _modelSigner = new SignatureV4({
      service: "bedrock",
      region: getRegion(),
      credentials: fromNodeProviderChain(),
      sha256: Sha256,
    });
  }
  return _modelSigner;
}

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
  const signed = await modelSigner_().sign(toSign);

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
    region: getRegion(),  // 惰性 fail-loud（同 modelSigner_）
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
