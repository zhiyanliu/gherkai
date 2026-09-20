# Planning 角色用 Qwen3-VL 兼任，不引入独立纯文本 planner

> **Status:** Partially-superseded-by 0044 ——结论存：不设独立 planner 槽、由引擎模型兼任与两集合不相交的理由；立场变：兼任者不再是 Qwen3-VL、现值由 [0044](./0044-engine-model-selection-and-override.md) 定；「何时重议」第一条已于 2026-09 满足并重新评估，结论仍是不拆。

Midscene 的 planning（把高层意图拆解成动作步骤）角色，**继续用与 grounding 相同的引擎模型**（成文时为 Qwen3-VL，现值见 [0044](./0044-engine-model-selection-and-override.md)），不配置独立的 `MIDSCENE_PLANNING_MODEL_*`。

## 为什么不是"用一个强推理纯文本模型做 planner"（实测推翻的直觉）

最初设想：planning 不需要视觉，可挑一个 Bedrock 上推理强的纯文本模型（性价比更高）。**实测证伪**（2026-06-23，本账号）：

1. **Midscene 的 planning 调用无条件附带截图**（`image_url`），且**没有任何 env/config 能关闭**。逐行核实源码确认（2026-06 首验 `@midscene/core` 1.9.8，装机版 1.12.8 复核仍成立）：planning 工作流（`ai-model/workflows/planning/standard-planning.mjs`）在两个消息分支都无条件附 `{type:'image_url'}`，`includeLocateInPlanning=false` 不去图、只改 system prompt 与定位解析；无纯文本 planning 代码路径；官方文档亦明示 planner 需 multimodal 模型。
2. **Bedrock 上所有走 chat-completions 的强推理纯文本模型都拒图像**。实测：`deepseek.v3.2` / `openai.gpt-oss-120b` / `qwen.qwen3-32b` / `qwen.qwen3-next-80b-a3b` 收到 `image_url` 均返回 `400 "Model does not support image modality"`（纯文本调用则 200）。Claude 系（claude-sonnet-4-6 等）干脆不在 `/openai/v1` chat-completions 面上（404）。

**两个集合不相交**：能被 Midscene 调用（chat-completions + 收图像）的 Bedrock 模型 = 只有 VL 模型（2026-06 的真值；2026-09 起 Bedrock 上的多模态推理模型如 GPT-5.6 / GPT-6 也能经同一接线收发图文，见 [0044](./0044-engine-model-selection-and-override.md) 背景 2）。强推理纯文本模型全部出局。

## 决定

- planning **复用同一个引擎模型**（本 ADR 成文时为 `qwen.qwen3-vl-235b-a22b`，现值见 [0044](./0044-engine-model-selection-and-override.md)），即不设 `MIDSCENE_PLANNING_MODEL_*`，让 default/grounding 模型兼任 planning。这是 AWS 约束 + Midscene 约束下唯一"既可达又收图"的务实解。
- 不引入独立 planner：纯文本模型会被拒图像；另找一个 Bedrock VL 模型做 planner 无实际增益（见 ADR 0003 的 VL 选型，Bedrock 上可用的 chat-completions VL 选项很窄）。

## 何时重议

- 若 Bedrock 将来开放强推理模型的 chat-completions + 图像输入（如某个推理模型加视觉），可重新评估"独立 planner 提升规划质量"。
- 若放弃 AWS 约束（ADR 0009），AWS 外的多模态推理模型（如 OpenAI 原生 gpt-5.x，多模态 + chat-completions）可作 planner——但这是对 [0009](./0009-maximize-aws-hard-constraint.md) 的破例，需另立 ADR。

**这两条的前提已在 2026-09 变化**（见 [0044](./0044-engine-model-selection-and-override.md) 背景 2）：Bedrock 上的多模态推理模型（GPT-5.6 / GPT-6）已可经现有接线收发图文——第一条的条件由此满足，默认模型本身即多模态推理模型，是否拆独立 planner 经此重新评估、结论仍是不拆（见上 Status 头）；第二条举的那类模型（2026-06 的例子是「OpenAI 原生 gpt-5.x」）也不再需要离开 AWS，本条只剩「AWS 外独有的模型」这一射程。

**不拆的理由**：独立 planner 会多一个模型槽与一处可漂的配置面，与 [0044](./0044-engine-model-selection-and-override.md) 决策 2「覆盖项 = worker 侧 env，两引擎对称」的对称性冲突；当前默认模型在评测集 A/B 里逐遍稳定、无可观测的规划质量缺口作驱动。

## 探针

`engines/midscene/spikes/04-planning-probe.ts`：验证任一候选的 (a) chat-completions 可达 + (b) image_url 容忍两关。当前所有纯文本候选卡在 (b)。
