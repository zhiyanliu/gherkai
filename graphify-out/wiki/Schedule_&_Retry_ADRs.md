# Schedule & Retry ADRs

> 9 nodes · cohesion 0.25

## Key Concepts

- **schedule(run_meta, engines, sink, opts) -> RunResult** (7 connections) — `docs/adr/0026-schedule-module.md`
- **ADR 0028: 网络/SSL 瞬时错误两层重试** (5 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **ADR 0026: schedule 模块 — 并发调度/失败隔离/优雅终止** (4 connections) — `docs/adr/0026-schedule-module.md`
- **ADR 0025: plan 模块 — .feature → job 列表** (2 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **_heartbeat_wrap（静默 worker 超时兜底）** (2 connections) — `docs/adr/0026-schedule-module.md`
- **三级归约（status + 原生量成本 + 墙钟）** (2 connections) — `docs/adr/0026-schedule-module.md`
- **network_error 分类（白名单具体瞬时类型）** (2 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **EX_WORKER_NETWORK = 80（带外退出码信号）** (1 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **重试域边界 = scope_started emit 之前** (1 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`

## Relationships

- [Report Store & Manifest](Report_Store_%26_Manifest.md) (2 shared connections)
- [Artifact Upload & Shutdown](Artifact_Upload_%26_Shutdown.md) (2 shared connections)
- [Plan Module Seams](Plan_Module_Seams.md) (1 shared connections)
- [Run Persistence & Preflight](Run_Persistence_%26_Preflight.md) (1 shared connections)
- [Detached Run Orchestration](Detached_Run_Orchestration.md) (1 shared connections)
- [Report Aggregation & Status](Report_Aggregation_%26_Status.md) (1 shared connections)

## Source Files

- `docs/adr/0025-plan-module-feature-to-jobs.md`
- `docs/adr/0026-schedule-module.md`
- `docs/adr/0028-transient-network-ssl-resilience.md`

## Audit Trail

- EXTRACTED: 17 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*