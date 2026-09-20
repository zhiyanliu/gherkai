# Architecture Overview Diagrams

> 38 nodes · cohesion 0.10

## Key Concepts

- **判定的计算路径：从单次投票到退出码** (16 connections) — `docs/internals/verdict-model.md`
- **CLI JSON 契约页（手写源）** (14 connections) — `docs/internals/cli-json-contract.md`
- **执行与推进（internals）** (14 connections) — `docs/internals/execution-and-reconciliation.md`
- **云端后端的五个载体** (13 connections) — `docs/internals/cloud-backend-carriers.md`
- **架构总览：五层结构、一次 run 的生命周期、包与发行物** (11 connections) — `docs/internals/architecture-overview.md`
- **产物与证据：产物落在哪、哪一份回答哪个问题** (11 connections) — `docs/internals/artifacts-and-evidence.md`
- **一条确定性 step 的生命周期：从写下正则到云端命中** (11 connections) — `docs/internals/deterministic-step-lifecycle.md`
- **docs/internals 索引（主题归属表）** (8 connections) — `docs/internals/README.md`
- **error_type 类别集（assertion_failed / timeout / guardrail / network_error / engine_error）** (3 connections) — `docs/internals/verdict-model.md`
- **job 收场态与归因的优先级（有序短路四问）** (3 connections) — `docs/internals/verdict-model.md`
- **gherkai 用户指南索引** (3 connections) — `docs/user-guide/README.md`
- **图：job 收场态判定（有序短路四问）** (2 connections) — `docs/diagrams/verdict-model-job-outcome.svg`
- **图：判定四层归约（worker 侧汇总 / core 侧归约）** (2 connections) — `docs/diagrams/verdict-model-reduction-layers.svg`
- **一次 run 的生命周期主干（parse → scope 分组 → begin → 驱动 → 判定归约与报告）** (2 connections) — `docs/internals/architecture-overview.md`
- **五类产物（definition / 运行态 / 判定真值 / 派生导航 / 现场证据）** (2 connections) — `docs/internals/artifacts-and-evidence.md`
- **提交时刻固定 revision（定义期解析、运行期照抄）** (2 connections) — `docs/internals/cloud-backend-carriers.md`
- **派发决策链：注册表 → 内建 URL 导航 → AI catch-all** (2 connections) — `docs/internals/deterministic-step-lifecycle.md`
- **两个真值源一个岔口（local 目录 vs cloud variant 镜像）** (2 connections) — `docs/internals/deterministic-step-lifecycle.md`
- **收尾写序与提交点（判定明细 → run 终态 → RunReport）** (2 connections) — `docs/internals/execution-and-reconciliation.md`
- **job 超时预算的三路 enforce** (2 connections) — `docs/internals/execution-and-reconciliation.md`
- **四层归约：票 → step → scenario → job → run** (2 connections) — `docs/internals/verdict-model.md`
- **七个状态（五终态 + pending / running 两前置态）** (2 connections) — `docs/internals/verdict-model.md`
- **图：scenario 到 job 的分组** (1 connections) — `docs/diagrams/writing-features-scenario-to-job.svg`
- **同一条链的两种载体（--backend local / cloud 只替换 adapter）** (1 connections) — `docs/internals/architecture-overview.md`
- **五层职责划分（用例 / 产品 / 执行 / 浏览器 / 被测应用）** (1 connections) — `docs/internals/architecture-overview.md`
- *... and 13 more nodes in this community*

## Relationships

- [AWS Deploy Package Docs](AWS_Deploy_Package_Docs.md) (6 shared connections)
- [Contributor Guardrail Docs](Contributor_Guardrail_Docs.md) (2 shared connections)
- [Verdict Evidence Glossary](Verdict_Evidence_Glossary.md) (1 shared connections)
- [CLI Command Dispatch](CLI_Command_Dispatch.md) (1 shared connections)
- [JSON Field Contract Tests](JSON_Field_Contract_Tests.md) (1 shared connections)

## Source Files

- `docs/diagrams/verdict-model-job-outcome.svg`
- `docs/diagrams/verdict-model-reduction-layers.svg`
- `docs/diagrams/writing-features-scenario-to-job.svg`
- `docs/internals/README.md`
- `docs/internals/architecture-overview.md`
- `docs/internals/artifacts-and-evidence.md`
- `docs/internals/cli-json-contract.md`
- `docs/internals/cloud-backend-carriers.md`
- `docs/internals/deterministic-step-lifecycle.md`
- `docs/internals/execution-and-reconciliation.md`
- `docs/internals/verdict-model.md`
- `docs/user-guide/README.md`

## Audit Trail

- EXTRACTED: 72 (92%)
- INFERRED: 5 (6%)
- AMBIGUOUS: 1 (1%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*