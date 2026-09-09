# Execution Architecture Decisions

> 41 nodes · cohesion 0.07

## Key Concepts

- **组合根注入（选实现不由 module 自选）** (8 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **流式 JSON Lines 事件流（三级 started/done 对齐）** (7 connections) — `docs/adr/0024-worker-core-protocol.md`
- **plan(features, config) → Job[]** (6 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **schedule(run_meta, engines, sink, opts) → RunResult** (6 connections) — `docs/adr/0026-schedule-module.md`
- **Engine port（run_scope(job) → 事件流）** (5 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **云端 store adapter（DdbRunStore / S3ResultStore / S3ReportStore）** (5 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **RunPersistence（存储编排应用服务）** (5 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **FargateEngine（云端执行 adapter）** (4 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **ReportStore port（RunReport 归集）** (4 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **ResultStore port（数据面：判定真值唯一权威）** (4 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **RunStore port（控制面：RunMeta + RunState）** (4 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **ArtifactUploader（worker 产物上传组件）** (4 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **决策 A：cli --backend {local,cloud} 单旋钮** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **compose.build_local_stores / build_cloud_stores** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **三层切分（definition / 控制面运行态 / 数据面判定）** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **终止契约（schedule 下逻辑「停」、机制归 adapter/worker）** (3 connections) — `docs/adr/0024-worker-core-protocol.md`
- **ReportRef {kind, ref: ResourceUri, label}** (3 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **两层重试（worker 内建连段 + core job 级）** (3 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **核心库窄腰 core/（解析→分组→调度→收集，零引擎依赖）** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **决策 C：Fargate/region/profile 配置走 CLI 参数注入** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **Run 数据模型（Step/Scenario/Feature/Scope/Job/Run）** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **SubprocessEngine（单个参数化 adapter）** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **@scope:<name>（会话作用域 = 执行单元 Job）** (2 connections) — `docs/adr/0019-feature-tags-scope-and-engine.md`
- **worker 确定性 step 注册表（@deterministic）** (2 connections) — `docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md`
- **DynamoDB events 表作 events-out 传输** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- *... and 16 more nodes in this community*

## Relationships

- [ADR Index & Dev Docs](ADR_Index_%26_Dev_Docs.md) (1 shared connections)

## Source Files

- `docs/adr/0016-execution-architecture-core-lib-run-model.md`
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

## Audit Trail

- EXTRACTED: 58 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*