# Midscene→Bedrock 鉴权：统一走 SigV4 自签（进程内），不用 bearer key

> **Status:** Accepted

承接 [0003](./0003-midscene-grounding-qwen3vl-bedrock.md)。两个引擎统一在纯 SigV4 / IAM 上，**不引入任何长期或短期 bearer key**。

经核实 `@midscene/core` 源码（首验 1.9.8，装机版 1.12.8 复核仍成立）：Midscene 有公开、带类型的逃生舱 **`createOpenAIClient`**，service-caller 会采纳你返回的 OpenAI client（`service-caller/openai-client.mjs` 的 `createAndWrapClient`，采纳返回值那段），底层 OpenAI SDK v6.3.0 支持自定义 `fetch`。`fetch` 能拿到每次请求的 method+url+headers+body——足以在进程内自签 AWS SigV4。因此「Midscene 只能发静态 bearer」这一限制只对 env-var 路径成立，代码路径下可自签。

**决定**：
- **必须用代码初始化 Agent**（不能纯靠 env-var）：Midscene 经 `createOpenAIClient` 返回一个 OpenAI client，其自定义 `fetch` 用 `@aws-sdk/signature-v4` + 默认凭证链对请求做 SigV4 签名（service `bedrock`，region 由注入的 `AWS_REGION` 决定——`getRegion()`/`getBaseUrl()` 惰性读、不硬编码 east，见 [0033](./0033-iac-aws-backend-and-composition-wiring.md)；base URL = `bedrock-runtime.<region>.amazonaws.com/openai/v1`。spike 当时用 `us-east-1`）。**SigV4 fetch 只能代码注入——env-var 路径（`MIDSCENE_MODEL_INIT_CONFIG_JSON` 的静态 headers）无法做逐请求签名。** **两套 SigV4 场景独立**：CDP endpoint 的 upgrade 请求签 service `bedrock-agentcore`（GET、无请求体、只手建 host；下「已实测」第 2 段），与这里的模型连接（service `bedrock`、POST 带体、只手建 host + content-type，`x-amz-date` 由 signer 补）是两套场景——凭证同走 AWS 默认链，但 signer 与签名代码各自一份、不可互用；签哪套由目标 endpoint 种类决定，AgentCore 浏览器会话与 endpoint 种类是两件事。
- 自签 fetch 顺带吸收 Bedrock 兼容层的方言：签名前去掉请求体里 `image_url.detail: "original"`（Midscene 的 GPT family 适配器固定发它、Bedrock 对任何模型都拒；[0044](./0044-engine-model-selection-and-override.md) 决策 3）。改体必须在签名**之前**（签名含 payload hash）。
- 模型名/family 也必须随 `opts.modelConfig` 进代码、**不能靠 env**：`MIDSCENE_MODEL_NAME` 与家族键（spike 期是 `MIDSCENE_MODEL_NAME=qwen.qwen3-vl-235b-a22b` + qwen3-vl 的 legacy 开关 `MIDSCENE_USE_QWEN3_VL=true`；现值与家族推断见 [0044](./0044-engine-model-selection-and-override.md) 决策 2，该 legacy 开关已列入其被拒方案）。虽是静态值、看着 env 能承载，但我们经 `opts.modelConfig` 给配置即让 Agent 切隔离 ModelConfigManager（隔离态不读 env，详见下「关键实现坑」），故上面「必须用代码初始化 Agent」这条不只管 fetch/鉴权，模型配置一并进代码。（[0044](./0044-engine-model-selection-and-override.md) 的 `MIDSCENE_MODEL_ID` / `MIDSCENE_MODEL_FAMILY` 是**我们的代码**读 env 后写进 `opts.modelConfig`，不是让 SDK 自己读 env，与本条不冲突。）
- 凭证走 AWS 默认链（本地档 = 开发机自身的 AWS 凭证；云端档 = 按引擎分立的 Fargate task role，见 [0033](./0033-iac-aws-backend-and-composition-wiring.md)「IAM 最小权限」；两档都已实测默认链可解析）。**零长期/短期 bearer key。**
- **spike 与生产同路**——不再走「spike 先用兜底 key」。

**为什么这个选择更稳（不只是更合心意）**：
- 端点侧 SigV4 已证绿——SigV4 + `/openai/v1` + 纯文本在本账号实测拿到正确回复（HTTP 200），且 image_url 字段被端点接受（见 [0003](./0003-midscene-grounding-qwen3vl-bedrock.md)）。注：0003 的证据止于文本应答与 image_url 字段被接受；合格图片的成功视觉应答由下节 spike 第 1 段坐实。
- 因此它**消除了 bearer 路那个最低置信的承重假设**（bearer 对 `/openai/v1`+vision 是否被接受、AWS 无文档）——根本不碰 bearer。
- 风险性质从「AWS 政策侧未知」变为「进程内 SigV4 fetch 接线是否字节级正确」——后者在我们掌控内。

**剩余风险（spike 第一锤要坐实）**：`createOpenAIClient` 的自定义 `fetch` 能否产出与 OpenAI SDK 序列化字节一致、且满足 Bedrock 签名头/body 预期的签名请求。要点：签 `init.body`（字符串本身、AS-IS hash）与 url；覆盖 SDK 用 dummy apiKey 设的 `Authorization` 头；只签最小规范头集（host/x-amz-date/content-type），避免对会被改动的易变头过度签名导致签名不符；处理凭证刷新；确认 Midscene 是否请求流式响应（SigV4 签的是请求，不影响响应流式）。

**退路（Option B，仅当自签 fetch 太脆时启用）**：本地跑 `aws-samples/bedrock-access-gateway`，它以 boto3 默认链（纯 IAM）签名转发、把 OpenAI `image_url`→Converse 图块；Midscene 指向 `http://localhost:<port>/v1` 配 dummy bearer。须先在账号+region 开通 `qwen.qwen3-vl-235b-a22b`（ON_DEMAND）否则网关返回 400。

## ✅ 已实测全通（2026-06-23，`engines/midscene/spikes/`）

三段式自检全绿，本 ADR 的承重未知**已关闭**：
- 第 1 段（模型连接）：openai-node + sigv4Fetch 调 qwen3-vl，文本 `"ok"` + 视觉 `"Red Blue"`，**一次过未撞 403**——SigV4 字节匹配正确。
- 第 2 段（浏览器连接/CDP）：`StartBrowserSession` + SigV4 签 upgrade（service `bedrock-agentcore`）+ Playwright `connectOverCDP` 连上云端浏览器、导航维基。
- 第 3 段（合体）：Midscene 经 `createOpenAIClient` 注入 sigv4Fetch，在 AgentCore 云端浏览器跑通 `aiAct` + 断言，出 `report.html`。
- **关键实现坑**（配方笔记 §7）：给 `opts.modelConfig` 即切隔离 ModelConfigManager——隔离态只读该对象、不读 `overrideAIConfig`/env，故模型配置必须随它一起给。（1.9.8 时给 `createOpenAIClient` 或 `modelConfig` 任一即切隔离；1.12.8 起只给前者会用 `AgentScopedModelConfigManager` 包住全局管理器、仍读 env——本项目两者都给，落在隔离支。）
