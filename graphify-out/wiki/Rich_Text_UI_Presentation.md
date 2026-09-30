# Rich Text UI Presentation

> 37 nodes · cohesion 0.10

## Key Concepts

- **textui.py** (19 connections) — `runtime/gherkai_runtime/textui.py`
- **render_table()** (16 connections) — `runtime/gherkai_runtime/textui.py`
- **test_textui.py** (15 connections) — `runtime/tests/test_textui.py`
- **TreeNode** (14 connections) — `runtime/gherkai_runtime/textui.py`
- **render_tree()** (11 connections) — `runtime/gherkai_runtime/textui.py`
- **ADR 0047 CLI 人读输出用 rich 渲染** (8 connections) — `docs/adr/0047-cli-human-readable-tables-with-rich.md`
- **use_color()** (6 connections) — `runtime/gherkai_runtime/textui.py`
- **_as_text()** (5 connections) — `runtime/gherkai_runtime/textui.py`
- **_console()** (5 connections) — `runtime/gherkai_runtime/textui.py`
- **output_width()** (5 connections) — `runtime/gherkai_runtime/textui.py`
- **plain()** (4 connections) — `runtime/gherkai_runtime/textui.py`
- **test_markup_and_emoji_codes_in_user_text_render_literally()** (4 connections) — `runtime/tests/test_textui.py`
- **Text** (4 connections)
- **NO_COLOR / FORCE_COLOR 颜色开关** (3 connections) — `docs/user-guide/configuration.md`
- **_stdout_is_tty()** (3 connections) — `runtime/gherkai_runtime/textui.py`
- **_shown()** (3 connections) — `runtime/tests/test_textui.py`
- **test_cjk_headers_and_ascii_cells_align_by_display_width()** (3 connections) — `runtime/tests/test_textui.py`
- **test_color_is_emitted_when_enabled_and_absent_when_disabled()** (3 connections) — `runtime/tests/test_textui.py`
- **test_identifier_columns_never_fold_but_wrap_columns_do()** (3 connections) — `runtime/tests/test_textui.py`
- **test_tree_has_guide_lines_and_keeps_long_lines_unwrapped()** (3 connections) — `runtime/tests/test_textui.py`
- **test_use_color_policy()** (3 connections) — `runtime/tests/test_textui.py`
- **rich 渲染库** (2 connections) — `docs/adr/0047-cli-human-readable-tables-with-rich.md`
- **worker 日志前缀颜色（按 job 启动顺序）** (2 connections) — `docs/adr/0047-cli-human-readable-tables-with-rich.md`
- **.find()** (2 connections) — `runtime/gherkai_runtime/textui.py`
- **test_no_ansi_when_stdout_is_not_a_tty_and_none_shows_dash()** (2 connections) — `runtime/tests/test_textui.py`
- *... and 12 more nodes in this community*

## Relationships

- [Explain Tree Rendering](Explain_Tree_Rendering.md) (13 shared connections)
- [Terminal Color Policy](Terminal_Color_Policy.md) (4 shared connections)
- [Agent Skill Reference Docs](Agent_Skill_Reference_Docs.md) (2 shared connections)
- [CLI Command Entrypoints](CLI_Command_Entrypoints.md) (2 shared connections)
- [Deploy Provider Discovery](Deploy_Provider_Discovery.md) (2 shared connections)
- [Package Contributor Docs](Package_Contributor_Docs.md) (1 shared connections)
- [Project Conventions Docs](Project_Conventions_Docs.md) (1 shared connections)
- [Worker Image Management](Worker_Image_Management.md) (1 shared connections)
- [Engine Listing and JSON Contract](Engine_Listing_and_JSON_Contract.md) (1 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (1 shared connections)
- [Worker Variant Listing](Worker_Variant_Listing.md) (1 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (1 shared connections)

## Source Files

- `docs/adr/0047-cli-human-readable-tables-with-rich.md`
- `docs/user-guide/configuration.md`
- `runtime/gherkai_runtime/textui.py`
- `runtime/tests/test_textui.py`

## Audit Trail

- EXTRACTED: 94 (98%)
- INFERRED: 2 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*