# CLI Plan & Submit

> 24 nodes · cohesion 0.12

## Key Concepts

- **_progress()** (23 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_submit()** (16 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_plan()** (9 connections) — `cli/gherkai_cli/__main__.py`
- **_load_and_plan()** (8 connections) — `cli/gherkai_cli/__main__.py`
- **_resolve_steps_dir()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_resolve_steps_dir_for_backend()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_submit_local()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_list_deterministic()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_preflight_worker_runtimes()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_setup_tunnel()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_probe_deterministic_dispatch()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **write_tunnel_file()** (3 connections) — `runtime/gherkai_runtime/detached.py`
- **解析使用方确定性 step 目录（ADR 0037 决策 4）：`--steps-dir` > env `GHERKAI_STEPS_DIR` > 默认…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **`_resolve_steps_dir` + cloud 档清零（ADR 0037 决策 4）：cloud 档 steps…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **本次 plan 用到的各引擎：worker 运行时能否定位 + （给了 steps 目录时）能否完成自述（ADR 0037 决策 3/4）。 - 定位链四级全…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **按引擎列出确定性 step 清单（ADR 0036）：spawn worker 自述、CLI 只转述——core/CLI 不持有 pattern 语义（ADR…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **plan 与 run 的共享前置装配：votes 校验 → 读 feature → plan。 成功返回 `Job[]`；任一前置失败返回**退出码…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **plan 的派发预期标注（ADR 0036 决策 4）：按引擎分组 step 文本、批量问 worker 命中结果。 返回 {(scope_id,…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **`--expose-local` 的 argparse 侧接线：编排在 `gherkai_runtime.tunnel_host`（ADR 0035 决策…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **plan 预检：读 feature → plan → 渲染 scope/job 分组 + 派发预期标注（ADR 0036）。 **零…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **进度/诊断输出 → stderr（业界惯例：stdout 留给该命令的核心产出/数据，stderr 给所有诊断）。 这样 `cli run … --json…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **[无状态跑批] 提交完就走（ADR 0034）：plan → 写 RunMeta+全 pending → 起首轮推进 → 打印 run_id → 立即退出。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **local submit：create_run（文件）+ 建 events SQLite + setsid fork per-run 进程推进。** (1 connections) — `cli/gherkai_cli/__main__.py`
- **local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。** (1 connections) — `runtime/gherkai_runtime/detached.py`

## Relationships

- [CLI Main Entry](CLI_Main_Entry.md) (13 shared connections)
- [Cloud Submit Preflight Gates](Cloud_Submit_Preflight_Gates.md) (9 shared connections)
- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (4 shared connections)
- [Run Status & Reconcile CLI](Run_Status_%26_Reconcile_CLI.md) (4 shared connections)
- [Plan Rendering & Output](Plan_Rendering_%26_Output.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [Feature Planning](Feature_Planning.md) (2 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (1 shared connections)
- [Tunnel Cleanup](Tunnel_Cleanup.md) (1 shared connections)
- [Deploy/Destroy Provider Dispatch](Deploy-Destroy_Provider_Dispatch.md) (1 shared connections)
- [Status Render & Exit Codes](Status_Render_%26_Exit_Codes.md) (1 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `runtime/gherkai_runtime/detached.py`

## Audit Trail

- EXTRACTED: 71 (95%)
- INFERRED: 4 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*