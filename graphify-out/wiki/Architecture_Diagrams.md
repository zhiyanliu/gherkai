# Architecture Diagrams

> 42 nodes · cohesion 0.07

## Key Concepts

- **架构全景（internals）** (25 connections) — `docs/internals/architecture-overview.md`
- **确定性 step 生命周期** (25 connections) — `docs/internals/deterministic-step-lifecycle.md`
- **判定模型：四层归约、状态与退出码** (14 connections) — `docs/internals/verdict-model.md`
- **CLI --json 字段契约** (10 connections) — `docs/internals/cli-json-contract.md`
- **执行与推进模型导览：run / submit × local / cloud** (10 connections) — `docs/internals/execution-and-reconciliation.md`
- **docs/internals 索引（主题归属表）** (9 connections) — `docs/internals/README.md`
- **reconcile.tick（无状态编排步骤）** (6 connections) — `docs/internals/execution-and-reconciliation.md`
- **七个状态（五终态 + 两前置态）** (6 connections) — `docs/internals/verdict-model.md`
- **job 墙钟超时预算与三路 enforce** (5 connections) — `docs/internals/execution-and-reconciliation.md`
- **kicker Lambda（冷启动器）** (4 connections) — `docs/internals/execution-and-reconciliation.md`
- **四层归约：票 → step → scenario → job → run** (4 connections) — `docs/internals/verdict-model.md`
- **detached 标记与两道拦截** (3 connections) — `docs/internals/execution-and-reconciliation.md`
- **五层结构（用例/产品/执行/浏览器/被测应用）** (2 connections) — `docs/internals/architecture-overview.md`
- **一次 run 的生命周期（parse→分组→begin→驱动→判定归约与报告）** (2 connections) — `docs/internals/architecture-overview.md`
- **证据链的串接（worker 产出→判定真值指针→explain 解引用）** (2 connections) — `docs/internals/artifacts-and-evidence.md`
- **确定性 step 不产产物（已知缺口）** (2 connections) — `docs/internals/deterministic-step-lifecycle.md`
- **收尾写序与提交点（try_finalize）** (2 connections) — `docs/internals/execution-and-reconciliation.md`
- **同一条事件流的四条物理通道** (2 connections) — `docs/internals/execution-and-reconciliation.md`
- **exit-observer Lambda（退出观察者）** (2 connections) — `docs/internals/execution-and-reconciliation.md`
- **reconciler Lambda（主推进器）** (2 connections) — `docs/internals/execution-and-reconciliation.md`
- **schedule（同步驱动 / 前台在线循环）** (2 connections) — `docs/internals/execution-and-reconciliation.md`
- **error_type 类别集** (2 connections) — `docs/internals/verdict-model.md`
- **各命令退出码语义** (2 connections) — `docs/internals/verdict-model.md`
- **--expose-local 隧道与 --tunnel-ttl** (2 connections) — `docs/user-guide/local-app-testing.md`
- **执行方式 × 执行后端四种组合** (2 connections) — `docs/user-guide/running-and-results.md`
- *... and 17 more nodes in this community*

## Relationships

- [Package Contributor Docs](Package_Contributor_Docs.md) (29 shared connections)
- [Agent Skill Reference Docs](Agent_Skill_Reference_Docs.md) (11 shared connections)
- [Runtime Architecture Concepts](Runtime_Architecture_Concepts.md) (3 shared connections)
- [Agent Skill ADRs](Agent_Skill_ADRs.md) (3 shared connections)
- [Verdict Status Aggregation](Verdict_Status_Aggregation.md) (2 shared connections)
- [Project Conventions Docs](Project_Conventions_Docs.md) (1 shared connections)

## Source Files

- `docs/diagrams/architecture-overview-layers.svg`
- `docs/diagrams/architecture-overview-run-lifecycle.svg`
- `docs/diagrams/deterministic-steps-registry-overview.svg`
- `docs/diagrams/deterministic-steps-truth-sources.svg`
- `docs/diagrams/readme-runtime-topology.svg`
- `docs/diagrams/run-execution.svg`
- `docs/diagrams/verdict-model-job-outcome.svg`
- `docs/diagrams/verdict-model-reduction-layers.svg`
- `docs/diagrams/writing-features-scenario-to-job.svg`
- `docs/internals/README.md`
- `docs/internals/architecture-overview.md`
- `docs/internals/artifacts-and-evidence.md`
- `docs/internals/cli-json-contract.md`
- `docs/internals/deterministic-step-lifecycle.md`
- `docs/internals/execution-and-reconciliation.md`
- `docs/internals/verdict-model.md`
- `docs/user-guide/local-app-testing.md`
- `docs/user-guide/running-and-results.md`
- `docs/user-guide/writing-features.md`

## Audit Trail

- EXTRACTED: 98 (92%)
- INFERRED: 6 (6%)
- AMBIGUOUS: 3 (3%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*