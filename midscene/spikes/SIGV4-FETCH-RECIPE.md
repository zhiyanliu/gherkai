# Midscene → Bedrock qwen3-vl 经 /openai/v1 的 SigV4 自签 fetch 配方

> spike 实现笔记（非 ADR）。决策见 [ADR 0008](../../docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md)。
> 来源：核实 smithy-typescript signature-v4 + openai-node v6.3.0 源码。**尚未端到端跑通——这是 spike 的任务。**

## 1. 代码（注入 Midscene `createOpenAIClient`）

```typescript
import OpenAI from "openai";
import { SignatureV4 } from "@aws-sdk/signature-v4";
import { HttpRequest } from "@aws-sdk/protocol-http";   // 漏这个 import = ReferenceError 崩溃（不是 403）
import { Sha256 } from "@aws-crypto/sha256-js";          // 传 CLASS，不是实例
import { fromNodeProviderChain } from "@aws-sdk/credential-providers";

const REGION = "us-east-1";   // 统一用 us-east-1：默认 region，且 AgentCore 会话 + qwen3-vl 200 均在此实测过
const HOST = `bedrock-runtime.${REGION}.amazonaws.com`;
const BASE_URL = `https://${HOST}/openai/v1`;            // 保持 /openai/v1（裸 /v1 会 404）

const signer = new SignatureV4({
  service: "bedrock",            // SigV4 service code 是 "bedrock"，不是 "bedrock-runtime"
  region: REGION,                // us-east-1

  credentials: fromNodeProviderChain(),  // 缓存+刷新；每次 .sign() 盖新 x-amz-date，自动避开 clock skew
  sha256: Sha256,
});

const sigv4Fetch: typeof fetch = async (input, init = {}) => {
  const urlStr = typeof input === "string" ? input : input.toString();
  const u = new URL(urlStr);
  const body = init.body as string | undefined;  // openai 已 JSON.stringify，原样透传，勿重新序列化

  // 关键：只签最小手建请求 { host, content-type }，绝不签 SDK 的整个 header 包。
  // 因为 smithy 会签请求对象上除固定 denylist 外的每个头，而 denylist 不含
  // content-length / x-stainless-* / accept-encoding —— 这些在 wire 上会被改 → 403 SignatureDoesNotMatch。
  const toSign = new HttpRequest({
    method: (init.method ?? "POST").toUpperCase(),
    protocol: u.protocol,
    hostname: u.hostname,
    path: u.pathname,                            // 签你真正 POST 的路径
    query: Object.fromEntries(u.searchParams),
    headers: { host: u.host, "content-type": "application/json" },  // host 必须手动设
    body,                                        // 精确字符串，SignatureV4 自己算 SHA256
  });
  const signed = await signer.sign(toSign);      // 别预设 x-amz-content-sha256，让 signer 加

  const headers = new Headers(init.headers);
  headers.delete("authorization");               // 删掉 openai 的 `Bearer unused`（冲突）
  headers.delete("content-length");              // 删掉，让 undici 重算
  for (const [k, v] of Object.entries(signed.headers)) headers.set(k, v);

  return fetch(urlStr, { method: toSign.method, headers, body, ...(init.signal ? { signal: init.signal } : {}) });
};

export const createOpenAIClient = (BaseOpenAI: typeof OpenAI) =>
  new BaseOpenAI({ baseURL: BASE_URL, apiKey: "unused", fetch: sigv4Fetch });

