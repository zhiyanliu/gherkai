# Cloud Backend Docs & Diagrams

> 49 nodes · cohesion 0.08

## Key Concepts

- **执行与推进模型导览（run/submit × local/cloud）** (27 connections) — `docs/internals/execution-and-reconciliation.md`
- **判定的计算路径：从单次投票到退出码** (23 connections) — `docs/internals/verdict-model.md`
- **ADR 0033: IaC AWS 后端与组合装配** (19 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **gherkai-deploy-aws contributor 手册** (16 connections) — `deploy_aws/DEVELOPMENT.md`
- **产物与证据：落点与阅读顺序（local × cloud）** (16 connections) — `docs/internals/artifacts-and-evidence.md`
- **云端后端的五个载体与改动传播** (16 connections) — `docs/internals/cloud-backend-carriers.md`
- **架构总览：五层结构、一次 run 的生命周期、包与发行物** (15 connections) — `docs/internals/architecture-overview.md`
- **一条确定性 step 的生命周期** (15 connections) — `docs/internals/deterministic-step-lifecycle.md`
- **ADR 0032: Fargate 执行环境** (11 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **Bundled JetBrains Mono WOFF2 Subsets** (11 connections) — `docs/diagrams/artifacts-evidence-chain.svg`
- **Internals 入口** (10 connections) — `docs/internals/README.md`
- **ADR 0017: 云端执行选 Fargate** (9 connections) — `docs/adr/0017-cloud-execution-fargate-over-runtime.md`
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
- **cli/DEVELOPMENT.md** (2 connections) — `core/DEVELOPMENT.md`
- **AgentCore Evaluations（去优先级的相邻选项）** (2 connections) — `docs/adr/0017-cloud-execution-fargate-over-runtime.md`
- *... and 24 more nodes in this community*

## Relationships

- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (28 shared connections)
- [Project Docs & Glossary](Project_Docs_%26_Glossary.md) (17 shared connections)
- [Model Selection ADRs](Model_Selection_ADRs.md) (11 shared connections)
- [Shared Feature Scope ADRs](Shared_Feature_Scope_ADRs.md) (8 shared connections)
- [Schedule Concurrency & Termination](Schedule_Concurrency_%26_Termination.md) (4 shared connections)
- [Release & Versioning Concepts](Release_%26_Versioning_Concepts.md) (3 shared connections)
- [CDK App & AWS Provider CLI](CDK_App_%26_AWS_Provider_CLI.md) (2 shared connections)
- [Deploy Provider & Container Seam](Deploy_Provider_%26_Container_Seam.md) (2 shared connections)
- [Browser And Tunnel Decisions](Browser_And_Tunnel_Decisions.md) (2 shared connections)
- [Backend CDK Stack Constructs](Backend_CDK_Stack_Constructs.md) (1 shared connections)
- [Worker Image Mapping & Cleanup](Worker_Image_Mapping_%26_Cleanup.md) (1 shared connections)
- [Execution Backend Choice](Execution_Backend_Choice.md) (1 shared connections)

## Source Files

- `core/DEVELOPMENT.md`
- `deploy_aws/DEVELOPMENT.md`
- `docs/adr/0017-cloud-execution-fargate-over-runtime.md`
- `docs/adr/0032-fargate-execution-environment.md`
- `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
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

## Audit Trail

- EXTRACTED: 157 (90%)
- INFERRED: 10 (6%)
- AMBIGUOUS: 7 (4%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*