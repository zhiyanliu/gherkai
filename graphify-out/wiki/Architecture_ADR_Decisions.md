# Architecture ADR Decisions

> 50 nodes · cohesion 0.09

## Key Concepts

- **ADR 0016 执行架构 / 组合根注入** (34 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **ADR 0024 worker↔core 协议** (26 connections) — `docs/adr/0024-worker-core-protocol.md`
- **ADR 0034 无状态跑批 reconciler** (22 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **ADR 0019 feature tag 的 scope 与引擎路由** (20 connections) — `docs/adr/0019-feature-tags-scope-and-engine.md`
- **ADR 0022 BDD runner 退役、核心解析 + 薄 worker** (19 connections) — `docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md`
- **ADR 0014 AI 优先断言与投票** (16 connections) — `docs/adr/0014-ai-first-assertions.md`
- **ADR 0020: step 措辞与确定性脚手架** (15 connections) — `docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md`
- **ADR 0027 run 报告归集索引** (14 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **ADR 0026 schedule 模块** (13 connections) — `docs/adr/0026-schedule-module.md`
- **ADR 0028 瞬时网络/SSL 韧性** (12 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **ADR 0036: 确定性能力可发现** (12 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **ADR 0013 跨引擎共享边界** (10 connections) — `docs/adr/0013-cross-engine-sharing-boundary.md`
- **ADR 0025 plan 模块：feature → jobs** (8 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **ADR 0015: v1.0 定位——AI 柔性的流程冒烟/探索性回归，不是精确回归** (7 connections) — `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- **ADR 0018: 通用 step 能力面** (7 connections) — `docs/adr/0018-generic-steps-capability.md`
- **ADR 0005 单一共享 .feature 文件** (6 connections) — `docs/adr/0005-single-shared-feature-file.md`
- **ADR 0006: 形态 A 两子工程、无编排器** (6 connections) — `docs/adr/0006-form-a-two-subprojects-no-orchestrator.md`
- **ADR 0023 Nova Act acting 锁 Python** (5 connections) — `docs/adr/0023-novaact-acting-python-locked-no-ts-core.md`
- **plan() 深模块接口** (5 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **scope seam（tag 分组 + engine 校验）** (5 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **@engine:<midscene|novaact> Tag (Engine Selection)** (3 connections) — `docs/adr/0019-feature-tags-scope-and-engine.md`
- **ADR 0021: 本地 cucumber 补丁（已退役）** (3 connections) — `docs/adr/0021-local-cucumber-patch-step-keyword-disambiguation.md`
- **第三方库 seam：gherkin-official 领域模型隔离** (3 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **跨引擎共享止于 features/（+ 使用方 steps/ 约定面）** (2 connections) — `docs/adr/0013-cross-engine-sharing-boundary.md`
- **对称布尔投票治抖动（assertion_votes）** (2 connections) — `docs/adr/0014-ai-first-assertions.md`
- *... and 25 more nodes in this community*

## Relationships

- [Architecture Decision Records](Architecture_Decision_Records.md) (21 shared connections)
- [DynamoDB Events Transport](DynamoDB_Events_Transport.md) (17 shared connections)
- [Project Conventions Docs](Project_Conventions_Docs.md) (14 shared connections)
- [Execution Model Concepts](Execution_Model_Concepts.md) (14 shared connections)
- [Termination & Engine Ports](Termination_%26_Engine_Ports.md) (14 shared connections)
- [CLI Usability & Evidence Docs](CLI_Usability_%26_Evidence_Docs.md) (13 shared connections)
- [Schedule Semantics Concepts](Schedule_Semantics_Concepts.md) (5 shared connections)
- [CLI Docs & Skill References](CLI_Docs_%26_Skill_References.md) (4 shared connections)
- [Act Timeout & Signal Handling](Act_Timeout_%26_Signal_Handling.md) (2 shared connections)
- [Domain Glossary](Domain_Glossary.md) (1 shared connections)
- [Cloud Run State Mechanisms](Cloud_Run_State_Mechanisms.md) (1 shared connections)

## Source Files

- `docs/adr/0005-single-shared-feature-file.md`
- `docs/adr/0006-form-a-two-subprojects-no-orchestrator.md`
- `docs/adr/0013-cross-engine-sharing-boundary.md`
- `docs/adr/0014-ai-first-assertions.md`
- `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- `docs/adr/0018-generic-steps-capability.md`
- `docs/adr/0019-feature-tags-scope-and-engine.md`
- `docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md`
- `docs/adr/0021-local-cucumber-patch-step-keyword-disambiguation.md`
- `docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md`
- `docs/adr/0023-novaact-acting-python-locked-no-ts-core.md`
- `docs/adr/0024-worker-core-protocol.md`
- `docs/adr/0025-plan-module-feature-to-jobs.md`
- `docs/adr/0026-schedule-module.md`
- `docs/adr/0027-runreport-aggregation-index.md`
- `docs/adr/0028-transient-network-ssl-resilience.md`
- `docs/adr/0034-detached-batch-reconciler.md`
- `docs/adr/0036-deterministic-capability-discovery.md`

## Audit Trail

- EXTRACTED: 208 (99%)
- INFERRED: 3 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*