# Midscene 的主力引擎模型不用 Bedrock GPT-5.5

> **Status:** Superseded-by 0044 ——Midscene 默认已改为 GPT-5.6 Terra（2026-09 评测集 A/B，见 0044「现值」）；核心事实已变：2026-09 实查 Bedrock 上 GPT-5.6 与 GPT-6 经 inference profile（如 `us.openai.gpt-6-astra`）支持 `/openai/v1/chat/completions` 且视觉通道可用（本文 2026-06 对 gpt-5.5 的结论对当时为真）；GPT 能否当 Midscene 主力 grounding 改由 [0044](./0044-engine-model-selection-and-override.md) 决策 1 的评测集 A/B 定——下文「次要理由」里的非拉丁文字定位弱项已由 0044 的 A/B 中文 UI 探针复核（GPT-5.6 三变体与 GPT-6 Astra 各 3/3，见 0044「Midscene 默认的选定依据」表）。

项目最初的原型指导文档（已退役）指定 Midscene 用 Bedrock 上的 OpenAI GPT-5.5 做引擎模型。经核实，此方案行不通，**放弃**。

## 核心事实（2026-06-23 本账号实测，AWS 直接报错坐实）

**Bedrock 上的 gpt-5.5 不支持 chat-completions API。** Midscene 只会调 chat-completions，故 gpt-5.5 无法驱动 Midscene。AWS 在 `bedrock-mantle` 端点直接返回：

```
POST https://bedrock-mantle.us-east-1.api.aws/v1/chat/completions
     {"model":"openai.gpt-5.5", ...}
-> 400  "The model 'openai.gpt-5.5' does not support the '/v1/chat/completions' API"
```

附带实测事实：
- gpt-5.5 在 mantle `models.list` 中**存在**（id `openai.gpt-5.5` / `openai.gpt-5.5-2026-04-23`），只在 **us-east-1**（us-west-2 仅有 gpt-5.4），但**不支持 chat-completions**——只能走 Responses API。
- `bedrock-runtime` 裸 `/v1/chat/completions` 对 gpt-5.5 返回 `UnknownOperationException`（一个 HTTP 200 但 body 是框架异常的假象，曾一度被误读为"通过"）。

> 诚实存档（本 ADR 的判断反复）：Responses-only → 中途误判为"支持 chat-completions"（被假 200 骗）→ 实测纠正回 **不支持 chat-completions**。用户最初的"Responses-only"判断是对的。教训：**只认响应 body，不认 HTTP 状态码**；web 核实 ≠ 账号实证。

## 次要理由（即便接口能通也不选它作主力 grounding）

GPT-5 系被 Midscene 官方点名对小字/非拉丁文字**视觉定位偏弱**（该弱项是 GPT-5 的 **per-model 属性**、非 Midscene 框架属性——换引擎模型即换该弱项，见 [0001](./0001-scope-limited-to-english-ui.md)「非英文的真实边界」），本就不适合当**主力 grounding** 角色（grounding 是 Midscene 引擎模型的核心职责）。

**决定**：Midscene 的主力视觉定位引擎模型改用走 chat-completions 的开源 VL 模型，托管在 AWS 上——即 Qwen3-VL on Bedrock（[0003](./0003-midscene-grounding-qwen3vl-bedrock.md)，已实测 chat-completions + 视觉通道可用）。gpt-5.5 因不支持 chat-completions 而**完全出局**，连可选 planning 角色都当不了（Midscene 无 Responses 代码路径）。
