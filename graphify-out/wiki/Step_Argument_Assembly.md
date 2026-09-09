# Step Argument Assembly

> 20 nodes · cohesion 0.15

## Key Concepts

- **test_argument.py** (13 connections) — `engines/novaact/tests/test_argument.py`
- **_argument_text()** (10 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_instruction()** (8 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_unquote()** (4 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_clean_cell()** (3 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_cell_with_newline_flattened()** (2 connections) — `engines/novaact/tests/test_argument.py`
- **test_cell_with_pipe_escaped()** (2 connections) — `engines/novaact/tests/test_argument.py`
- **test_datatable_empty_rows()** (2 connections) — `engines/novaact/tests/test_argument.py`
- **test_datatable_to_markdown()** (2 connections) — `engines/novaact/tests/test_argument.py`
- **test_docstring_passthrough()** (2 connections) — `engines/novaact/tests/test_argument.py`
- **test_instruction_appends_argument()** (2 connections) — `engines/novaact/tests/test_argument.py`
- **test_instruction_docstring()** (2 connections) — `engines/novaact/tests/test_argument.py`
- **test_instruction_no_argument_is_bare_unquoted()** (2 connections) — `engines/novaact/tests/test_argument.py`
- **test_no_argument()** (2 connections) — `engines/novaact/tests/test_argument.py`
- **test_unquote_ascii_ws_only_keeps_bom()** (2 connections) — `engines/novaact/tests/test_argument.py`
- **step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **喂 AI 的完整指令 = 去引号的 step 自然语言 + （可选）多行参数（ADR 0024：text(+argument) 一起喂引擎）。** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **step argument（DataTable/DocString）拼接单测（ADR 0024/0025）。 验证 _argument_text /…** (1 connections) — `engines/novaact/tests/test_argument.py`

## Relationships

- [Nova Act Worker](Nova_Act_Worker.md) (6 shared connections)
- [Step Dispatch Execution](Step_Dispatch_Execution.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_argument.py`

## Audit Trail

- EXTRACTED: 35 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*