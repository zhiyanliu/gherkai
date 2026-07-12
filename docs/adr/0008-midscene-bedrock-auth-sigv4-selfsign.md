# Midscene→Bedrock 鉴权：统一走 SigV4 自签（进程内），不用 bearer key

> **Status:** Accepted

承接 [0003](./0003-midscene-grounding-qwen3vl-bedrock.md)。两个引擎统一在纯 SigV4 / IAM 上，**不引入任何长期或短期 bearer key**。

经核实 `@midscene/core 1.9.8` 源码：Midscene 有公开、带类型的逃生舱 **`createOpenAIClient`**，service-caller 会采纳你返回的 OpenAI client（`service-caller/index.mjs:154-157`），底层 OpenAI SDK v6.3.0 支持自定义 `fetch`。`fetch` 能拿到每次请求的 method+url+headers+body——足以在进程内自签 AWS SigV4。因此「Midscene 只能发静态 bearer」这一限制只对 env-var 路径成立，代码路径下可自签。

**决定**：
- **必须用代码初始化 Agent**（不能纯靠 env-var）：Midscene 经 `createOpenAIClient` 返回一个 OpenAI client，其自定义 `fetch` 用 `@aws-sdk/signature-v4` + 默认凭证链对请求做 SigV4 签名（service `bedrock`，region 由注入的 `AWS_REGION` 决定——`getRegion()`/`getBaseUrl()` 惰性读、不硬编码 east，见 [0033](./0033-iac-aws-backend-and-composition-wiring.md)；base URL = `bedrock-runtime.<region>.amazonaws.com/openai/v1`。spike 当时用 `us-east-1`）。**SigV4 fetch 只能代码注入——env-var 路径（`MIDSCENE_MODEL_INIT_CONFIG_JSON` 的静态 headers）无法做逐请求签名。**
- 模型名/family 仍可经 env 配：`MIDSCENE_MODEL_NAME=qwen.qwen3-vl-235b-a22b`、`MIDSCENE_USE_QWEN3_VL=true`（承载 qwen3-vl family 的 legacy 开关，实际 MODEL_CONFIG 与 `SIGV4-FETCH-RECIPE.md` 用的是它；这两个是静态值，env 可承载；只有 fetch/鉴权必须代码）。
- 凭证走 AWS 默认链（本机 IAM user `zhiyan` 的静态密钥；已实测默认链可解析）。**零长期/短期 bearer key。**
- **spike 与生产同路**——不再走「spike 先用兜底 key」。

**为什么这个选择更稳（不只是更合心意）**：
- 端点侧 SigV4 已证绿——SigV4 + `/openai/v1` + 纯文本在本账号实测拿到正确回复（HTTP 200），且 image_url 字段被端点接受（见 [0003](./0003-midscene-grounding-qwen3vl-bedrock.md)）。注：合格图片的成功视觉应答尚未实证，留待 spike。
- 因此它**消除了 bearer 路那个最低置信的承重假设**（bearer 对 `/openai/v1`+vision 是否被接受、AWS 无文档）——根本不碰 bearer。
- 风险性质从「AWS 政策侧未知」变为「进程内 SigV4 fetch 接线是否字节级正确」——后者在我们掌控内。

**剩余风险（spike 第一锤要坐实）**：`createOpenAIClient` 的自定义 `fetch` 能否产出与 OpenAI SDK 序列化字节一致、且满足 Bedrock 签名头/body 预期的签名请求。要点：签 `init.body`（字符串本身、AS-IS hash）与 url；覆盖 SDK 用 dummy apiKey 设的 `Authorization` 头；只签最小规范头集（host/x-amz-date/content-type），避免对会被改动的易变头过度签名导致签名不符；处理凭证刷新；确认 Midscene 是否请求流式响应（SigV4 签的是请求，不影响响应流式）。

**退路（Option B，仅当自签 fetch 太脆时启用）**：本地跑 `aws-samples/bedrock-access-gateway`，它以 boto3 默认链（纯 IAM）签名转发、把 OpenAI `image_url`→Converse 图块；Midscene 指向 `http://localhost:<port>/v1` 配 dummy bearer。须先在账号+region 开通 `qwen.qwen3-vl-235b-a22b`（ON_DEMAND）否则网关返回 400。

**第一个实验**：写好 SigV4 fetch 后，跑一次真实 Midscene `aiTap`/`aiAssert`（本地琐碎页面），一次绿灯即坐实自签接线全链路可用。

## ✅ 已实测全通（2026-06-23，`engines/midscene/spikes/`）

三段式自检全绿，本 ADR 的承重未知**已关闭**：
- 第 1 段（模型连接）：openai-node + sigv4Fetch 调 qwen3-vl，文本 `"ok"` + 视觉 `"Red Blue"`，**一次过未撞 403**——SigV4 字节匹配正确。
- 第 2 段（浏览器连接/CDP）：`StartBrowserSession` + SigV4 签 upgrade（service `bedrock-agentcore`）+ Playwright `connectOverCDP` 连上云端浏览器、导航维基。
- 第 3 段（合体）：Midscene 经 `createOpenAIClient` 注入 sigv4Fetch，在 AgentCore 云端浏览器跑通 `aiAct` + 断言，出 `report.html`。
- **关键实现坑**（配方笔记 §7）：传 `createOpenAIClient` 会让 Agent 切隔离 ModelConfigManager，模型配置必须随 `opts.modelConfig` 一起给，不能靠 `overrideAIConfig`/env。
