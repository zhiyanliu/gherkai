# Execution Architecture ADRs

> 41 nodes · cohesion 0.08

## Key Concepts

- **ADR 0024: worker–core 协议** (42 connections) — `docs/adr/0024-worker-core-protocol.md`
- **ADR 0042: step 证据与 explain** (23 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **ADR 0033: IaC AWS 后端与组合装配** (19 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **novaact 引擎开发笔记** (13 connections) — `engines/novaact/DEVELOPMENT.md`
- **ADR 0026: schedule 模块（job 间并发调度 + 失败隔离 + 优雅终止）** (12 connections) — `docs/adr/0026-schedule-module.md`
- **ADR 0029: 引擎产物上 S3** (12 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **ADR 0032: Fargate 执行环境** (11 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **ADR 0028: 瞬时网络/SSL 韧性** (10 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **ADR 0028: 网络/SSL 瞬时错误鲁棒性（两层重试 + network_error）** (10 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **ADR 0017: 云端执行选 Fargate** (9 connections) — `docs/adr/0017-cloud-execution-fargate-over-runtime.md`
- **ADR 0027: RunReport 跨引擎归集索引** (9 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **ADR 0029: engine artifact→S3（worker 上传、注入驱动）** (6 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **ADR 0031: job 生命周期状态与 severity** (5 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **输入契约：一个 scope 的 Job（展开后的有序 step）** (4 connections) — `docs/adr/0024-worker-core-protocol.md`
- **ADR 0016: 执行架构与核心库 run 模型** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **Fargate/ECS RunTask 执行后端** (3 connections) — `docs/adr/0017-cloud-execution-fargate-over-runtime.md`
- **安全点（step_done/act 边界）提前上传 + SIGTERM handler 兜底** (3 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **AgentCore Evaluations（去优先级的相邻选项）** (2 connections) — `docs/adr/0017-cloud-execution-fargate-over-runtime.md`
- **AgentCore Runtime（被否的执行面选项）** (2 connections) — `docs/adr/0017-cloud-execution-fargate-over-runtime.md`
- **assertionVotes 投票次数** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **成本信封：engine 只报原生量、core 只合计** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **errorType 规范化失败分类** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **votes 只记 tally 不记 per-vote 序列** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **Upload Error Classification** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **ADR 0030: 实时持久化接缝** (2 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- *... and 16 more nodes in this community*

## Relationships

- [Contributor Docs And ADRs](Contributor_Docs_And_ADRs.md) (29 shared connections)
- [Engine And Model ADRs](Engine_And_Model_ADRs.md) (15 shared connections)
- [Architecture Diagram Catalog](Architecture_Diagram_Catalog.md) (10 shared connections)
- [Shared Feature Boundary ADRs](Shared_Feature_Boundary_ADRs.md) (8 shared connections)
- [Schedule Governance Knobs](Schedule_Governance_Knobs.md) (8 shared connections)
- [Packaging And Capability Surface](Packaging_And_Capability_Surface.md) (6 shared connections)
- [Artifact Upload Design](Artifact_Upload_Design.md) (3 shared connections)
- [Fargate Deployment Wiring](Fargate_Deployment_Wiring.md) (3 shared connections)
- [E2E Harness Script](E2E_Harness_Script.md) (2 shared connections)
- [Status Severity & Exit Codes](Status_Severity_%26_Exit_Codes.md) (2 shared connections)
- [Composition Root Architecture](Composition_Root_Architecture.md) (1 shared connections)
- [Docs And Skill Guardrails](Docs_And_Skill_Guardrails.md) (1 shared connections)

## Source Files

- `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- `docs/adr/0017-cloud-execution-fargate-over-runtime.md`
- `docs/adr/0019-feature-tags-scope-and-engine.md`
- `docs/adr/0024-worker-core-protocol.md`
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
- `engines/novaact/DEVELOPMENT.md`

## Audit Trail

- EXTRACTED: 160 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*