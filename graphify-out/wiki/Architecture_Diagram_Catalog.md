# Architecture Diagram Catalog

> 44 nodes · cohesion 0.08

## Key Concepts

- **执行与推进模型导览（run/submit × local/cloud）** (27 connections) — `docs/internals/execution-and-reconciliation.md`
- **判定的计算路径：从单次投票到退出码** (23 connections) — `docs/internals/verdict-model.md`
- **产物与证据：落点与阅读顺序（local × cloud）** (16 connections) — `docs/internals/artifacts-and-evidence.md`
- **云端后端的五个载体与改动传播** (16 connections) — `docs/internals/cloud-backend-carriers.md`
- **架构总览：五层结构、一次 run 的生命周期、包与发行物** (15 connections) — `docs/internals/architecture-overview.md`
- **一条确定性 step 的生命周期** (15 connections) — `docs/internals/deterministic-step-lifecycle.md`
- **Bundled JetBrains Mono WOFF2 Subsets** (11 connections) — `docs/diagrams/artifacts-evidence-chain.svg`
- **Internals 入口** (10 connections) — `docs/internals/README.md`
- **gherkai CLI 的 --json 字段契约** (9 connections) — `docs/internals/cli-json-contract.md`
- **Cloud Delivery Identity Diagram** (5 connections) — `docs/diagrams/cloud-delivery-identity.svg`
- **Execution Timeout Chain Diagram** (4 connections) — `docs/diagrams/execution-timeout-chain.svg`
- **Archify Diagram Viewer Preset (classic, showcase quality)** (3 connections) — `docs/diagrams/artifacts-evidence-chain.svg`
- **Artifacts Evidence Chain Diagram** (3 connections) — `docs/diagrams/artifacts-evidence-chain.svg`
- **Cloud Backend Carriers Revision Pinning Diagram** (3 connections) — `docs/diagrams/cloud-backend-carriers-revision-pinning.svg`
- **Cloud Backend Upgrade Windows Diagram** (3 connections) — `docs/diagrams/cloud-backend-upgrade-windows.svg`
- **Deterministic Steps Registry Overview Diagram** (3 connections) — `docs/diagrams/deterministic-steps-registry-overview.svg`
- **Deterministic Steps Truth Sources Diagram** (3 connections) — `docs/diagrams/deterministic-steps-truth-sources.svg`
- **Execution Cloud Cascade Diagram** (3 connections) — `docs/diagrams/execution-cloud-cascade.svg`
- **五层职责切分（用例/产品/执行/浏览器/被测应用）** (3 connections) — `docs/internals/architecture-overview.md`
- **Configuration Env Inheritance Diagram** (2 connections) — `docs/diagrams/configuration-env-inheritance.svg`
- **Execution Detached Gates Diagram** (2 connections) — `docs/diagrams/execution-detached-gates.svg`
- **Getting Started Component Ownership Diagram** (2 connections) — `docs/diagrams/getting-started-component-ownership.svg`
- **kind=evidence 的解引用边界** (2 connections) — `docs/internals/artifacts-and-evidence.md`
- **判定真值 jobs/*.json** (2 connections) — `docs/internals/artifacts-and-evidence.md`
- **提交时刻解析并固定 task-def revision** (2 connections) — `docs/internals/cloud-backend-carriers.md`
- *... and 19 more nodes in this community*

## Relationships

- [Contributor Docs And ADRs](Contributor_Docs_And_ADRs.md) (16 shared connections)
- [Cloud Backend Concepts](Cloud_Backend_Concepts.md) (13 shared connections)
- [Execution Architecture ADRs](Execution_Architecture_ADRs.md) (10 shared connections)
- [Engine And Model ADRs](Engine_And_Model_ADRs.md) (4 shared connections)
- [Shared Feature Boundary ADRs](Shared_Feature_Boundary_ADRs.md) (3 shared connections)
- [Packaging And Capability Surface](Packaging_And_Capability_Surface.md) (2 shared connections)
- [Midscene Worker Entry](Midscene_Worker_Entry.md) (1 shared connections)
- [Docs And Skill Guardrails](Docs_And_Skill_Guardrails.md) (1 shared connections)

## Source Files

- `docs/diagrams/artifacts-evidence-chain.svg`
- `docs/diagrams/cloud-backend-carriers-revision-pinning.svg`
- `docs/diagrams/cloud-backend-upgrade-windows.svg`
- `docs/diagrams/cloud-delivery-identity.svg`
- `docs/diagrams/configuration-env-inheritance.svg`
- `docs/diagrams/deterministic-steps-registry-overview.svg`
- `docs/diagrams/deterministic-steps-truth-sources.svg`
- `docs/diagrams/execution-cloud-cascade.svg`
- `docs/diagrams/execution-detached-gates.svg`
- `docs/diagrams/execution-timeout-chain.svg`
- `docs/diagrams/getting-started-component-ownership.svg`
- `docs/diagrams/local-app-testing-tunnel-topology.svg`
- `docs/diagrams/readme-runtime-topology.svg`
- `docs/diagrams/run-execution.svg`
- `docs/diagrams/verdict-model-job-outcome.svg`
- `docs/diagrams/verdict-model-reduction-layers.svg`
- `docs/diagrams/writing-features-scenario-to-job.svg`
- `docs/internals/README.md`
- `docs/internals/architecture-overview.md`
- `docs/internals/artifacts-and-evidence.md`

## Audit Trail

- EXTRACTED: 113 (88%)
- INFERRED: 9 (7%)
- AMBIGUOUS: 7 (5%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*