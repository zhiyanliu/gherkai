# Planning 角色用 Qwen3-VL 兼任，不引入独立纯文本 planner

Midscene 的 planning（把高层意图拆解成动作步骤）角色，**继续用 grounding 同款的 Qwen3-VL**，不配置独立的 `MIDSCENE_PLANNING_MODEL_*`。

## 为什么不是"用一个强推理纯文本模型做 planner"（实测推翻的直觉）

最初设想：planning 不需要视觉，可挑一个 Bedrock 上推理强的纯文本模型（性价比更高）。**实测证伪**（2026-06-23，本账号）：

1. **Midscene 的 planning 调用无条件附带截图**（`image_url`），且**没有任何 env/config 能关闭**。逐行核实安装的 `@midscene/core@1.9.8` 源码确认：`llm-planning.js` 的 `plan()` 在两个消息分支都附 `{type:'image_url'}`，`includeLocateInPlanning=false` 只改 system prompt、不去图；无纯文本 planning 代码路径；官方文档亦明示 planner 需 multimodal 模型。
2. **Bedrock 上所有走 chat-completions 的强推理纯文本模型都拒图像**。实测：`deepseek.v3.2` / `openai.gpt-oss-120b` / `qwen.qwen3-32b` / `qwen.qwen3-next-80b-a3b` 收到 `image_url` 均返回 `400 "Model does not support image modality"`（纯文本调用则 200）。Claude 系（claude-sonnet-4-6 等）干脆不在 `/openai/v1` chat-completions 面上（404）。

**两个集合不相交**：能被 Midscene 调用（chat-completions + 收图像）的 Bedrock 模型 = 只有 VL 模型。强推理纯文本模型全部出局。

## 决定

- planning **复用 Qwen3-VL**（`qwen.qwen3-vl-235b-a22b`），即不设 `MIDSCENE_PLANNING_MODEL_*`，让 default/grounding 模型兼任 planning。这是 AWS 约束 + Midscene 约束下唯一"既可达又收图"的务实解。
- 不引入独立 planner：纯文本模型会被拒图像；另找一个 Bedrock VL 模型做 planner 无实际增益（见 ADR 0003 的 VL 选型，Bedrock 上可用的 chat-completions VL 选项很窄）。

## 何时重议

- 若 Bedrock 将来开放强推理模型的 chat-completions + 图像输入（如某个推理模型加视觉），可重新评估"独立 planner 提升规划质量"。
- 若放弃 AWS 约束（ADR 0009），AWS 外的多模态推理模型（如 OpenAI 原生 gpt-5.x，多模态 + chat-completions）可作 planner——但这是对 [0009](./0009-maximize-aws-hard-constraint.md) 的破例，需另立 ADR。

## 探针

`midscene/spikes/midscene-sigv4/04-planning-probe.ts`：验证任一候选的 (a) chat-completions 可达 + (b) image_url 容忍两关。当前所有纯文本候选卡在 (b)。
