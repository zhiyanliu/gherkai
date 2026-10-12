# Shared Feature Boundary ADRs

> 30 nodes · cohesion 0.10

## Key Concepts

- **ADR 0037: 分发与打包** (33 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **ADR 0022: BDD runner 退役，核心解析 + 薄 worker** (17 connections) — `docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md`
- **ADR 0020: step 措辞默认 AI、确定性作为脚手架** (15 connections) — `docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md`
- **ADR 0013: 跨引擎共享边界** (10 connections) — `docs/adr/0013-cross-engine-sharing-boundary.md`
- **ADR 0005: 单一共享 feature 文件** (7 connections) — `docs/adr/0005-single-shared-feature-file.md`
- **ADR 0023: Nova Act acting 锁 Python** (7 connections) — `docs/adr/0023-novaact-acting-python-locked-no-ts-core.md`
- **ADR 0006: 形态 A——两个子工程、无编排器** (5 connections) — `docs/adr/0006-form-a-two-subprojects-no-orchestrator.md`
- **patch-package 补丁 @cucumber+cucumber+13.0.0** (5 connections) — `docs/adr/0021-local-cucumber-patch-step-keyword-disambiguation.md`
- **双语言裂缝（物理约束）** (3 connections) — `docs/adr/0006-form-a-two-subprojects-no-orchestrator.md`
- **ADR 0021: 本地 patch @cucumber/cucumber 按关键字消歧** (3 connections) — `docs/adr/0021-local-cucumber-patch-step-keyword-disambiguation.md`
- **公共设施落在核心库层（报告归集/会话生命周期/跑批入口）** (2 connections) — `docs/adr/0013-cross-engine-sharing-boundary.md`
- **跨引擎共享止于 features/（Gherkin 单一事实源）** (2 connections) — `docs/adr/0013-cross-engine-sharing-boundary.md`
- **确定性 step（测试开发按需自建）** (2 connections) — `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- **默认 AI 判断的裸 When/Then step** (2 connections) — `docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md`
- **URL 形态自动分流（导航不写死动词）** (2 connections) — `docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md`
- **B1 退役清单（cucumber 入口 + 补丁 + bdd conftest）** (2 connections) — `docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md`
- **薄 worker 子进程（一次调用=一个 scope=一个 job）** (2 connections) — `docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md`
- **两个引擎都作为子进程 worker、核心语言自由选 Python** (2 connections) — `docs/adr/0023-novaact-acting-python-locked-no-ts-core.md`
- **Nova Act REST API = 客户端驱动的工具调用循环** (2 connections) — `docs/adr/0023-novaact-acting-python-locked-no-ts-core.md`
- **Python nova-act SDK 的 Playwright/CDP 客户端循环** (2 connections) — `docs/adr/0023-novaact-acting-python-locked-no-ts-core.md`
- **全 TS 核心路径（被证伪关闭）** (2 connections) — `docs/adr/0023-novaact-acting-python-locked-no-ts-core.md`
- **2 镜像：Nova / Midscene 各一** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **确定性 step 脚手架（QA 零预设）** (1 connections) — `docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md`
- **QA 与测试开发的角色边界** (1 connections) — `docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md`
- **补丁的保守回退策略** (1 connections) — `docs/adr/0021-local-cucumber-patch-step-keyword-disambiguation.md`
- *... and 5 more nodes in this community*

## Relationships

- [Engine And Model ADRs](Engine_And_Model_ADRs.md) (17 shared connections)
- [Contributor Docs And ADRs](Contributor_Docs_And_ADRs.md) (16 shared connections)
- [Execution Architecture ADRs](Execution_Architecture_ADRs.md) (8 shared connections)
- [Packaging And Capability Surface](Packaging_And_Capability_Surface.md) (6 shared connections)
- [Architecture Diagram Catalog](Architecture_Diagram_Catalog.md) (3 shared connections)
- [E2E Harness Script](E2E_Harness_Script.md) (1 shared connections)

## Source Files

- `docs/adr/0005-single-shared-feature-file.md`
- `docs/adr/0006-form-a-two-subprojects-no-orchestrator.md`
- `docs/adr/0013-cross-engine-sharing-boundary.md`
- `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- `docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md`
- `docs/adr/0021-local-cucumber-patch-step-keyword-disambiguation.md`
- `docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md`
- `docs/adr/0023-novaact-acting-python-locked-no-ts-core.md`
- `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- `docs/adr/0037-distribution-and-packaging.md`

## Audit Trail

- EXTRACTED: 94 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*