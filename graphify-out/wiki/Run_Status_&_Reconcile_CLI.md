# Run Status & Reconcile CLI

> 8 nodes · cohesion 0.25

## Key Concepts

- **_cmd_status()** (7 connections) — `cli/gherkai_cli/__main__.py`
- **_status_cloud()** (7 connections) — `cli/gherkai_cli/__main__.py`
- **_validate_max_concurrency()** (7 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_reconcile()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **cloud status：读 DDB RunState 渲染。--wait 则无感接力兜底——**检测卡住才** invoke kicker Lambda 做…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **per-run 进程入口（submit setsid fork 它，非用户直接调）：跑 reconcile loop 到全 done 自退（ADR…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **`--max-concurrency` 入口校验（对齐 `--tunnel-ttl`/`--grace`/`--assertion-votes`…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **[无状态跑批] 查 run 进度/结果。 - local：读文件 RunState；--wait 则本机接力 tick 到终态（三触发源之一，per-run…** (1 connections) — `cli/gherkai_cli/__main__.py`

## Relationships

- [CLI Main Entry](CLI_Main_Entry.md) (4 shared connections)
- [CLI Plan & Submit](CLI_Plan_%26_Submit.md) (4 shared connections)
- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (2 shared connections)
- [Status Render & Exit Codes](Status_Render_%26_Exit_Codes.md) (2 shared connections)
- [Cloud Submit Preflight Gates](Cloud_Submit_Preflight_Gates.md) (2 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`

## Audit Trail

- EXTRACTED: 21 (95%)
- INFERRED: 1 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*