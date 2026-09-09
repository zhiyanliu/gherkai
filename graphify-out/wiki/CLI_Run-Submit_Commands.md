# CLI Run/Submit Commands

> 21 nodes · cohesion 0.16

## Key Concepts

- **_progress()** (23 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_run()** (16 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_submit()** (16 connections) — `cli/gherkai_cli/__main__.py`
- **_load_and_plan()** (8 connections) — `cli/gherkai_cli/__main__.py`
- **_validate_max_concurrency()** (7 connections) — `cli/gherkai_cli/__main__.py`
- **_resolve_steps_dir_for_backend()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_submit_local()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_validate_worker_variant()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_preflight_worker_runtimes()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_setup_tunnel()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_worker_meta_fields()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **`_resolve_steps_dir` + cloud 档清零（ADR 0037 决策 4）：cloud 档 steps…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **本次 plan 用到的各引擎：worker 运行时能否定位 + （给了 steps 目录时）能否完成自述（ADR 0037 决策 3/4）。 - 定位链四级全…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **plan 与 run 的共享前置装配：votes 校验 → 读 feature → plan。 成功返回 `Job[]`；任一前置失败返回**退出码…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **`--max-concurrency` 入口校验（对齐 `--tunnel-ttl`/`--grace`/`--assertion-votes`…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **`--worker-variant` 入口校验 + local 档提示（对齐 `--max-concurrency` 的入口校验惯例，ADR 0038）。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **`--expose-local` 的 argparse 侧接线：编排在 `gherkai_runtime.tunnel_host`（ADR 0035 决策…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **进度/诊断输出 → stderr（业界惯例：stdout 留给该命令的核心产出/数据，stderr 给所有诊断）。 这样 `cli run … --json…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **[无状态跑批] 提交完就走（ADR 0034）：plan → 写 RunMeta+全 pending → 起首轮推进 → 打印 run_id → 立即退出。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **local submit：create_run（文件）+ 建 events SQLite + setsid fork per-run 进程推进。** (1 connections) — `cli/gherkai_cli/__main__.py`
- **variant 解析结果 → definition 字段（ADR 0038）：人读的 variant 名 + 引擎 → revision ARN。…** (1 connections) — `cli/gherkai_cli/__main__.py`

## Relationships

- [CLI Main Entry](CLI_Main_Entry.md) (20 shared connections)
- [Plan Command & Rendering](Plan_Command_%26_Rendering.md) (4 shared connections)
- [Status Command Rendering](Status_Command_Rendering.md) (4 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (3 shared connections)
- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (3 shared connections)
- [List Deterministic CLI Command](List_Deterministic_CLI_Command.md) (3 shared connections)
- [Tunnel Cleanup](Tunnel_Cleanup.md) (2 shared connections)
- [Feature Planning to Jobs](Feature_Planning_to_Jobs.md) (2 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (1 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (1 shared connections)
- [Deploy/Destroy CLI Commands](Deploy-Destroy_CLI_Commands.md) (1 shared connections)
- [SQLite Event Log Store](SQLite_Event_Log_Store.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`

## Audit Trail

- EXTRACTED: 74 (94%)
- INFERRED: 5 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*