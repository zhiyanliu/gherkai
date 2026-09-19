# 最大化使用 AWS 是不可谈判的硬前提

> **Status:** Accepted

整个工具的所有技术选型——模型托管、浏览器层、鉴权、未来的编排——都必须**优先落在 AWS 之内**（Bedrock / AgentCore / SageMaker / IAM 等）。这是项目的硬约束，不是可权衡的偏好。

**决定**：当某个能力在 AWS 内有可用方案时，即采用 AWS 方案，**即使 AWS 外存在质量/便利性更好的替代**。离开 AWS 的方案只有在「AWS 内确实无任何可行选项」时才进入考虑，且需另立 ADR 显式记录为对本约束的例外。

**适用面** = 交付物的**运行栈**（模型托管 / 浏览器层 / 鉴权 / 存储 / 编排，即上文列举的轴）。contributor 侧的源码托管与 CI、发布方侧的包索引与镜像 registry（GitHub / PyPI / npm / GHCR，见 [0037](./0037-distribution-and-packaging.md) 决策 5、8）是发布通道、不在其内——运行期真正被拉起的 worker 镜像仍在使用方私有 ECR（[0038](./0038-worker-image-delivery.md)）。发布通道放 AWS 外不是例外、不进下面的例外清单。

**已据此约束做出的选择**：
- [0003](./0003-midscene-grounding-qwen3vl-bedrock.md) / [0044](./0044-engine-model-selection-and-override.md)：Midscene 的引擎模型在 Bedrock 内选（原默认 Qwen3-VL，2026-09 评测集 A/B 后改为 `us.openai.gpt-5.6-terra`），而非 AWS 外的模型。引擎默认模型的候选集同受本约束界定（[0044](./0044-engine-model-selection-and-override.md) 决策 3：只用 Bedrock OpenAI 兼容端点调得到的模型）。
- [0004](./0004-novaact-iam-auth-via-workflow.md) / [0008](./0008-midscene-bedrock-auth-sigv4-selfsign.md)：两个引擎统一走 IAM/SigV4，不引入额外凭证体系。
- [0003](./0003-midscene-grounding-qwen3vl-bedrock.md) 的被排除项：AWS 外的 VL 模型（Doubao、gemini 等）即便定位质量可能更好，也因在 AWS 外而不选。（注：gpt-5.5 的排除是另一回事——它在 Bedrock 内，但不支持 chat-completions，见 [0002](./0002-midscene-not-driven-by-gpt55.md)，与本 AWS 约束无关。）
- [0012](./0012-planning-shares-qwen3vl-no-text-planner.md)：planning 角色由 Midscene 的引擎模型兼任（现值见 [0044](./0044-engine-model-selection-and-override.md)），不引入 AWS 外的多模态推理模型作独立 planner（当年依据是「AWS 内『chat-completions + 收图像』的选项只有 VL 模型」；2026-09 实查该集合已扩到 GPT-5.6 / GPT-6 / Kimi，但仍全在 Bedrock 内——离开 AWS 才有的选项按本约束不取，属需另立 ADR 的破例）。

**已记录的例外**（按上「决定」段的登记要求）：
- [0035](./0035-local-app-testing-via-tunnel.md)：本地应用测试的出站隧道用 ngrok（AWS 外 SaaS）——「开发机 → 云端浏览器」的入站通道在 AWS 内实查无等价物（SSM 端口转发方向相反；IoT Secure Tunneling 两端 localproxy、不产公网 URL；AgentCore Browser VPC 模式够不到开发者笔记本，已评估并缓），满足本约束的「AWS 内确实无任何可行选项」条件。例外面被压到最小：经可插拔 `TunnelProvider` 口子隔离、仅 `--expose-local` 显式启用、数据面只有被测应用自身流量——模型/浏览器/存储/编排仍全在 AWS 内。

**明确的非目标**：即便将来 spike 实测发现 AWS 内方案（如 Qwen3-VL 英文定位质量）不如 AWS 外方案，**也不以「离开 AWS」作为默认出路**；应优先在 AWS 内寻找改进（换 Bedrock 上其他模型、自托管于 SageMaker、调 grounding 策略等）。
