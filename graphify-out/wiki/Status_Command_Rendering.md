# Status Command Rendering

> 18 nodes · cohesion 0.17

## Key Concepts

- **_render_status()** (12 connections) — `cli/gherkai_cli/__main__.py`
- **_mk_state()** (8 connections) — `cli/tests/test_main.py`
- **_cmd_status()** (7 connections) — `cli/gherkai_cli/__main__.py`
- **_status_cloud()** (7 connections) — `cli/gherkai_cli/__main__.py`
- **_args()** (6 connections) — `cli/tests/test_main.py`
- **test_render_status_json_no_hint()** (5 connections) — `cli/tests/test_main.py`
- **test_render_status_pending_hints_wait()** (5 connections) — `cli/tests/test_main.py`
- **test_render_status_running_no_hint()** (5 connections) — `cli/tests/test_main.py`
- **test_render_status_terminal_no_hint_and_exitcode()** (5 connections) — `cli/tests/test_main.py`
- **test_render_status_wait_pending_no_hint()** (5 connections) — `cli/tests/test_main.py`
- **cloud status：读 DDB RunState 渲染。--wait 则无感接力兜底——**检测卡住才** invoke kicker Lambda 做…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **渲染 RunState + pending 诊断提示 + 退出码——**local/cloud 共享一份**（保两路一致，ADR 0034）。 state…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **[无状态跑批] 查 run 进度/结果。 - local：读文件 RunState；--wait 则本机接力 tick 到终态（三触发源之一，per-run…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。** (1 connections) — `cli/tests/test_main.py`
- **running → 不提示（在跑、正常）。退出码 0。** (1 connections) — `cli/tests/test_main.py`
- **终态：passed→0、其余终态→1（含派生终态 skipped/aborted），均不提示。** (1 connections) — `cli/tests/test_main.py`
- **--wait 下即使 pending 也不打提示（--wait 本身在接力、提示多余）。** (1 connections) — `cli/tests/test_main.py`
- **--json（机读）：pending 也不打人读提示，且 stdout 是可解析 JSON。** (1 connections) — `cli/tests/test_main.py`

## Relationships

- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (8 shared connections)
- [CLI Run/Submit Commands](CLI_Run-Submit_Commands.md) (4 shared connections)
- [CLI Main Entry](CLI_Main_Entry.md) (4 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (3 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (2 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/tests/test_main.py`

## Audit Trail

- EXTRACTED: 45 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*