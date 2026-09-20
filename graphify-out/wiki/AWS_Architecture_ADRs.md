# AWS Architecture ADRs

> 17 nodes · cohesion 0.24

## Key Concepts

- **ADR 0038 worker 镜像交付** (14 connections) — `docs/adr/0038-worker-image-delivery.md`
- **ADR 0044: 引擎模型的选择与覆盖** (14 connections) — `docs/adr/0044-engine-model-selection-and-override.md`
- **ADR 0009 最大化使用 AWS 是硬前提** (8 connections) — `docs/adr/0009-maximize-aws-hard-constraint.md`
- **ADR 0033 IaC AWS 后端与组合装配** (8 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **ADR 0003 Midscene grounding 用 Bedrock Qwen3-VL** (7 connections) — `docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md`
- **ADR 0004 Nova Act 纯 IAM 鉴权（经 Workflow）** (7 connections) — `docs/adr/0004-novaact-iam-auth-via-workflow.md`
- **gherkai deploy push-worker 八步流程** (5 connections) — `docs/adr/0038-worker-image-delivery.md`
- **variant：一套具名确定性 step 集 = 一个定制镜像** (5 connections) — `docs/adr/0038-worker-image-delivery.md`
- **ADR 0008 Midscene→Bedrock 走进程内 SigV4 自签** (4 connections) — `docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md`
- **ADR 0002 Midscene 不用 Bedrock GPT-5.5** (3 connections) — `docs/adr/0002-midscene-not-driven-by-gpt55.md`
- **ADR 0012 Planning 由引擎模型兼任，不引独立 planner** (3 connections) — `docs/adr/0012-planning-shares-qwen3vl-no-text-planner.md`
- **默认 variant 指针（SSM worker-default）** (3 connections) — `docs/adr/0038-worker-image-delivery.md`
- **按 digest 引用镜像的 task-def revision（显式 revision，不取 family 最新）** (3 connections) — `docs/adr/0038-worker-image-delivery.md`
- **GHCR 基础镜像（linux/amd64、零使用方内容）** (2 connections) — `docs/adr/0038-worker-image-delivery.md`
- **清理 pass：退休 tag + 静默期 + 运行中 run 引用检查** (2 connections) — `docs/adr/0038-worker-image-delivery.md`
- **按引擎 env 覆盖模型（NOVA_MODEL_ID / MIDSCENE_MODEL_ID + FAMILY）** (2 connections) — `docs/adr/0044-engine-model-selection-and-override.md`
- **ADR 0028 瞬时网络/SSL 韧性** (1 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`

## Relationships

- [Tunnel & Capability ADRs](Tunnel_%26_Capability_ADRs.md) (10 shared connections)
- [Architecture ADRs (Core)](Architecture_ADRs_%28Core%29.md) (6 shared connections)
- [Docs & Terminology ADRs](Docs_%26_Terminology_ADRs.md) (5 shared connections)
- [AWS Deploy Package Docs](AWS_Deploy_Package_Docs.md) (3 shared connections)
- [Contributor Guardrail Docs](Contributor_Guardrail_Docs.md) (1 shared connections)

## Source Files

- `docs/adr/0002-midscene-not-driven-by-gpt55.md`
- `docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md`
- `docs/adr/0004-novaact-iam-auth-via-workflow.md`
- `docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md`
- `docs/adr/0009-maximize-aws-hard-constraint.md`
- `docs/adr/0012-planning-shares-qwen3vl-no-text-planner.md`
- `docs/adr/0028-transient-network-ssl-resilience.md`
- `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- `docs/adr/0038-worker-image-delivery.md`
- `docs/adr/0044-engine-model-selection-and-override.md`

## Audit Trail

- EXTRACTED: 56 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*