# Core Protocol Documentation

> 56 nodes · cohesion 0.06

## Key Concepts

- **ADR 0024 worker↔核心协议** (36 connections) — `docs/adr/0024-worker-core-protocol.md`
- **ADR 0034 无状态批量运行** (23 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **ADR 0030 实时写接缝** (22 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **ADR 0042 step 证据与 explain** (22 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **core 包 contributor 文档** (13 connections) — `core/DEVELOPMENT.md`
- **ADR 0027 RunReport 归集索引** (13 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **ADR 0028: 瞬时网络/SSL 韧性** (13 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **ADR 0026: schedule 模块** (12 connections) — `docs/adr/0026-schedule-module.md`
- **ADR 0031 job 生命周期状态与严重度** (10 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **ADR 0025 plan 模块（解析 + scope 分组）** (8 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **core 测试说明（单测 + 集成测试）** (6 connections) — `core/tests/README.md`
- **plan() 接口** (5 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **worker 上传 S3、报 s3:// ref** (5 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **stopTimeout=120 / grace 预算校准** (5 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **ReportRef {kind, ref, label}** (4 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **task role IAM 最小权限** (4 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **流式 JSON Lines 事件流（三级 started/done 对齐）** (3 connections) — `docs/adr/0024-worker-core-protocol.md`
- **reportRefs（不透明产物引用，kind 开放标签）** (3 connections) — `docs/adr/0024-worker-core-protocol.md`
- **S3 Key Mirrors Local Run Tree** (3 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Mandatory Upload Timeouts (Bounded Worker Exit)** (3 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **act/step 安全点提前上传** (3 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **e2e_harness 使用说明** (3 connections) — `tools/e2e_harness.md`
- **artifact_upload.py (Nova uploader module)** (2 connections) — `artifact_upload.py`
- **step_skipped 事件（scope 内短路）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **JobSource（job 入口可注入接口）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- *... and 31 more nodes in this community*

## Relationships

- [CLI Docs and ADRs](CLI_Docs_and_ADRs.md) (59 shared connections)
- [Architecture Diagrams](Architecture_Diagrams.md) (13 shared connections)
- [Engine Runtime Mechanisms](Engine_Runtime_Mechanisms.md) (6 shared connections)
- [Artifact Upload Strategy](Artifact_Upload_Strategy.md) (5 shared connections)
- [Skill and Packaging Features](Skill_and_Packaging_Features.md) (5 shared connections)
- [Skill and Release ADRs](Skill_and_Release_ADRs.md) (3 shared connections)
- [Lifecycle Status Model](Lifecycle_Status_Model.md) (3 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (2 shared connections)
- [Cloud Store Wiring](Cloud_Store_Wiring.md) (2 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (1 shared connections)
- [Detached Run Mechanisms](Detached_Run_Mechanisms.md) (1 shared connections)
- [Agent Skill Reference Docs](Agent_Skill_Reference_Docs.md) (1 shared connections)

## Source Files

- `artifact_upload.py`
- `core/DEVELOPMENT.md`
- `core/tests/README.md`
- `docs/adr/0024-worker-core-protocol.md`
- `docs/adr/0025-plan-module-feature-to-jobs.md`
- `docs/adr/0026-schedule-module.md`
- `docs/adr/0027-runreport-aggregation-index.md`
- `docs/adr/0028-transient-network-ssl-resilience.md`
- `docs/adr/0029-engine-artifacts-to-s3.md`
- `docs/adr/0030-realtime-persistence-seam.md`
- `docs/adr/0031-job-lifecycle-states-and-severity.md`
- `docs/adr/0032-fargate-execution-environment.md`
- `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- `docs/adr/0034-detached-batch-reconciler.md`
- `docs/adr/0042-step-evidence-and-explain.md`
- `tools/e2e_harness.md`

## Audit Trail

- EXTRACTED: 179 (96%)
- INFERRED: 7 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*