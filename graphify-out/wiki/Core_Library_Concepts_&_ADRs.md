# Core Library Concepts & ADRs

> 61 nodes · cohesion 0.06

## Key Concepts

- **ADR 0024: worker–core 协议** (42 connections) — `docs/adr/0024-worker-core-protocol.md`
- **ADR 0016: 执行架构 — 核心库与 run 模型** (37 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **ADR 0034: detached 批量运行与推进器** (27 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **core 包 contributor 文档** (18 connections) — `core/DEVELOPMENT.md`
- **runtime 包 contributor 文档** (16 connections) — `runtime/DEVELOPMENT.md`
- **ADR 0030: 实时落库缝** (15 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **ADR 0019: feature tag 的范围与引擎路由** (14 connections) — `docs/adr/0019-feature-tags-scope-and-engine.md`
- **ADR 0029: 引擎产物上 S3** (12 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **ADR 0031: job 生命周期状态与严重度** (11 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **ADR 0027: run 报告归集索引** (10 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **ADR 0028: 瞬时网络/SSL 韧性** (10 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **ADR 0026: schedule 模块** (9 connections) — `docs/adr/0026-schedule-module.md`
- **core 测试说明（单测 + 集成测试）** (7 connections) — `core/tests/README.md`
- **ADR 0025: plan 模块（feature → jobs）** (7 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **输出契约：流式 JSON Lines 事件流** (6 connections) — `docs/adr/0024-worker-core-protocol.md`
- **stopTimeout=120 / grace 预算校准** (5 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **组合根 build_fargate_engines 接线（report ⊥ 执行）** (5 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **资源清单（DDB 2 表 / S3 桶 / ECS / Lambda 链 / SSM）** (5 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **输入契约：一个 scope 的 Job（展开后的有序 step）** (4 connections) — `docs/adr/0024-worker-core-protocol.md`
- **IAM 最小权限（task role 动作×资源两维收窄）** (4 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **@engine:<midscene|novaact> 引擎选择 tag** (3 connections) — `docs/adr/0019-feature-tags-scope-and-engine.md`
- **S3 Key Mirrors Local Run Tree** (3 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **S3ReportStore (no artifact copy, href==ref)** (3 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **安全点（step_done/act 边界）提前上传 + SIGTERM handler 兜底** (3 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **preflight fail-fast（探资源存在性、错误点名 prefix）** (3 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- *... and 36 more nodes in this community*

## Relationships

- [Cloud Backend Docs & Diagrams](Cloud_Backend_Docs_%26_Diagrams.md) (28 shared connections)
- [Model Selection ADRs](Model_Selection_ADRs.md) (25 shared connections)
- [Shared Feature Scope ADRs](Shared_Feature_Scope_ADRs.md) (19 shared connections)
- [Schedule Concurrency & Termination](Schedule_Concurrency_%26_Termination.md) (6 shared connections)
- [Release & Versioning Concepts](Release_%26_Versioning_Concepts.md) (5 shared connections)
- [Project Docs & Glossary](Project_Docs_%26_Glossary.md) (4 shared connections)
- [Browser And Tunnel Decisions](Browser_And_Tunnel_Decisions.md) (4 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (3 shared connections)
- [Composition Root Architecture](Composition_Root_Architecture.md) (3 shared connections)
- [Status Severity And Exit Codes](Status_Severity_And_Exit_Codes.md) (3 shared connections)
- [Run Store Ports & Write Order](Run_Store_Ports_%26_Write_Order.md) (3 shared connections)
- [Test Fixtures & Conftest](Test_Fixtures_%26_Conftest.md) (2 shared connections)

## Source Files

- `core/DEVELOPMENT.md`
- `core/tests/README.md`
- `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- `docs/adr/0019-feature-tags-scope-and-engine.md`
- `docs/adr/0024-worker-core-protocol.md`
- `docs/adr/0025-plan-module-feature-to-jobs.md`
- `docs/adr/0026-schedule-module.md`
- `docs/adr/0027-runreport-aggregation-index.md`
- `docs/adr/0028-transient-network-ssl-resilience.md`
- `docs/adr/0029-engine-artifacts-to-s3.md`
- `docs/adr/0030-realtime-persistence-seam.md`
- `docs/adr/0031-job-lifecycle-states-and-severity.md`
- `docs/adr/0032-fargate-execution-environment.md`
- `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- `docs/adr/0034-detached-batch-reconciler.md`
- `runtime/DEVELOPMENT.md`

## Audit Trail

- EXTRACTED: 227 (99%)
- INFERRED: 2 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*