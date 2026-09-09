# ADR Index & Dev Docs

> 34 nodes · cohesion 0.25

## Key Concepts

- **ADR 0016 执行架构** (24 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **ADR 0024 worker↔core 协议** (21 connections) — `docs/adr/0024-worker-core-protocol.md`
- **cli/DEVELOPMENT.md** (20 connections) — `cli/DEVELOPMENT.md`
- **deploy_aws/DEVELOPMENT.md** (20 connections) — `deploy_aws/DEVELOPMENT.md`
- **ADR 0037 分发与打包** (20 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **DEVELOPMENT.md** (18 connections) — `DEVELOPMENT.md`
- **novaact/DEVELOPMENT.md** (17 connections) — `engines/novaact/DEVELOPMENT.md`
- **ADR 0033 IaC 与装配** (15 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **execution-and-reconciliation.md** (15 connections) — `docs/guides/execution-and-reconciliation.md`
- **midscene/DEVELOPMENT.md** (15 connections) — `engines/midscene/DEVELOPMENT.md`
- **ADR 0026 schedule 契约** (14 connections) — `docs/adr/0026-schedule-module.md`
- **ADR 0034 无状态跑批 reconciler** (14 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **ADR 0030 实时写接缝** (13 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **ADR 0038 镜像交付** (13 connections) — `docs/adr/0038-worker-image-delivery.md`
- **runtime/DEVELOPMENT.md** (12 connections) — `runtime/DEVELOPMENT.md`
- **ADR 0022 薄 worker** (11 connections) — `docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md`
- **ADR 0036 能力自述** (11 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **ADR 0027 报告聚合** (10 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **ADR 0028 瞬时网络/SSL 韧性** (9 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **ADR 0029 产物上传 S3** (9 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **ADR 0020 step 措辞与角色边界** (8 connections) — `docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md`
- **ADR 0031: job 生命周期态 skipped/aborted + severity 数值序** (8 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **ADR 0019 feature 标签定 scope 与引擎** (7 connections) — `docs/adr/0019-feature-tags-scope-and-engine.md`
- **ADR 0025: plan 模块（.feature → job 列表）** (7 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **ADR 0032: Fargate 执行环境（中断丢失/grace/即时上传）** (7 connections) — `docs/adr/0032-fargate-execution-environment.md`
- *... and 9 more nodes in this community*

## Relationships

- [Foundational ADR Principles](Foundational_ADR_Principles.md) (16 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (10 shared connections)
- [Deploy AWS README](Deploy_AWS_README.md) (8 shared connections)
- [Status Model & Concurrency Gates](Status_Model_%26_Concurrency_Gates.md) (7 shared connections)
- [Project Conventions & README Guards](Project_Conventions_%26_README_Guards.md) (6 shared connections)
- [Midscene Worker Integration Docs](Midscene_Worker_Integration_Docs.md) (3 shared connections)
- [CI and Release Workflows](CI_and_Release_Workflows.md) (2 shared connections)
- [CDK App & Deploy CLI](CDK_App_%26_Deploy_CLI.md) (2 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (2 shared connections)
- [Stack Synth Fixtures](Stack_Synth_Fixtures.md) (2 shared connections)
- [User-Facing Text Policy (ADR 0039)](User-Facing_Text_Policy_%28ADR_0039%29.md) (2 shared connections)
- [Worker READMEs and Harness Docs](Worker_READMEs_and_Harness_Docs.md) (2 shared connections)

## Source Files

- `.github/workflows/README.md`
- `DEVELOPMENT.md`
- `cli/DEVELOPMENT.md`
- `deploy_aws/DEVELOPMENT.md`
- `docs/adr/0005-single-shared-feature-file.md`
- `docs/adr/0013-cross-engine-sharing-boundary.md`
- `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- `docs/adr/0017-cloud-execution-fargate-over-runtime.md`
- `docs/adr/0019-feature-tags-scope-and-engine.md`
- `docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md`
- `docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md`
- `docs/adr/0024-worker-core-protocol.md`
- `docs/adr/0025-plan-module-feature-to-jobs.md`
- `docs/adr/0026-schedule-module.md`
- `docs/adr/0027-runreport-aggregation-index.md`
- `docs/adr/0028-transient-network-ssl-resilience.md`
- `docs/adr/0029-engine-artifacts-to-s3.md`
- `docs/adr/0030-realtime-persistence-seam.md`
- `docs/adr/0031-job-lifecycle-states-and-severity.md`

## Audit Trail

- EXTRACTED: 224 (100%)
- INFERRED: 1 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*