// 请求体携带 model id（路径里不放、不用 inference-profile ARN）：
//   { model: "qwen.qwen3-vl-235b-a22b", messages: [...] }   ← bare id, ON_DEMAND, us-east-1
// 坑：bedrock-mantle/quickstart 示例用 "...-instruct" 后缀；bedrock-runtime 用裸 id。抄错 → 400/404（非 403）。
```

## 2. npm 依赖

```
npm i @aws-sdk/signature-v4 @aws-sdk/protocol-http @aws-crypto/sha256-js @aws-sdk/credential-providers
```
（`openai` v6.3.0 已在；4 个 AWS 包经核实仓库里都没有，须装。）

## 3. 失败模式表

| 症状 | 原因 | 修 |
|---|---|---|
| **403 SignatureDoesNotMatch** | **过度签名易变头**（头号坑）：签了 SDK 整个 header 包，`x-stainless-retry-count`(重试 0→1)/`content-length`/`accept-encoding` 进了 SignedHeaders 又在 wire 上被改 | 只签手建 `{host, content-type}`，绝不快照+签 SDK 头 |
| 403 | host 签成裸 hostname 但走了非 443 端口/代理 | baseURL host 不带端口；有端口则签 `u.host` |
| 403 | signer region ≠ host region；或 sign 与 send 之间 body 被重新序列化；或复用了过期签名 | region 对齐；body 原样透传；每请求重签（别缓存 `signed`） |
| 403 auth 混乱 | openai 的 `Bearer unused` 没删掉 | 先 `headers.delete("authorization")` |
| **400 ValidationException** | 签名 OK 但 payload 错：model id 错、`-instruct` 后缀错、字段不支持 | 用裸 `qwen.qwen3-vl-235b-a22b`，无 profile ARN |
| 404 | 路径面错（`/v1` vs `/openai/v1`）或模型不在该 region | 保持 `/openai/v1`；确认 qwen3-vl 在 us-east-1 |
| `ReferenceError: HttpRequest is not defined` | 漏 import | 加 `@aws-sdk/protocol-http` |

## 4. 首跑最可能的失败 + 最快诊断

最可能：若有人"简化"成签 SDK 整个 header 包 → 403。诊断：Bedrock 403 响应体会回显它算的 `CanonicalRequest`/`SignedHeaders`，与 wire 上实际头一 diff 即见元凶。runner-up：漏 `HttpRequest` import（ReferenceError）或 4 个 AWS 包没装。

## 5. 账号实测结论（2026-06-23，本账号 SigV4 直发，已坐实路径/model-id）

| 测试 | 结果 | 结论 |
|---|---|---|
| `/openai/v1` + 裸 `qwen.qwen3-vl-235b-a22b` + 文本 | **HTTP 200 `'ok'`** | ✅ 路径用 `/openai/v1`、用裸 id |
| 同上 + image_url | 400 "Failed to sanitize image: unsupported image" | ⚠️ 端点**认 image_url 字段**、走到图像解析；400 是因为测试用的 1x1 占位图不合格，非接口问题 |
| `-instruct` 后缀 | 400 "model identifier is invalid" | ✅ **不要** `-instruct` |
| 裸 `/v1` | 无 `choices`（不走） | ✅ 必须 `/openai/v1` |

→ 路径/model-id 不再是"最低置信"，已实证。

## 6. TS 端到端实测（2026-06-23，`midscene/spikes/01-model-sigv4.ts`）—— 已全绿

用 openai-node v6.3.0 + 本配方的 `sigv4Fetch`，在本账号实跑：
- **[01a] 文本** → `"ok"`（HTTP 200）：TS SigV4 自签**字节匹配正确**，最小手建请求签名法有效，`Bearer unused` 删除有效，混版本 SigV4 包（3.370.0 / 3.1074.0）无兼容问题。**一次过，未撞 403。**
- **[01b] 视觉**（64x64 真实 PNG，左红右蓝）→ `"Red Blue"`：image_url 经 SigV4 **过了 Bedrock 图像 sanitize**（此前 1x1 占位图 400 确认只是图不合格）；qwen3-vl 真能看图识别；openai-node 多模态 content 数组被接受。

→ ADR 0008「TS SigV4 字节匹配」与 ADR 0003「视觉成功应答待实证」两个承重未知**均已关闭**。

## 7. 合体实测（第 3 段，`03-midscene-grounding.ts`）—— 全通

整条 Midscene 腿端到端跑通（AgentCore 云端浏览器 + SigV4 自签 + 维基用例）：
- `aiAct("搜 OpenAI 并提交")` → 真进到 `https://en.wikipedia.org/wiki/OpenAI`（58.9s，含规划+定位+多步动作）
- A 确定性断言（url 含 `/wiki/OpenAI`）：pass
- B AI 断言（`aiAssert`）×10：**10/10 pass，抖动率 0%，与 A 完全一致**，平均 10.45s/次
- `report.html` 正常生成；真实整页截图过 Bedrock 图像 sanitize（无 400）

### ⚠️ 关键坑（实跑才挖出，配方原文没有）：createOpenAIClient → 隔离 ModelConfigManager

源码 `@midscene/core agent.js:852-853`：
```js
const hasCustomConfig = opts?.modelConfig || opts?.createOpenAIClient;
this.modelConfigManager = hasCustomConfig
  ? new ModelConfigManager(opts?.modelConfig, opts?.createOpenAIClient)  // 隔离模式
  : globalModelConfigManager;                                            // 吃 overrideAIConfig/env
```
**一旦给 Agent 传 `createOpenAIClient`，它切到隔离 ModelConfigManager，只读 `opts.modelConfig`，完全无视 `overrideAIConfig` 和全局 env。** 因此模型配置必须随 `opts.modelConfig` 一起给：
```ts
new PlaywrightAgent(page, {
  modelConfig: { MIDSCENE_MODEL_NAME, MIDSCENE_MODEL_BASE_URL, MIDSCENE_MODEL_API_KEY: "unused", MIDSCENE_USE_QWEN3_VL: "true" },
  createOpenAIClient: async () => new OpenAI({ baseURL, apiKey: "unused", fetch: sigv4Fetch }),
});
```
否则报 `Model configuration is incomplete: MIDSCENE_MODEL_NAME is required`。
另注：`process.env.MIDSCENE_*` 在 import 后再设无效（GlobalConfigManager import 时已缓存）；`aiAction` 已废弃，用 `aiAct`。

### 剩余
- `@aws-sdk/signature-v4` 版本未 pin（已实测当前装入版本可用）。
