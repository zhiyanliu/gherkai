# Midscene 调 Bedrock 的 SigV4 自签：签什么、不签什么、怎么排障

> 本文讲**进程内 SigV4 自签这条链路如何工作、哪些细节决定它能不能过签名校验**（机制），不讨论为什么选自签而不用 bearer key：决策与理由在 [ADR 0008](../adr/0008-midscene-bedrock-auth-sigv4-selfsign.md)，模型与家族的取值在 [ADR 0044](../adr/0044-engine-model-selection-and-override.md)；实现在 `engines/midscene/src/lib/agentcore-sigv4.mts`，与代码或 ADR 不一致时以它们为准。本文的价值在失败模式表：签名错误的症状彼此相似（多数是 403），只凭症状很难反推原因。

## 1. 链路一句话

Midscene 的 `createOpenAIClient` 回调把一个带自定义 `fetch` 的 OpenAI client 交给 SDK；该 `fetch` 对每个请求用 AWS 默认凭证链做 SigV4 签名（service 名 `bedrock`，region 来自 `AWS_REGION`），再原样发往 `https://bedrock-runtime.<region>.amazonaws.com/openai/v1`。模型配置随 `modelConfig` 一起给进 Agent，使 SDK 落在隔离的模型配置管理器上、不读全局 env（细节与版本差异见 ADR 0008「关键实现坑」）。

## 2. 签名契约：五条决定成败的细节

1. **只签手建的最小请求**：方法、协议、主机、路径、查询串、`host` 与 `content-type` 两个头、请求体。不要把 SDK 请求对象上的全部头拿去签——签名库会签除固定黑名单之外的每个头，而 `content-length`、`accept-encoding`、`x-stainless-*`（SDK 的重试计数会从 0 变 1）不在黑名单里、又会在线路上被改，签进去必得 403。
2. **请求体原样透传**：SDK 已经序列化成字符串，签名按这个字符串算哈希；签完再改一个字节即失配。要改请求体（见第 4 条）必须在签名之前。
3. **每个请求重签**：签名含时间戳，缓存签好的头会在几分钟后失效；凭证提供者自带缓存与刷新，不必自己管。
4. **签名前改体**：Bedrock 的 OpenAI 兼容层不认 `image_url.detail: "original"`，而 Midscene 的 GPT 家族适配器固定发它，所以在签名前从请求体删掉这个字段（ADR 0044 决策 3）。
5. **发送前改头**：删掉 SDK 用占位 key 设的 `Authorization: Bearer …`（与 SigV4 的 Authorization 冲突），删掉 `content-length` 让 HTTP 客户端重算，再把签名库给出的头合并进去。

模型 id 放请求体，不放路径、不用 inference profile ARN；GPT 系列用带 `us.` / `global.` 前缀的 inference profile id（ADR 0044）。

## 3. 失败模式表

| 症状 | 原因 | 处置 |
|---|---|---|
| 403 SignatureDoesNotMatch | 签了会被改动的头（第 2 节第 1 条，最常见） | 只签手建的最小请求；对照响应体回显的 CanonicalRequest 与 SignedHeaders，与线路上实际的头做差 |
| 403 | `host` 签成裸主机名但请求带了端口或走了代理 | 签 URL 对象的 `host`（含端口），baseURL 不带端口 |
| 403 | 签名 region 与主机 region 不一致；签完后请求体被重新序列化；复用了过期签名 | region 对齐；请求体原样透传；每请求重签 |
| 403 且鉴权头混乱 | SDK 的 `Bearer unused` 没删 | 合并签名头前先删 `authorization` |
| 400 ValidationException「model identifier is invalid」 | 模型 id 错（含旧 Qwen id 的 `-instruct` 后缀） | 用 ADR 0044 列出的现值 |
| 400「value did not match any expected variant」 | 请求体带了 `image_url.detail: "original"` | 签名前删字段 |
| 404 | 路径用了 `/v1` 而不是 `/openai/v1`；或模型不在该 region | 保持 `/openai/v1`；核模型在 region 的可用性 |
| `ReferenceError: HttpRequest is not defined` | 漏了 `@aws-sdk/protocol-http` 的 import | 补 import；这是崩溃不是鉴权失败 |
| `Model configuration is incomplete` | 模型配置没有随 `modelConfig` 给进 Agent，隔离态不读 env | 按 ADR 0008 把模型名与家族随 `modelConfig` 给 |

首次接线最可能遇到的是第一行：若有人把签名「简化」成签 SDK 的整个头包，一定 403。Bedrock 的 403 响应体会回显它算出的 CanonicalRequest，与线路上实际发出的头逐项对照即可定位。

## 4. 依赖与自检

签名链用到 `@aws-sdk/signature-v4`、`@aws-sdk/protocol-http`、`@aws-crypto/sha256-js`、`@aws-sdk/credential-providers` 与 `openai`，版本以 `engines/midscene/package.json` 为准（这几个包有意不钉精确版本，只两个引擎 SDK 钉精确版本，见 ADR 0042 决策六）。从零接线或换环境时，先用 `engines/midscene/spikes/01-model-sigv4.ts` 单独核模型连接，再用 `03-midscene-grounding.ts` 核 Midscene 整条链（运行方式见 `engines/midscene/DEVELOPMENT.md`）。

## 延伸阅读

- [`architecture-overview.md`](./architecture-overview.md)：这条链在 Midscene worker 里的位置。
- [ADR 0008](../adr/0008-midscene-bedrock-auth-sigv4-selfsign.md)：为什么自签而不用 bearer，以及已关闭的承重未知。
- [ADR 0044](../adr/0044-engine-model-selection-and-override.md)：模型 id、家族与覆盖链。
