// 共享：Midscene → Bedrock/AgentCore 的两套 SigV4 签名场景。
// 被 spike（tsx 直跑）和 worker（run-scope）共用。
// 用 .mts 扩展名：模块体系不依赖 package.json#type（ADR 0037 决策 3，全包统一 .mts → .mjs）。
//
// 两套签名 service code 不同（CONTEXT「AgentCore 浏览器会话」已警示别混）：
//   - 模型连接 → service "bedrock"           （Bedrock /openai/v1 chat-completions）
//   - 浏览器连接（CDP）→ service "bedrock-agentcore"  （AgentCore CDP WebSocket upgrade）
// 配方与失败模式见 repo 里的 engines/midscene/spikes/SIGV4-FETCH-RECIPE.md（不随包发行）+ 根 docs/adr/0008。
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
  if (!r) throw new Error("Midscene worker: AWS_REGION 未设——连 AgentCore/Bedrock 需显式 region");
  return r;
}
export function getBaseUrl(): string {
  return `https://bedrock-runtime.${getRegion()}.amazonaws.com/openai/v1`;
}
// === 模型选择：默认钉死一个具体 id + env 覆盖（ADR 0044 决策 1/2）===
// DEFAULT_MODEL 是「现值」：由本仓库评测集 A/B 选出、换默认只随发版（不用 latest 类别名——换模型是有评估的
// 显式发布）。单独导出好让「默认是什么」被单测与调用方引用；MODEL 是**本进程真要喂给 SDK 的那个**（有覆盖即
// 覆盖值），modelConfig() 与能力自述的 model_id 都取它，故两处天然跟 env 走、不会各自漂。
// **模块级只取值、不校验、不抛**（同上面 region 的惰性 fail-loud 之律：import 本模块不该失败）；取不出 family
// 那种坏配置由 modelFamily() 在 worker 启动期一次性挡下。
export const DEFAULT_MODEL = "qwen.qwen3-vl-235b-a22b";
export const MODEL = process.env.MIDSCENE_MODEL_ID || DEFAULT_MODEL;  // 空串当未设（镜像 ENV 留空 / export 空值）——与本文件 getRegion 的 `if (!r)`、modelFamily 的 `if (explicit)` 同一判据

// 模型 id → Midscene family 的推断表，逐条对应 ADR 0044 决策 2 的那张表（**一处常量，别在别处再写一份**）。
// 用正则而非通配串：ADR 表里带前导 `*` 的项不锚首——inference profile id 会带 region 前缀（`us.openai.gpt-6-astra`、
// `global.openai.…`），锚首就漏；不带前导 `*` 的锚首（`^`）。右列 family 名的合法取值是 Midscene 的真值。
const MODEL_FAMILY_PATTERNS: readonly (readonly [RegExp, string])[] = [
  [/qwen\.qwen3-vl/, "qwen3-vl"],   // *qwen.qwen3-vl*（含 us./global. 前缀的 inference profile 形态）
  [/openai\.gpt-6/, "gpt-6"],       // *openai.gpt-6*
  [/openai\.gpt-5/, "gpt-5"],       // *openai.gpt-5*
  [/kimi-k2/, "kimi"],              // *kimi-k2*
  [/kimi-k3/, "kimi3"],             // *kimi-k3*
  [/deepseek\./, "deepseek"],       // *deepseek.*
  [/^zai\.glm-.*v/, "glm-v"],       // zai.glm-*v*
];

/** 交给 Midscene 的 family 名（ADR 0044 决策 2）：显式 env `MIDSCENE_MODEL_FAMILY` 优先，否则按上表按模型 id 推断。
 *  family 决定 Midscene 用哪套提示词与请求参数，**猜错的后果是静默劣化而不是报错**，故推不出即抛、不兜底猜。
 *  抛点被 worker 启动期调一次（run-scope.main，入口分派之前）→ 坏配置在建云端浏览器会话之前就被挡下。
 *  显式值不在此校验取值：合法 family 清单随 Midscene 版本变、是 SDK 的真值，复刻即第二事实源，交 SDK 自己拒。 */
export function modelFamily(modelId: string = MODEL): string {
  const explicit = process.env.MIDSCENE_MODEL_FAMILY;
  if (explicit) return explicit;
  for (const [pattern, family] of MODEL_FAMILY_PATTERNS) {
    if (pattern.test(modelId)) return family;
  }
  throw new Error(
    `Midscene worker: 模型 ${modelId} 不在已知家族里——无法确定该按哪种模型去驱动浏览器。`
    + `请设 MIDSCENE_MODEL_FAMILY 指明它属于哪个家族（可取值见 Midscene 文档 https://midscenejs.com/model-common-config.html），`
    + `或把 MIDSCENE_MODEL_ID 换回已支持的模型。`
  );
}

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

/** Bedrock OpenAI 兼容层的方言适配（ADR 0044 决策 3 / ADR 0008）：去掉 `image_url.detail: "original"`。
 *  OpenAI 原生认这个取值，Bedrock 对任何模型都 400「Invalid 'content': value did not match any expected variant」；
 *  Midscene 的 gpt-5 / gpt-6 family 适配器对定位请求固定发它、无配置可关。只删这一个字段、其余原样；非 JSON /
 *  无 messages 的体原样返回。**必须在签名之前改**（SigV4 含 payload hash，签完再改即 403）。导出供单测。 */
export function bedrockCompatBody(body: string): string {
  let parsed: unknown;
  try { parsed = JSON.parse(body); } catch { return body; }
  if (!parsed || typeof parsed !== "object" || !Array.isArray((parsed as { messages?: unknown }).messages)) return body;
  let changed = false;
  for (const m of (parsed as { messages: unknown[] }).messages) {
    const content = (m as { content?: unknown })?.content;
    if (!Array.isArray(content)) continue;
    for (const part of content) {
      const img = (part as { image_url?: { detail?: unknown } })?.image_url;
      if (img && typeof img === "object" && img.detail === "original") { delete img.detail; changed = true; }
    }
  }
  return changed ? JSON.stringify(parsed) : body;
}

export const sigv4Fetch: typeof fetch = async (input, init = {}) => {
  const urlStr = typeof input === "string" ? input : input.toString();
  const u = new URL(urlStr);
  const rawBody = (init.body as string | undefined) ?? undefined;
  const body = rawBody === undefined ? undefined : bedrockCompatBody(rawBody);

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

  const headers = new Headers(init.headers);  // init 已是 RequestInit，headers 类型即 HeadersInit（无需 cast）
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
