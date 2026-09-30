# Architecture Diagrams

> 44 nodes · cohesion 0.07

## Key Concepts

- **架构全景（internals）** (26 connections) — `docs/internals/architecture-overview.md`
- **确定性 step 生命周期** (26 connections) — `docs/internals/deterministic-step-lifecycle.md`
- **产物与证据** (25 connections) — `docs/internals/artifacts-and-evidence.md`
- **云端后端载体** (21 connections) — `docs/internals/cloud-backend-carriers.md`
- **判定模型：四层归约、状态与退出码** (15 connections) — `docs/internals/verdict-model.md`
- **CLI --json 字段契约** (12 connections) — `docs/internals/cli-json-contract.md`
- **执行与推进模型导览：run / submit × local / cloud** (11 connections) — `docs/internals/execution-and-reconciliation.md`
- **docs/internals 索引（主题归属表）** (9 connections) — `docs/internals/README.md`
- **七个状态（五终态 + 两前置态）** (6 connections) — `docs/internals/verdict-model.md`
- **四层归约：票 → step → scenario → job → run** (4 connections) — `docs/internals/verdict-model.md`
- **本机与云端：同一条链的两种载体** (2 connections) — `docs/internals/architecture-overview.md`
- **五层结构（用例/产品/执行/浏览器/被测应用）** (2 connections) — `docs/internals/architecture-overview.md`
- **一次 run 的生命周期（parse→分组→begin→驱动→判定归约与报告）** (2 connections) — `docs/internals/architecture-overview.md`
- **证据链的串接（worker 产出→判定真值指针→explain 解引用）** (2 connections) — `docs/internals/artifacts-and-evidence.md`
- **五个载体（stack / Lambda asset / 基础镜像 / variant 镜像 / SSM）** (2 connections) — `docs/internals/cloud-backend-carriers.md`
- **提交时刻固定 task-def revision（定义期解析、运行期照抄）** (2 connections) — `docs/internals/cloud-backend-carriers.md`
- **确定性 step 不产产物（已知缺口）** (2 connections) — `docs/internals/deterministic-step-lifecycle.md`
- **两个真值源：local 的 steps 目录 vs cloud 的 variant 镜像** (2 connections) — `docs/internals/deterministic-step-lifecycle.md`
- **收尾写序与提交点（try_finalize）** (2 connections) — `docs/internals/execution-and-reconciliation.md`
- **各命令退出码语义** (2 connections) — `docs/internals/verdict-model.md`
- **执行方式 × 执行后端四种组合** (2 connections) — `docs/user-guide/running-and-results.md`
- **AI 断言投票（--assertion-votes）** (2 connections) — `docs/user-guide/writing-features.md`
- **图：五层全景** (1 connections) — `docs/diagrams/architecture-overview-layers.svg`
- **图：一次 run 的主干** (1 connections) — `docs/diagrams/architecture-overview-run-lifecycle.svg`
- **图：证据链** (1 connections) — `docs/diagrams/artifacts-evidence-chain.svg`
- *... and 19 more nodes in this community*

## Relationships

- [CLI Docs and ADRs](CLI_Docs_and_ADRs.md) (23 shared connections)
- [Glossary and Changelog](Glossary_and_Changelog.md) (15 shared connections)
- [Core Protocol Documentation](Core_Protocol_Documentation.md) (13 shared connections)
- [Skill and Packaging Features](Skill_and_Packaging_Features.md) (3 shared connections)
- [Skill and Release ADRs](Skill_and_Release_ADRs.md) (3 shared connections)
- [Advancement Channels](Advancement_Channels.md) (2 shared connections)
- [Lifecycle Status Model](Lifecycle_Status_Model.md) (2 shared connections)
- [Project Conventions Glossary](Project_Conventions_Glossary.md) (1 shared connections)
- [Agent Skill Reference Docs](Agent_Skill_Reference_Docs.md) (1 shared connections)

## Source Files

- `docs/diagrams/architecture-overview-layers.svg`
- `docs/diagrams/architecture-overview-run-lifecycle.svg`
- `docs/diagrams/artifacts-evidence-chain.svg`
- `docs/diagrams/cloud-backend-carriers-revision-pinning.svg`
- `docs/diagrams/cloud-delivery-identity.svg`
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
- `docs/internals/cloud-backend-carriers.md`
- `docs/internals/deterministic-step-lifecycle.md`
- `docs/internals/execution-and-reconciliation.md`
- `docs/internals/verdict-model.md`

## Audit Trail

- EXTRACTED: 122 (92%)
- INFERRED: 7 (5%)
- AMBIGUOUS: 3 (2%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*