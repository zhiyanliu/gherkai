# Architecture ADRs (Core)

> 28 nodes · cohesion 0.15

## Key Concepts

- **ADR 0024 worker/core 协议** (18 connections) — `docs/adr/0024-worker-core-protocol.md`
- **ADR 0016 执行架构：核心库与 run 模型** (15 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **ADR 0022 BDD runner 退役、核心解析 + 薄 worker** (13 connections) — `docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md`
- **ADR 0001 UI 语言支持范围按引擎划分** (12 connections) — `docs/adr/0001-scope-limited-to-english-ui.md`
- **ADR 0010 两引擎 spike 做成苹果对苹果基准** (8 connections) — `docs/adr/0010-spike-as-apples-to-apples-benchmark.md`
- **ADR 0014 AI 优先的断言** (8 connections) — `docs/adr/0014-ai-first-assertions.md`
- **ADR 0019 feature tag 的 scope 与引擎路由** (7 connections) — `docs/adr/0019-feature-tags-scope-and-engine.md`
- **ADR 0020 step 措辞默认 AI + 确定性脚手架** (7 connections) — `docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md`
- **ADR 0006 形态 A：两子工程并列，暂不上编排器** (4 connections) — `docs/adr/0006-form-a-two-subprojects-no-orchestrator.md`
- **ADR 0007 程序化登录，HITL 仅作逃生舱** (4 connections) — `docs/adr/0007-programmatic-login-hitl-as-escape-hatch.md`
- **ADR 0015: v1.0 定位柔性冒烟** (4 connections) — `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- **ADR 0017: 云端执行倾向 Fargate/ECS** (4 connections) — `docs/adr/0017-cloud-execution-fargate-over-runtime.md`
- **ADR 0018 通用 step 能力** (4 connections) — `docs/adr/0018-generic-steps-capability.md`
- **ADR 0005 用例写在单一共享 .feature 文件** (3 connections) — `docs/adr/0005-single-shared-feature-file.md`
- **ADR 0013: 跨引擎共享的边界** (3 connections) — `docs/adr/0013-cross-engine-sharing-boundary.md`
- **核心注入接口 ports（Engine / RunStore / ResultStore / ReportStore）** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **ADR 0023 Nova Act acting 锁 Python** (3 connections) — `docs/adr/0023-novaact-acting-python-locked-no-ts-core.md`
- **worker I/O 边缘可注入接口（JobSource / EventSink）** (3 connections) — `docs/adr/0024-worker-core-protocol.md`
- **投票治判定抖动（assertion_votes）** (2 connections) — `docs/adr/0014-ai-first-assertions.md`
- **决策 A：--backend {local,cloud} 单一开关** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **组合根共享层抽为平级产品本体包（runtime/）** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **ADR 0021: 本地 patch cucumber 按关键字消歧** (2 connections) — `docs/adr/0021-local-cucumber-patch-step-keyword-disambiguation.md`
- **确定性 step 注册表（@deterministic，住 worker）** (2 connections) — `docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md`
- **DynamoDB 作 events-out 传输（共享 events 表 + Query 轮询）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **Run 数据模型（Step/Scenario/Feature/Scope/Job/Run）** (1 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- *... and 3 more nodes in this community*

## Relationships

- [Tunnel & Capability ADRs](Tunnel_%26_Capability_ADRs.md) (8 shared connections)
- [AWS Architecture ADRs](AWS_Architecture_ADRs.md) (6 shared connections)
- [Docs & Terminology ADRs](Docs_%26_Terminology_ADRs.md) (4 shared connections)
- [Contributor Guardrail Docs](Contributor_Guardrail_Docs.md) (3 shared connections)
- [AWS Deploy Package Docs](AWS_Deploy_Package_Docs.md) (2 shared connections)

## Source Files

- `docs/adr/0001-scope-limited-to-english-ui.md`
- `docs/adr/0005-single-shared-feature-file.md`
- `docs/adr/0006-form-a-two-subprojects-no-orchestrator.md`
- `docs/adr/0007-programmatic-login-hitl-as-escape-hatch.md`
- `docs/adr/0010-spike-as-apples-to-apples-benchmark.md`
- `docs/adr/0013-cross-engine-sharing-boundary.md`
- `docs/adr/0014-ai-first-assertions.md`
- `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- `docs/adr/0017-cloud-execution-fargate-over-runtime.md`
- `docs/adr/0018-generic-steps-capability.md`
- `docs/adr/0019-feature-tags-scope-and-engine.md`
- `docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md`
- `docs/adr/0021-local-cucumber-patch-step-keyword-disambiguation.md`
- `docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md`
- `docs/adr/0023-novaact-acting-python-locked-no-ts-core.md`
- `docs/adr/0024-worker-core-protocol.md`

## Audit Trail

- EXTRACTED: 78 (96%)
- INFERRED: 3 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*