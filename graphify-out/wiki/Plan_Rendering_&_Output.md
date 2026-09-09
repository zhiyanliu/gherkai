# Plan Rendering & Output

> 9 nodes · cohesion 0.22

## Key Concepts

- **render_plan_text()** (6 connections) — `cli/gherkai_cli/render.py`
- **plan_to_dict()** (5 connections) — `cli/gherkai_cli/render.py`
- **_arg_hint()** (3 connections) — `cli/gherkai_cli/render.py`
- **_dispatch_hint()** (3 connections) — `cli/gherkai_cli/render.py`
- **Job** (2 connections)
- **plan 产出 Job[] → 人看的多行预检视图（scope/engine/scenario/step，不真跑）。 dispatch（可选，ADR 0036…** (1 connections) — `cli/gherkai_cli/render.py`
- **step 的派发预期标注（ADR 0036）：确定性命中/冲突才标，AI 默认不标（噪声控制）。** (1 connections) — `cli/gherkai_cli/render.py`
- **step 多行参数的轻量标注（文本视图保持紧凑；完整 content/rows 用 --json 看）。 dataTable →…** (1 connections) — `cli/gherkai_cli/render.py`
- **plan 产出 → 机器可读 dict（--json）。复用 gherkai_core.serialize 的 job 序列化保单一真理源。 dispatch…** (1 connections) — `cli/gherkai_cli/render.py`

## Relationships

- [Run Result Rendering](Run_Result_Rendering.md) (4 shared connections)
- [CLI Plan & Submit](CLI_Plan_%26_Submit.md) (2 shared connections)
- [S3 Result Store](S3_Result_Store.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`

## Audit Trail

- EXTRACTED: 15 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*