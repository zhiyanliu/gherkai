# Terminal UI Rendering

> 32 nodes · cohesion 0.12

## Key Concepts

- **textui.py** (16 connections) — `runtime/gherkai_runtime/textui.py`
- **render_table()** (16 connections) — `runtime/gherkai_runtime/textui.py`
- **test_textui.py** (15 connections) — `runtime/tests/test_textui.py`
- **TreeNode** (14 connections) — `runtime/gherkai_runtime/textui.py`
- **render_tree()** (11 connections) — `runtime/gherkai_runtime/textui.py`
- **_as_text()** (5 connections) — `runtime/gherkai_runtime/textui.py`
- **_console()** (5 connections) — `runtime/gherkai_runtime/textui.py`
- **output_width()** (5 connections) — `runtime/gherkai_runtime/textui.py`
- **use_color()** (5 connections) — `runtime/gherkai_runtime/textui.py`
- **plain()** (4 connections) — `runtime/gherkai_runtime/textui.py`
- **test_markup_and_emoji_codes_in_user_text_render_literally()** (4 connections) — `runtime/tests/test_textui.py`
- **Text** (4 connections)
- **_stdout_is_tty()** (3 connections) — `runtime/gherkai_runtime/textui.py`
- **_shown()** (3 connections) — `runtime/tests/test_textui.py`
- **test_cjk_headers_and_ascii_cells_align_by_display_width()** (3 connections) — `runtime/tests/test_textui.py`
- **test_color_is_emitted_when_enabled_and_absent_when_disabled()** (3 connections) — `runtime/tests/test_textui.py`
- **test_identifier_columns_never_fold_but_wrap_columns_do()** (3 connections) — `runtime/tests/test_textui.py`
- **test_tree_has_guide_lines_and_keeps_long_lines_unwrapped()** (3 connections) — `runtime/tests/test_textui.py`
- **test_use_color_policy()** (3 connections) — `runtime/tests/test_textui.py`
- **.find()** (2 connections) — `runtime/gherkai_runtime/textui.py`
- **test_no_ansi_when_stdout_is_not_a_tty_and_none_shows_dash()** (2 connections) — `runtime/tests/test_textui.py`
- **人读输出的呈现件（ADR 0047）：表格、树、语义颜色，cli 与 deploy provider 两个前端包共用。 - 表格给「多行同结构」的清单，树给…** (1 connections) — `runtime/gherkai_runtime/textui.py`
- **树的一个节点：`label` 是字符串或 Text，`add()` 返回子节点以便继续挂。** (1 connections) — `runtime/gherkai_runtime/textui.py`
- **深度优先找第一个 label 含 needle 的节点（测试与诊断用）。** (1 connections) — `runtime/gherkai_runtime/textui.py`
- **层级结构 → 带引导线的多行文本（末尾不带换行）。不折行：长的地址、原因、推理文本保持一行、由终端自行软换行，…** (1 connections) — `runtime/gherkai_runtime/textui.py`
- *... and 7 more nodes in this community*

## Relationships

- [Explain Rendering](Explain_Rendering.md) (14 shared connections)
- [Provider Resolution and Doctor](Provider_Resolution_and_Doctor.md) (3 shared connections)
- [CLI Command Handlers](CLI_Command_Handlers.md) (1 shared connections)
- [Worker Image Lifecycle](Worker_Image_Lifecycle.md) (1 shared connections)
- [Plan CLI Command](Plan_CLI_Command.md) (1 shared connections)
- [List Workers Command](List_Workers_Command.md) (1 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (1 shared connections)
- [Tunnel Host Orchestration](Tunnel_Host_Orchestration.md) (1 shared connections)
- [Test Fixtures and Conftest](Test_Fixtures_and_Conftest.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/textui.py`
- `runtime/tests/test_textui.py`

## Audit Trail

- EXTRACTED: 82 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*