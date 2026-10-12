# Core Domain And Ports

> 12 nodes · cohesion 0.21

## Key Concepts

- **reconcile.py（无状态推进 tick）** (4 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **Job（提交给执行面的单元 = Scope）** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **JobResult（持有 Job 的判定结果）** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **RunMeta（definition：前置身份 + Job[]）** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **RunResult（机器可读汇总判定）** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **RunState（控制面运行态）** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **三层切分：definition / 控制面运行态 / 数据面判定** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **Launcher port（CAS 抢占后起一个 job）** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **project.py（events → RunState/JobResult 纯归约投影）** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **Scope（session scope，执行单元）** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **detached.py（local 无状态批量运行宿主）** (1 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **EventLog port（无状态推进的写模型）** (1 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`

## Relationships

- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (2 shared connections)

## Source Files

- `docs/adr/0016-execution-architecture-core-lib-run-model.md`

## Audit Trail

- EXTRACTED: 15 (94%)
- INFERRED: 1 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*