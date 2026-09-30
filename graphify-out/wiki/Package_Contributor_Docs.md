# Package Contributor Docs

> 116 nodes · cohesion 0.05

## Key Concepts

- **ADR 0016 执行架构与分层** (41 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **ADR 0024 worker↔核心协议** (35 connections) — `docs/adr/0024-worker-core-protocol.md`
- **ADR 0037 分发与包化** (34 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **产物与证据** (25 connections) — `docs/internals/artifacts-and-evidence.md`
- **ADR 0030 实时写接缝** (21 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **ADR 0034 无状态批量运行** (21 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **ADR 0042 step 证据与 explain** (21 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **cli 包 contributor 文档** (20 connections) — `cli/DEVELOPMENT.md`
- **ADR 0038 worker 镜像交付** (18 connections) — `docs/adr/0038-worker-image-delivery.md`
- **ADR 0019 feature tag 语义** (17 connections) — `docs/adr/0019-feature-tags-scope-and-engine.md`
- **ADR 0022 core 解析 + 薄 worker（注册表即扩展点）** (16 connections) — `docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md`
- **ADR 0033 IaC AWS 后端与组合装配** (16 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **ADR 0014 AI 优先的断言策略** (15 connections) — `docs/adr/0014-ai-first-assertions.md`
- **ADR 0029 引擎产物上传 S3** (15 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Nova Act worker 开发笔记** (15 connections) — `engines/novaact/DEVELOPMENT.md`
- **ADR 0020 默认 AI / 确定性脚手架** (14 connections) — `docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md`
- **ADR 0028: 瞬时网络/SSL 韧性** (13 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **ADR 0035 本机应用隧道暴露** (13 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **ADR 0036 确定性能力自述** (13 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **ADR 0027 RunReport 归集索引** (12 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **ADR 0041 面向 agent 的 CLI 可用性** (12 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **ADR 0044 模型选择与覆盖** (12 connections) — `docs/adr/0044-engine-model-selection-and-override.md`
- **ADR 0001: 范围限定英文 UI** (11 connections) — `docs/adr/0001-scope-limited-to-english-ui.md`
- **ADR 0026: schedule 模块** (11 connections) — `docs/adr/0026-schedule-module.md`
- **ADR 0013 跨引擎共享边界** (10 connections) — `docs/adr/0013-cross-engine-sharing-boundary.md`
- *... and 91 more nodes in this community*

## Relationships

- [Architecture Diagrams](Architecture_Diagrams.md) (29 shared connections)
- [Reconciler Mechanism Concepts](Reconciler_Mechanism_Concepts.md) (15 shared connections)
- [Agent Skill ADRs](Agent_Skill_ADRs.md) (12 shared connections)
- [Agent Skill Reference Docs](Agent_Skill_Reference_Docs.md) (12 shared connections)
- [Artifact Pre-Send Uploads](Artifact_Pre-Send_Uploads.md) (8 shared connections)
- [Project Conventions Docs](Project_Conventions_Docs.md) (7 shared connections)
- [Engine Runtime Mechanisms](Engine_Runtime_Mechanisms.md) (6 shared connections)
- [Artifact Rescue Decisions](Artifact_Rescue_Decisions.md) (4 shared connections)
- [Fargate Naming & Wiring](Fargate_Naming_%26_Wiring.md) (3 shared connections)
- [Verdict Status Aggregation](Verdict_Status_Aggregation.md) (3 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (2 shared connections)
- [Runtime Architecture Concepts](Runtime_Architecture_Concepts.md) (2 shared connections)

## Source Files

- `.github/workflows/ci.yml`
- `CONTEXT.md`
- `cli/DEVELOPMENT.md`
- `core/tests/README.md`
- `deploy_aws/DEVELOPMENT.md`
- `deploy_aws/README.md`
- `docs/adr/0001-scope-limited-to-english-ui.md`
- `docs/adr/0002-midscene-not-driven-by-gpt55.md`
- `docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md`
- `docs/adr/0004-novaact-iam-auth-via-workflow.md`
- `docs/adr/0005-single-shared-feature-file.md`
- `docs/adr/0006-form-a-two-subprojects-no-orchestrator.md`
- `docs/adr/0007-programmatic-login-hitl-as-escape-hatch.md`
- `docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md`
- `docs/adr/0009-maximize-aws-hard-constraint.md`
- `docs/adr/0010-spike-as-apples-to-apples-benchmark.md`
- `docs/adr/0011-agentcore-browser-system-default-vs-custom.md`
- `docs/adr/0012-planning-shares-qwen3vl-no-text-planner.md`
- `docs/adr/0013-cross-engine-sharing-boundary.md`
- `docs/adr/0014-ai-first-assertions.md`

## Audit Trail

- EXTRACTED: 408 (97%)
- INFERRED: 12 (3%)
- AMBIGUOUS: 2 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*