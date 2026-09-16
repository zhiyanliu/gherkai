# Run Status Rendering

> 15 nodes · cohesion 0.18

## Key Concepts

- **_render_status()** (15 connections) — `cli/gherkai_cli/__main__.py`
- **_args()** (8 connections) — `cli/tests/test_main.py`
- **test_render_status_json_no_hint()** (5 connections) — `cli/tests/test_main.py`
- **test_render_status_pending_hints_wait()** (5 connections) — `cli/tests/test_main.py`
- **test_render_status_running_no_hint()** (5 connections) — `cli/tests/test_main.py`
- **test_render_status_terminal_no_hint_and_exitcode()** (5 connections) — `cli/tests/test_main.py`
- **test_render_status_terminal_prints_artifact_locations()** (5 connections) — `cli/tests/test_main.py`
- **test_render_status_wait_pending_no_hint()** (5 connections) — `cli/tests/test_main.py`
- **渲染 RunState + pending 诊断提示 + 终态产物位置 + 退出码——**local/cloud 共享一份**（保两路一致，ADR…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。** (1 connections) — `cli/tests/test_main.py`
- **pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。** (1 connections) — `cli/tests/test_main.py`
- **running → 不提示（在跑、正常）。退出码 0。** (1 connections) — `cli/tests/test_main.py`
- **终态：passed→0、其余终态→1（含派生终态 skipped/aborted），均不提示。** (1 connections) — `cli/tests/test_main.py`
- **--wait 下即使 pending 也不打提示（--wait 本身在接力、提示多余）。** (1 connections) — `cli/tests/test_main.py`
- **--json（机读）：pending 也不打人读提示，且 stdout 是可解析 JSON。** (1 connections) — `cli/tests/test_main.py`

## Relationships

- [Run State Rendering](Run_State_Rendering.md) (9 shared connections)
- [CLI Run Command Tests](CLI_Run_Command_Tests.md) (7 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (5 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/tests/test_main.py`

## Audit Trail

- EXTRACTED: 40 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*