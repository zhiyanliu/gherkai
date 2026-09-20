# CLI Render Layer

> 30 nodes · cohesion 0.10

## Key Concepts

- **render.py** (26 connections) — `cli/gherkai_cli/render.py`
- **_step_lines()** (9 connections) — `cli/gherkai_cli/render.py`
- **plan_to_dict()** (6 connections) — `cli/gherkai_cli/render.py`
- **render_explain_text()** (6 connections) — `cli/gherkai_cli/render.py`
- **render_plan_text()** (6 connections) — `cli/gherkai_cli/render.py`
- **_act_lines()** (5 connections) — `cli/gherkai_cli/render.py`
- **_one_line()** (5 connections) — `cli/gherkai_cli/render.py`
- **explain_step_expands()** (4 connections) — `cli/gherkai_cli/render.py`
- **_ref_line()** (4 connections) — `cli/gherkai_cli/render.py`
- **_arg_hint()** (3 connections) — `cli/gherkai_cli/render.py`
- **_cost_bits()** (3 connections) — `cli/gherkai_cli/render.py`
- **_dispatch_hint()** (3 connections) — `cli/gherkai_cli/render.py`
- **_evidence_ref()** (3 connections) — `cli/gherkai_cli/render.py`
- **_ms()** (3 connections) — `cli/gherkai_cli/render.py`
- **_thought_lines()** (3 connections) — `cli/gherkai_cli/render.py`
- **Job** (2 connections)
- **渲染：把 ADR 0024 事件流与 RunResult 变成人看的文本 / 机器读的 JSON（cli 表层）。 core…** (1 connections) — `cli/gherkai_cli/render.py`
- **plan 产出 Job[] → 人看的多行预检视图（scope/engine/scenario/step，不实际运行）。 dispatch（可选，ADR…** (1 connections) — `cli/gherkai_cli/render.py`
- **step 的派发预期标注（ADR 0036）：确定性命中/冲突才标，AI 默认不标（噪声控制）。** (1 connections) — `cli/gherkai_cli/render.py`
- **step 多行参数的轻量标注（文本视图保持紧凑；完整 content/rows 用 --json 看）。 dataTable →…** (1 connections) — `cli/gherkai_cli/render.py`
- **plan 产出 → 机器可读 dict（--json）。复用 gherkai_core.serialize 的 job 序列化保单一真理源。 dispatch…** (1 connections) — `cli/gherkai_cli/render.py`
- **这个 step 要不要展开证据（ADR 0042 决策四）：默认展开 failed / error / skipped， `--all` 或显式…** (1 connections) — `cli/gherkai_cli/render.py`
- **产物 ref 一行（与 render_text 的 step/scope 行措辞相同，label 缺省回落 kind）。** (1 connections) — `cli/gherkai_cli/render.py`
- **该 step 的 evidence ref（截断提示里指给读者的「完整内容在哪」）；没有则空串。** (1 connections) — `cli/gherkai_cli/render.py`
- **一段推理文本 → 文本行（超预算截断，除 --full；多行原文的续行对齐到 `thought: ` 之后）。 文本形态的 key 一律用 `--json`…** (1 connections) — `cli/gherkai_cli/render.py`
- *... and 5 more nodes in this community*

## Relationships

- [Explain Rendering Tests](Explain_Rendering_Tests.md) (6 shared connections)
- [CLI Command Dispatch](CLI_Command_Dispatch.md) (4 shared connections)
- [Explain Command](Explain_Command.md) (3 shared connections)
- [Local & S3 Result Stores](Local_%26_S3_Result_Stores.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [JSON Field Contract Tests](JSON_Field_Contract_Tests.md) (2 shared connections)
- [CLI Entry Wiring Tests](CLI_Entry_Wiring_Tests.md) (1 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`

## Audit Trail

- EXTRACTED: 63 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*