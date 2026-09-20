# Status Command

> 20 nodes · cohesion 0.16

## Key Concepts

- **_render_status()** (15 connections) — `cli/gherkai_cli/__main__.py`
- **_mk_state()** (9 connections) — `cli/tests/test_main.py`
- **_args()** (8 connections) — `cli/tests/test_main.py`
- **_cmd_status()** (7 connections) — `cli/gherkai_cli/__main__.py`
- **_status_cloud()** (7 connections) — `cli/gherkai_cli/__main__.py`
- **test_render_status_json_no_hint()** (5 connections) — `cli/tests/test_main.py`
- **test_render_status_pending_hints_wait()** (5 connections) — `cli/tests/test_main.py`
- **test_render_status_running_no_hint()** (5 connections) — `cli/tests/test_main.py`
- **test_render_status_terminal_no_hint_and_exitcode()** (5 connections) — `cli/tests/test_main.py`
- **test_render_status_terminal_prints_artifact_locations()** (5 connections) — `cli/tests/test_main.py`
- **test_render_status_wait_pending_no_hint()** (5 connections) — `cli/tests/test_main.py`
- **渲染 RunState + pending 诊断提示 + 终态产物位置 + 退出码——**local/cloud 共享一份**（保两路一致，ADR…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **[无状态批量运行] 查 run 进度/结果。 - local：读文件 RunState；--wait 则本机接力 tick 到终态（三触发源之一，per-…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **cloud status：读 DDB RunState 渲染。--wait 则无感接力兜底——**检测卡住才** invoke kicker Lambda 做…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。** (1 connections) — `cli/tests/test_main.py`
- **pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。** (1 connections) — `cli/tests/test_main.py`
- **running → 不提示（在运行、正常）。退出码 0。** (1 connections) — `cli/tests/test_main.py`
- **终态：passed→0、其余终态→1（含派生终态 skipped/aborted），均不提示。** (1 connections) — `cli/tests/test_main.py`
- **--wait 下即使 pending 也不打提示（--wait 本身在接力、提示多余）。** (1 connections) — `cli/tests/test_main.py`
- **--json（机读）：pending 也不打人读提示，且 stdout 是可解析 JSON。** (1 connections) — `cli/tests/test_main.py`

## Relationships

- [CLI Entry Wiring Tests](CLI_Entry_Wiring_Tests.md) (8 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (5 shared connections)
- [CLI Command Dispatch](CLI_Command_Dispatch.md) (4 shared connections)
- [Run & Submit Commands](Run_%26_Submit_Commands.md) (4 shared connections)
- [CLI Plan Command Behavior](CLI_Plan_Command_Behavior.md) (1 shared connections)
- [Local & S3 Result Stores](Local_%26_S3_Result_Stores.md) (1 shared connections)
- [Doctor & Skill Install](Doctor_%26_Skill_Install.md) (1 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/tests/test_main.py`

## Audit Trail

- EXTRACTED: 53 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*