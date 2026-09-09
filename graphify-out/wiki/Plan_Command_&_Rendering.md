# Plan Command & Rendering

> 20 nodes · cohesion 0.13

## Key Concepts

- **render.py** (16 connections) — `cli/gherkai_cli/render.py`
- **render_text()** (10 connections) — `cli/gherkai_cli/render.py`
- **_cmd_plan()** (9 connections) — `cli/gherkai_cli/__main__.py`
- **render_plan_text()** (6 connections) — `cli/gherkai_cli/render.py`
- **plan_to_dict()** (5 connections) — `cli/gherkai_cli/render.py`
- **_probe_deterministic_dispatch()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_arg_hint()** (3 connections) — `cli/gherkai_cli/render.py`
- **_cost_bits()** (3 connections) — `cli/gherkai_cli/render.py`
- **_dispatch_hint()** (3 connections) — `cli/gherkai_cli/render.py`
- **_ms()** (2 connections) — `cli/gherkai_cli/render.py`
- **Job** (2 connections)
- **plan 的派发预期标注（ADR 0036 决策 4）：按引擎分组 step 文本、批量问 worker 命中结果。 返回 {(scope_id,…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **plan 预检：读 feature → plan → 渲染 scope/job 分组 + 派发预期标注（ADR 0036）。 **零…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **渲染：把 ADR 0024 事件流与 RunResult 变成人看的文本 / 机器读的 JSON（cli 表层）。 core…** (1 connections) — `cli/gherkai_cli/render.py`
- **plan 产出 Job[] → 人看的多行预检视图（scope/engine/scenario/step，不真跑）。 dispatch（可选，ADR 0036…** (1 connections) — `cli/gherkai_cli/render.py`
- **step 的派发预期标注（ADR 0036）：确定性命中/冲突才标，AI 默认不标（噪声控制）。** (1 connections) — `cli/gherkai_cli/render.py`
- **step 多行参数的轻量标注（文本视图保持紧凑；完整 content/rows 用 --json 看）。 dataTable →…** (1 connections) — `cli/gherkai_cli/render.py`
- **plan 产出 → 机器可读 dict（--json）。复用 gherkai_core.serialize 的 job 序列化保单一真理源。 dispatch…** (1 connections) — `cli/gherkai_cli/render.py`
- **原生量成本拼装（core 只合计原生量，美元折算交消费者，ADR 0024）。** (1 connections) — `cli/gherkai_cli/render.py`
- **RunResult → 人看的多行汇总（嵌套 job/scenario/step + 时长 + 成本 + 报告指针）。…** (1 connections) — `cli/gherkai_cli/render.py`

## Relationships

- [CLI Run/Submit Commands](CLI_Run-Submit_Commands.md) (4 shared connections)
- [CLI Main Entry](CLI_Main_Entry.md) (3 shared connections)
- [Render & ReportStore Local](Render_%26_ReportStore_Local.md) (3 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (3 shared connections)
- [ResultStore Local/S3](ResultStore_Local-S3.md) (2 shared connections)
- [List Deterministic CLI Command](List_Deterministic_CLI_Command.md) (1 shared connections)
- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (1 shared connections)
- [Event Formatting & Cost Model](Event_Formatting_%26_Cost_Model.md) (1 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (1 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (1 shared connections)
- [CI and Release Workflows](CI_and_Release_Workflows.md) (1 shared connections)
- [ADR Index & Dev Docs](ADR_Index_%26_Dev_Docs.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/gherkai_cli/render.py`

## Audit Trail

- EXTRACTED: 46 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*