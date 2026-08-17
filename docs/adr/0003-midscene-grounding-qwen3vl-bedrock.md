# Midscene 主力视觉定位模型用 Bedrock 上的 Qwen3-VL

> **Status:** Accepted

承接 [0002](./0002-midscene-not-driven-by-gpt55.md)：Midscene 的主力 grounding 大脑选 **Qwen3-VL 235B**（`qwen.qwen3-vl-235b-a22b`），托管在 **AWS Bedrock 原生**（serverless ON_DEMAND，在 `us-east-1`/`us-west-2` 均可用）。（**planning 也复用此模型、不引独立文本规划器**——见 [0012](./0012-planning-shares-qwen3vl-no-text-planner.md)。）**spike/实测阶段主要用 `us-east-1`**（AgentCore 会话 + 后续全链路 spike 在此，见 [0008](./0008-midscene-bedrock-auth-sigv4-selfsign.md) 06-23 全通）；**唯 qwen3-vl chat-completions 的最初协议坐实在 `us-west-2`**（06-22，见下方历史实测记录）——两 region 都验过、模型两区均可用。**region 现已全可配、无硬编码默认**（`--region` > `AWS_REGION` > `AWS_DEFAULT_REGION` > profile config，全 miss 则 fail-loud、不兜 east——见 [0016](./0016-execution-architecture-core-lib-run-model.md) 决策 C / [0033](./0033-iac-aws-backend-and-composition-wiring.md)）。

**为什么是它**：经实测发包确认，它在 `bedrock-runtime.{region}.amazonaws.com/openai/v1/chat/completions` 上以 OpenAI **chat-completions** 协议返回真实**文本**应答（HTTP 200），且 **image_url 字段被端点接受并进入图像解析**——而 Midscene 的 service-caller 硬走 `openai.chat.completions.create`、无任何 Responses 代码路径。这是它与 GPT-5.5 的决定性区别：协议对得上、接受图像输入、可被 Midscene 直接驱动。它是唯一同时满足「开源 / chat-completions / AWS 托管」三项硬约束的选项。（被测 UI 的语言不进本选型的约束集：语言弱项属具体大脑而非框架，见 [0001](./0001-scope-limited-to-english-ui.md)「非英文的真实边界」。）
> 注：视觉通道「字段被接受」≠「已用合格图片拿到成功视觉应答」——后者尚未实证（测试用的占位图被图像 sanitize 拒为 400），是 spike 第一锤要坐实的。见下「未实测项」。

**被排除的替代**：Qwen2.5-VL、UI-TARS（非 Bedrock 原生，且 UI-TARS 被 Midscene 官方不推荐作默认）；Doubao（AWS 上没有）；Bedrock 上的 GLM（仅文本，不能 grounding）；gemini-3.5-flash（闭源、非 AWS）。

**接线要点（与文档/直觉相悖，务必照抄）**：
- 路径用 `bedrock-runtime` 的 `/openai/v1`，**不是**裸 `/v1`，**不是** `bedrock-mantle`。
- `MIDSCENE_USE_QWEN3_VL=true`（等价于 modelFamily=qwen3-vl；代码与 `SIGV4-FETCH-RECIPE.md` 实际用的是这个 legacy 开关，非 `MIDSCENE_MODEL_FAMILY`）。
- gpt-5.5 连可选 planner 都当不了（Midscene 无 Responses 路径），**直接弃用**，别留在任何 `MIDSCENE_*_MODEL_*` 槽位。

**已在本账号实测（2026-06-22）**：用 IAM/SigV4 凭证向 `bedrock-runtime.us-west-2.amazonaws.com/openai/v1/chat/completions` 发真实请求，`qwen.qwen3-vl-235b-a22b` 返回 HTTP 200。证实：模型访问已授予、chat-completions 协议可用、在本账号 region 可达。

**鉴权方式**：上述实测走的是 SigV4。Midscene 经 `createOpenAIClient` 自签 SigV4 接入（不用 bearer key），详见 [0008](./0008-midscene-bedrock-auth-sigv4-selfsign.md)；接线配方与账号实测见 `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md`。

**未实测项**：Qwen3-VL 的逐像素定位质量（仅属推断，须 spike 实测；与 UI 语言正交——中文页面单次真跑已通过，见 [0001](./0001-scope-limited-to-english-ui.md)「非英文的真实边界」）；235B MoE 的成本/延迟/配额。若 spike 实测定位质量不达标，按 [0009](./0009-maximize-aws-hard-constraint.md) 在 **AWS 内**寻找改进（换 Bedrock 其他 VL 模型 / SageMaker 自托管 / 调 grounding 策略），**不**以离开 AWS 为出路。
