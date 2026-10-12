# Schedule Concurrency & Termination

> 51 nodes · cohesion 0.06

## Key Concepts

- **ADR 0026: schedule 模块（job 间并发调度 + 失败隔离 + 优雅终止）** (12 connections) — `docs/adr/0026-schedule-module.md`
- **ADR 0028: 网络/SSL 瞬时错误鲁棒性（两层重试 + network_error）** (10 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **ADR 0027: RunReport 跨引擎归集索引** (9 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **schedule(run_meta, engines, sink, opts)** (7 connections) — `docs/adr/0026-schedule-module.md`
- **ADR 0029: engine artifact→S3（worker 上传、注入驱动）** (6 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **worker 上传产物并报 s3:// ref** (6 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **index.html（判定明细树 + 产物导航，单文件零 JS）** (5 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **ReportStore.write（整 run 一次写）** (5 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **ADR 0031: job 生命周期状态与 severity** (5 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **job 级网络瞬时故障重试（network_retry）** (4 connections) — `docs/adr/0026-schedule-module.md`
- **ScheduleOpts（治理旋钮 = 注入参数 + 保守默认）** (4 connections) — `docs/adr/0026-schedule-module.md`
- **ReportRef {kind, ref, label}** (4 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **两层重试（worker 内建连段 + core job 级）** (4 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **ADR 0016: 执行架构与核心库 run 模型** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **优雅终止：schedule 只调 handle.stop(grace)** (3 connections) — `docs/adr/0026-schedule-module.md`
- **per-job 墙钟预算 Job.timeout_s 超时兜底** (3 connections) — `docs/adr/0026-schedule-module.md`
- **status 三级归约（scenario→job→run）** (3 connections) — `docs/adr/0026-schedule-module.md`
- **step_skipped 归约（短路步零污染 scenario 判定）** (3 connections) — `docs/adr/0026-schedule-module.md`
- **href 相对化（local 相对 / cloud 恒等 ref）** (3 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **manifest.json（薄信封 + 扁平 report_index）** (3 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **ResourceUri（带 scheme 的统一资源指针）** (3 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **run_id（归集索引主键，生成权在组合根）** (3 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **compose.prune_empty_dirs()** (3 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **失败隔离 / failFast 旋钮** (2 connections) — `docs/adr/0026-schedule-module.md`
- **_heartbeat_wrap（静默 worker 心跳注入）** (2 connections) — `docs/adr/0026-schedule-module.md`
- *... and 26 more nodes in this community*

## Relationships

- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (6 shared connections)
- [Cloud Backend Docs & Diagrams](Cloud_Backend_Docs_%26_Diagrams.md) (4 shared connections)
- [Model Selection ADRs](Model_Selection_ADRs.md) (1 shared connections)
- [Artifact Upload Design](Artifact_Upload_Design.md) (1 shared connections)

## Source Files

- `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- `docs/adr/0019-feature-tags-scope-and-engine.md`
- `docs/adr/0026-schedule-module.md`
- `docs/adr/0027-runreport-aggregation-index.md`
- `docs/adr/0028-transient-network-ssl-resilience.md`
- `docs/adr/0029-engine-artifacts-to-s3.md`
- `docs/adr/0030-realtime-persistence-seam.md`
- `docs/adr/0031-job-lifecycle-states-and-severity.md`
- `docs/adr/0034-detached-batch-reconciler.md`

## Audit Trail

- EXTRACTED: 84 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*