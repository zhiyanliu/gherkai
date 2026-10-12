# Shared Feature Scope ADRs

> 50 nodes · cohesion 0.06

## Key Concepts

- **ADR 0037: 分发与打包** (33 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **ADR 0022: BDD runner 退役，核心解析 + 薄 worker** (17 connections) — `docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md`
- **ADR 0020: step 措辞默认 AI、确定性作为脚手架** (15 connections) — `docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md`
- **ADR 0036: 确定性能力可发现** (12 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **ADR 0013: 跨引擎共享边界** (10 connections) — `docs/adr/0013-cross-engine-sharing-boundary.md`
- **ADR 0018: 通用 step 能力** (9 connections) — `docs/adr/0018-generic-steps-capability.md`
- **ADR 0015: v1 定位——柔性冒烟而非回归** (8 connections) — `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- **ADR 0005: 单一共享 feature 文件** (7 connections) — `docs/adr/0005-single-shared-feature-file.md`
- **ADR 0023: Nova Act acting 锁 Python** (7 connections) — `docs/adr/0023-novaact-acting-python-locked-no-ts-core.md`
- **ADR 0006: 形态 A——两个子工程、无编排器** (5 connections) — `docs/adr/0006-form-a-two-subprojects-no-orchestrator.md`
- **patch-package 补丁 @cucumber+cucumber+13.0.0** (5 connections) — `docs/adr/0021-local-cucumber-patch-step-keyword-disambiguation.md`
- **worker --capabilities 自述入口** (5 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **steps/ 定制面（随 definition 走 + env 注入）** (5 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **柔性冒烟定位（精确度光谱最左端）** (4 connections) — `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- **双语言裂缝（物理约束）** (3 connections) — `docs/adr/0006-form-a-two-subprojects-no-orchestrator.md`
- **版本切分（v0.1 → v1.4 完成线）** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **ADR 0021: 本地 patch @cucumber/cucumber 按关键字消歧** (3 connections) — `docs/adr/0021-local-cucumber-patch-step-keyword-disambiguation.md`
- **variant（一套具名确定性 step 集 = 一个定制镜像）** (3 connections) — `docs/adr/0038-worker-image-delivery.md`
- **公共设施落在核心库层（报告归集/会话生命周期/跑批入口）** (2 connections) — `docs/adr/0013-cross-engine-sharing-boundary.md`
- **跨引擎共享止于 features/（Gherkin 单一事实源）** (2 connections) — `docs/adr/0013-cross-engine-sharing-boundary.md`
- **默认 AI 判断断言层（QA 零代码）** (2 connections) — `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- **确定性 step（测试开发按需自建）** (2 connections) — `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- **柔性漏检（页面真变了但 AI 宽容判过）** (2 connections) — `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- **判定抖动（AI 结论不一致 = flakiness）** (2 connections) — `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- **点名核对（QA 纯自然语言点名要核对的项）** (2 connections) — `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- *... and 25 more nodes in this community*

## Relationships

- [Model Selection ADRs](Model_Selection_ADRs.md) (24 shared connections)
- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (19 shared connections)
- [Release & Versioning Concepts](Release_%26_Versioning_Concepts.md) (9 shared connections)
- [Cloud Backend Docs & Diagrams](Cloud_Backend_Docs_%26_Diagrams.md) (8 shared connections)
- [Browser And Tunnel Decisions](Browser_And_Tunnel_Decisions.md) (2 shared connections)
- [Project Docs & Glossary](Project_Docs_%26_Glossary.md) (2 shared connections)
- [E2E Interrupt Harness](E2E_Interrupt_Harness.md) (1 shared connections)

## Source Files

- `docs/adr/0005-single-shared-feature-file.md`
- `docs/adr/0006-form-a-two-subprojects-no-orchestrator.md`
- `docs/adr/0013-cross-engine-sharing-boundary.md`
- `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- `docs/adr/0018-generic-steps-capability.md`
- `docs/adr/0019-feature-tags-scope-and-engine.md`
- `docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md`
- `docs/adr/0021-local-cucumber-patch-step-keyword-disambiguation.md`
- `docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md`
- `docs/adr/0023-novaact-acting-python-locked-no-ts-core.md`
- `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- `docs/adr/0035-local-app-testing-via-tunnel.md`
- `docs/adr/0036-deterministic-capability-discovery.md`
- `docs/adr/0037-distribution-and-packaging.md`
- `docs/adr/0038-worker-image-delivery.md`

## Audit Trail

- EXTRACTED: 134 (99%)
- INFERRED: 2 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*