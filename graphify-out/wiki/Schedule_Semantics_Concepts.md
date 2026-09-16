# Schedule Semantics Concepts

> 43 nodes · cohesion 0.06

## Key Concepts

- **RunResult（事件流归约终值）** (6 connections) — `docs/adr/0026-schedule-module.md`
- **schedule(run_meta, engines, sink, opts, ...)** (5 connections) — `docs/adr/0026-schedule-module.md`
- **ReportRef {kind, ref, label}** (5 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **ReportStore.write（整 run 一次写）** (5 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **ScheduleOpts（并发/隔离/grace/重试/心跳旋钮）** (4 connections) — `docs/adr/0026-schedule-module.md`
- **make_href / href 相对化** (4 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **RunReport（统一目录 + 导航入口）** (4 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **两层重试（worker 内 + core/schedule）** (4 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **worker 上传产物并报 s3:// ref** (4 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **优雅终止（schedule 只下逻辑「停」指令）** (3 connections) — `docs/adr/0026-schedule-module.md`
- **job 级网络重试（network_retry，默认 0）** (3 connections) — `docs/adr/0026-schedule-module.md`
- **RunMeta（run definition: run_id + created_at + jobs）** (3 connections) — `docs/adr/0026-schedule-module.md`
- **manifest.json（薄信封 + 扁平 report_index）** (3 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **不透明搬运铁律（model/wire/schedule/ReportStore）** (3 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **ResourceUri（NewType 统一资源指针）** (3 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **_is_transient_network / isTransientNetwork** (3 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **core/ReportStore 一行不改（s3:// 天然穿透）** (3 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **上传成功后删本地** (3 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **墙钟时长归约（duration_ms 四级）** (2 connections) — `docs/adr/0026-schedule-module.md`
- **failFast 与失败隔离** (2 connections) — `docs/adr/0026-schedule-module.md`
- **_heartbeat_wrap（静默 worker 存活心跳）** (2 connections) — `docs/adr/0026-schedule-module.md`
- **Job.timeout_s 超时兜底** (2 connections) — `docs/adr/0026-schedule-module.md`
- **index.html（判定明细树 + 产物导航）** (2 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **JobResult 持有 Job（engine/scope_id property delegate）** (2 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **run_id（归集索引主键，组合根生成）** (2 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- *... and 18 more nodes in this community*

## Relationships

- [Architecture ADR Decisions](Architecture_ADR_Decisions.md) (5 shared connections)
- [Termination & Engine Ports](Termination_%26_Engine_Ports.md) (1 shared connections)

## Source Files

- `docs/adr/0026-schedule-module.md`
- `docs/adr/0027-runreport-aggregation-index.md`
- `docs/adr/0028-transient-network-ssl-resilience.md`
- `docs/adr/0029-engine-artifacts-to-s3.md`

## Audit Trail

- EXTRACTED: 55 (96%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 1 (2%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*