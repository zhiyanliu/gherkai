# 引擎模型的选择与覆盖：默认钉版、按引擎 env 覆盖

> **Status:** Accepted（2026-09-17）

## 背景

两引擎各依赖一个云端模型：Nova Act 引擎的模型由 Nova Act 服务托管（`Workflow(model_id=...)`，[0004](./0004-novaact-iam-auth-via-workflow.md)）；Midscene 引擎经 Bedrock 的 OpenAI 兼容端点（`/openai/v1`，SigV4 service `bedrock`）调视觉模型。三个事实使「单一最佳模型」不成立：

1. **上游推荐随版本变、且各家评价都基于私有评测集**。Midscene 1.12 文档把我们用了半年的 Qwen3-VL 标为「老一代，不推荐」，改荐 Qwen3.x plus、Doubao Seed 2.1、Gemini 3.5 flash——三者在 Bedrock 上都没有；它给 GPT-5.6 / GPT-6 / Kimi 的评价也来自私有评测。这些结论对我们的用例没有可比性。
2. **AWS 上 Midscene 支持的家族在增加**。2026-09 us-east-1 实查：GPT-6 Astra、GPT-5.6 sol / terra / luna（经 inference profile）、Kimi K2.5、Qwen3-VL 四者都能经我们现有的 SigV4 + OpenAI 兼容接线收发图文；Claude、Amazon Nova、Gemma、Mistral 虽有视觉能力但 Midscene 无对应 family。
3. **模型换代会稠密地改判定**。[0004](./0004-novaact-iam-auth-via-workflow.md) 的 A/B：9 个 scenario 有 1 个在两个模型间三遍一致翻转。使用方的应用、语言、预算不同，适合的模型也不同。

## 决策

1. **默认钉版、随发版评估升级，两引擎同律**。每个引擎的默认模型是钉死的具体 id，由本仓库的评测集（`features/` 下两引擎各自的 wikipedia 用例与失败探针、各跑三遍）A/B 选出；换默认只随 gherkai 发版并在 Release 正文点明。Nova 的选型理由与证据在 [0004](./0004-novaact-iam-auth-via-workflow.md)「模型版本选择策略」；Midscene 的默认见下「现值」。
2. **覆盖旋钮 = worker 侧 env，两引擎对称**。Nova：`NOVA_MODEL_ID`（[0004](./0004-novaact-iam-auth-via-workflow.md)）。Midscene：`MIDSCENE_MODEL_ID`（Bedrock 模型 id 或 inference profile id，如 `us.openai.gpt-6-astra`）+ 可选 `MIDSCENE_MODEL_FAMILY`（Midscene 的 family 名）。family 缺省时按 id 推断，表住 worker（`lib/agentcore-sigv4`）：`qwen.qwen3-vl*` → `qwen3-vl`、`*openai.gpt-6*` → `gpt-6`、`*openai.gpt-5*` → `gpt-5`、`*kimi-k2*` → `kimi`、`*kimi-k3*` → `kimi3`、`deepseek.*` → `deepseek`、`zai.glm-*v*` → `glm-v`；显式给了以显式为准；推不出且未给 → worker 启动即 fail-loud、点名要设 `MIDSCENE_MODEL_FAMILY`——family 决定 Midscene 的提示词与请求参数适配，猜错的后果是静默劣化而不是报错，所以宁可拒绝。生效面与 Nova 一致：本机跑在 shell 里设即生效（worker 继承 env，组合根不清这几个键）；云端 Fargate 容器 env 是显式枚举，烙进定制 worker 镜像的 `ENV`（[0038](./0038-worker-image-delivery.md) variant 机制）。
3. **可用集合由接线决定，不另做适配**。Midscene 腿只能用 Bedrock OpenAI 兼容端点调得到、且 Midscene 有 family 的模型；GPT 系列须用 inference profile id、参数走 `max_completion_tokens`（Midscene 的 `gpt-5` / `gpt-6` family 适配器负责，实测直接给模型 id 或用 `max_tokens` 都被端点 400）；推理型模型的 token 成本含 reasoning tokens。preview 或无支持承诺的模型由使用方自担，同 [0004](./0004-novaact-iam-auth-via-workflow.md)。
4. **可见性**。worker `--capabilities` 自报 `model_id`（[0036](./0036-deterministic-capability-discovery.md)「5.」），`doctor` 显示本机 worker 实际用的模型；使用者向披露在 README「判定由谁做出」一节。

**现值**：Nova `nova-act-v1.0`；Midscene `qwen.qwen3-vl-235b-a22b`（候选 GPT-6 Astra、Kimi K2.5 的 A/B 按本 ADR 决策 1 的评测集进行，结论回填本条与 README 披露表）。

## 被拒 / 留口子

- **run 级 `--model <engine>=<id>`，随 definition 持久化、各宿主注入**（`--steps-dir` 的先例，[0037](./0037-distribution-and-packaging.md) 决策 4）——让云端使用方不必烙镜像。留口子不做：等 A/B 数据与真实需求；本机 spawn / 前台 Fargate / detached Lambda / 能力自述四个注入面就是四个会漂的地方。
- **在 gherkai 侧为各家模型写适配**——Midscene 已有 family 适配器，复刻即第二事实源；Nova 侧只有一个服务，无此需求。
- **Midscene 无 family 的视觉模型**（Amazon Nova Lite / Pro、Claude、Gemma 3、Mistral）——要自写适配器，违背薄 worker（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）。
- **单一 family 硬编码**（旧态 `MIDSCENE_USE_QWEN3_VL: "true"`）——被推断表 + 显式覆盖替代。

## 边界与互链

- [0004](./0004-novaact-iam-auth-via-workflow.md)：Nova 鉴权形态与 Nova 侧选型证据。
- [0036](./0036-deterministic-capability-discovery.md)「5.」：自述对象的 `model_id` 键。
- [0038](./0038-worker-image-delivery.md)：云端覆盖走 variant 镜像 `ENV`。
- [0042](./0042-step-evidence-and-explain.md) 决策六：SDK 版本钉死，与本 ADR 的模型钉版同一逻辑。
