# Engine And Model ADRs

> 56 nodes · cohesion 0.06

## Key Concepts

- **ADR 0014: AI 优先断言** (24 connections) — `docs/adr/0014-ai-first-assertions.md`
- **ADR 0044: 引擎模型选择与覆盖** (21 connections) — `docs/adr/0044-engine-model-selection-and-override.md`
- **ADR 0038: worker 镜像交付** (20 connections) — `docs/adr/0038-worker-image-delivery.md`
- **ADR 0001: 范围限于英文 UI** (18 connections) — `docs/adr/0001-scope-limited-to-english-ui.md`
- **ADR 0003: Midscene grounding 用 Qwen3-VL on Bedrock** (13 connections) — `docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md`
- **ADR 0010: spike 作为对等基准** (12 connections) — `docs/adr/0010-spike-as-apples-to-apples-benchmark.md`
- **ADR 0004: Nova Act 经 Workflow 的 IAM 鉴权** (11 connections) — `docs/adr/0004-novaact-iam-auth-via-workflow.md`
- **ADR 0009: 最大化使用 AWS（硬约束）** (10 connections) — `docs/adr/0009-maximize-aws-hard-constraint.md`
- **文档地图（按读者分类的文档索引）** (10 connections) — `docs/README.md`
- **ADR 0018: 通用 step 能力** (9 connections) — `docs/adr/0018-generic-steps-capability.md`
- **ADR 0008: Midscene Bedrock 鉴权 SigV4 自签** (8 connections) — `docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md`
- **ADR 0015: v1 定位——柔性冒烟而非回归** (8 connections) — `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- **ADR 0002: Midscene 不由 GPT-5.5 驱动** (6 connections) — `docs/adr/0002-midscene-not-driven-by-gpt55.md`
- **ADR 0012: planning 复用视觉模型、不引独立文本规划器** (6 connections) — `docs/adr/0012-planning-shares-qwen3vl-no-text-planner.md`
- **SIGV4-FETCH-RECIPE.md 接线配方** (6 connections) — `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md`
- **ADR 0007: 程序化登录，HITL 作逃生口** (5 connections) — `docs/adr/0007-programmatic-login-hitl-as-escape-hatch.md`
- **gherkai README** (5 connections) — `README.md`
- **gherkai (UI 自动化测试工具)** (5 connections) — `README.md`
- **AI 断言布尔投票与抖动治理** (4 connections) — `docs/adr/0014-ai-first-assertions.md`
- **柔性冒烟定位（精确度光谱最左端）** (4 connections) — `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- **Model qwen.qwen3-vl-235b-a22b (Bedrock ON_DEMAND)** (3 connections) — `docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md`
- **createOpenAIClient 逃生舱 + sigv4Fetch** (3 connections) — `docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md`
- **版本切分（v0.1 → v1.4 完成线）** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **CLAUDE.md（项目约定）** (2 connections) — `CLAUDE.md`
- **CONTEXT.md（领域概念与术语）** (2 connections) — `CONTEXT.md`
- *... and 31 more nodes in this community*

## Relationships

- [Contributor Docs And ADRs](Contributor_Docs_And_ADRs.md) (22 shared connections)
- [Shared Feature Boundary ADRs](Shared_Feature_Boundary_ADRs.md) (17 shared connections)
- [Execution Architecture ADRs](Execution_Architecture_ADRs.md) (15 shared connections)
- [Docs And Skill Guardrails](Docs_And_Skill_Guardrails.md) (6 shared connections)
- [Architecture Diagram Catalog](Architecture_Diagram_Catalog.md) (4 shared connections)
- [Cloud Backend Concepts](Cloud_Backend_Concepts.md) (3 shared connections)
- [Changelog Features](Changelog_Features.md) (3 shared connections)
- [Packaging And Capability Surface](Packaging_And_Capability_Surface.md) (2 shared connections)
- [Fargate Deployment Wiring](Fargate_Deployment_Wiring.md) (2 shared connections)
- [Contributor Docs And Skills](Contributor_Docs_And_Skills.md) (2 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (1 shared connections)
- [AWS Worker Image Registry](AWS_Worker_Image_Registry.md) (1 shared connections)

## Source Files

- `.github/workflows/README.md`
- `CLAUDE.md`
- `CONTEXT.md`
- `README.md`
- `docs/README.md`
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
- `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- `docs/adr/0018-generic-steps-capability.md`
- `docs/adr/0019-feature-tags-scope-and-engine.md`
- `docs/adr/0036-deterministic-capability-discovery.md`

## Audit Trail

- EXTRACTED: 166 (95%)
- INFERRED: 8 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*