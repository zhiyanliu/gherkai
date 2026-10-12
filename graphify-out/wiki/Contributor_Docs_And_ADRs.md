# Contributor Docs And ADRs

> 42 nodes · cohesion 0.08

## Key Concepts

- **ADR 0016: 执行架构 — 核心库与 run 模型** (37 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **ADR 0034: detached 批量运行与推进器** (27 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **core 包 contributor 文档** (18 connections) — `core/DEVELOPMENT.md`
- **gherkai-deploy-aws contributor 手册** (16 connections) — `deploy_aws/DEVELOPMENT.md`
- **Midscene 引擎开发笔记（contributor）** (16 connections) — `engines/midscene/DEVELOPMENT.md`
- **runtime 包 contributor 文档** (16 connections) — `runtime/DEVELOPMENT.md`
- **ADR 0030: 实时落库缝** (15 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **ADR 0019: feature tag 的范围与引擎路由** (14 connections) — `docs/adr/0019-feature-tags-scope-and-engine.md`
- **ADR 0035: 本地应用经隧道测试** (14 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **ADR 0036: 确定性能力可发现** (12 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **ADR 0031: job 生命周期状态与严重度** (11 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **ADR 0027: run 报告归集索引** (10 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **ADR 0026: schedule 模块** (9 connections) — `docs/adr/0026-schedule-module.md`
- **core 测试说明（单测 + 集成测试）** (7 connections) — `core/tests/README.md`
- **ADR 0025: plan 模块（feature → jobs）** (7 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **ADR 0011: AgentCore 浏览器 system default vs custom** (6 connections) — `docs/adr/0011-agentcore-browser-system-default-vs-custom.md`
- **输出契约：流式 JSON Lines 事件流** (6 connections) — `docs/adr/0024-worker-core-protocol.md`
- **CONTRIBUTING（contributor 入口）** (3 connections) — `CONTRIBUTING.md`
- **@engine:<midscene|novaact> 引擎选择 tag** (3 connections) — `docs/adr/0019-feature-tags-scope-and-engine.md`
- **S3 Key Mirrors Local Run Tree** (3 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **S3ReportStore (no artifact copy, href==ref)** (3 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **cli/DEVELOPMENT.md** (2 connections) — `core/DEVELOPMENT.md`
- **自建 custom browser（create-browser）** (2 connections) — `docs/adr/0011-agentcore-browser-system-default-vs-custom.md`
- **tunnel.py（--expose-local 隧道 provider）** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **@scope:<name> 会话作用域 tag** (2 connections) — `docs/adr/0019-feature-tags-scope-and-engine.md`
- *... and 17 more nodes in this community*

## Relationships

- [Execution Architecture ADRs](Execution_Architecture_ADRs.md) (29 shared connections)
- [Engine And Model ADRs](Engine_And_Model_ADRs.md) (22 shared connections)
- [Shared Feature Boundary ADRs](Shared_Feature_Boundary_ADRs.md) (16 shared connections)
- [Architecture Diagram Catalog](Architecture_Diagram_Catalog.md) (16 shared connections)
- [Packaging And Capability Surface](Packaging_And_Capability_Surface.md) (9 shared connections)
- [Fargate Deployment Wiring](Fargate_Deployment_Wiring.md) (4 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (3 shared connections)
- [Run Store Persistence Ports](Run_Store_Persistence_Ports.md) (3 shared connections)
- [Midscene Worker Entry](Midscene_Worker_Entry.md) (3 shared connections)
- [Cloud Backend Concepts](Cloud_Backend_Concepts.md) (3 shared connections)
- [Cloud Adapter Test Fixtures](Cloud_Adapter_Test_Fixtures.md) (2 shared connections)
- [Composition Root Architecture](Composition_Root_Architecture.md) (2 shared connections)

## Source Files

- `CONTRIBUTING.md`
- `core/DEVELOPMENT.md`
- `core/tests/README.md`
- `deploy_aws/DEVELOPMENT.md`
- `docs/adr/0011-agentcore-browser-system-default-vs-custom.md`
- `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- `docs/adr/0019-feature-tags-scope-and-engine.md`
- `docs/adr/0024-worker-core-protocol.md`
- `docs/adr/0025-plan-module-feature-to-jobs.md`
- `docs/adr/0026-schedule-module.md`
- `docs/adr/0027-runreport-aggregation-index.md`
- `docs/adr/0029-engine-artifacts-to-s3.md`
- `docs/adr/0030-realtime-persistence-seam.md`
- `docs/adr/0031-job-lifecycle-states-and-severity.md`
- `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- `docs/adr/0034-detached-batch-reconciler.md`
- `docs/adr/0035-local-app-testing-via-tunnel.md`
- `docs/adr/0036-deterministic-capability-discovery.md`
- `engines/midscene/DEVELOPMENT.md`
- `runtime/DEVELOPMENT.md`

## Audit Trail

- EXTRACTED: 209 (100%)
- INFERRED: 1 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*