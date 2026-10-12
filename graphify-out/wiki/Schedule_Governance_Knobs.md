# Schedule Governance Knobs

> 42 nodes · cohesion 0.06

## Key Concepts

- **schedule(run_meta, engines, sink, opts)** (7 connections) — `docs/adr/0026-schedule-module.md`
- **worker 上传产物并报 s3:// ref** (6 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **index.html（判定明细树 + 产物导航，单文件零 JS）** (5 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **ReportStore.write（整 run 一次写）** (5 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **job 级网络瞬时故障重试（network_retry）** (4 connections) — `docs/adr/0026-schedule-module.md`
- **ScheduleOpts（治理旋钮 = 注入参数 + 保守默认）** (4 connections) — `docs/adr/0026-schedule-module.md`
- **ReportRef {kind, ref, label}** (4 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **两层重试（worker 内建连段 + core job 级）** (4 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
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
- **job 级乐观归约的内容完整前置（须见 scope_done）** (2 connections) — `docs/adr/0026-schedule-module.md`
- **不透明搬运铁律（model/wire/schedule 永不解引用 ref）** (2 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **RunReport = 归集索引（不融合内容）** (2 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **EX_WORKER_NETWORK = 80（退出码携带 network 信号）** (2 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **_is_transient_network / isTransientNetwork（异常链遍历 + 阶段收窄）** (2 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **network_error 分类（白名单具体瞬时类型）** (2 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- *... and 17 more nodes in this community*

## Relationships

- [Execution Architecture ADRs](Execution_Architecture_ADRs.md) (8 shared connections)
- [Artifact Upload Design](Artifact_Upload_Design.md) (1 shared connections)
- [Contributor Docs And ADRs](Contributor_Docs_And_ADRs.md) (1 shared connections)

## Source Files

- `docs/adr/0026-schedule-module.md`
- `docs/adr/0027-runreport-aggregation-index.md`
- `docs/adr/0028-transient-network-ssl-resilience.md`
- `docs/adr/0029-engine-artifacts-to-s3.md`

## Audit Trail

- EXTRACTED: 58 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*