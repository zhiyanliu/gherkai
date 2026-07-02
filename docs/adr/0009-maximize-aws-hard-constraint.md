# 最大化使用 AWS 是不可谈判的硬前提

> **Status:** Accepted

整个框架的所有技术选型——模型托管、浏览器层、鉴权、未来的编排——都必须**优先落在 AWS 之内**（Bedrock / AgentCore / SageMaker / IAM 等）。这是项目的硬约束，不是可权衡的偏好。

**决定**：当某个能力在 AWS 内有可用方案时，即采用 AWS 方案，**即使 AWS 外存在质量/便利性更好的替代**。离开 AWS 的方案只有在「AWS 内确实无任何可行选项」时才进入考虑，且需另立 ADR 显式记录为对本约束的例外。

**已据此约束做出的选择**：
- [0003](./0003-midscene-grounding-qwen3vl-bedrock.md)：Midscene 大脑选 Bedrock 上的 Qwen3-VL，而非 AWS 外的模型。
- [0004](./0004-novaact-iam-auth-via-workflow.md) / [0008](./0008-midscene-bedrock-auth-sigv4-selfsign.md)：两个引擎统一走 IAM/SigV4，不引入额外凭证体系。
- [0003](./0003-midscene-grounding-qwen3vl-bedrock.md) 的被排除项：AWS 外的 VL 模型（Doubao、gemini 等）即便定位质量可能更好，也因在 AWS 外而不选。（注：gpt-5.5 的排除是另一回事——它在 Bedrock 内，但不支持 chat-completions，见 [0002](./0002-midscene-not-driven-by-gpt55.md)，与本 AWS 约束无关。）

**明确的非目标**：即便将来 spike 实测发现 AWS 内方案（如 Qwen3-VL 英文定位质量）不如 AWS 外方案，**也不以「离开 AWS」作为默认出路**；应优先在 AWS 内寻找改进（换 Bedrock 上其他模型、自托管于 SageMaker、调 grounding 策略等）。
