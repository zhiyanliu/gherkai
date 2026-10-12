# Model Selection ADRs

> 40 nodes · cohesion 0.10

## Key Concepts

- **ADR 0014: AI 优先断言** (24 connections) — `docs/adr/0014-ai-first-assertions.md`
- **ADR 0042: step 证据与 explain** (23 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **ADR 0044: 引擎模型选择与覆盖** (21 connections) — `docs/adr/0044-engine-model-selection-and-override.md`
- **ADR 0038: worker 镜像交付** (20 connections) — `docs/adr/0038-worker-image-delivery.md`
- **ADR 0001: 范围限于英文 UI** (18 connections) — `docs/adr/0001-scope-limited-to-english-ui.md`
- **ADR 0003: Midscene grounding 用 Qwen3-VL on Bedrock** (13 connections) — `docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md`
- **novaact 引擎开发笔记** (13 connections) — `engines/novaact/DEVELOPMENT.md`
- **ADR 0010: spike 作为对等基准** (12 connections) — `docs/adr/0010-spike-as-apples-to-apples-benchmark.md`
- **ADR 0004: Nova Act 经 Workflow 的 IAM 鉴权** (11 connections) — `docs/adr/0004-novaact-iam-auth-via-workflow.md`
- **ADR 0009: 最大化使用 AWS（硬约束）** (10 connections) — `docs/adr/0009-maximize-aws-hard-constraint.md`
- **ADR 0008: Midscene Bedrock 鉴权 SigV4 自签** (8 connections) — `docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md`
- **ADR 0002: Midscene 不由 GPT-5.5 驱动** (6 connections) — `docs/adr/0002-midscene-not-driven-by-gpt55.md`
- **ADR 0012: planning 复用视觉模型、不引独立文本规划器** (6 connections) — `docs/adr/0012-planning-shares-qwen3vl-no-text-planner.md`
- **SIGV4-FETCH-RECIPE.md 接线配方** (6 connections) — `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md`
- **ADR 0007: 程序化登录，HITL 作逃生口** (5 connections) — `docs/adr/0007-programmatic-login-hitl-as-escape-hatch.md`
- **AI 断言布尔投票与抖动治理** (4 connections) — `docs/adr/0014-ai-first-assertions.md`
- **Model qwen.qwen3-vl-235b-a22b (Bedrock ON_DEMAND)** (3 connections) — `docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md`
- **createOpenAIClient 逃生舱 + sigv4Fetch** (3 connections) — `docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md`
- **概念：非英文应用用 @engine:midscene 路由** (2 connections) — `docs/adr/0001-scope-limited-to-english-ui.md`
- **概念：Nova Act 中文词语级文本匹配短板** (2 connections) — `docs/adr/0001-scope-limited-to-english-ui.md`
- **概念：Midscene 仅走 chat-completions 接口** (2 connections) — `docs/adr/0002-midscene-not-driven-by-gpt55.md`
- **NOVA_MODEL_ID opt-in 环境变量旋钮** (2 connections) — `docs/adr/0004-novaact-iam-auth-via-workflow.md`
- **Nova 模型版本钉死 GA（nova-act-v1.0）策略** (2 connections) — `docs/adr/0004-novaact-iam-auth-via-workflow.md`
- **签名前剥除 image_url.detail="original"** (2 connections) — `docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md`
- **对称布尔断言路径（aiBoolean ↔ act_get(BOOL_SCHEMA)）** (2 connections) — `docs/adr/0010-spike-as-apples-to-apples-benchmark.md`
- *... and 15 more nodes in this community*

## Relationships

- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (25 shared connections)
- [Shared Feature Scope ADRs](Shared_Feature_Scope_ADRs.md) (24 shared connections)
- [Cloud Backend Docs & Diagrams](Cloud_Backend_Docs_%26_Diagrams.md) (11 shared connections)
- [Project Docs & Glossary](Project_Docs_%26_Glossary.md) (6 shared connections)
- [Release & Versioning Concepts](Release_%26_Versioning_Concepts.md) (6 shared connections)
- [Documentation Guardrail Rules](Documentation_Guardrail_Rules.md) (6 shared connections)
- [Browser And Tunnel Decisions](Browser_And_Tunnel_Decisions.md) (3 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (1 shared connections)
- [Worker Image Mapping & Cleanup](Worker_Image_Mapping_%26_Cleanup.md) (1 shared connections)
- [Composition Root Architecture](Composition_Root_Architecture.md) (1 shared connections)
- [Artifact Upload Design](Artifact_Upload_Design.md) (1 shared connections)
- [Schedule Concurrency & Termination](Schedule_Concurrency_%26_Termination.md) (1 shared connections)

## Source Files

- `docs/adr/0001-scope-limited-to-english-ui.md`
- `docs/adr/0002-midscene-not-driven-by-gpt55.md`
- `docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md`
- `docs/adr/0004-novaact-iam-auth-via-workflow.md`
- `docs/adr/0007-programmatic-login-hitl-as-escape-hatch.md`
- `docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md`
- `docs/adr/0009-maximize-aws-hard-constraint.md`
- `docs/adr/0010-spike-as-apples-to-apples-benchmark.md`
- `docs/adr/0012-planning-shares-qwen3vl-no-text-planner.md`
- `docs/adr/0014-ai-first-assertions.md`
- `docs/adr/0024-worker-core-protocol.md`
- `docs/adr/0030-realtime-persistence-seam.md`
- `docs/adr/0036-deterministic-capability-discovery.md`
- `docs/adr/0038-worker-image-delivery.md`
- `docs/adr/0042-step-evidence-and-explain.md`
- `docs/adr/0044-engine-model-selection-and-override.md`
- `docs/ai-eng/REFERENCES.md`
- `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md`
- `engines/novaact/DEVELOPMENT.md`

## Audit Trail

- EXTRACTED: 160 (96%)
- INFERRED: 6 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*