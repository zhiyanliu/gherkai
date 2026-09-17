# Midscene 主力视觉定位模型用 Bedrock 上的 Qwen3-VL

> **Status:** Superseded-by 0044 ——2026-09 评测集 A/B 后 Midscene 默认改为 `us.openai.gpt-5.6-terra`（依据与成本 / 驻留取舍内联在 0044「现值」）；Qwen3-VL 留作 `MIDSCENE_MODEL_ID` 的可选模型，本文保留其选型历史与 Bedrock 侧机制事实。

承接 [0002](./0002-midscene-not-driven-by-gpt55.md)：Midscene 的主力 grounding 大脑选 **Qwen3-VL 235B**（`qwen.qwen3-vl-235b-a22b`），托管在 **AWS Bedrock 原生**（serverless ON_DEMAND，在 `us-east-1`/`us-west-2` 均可用）。（**planning 也复用此模型、不引独立文本规划器**——见 [0012](./0012-planning-shares-qwen3vl-no-text-planner.md)。）**spike/实测阶段主要用 `us-east-1`**（AgentCore 会话 + 后续全链路 spike 在此，见 [0008](./0008-midscene-bedrock-auth-sigv4-selfsign.md) 06-23 全通）；**唯 qwen3-vl chat-completions 的最初协议坐实在 `us-west-2`**（06-22，见下方历史实测记录）——两 region 都验过、模型两区均可用。**region 现已全可配、无硬编码默认**（`--region` > `AWS_REGION` > `AWS_DEFAULT_REGION` > profile config，全 miss 则 fail-loud、不兜 east——见 [0016](./0016-execution-architecture-core-lib-run-model.md) 决策 C / [0033](./0033-iac-aws-backend-and-composition-wiring.md)）。

**为什么是它**：经实测发包确认，它在 `bedrock-runtime.{region}.amazonaws.com/openai/v1/chat/completions` 上以 OpenAI **chat-completions** 协议返回真实**文本**应答（HTTP 200），且 **image_url 字段被端点接受并进入图像解析**——而 Midscene 的 service-caller 硬走 `openai.chat.completions.create`、无任何 Responses 代码路径。这是它与 GPT-5.5 的决定性区别：协议对得上、接受图像输入、可被 Midscene 直接驱动。它是唯一同时满足「开源 / chat-completions / AWS 托管」三项硬约束的选项。（被测 UI 的语言不进本选型的约束集：语言弱项属具体大脑而非框架，见 [0001](./0001-scope-limited-to-english-ui.md)「非英文的真实边界」。）
> 注：上述发包只坐实到「字段被接受」这一层——当时的占位图被图像 sanitize 拒为 400，未拿到成功视觉应答。**视觉通道此后已端到端真验**：wikipedia 用例动作成功 + AI 断言 10/10、零抖动（2026-06-23，AgentCore 云端，见 [0010](./0010-spike-as-apples-to-apples-benchmark.md) 对标表）；中文页面的视觉定位与文本断言亦通过（见 [0001](./0001-scope-limited-to-english-ui.md)「非英文的真实边界」）。

**被排除的替代**：Qwen2.5-VL、UI-TARS（非 Bedrock 原生，且 UI-TARS 被 Midscene 官方不推荐作默认）；Doubao（AWS 上没有）；Bedrock 上的 GLM（仅文本，不能 grounding）；gemini-3.5-flash（闭源、非 AWS）。

**接线要点（与文档/直觉相悖，务必照抄）**：
- 路径用 `bedrock-runtime` 的 `/openai/v1`，**不是**裸 `/v1`，**不是** `bedrock-mantle`。
- family `qwen3-vl`：代码经 `opts.modelConfig` 传 `MIDSCENE_MODEL_FAMILY`（按模型 id 推断或 env 显式给，[0044](./0044-engine-model-selection-and-override.md) 决策 2）；曾用 legacy 开关 `MIDSCENE_USE_QWEN3_VL=true`（`SIGV4-FETCH-RECIPE.md` 里仍是旧写法），两者在 SDK 内等价。
- gpt-5.5 连可选 planner 都当不了（Midscene 无 Responses 路径），**直接弃用**，别留在任何 `MIDSCENE_*_MODEL_*` 槽位。

**已在本账号实测（2026-06-22）**：用 IAM/SigV4 凭证向 `bedrock-runtime.us-west-2.amazonaws.com/openai/v1/chat/completions` 发真实请求，`qwen.qwen3-vl-235b-a22b` 返回 HTTP 200。证实：模型访问已授予、chat-completions 协议可用、在本账号 region 可达。

**鉴权方式**：上述实测走的是 SigV4。Midscene 经 `createOpenAIClient` 自签 SigV4 接入（不用 bearer key），详见 [0008](./0008-midscene-bedrock-auth-sigv4-selfsign.md)；接线配方与账号实测见 `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md`。

**未实测项**：Qwen3-VL 逐像素定位质量的**量化基准**（单次真跑已通过，但无 N 次抖动/精度数据；与 UI 语言正交——中文页面的动作步已 3 次独立跑 3/3、AI 断言 10 票 ×3 次一致，见 [0001](./0001-scope-limited-to-english-ui.md)「非英文的真实边界」；那组数据只到「动作成功 / 断言一致」层，同样没有逐像素定位精度基准）；235B MoE 的成本/配额。（延迟已有实证参照：[0010](./0010-spike-as-apples-to-apples-benchmark.md) 对标表记动作步端到端 58.9s、AI 断言平均 10.45s/次——含浏览器的墙钟口径。）若 spike 实测定位质量不达标，按 [0009](./0009-maximize-aws-hard-constraint.md) 在 **AWS 内**寻找改进（换 Bedrock 其他 VL 模型 / SageMaker 自托管 / 调 grounding 策略），**不**以离开 AWS 为出路。

**待观察（上游代际）**：Midscene 官方模型表已把 Qwen3-VL 整个 series 标为「旧版本模型，不推荐使用。建议优先使用 Qwen3.x 系列」（定位测评推荐序 Qwen3.7 > Qwen3.5 > Qwen3.6，基于其私有测评集）；但 Bedrock 实查（us-east-1/us-west-2，IMAGE modality）Qwen 视觉模型**有且仅有**本 ADR 所选 `qwen.qwen3-vl-235b-a22b`——[0009](./0009-maximize-aws-hard-constraint.md)「AWS 内托管」约束下 Qwen 系暂无升级路径，且装机版 @midscene/core 的 `qwen3-vl` 适配仍在（不推荐 ≠ 移除支持）。但 Bedrock 上另有 Midscene 支持的 family（2026-09 实查 GPT-6 Astra、GPT-5.6 经 inference profile、Kimi K2.5 都能经 chat-completions 收发图文），**是否换默认按 [0044](./0044-engine-model-selection-and-override.md) 决策 1 的评测集 A/B 定**；换默认 = 改 worker 侧 `DEFAULT_MODEL` 常量 + 改 IaC 里 `bedrock:InvokeModel` 的模型 ARN pin 并重新部署，使用方本机可经 env `MIDSCENE_MODEL_ID` 覆盖、云端还需部署侧放行（[0044](./0044-engine-model-selection-and-override.md) 决策 2）。
