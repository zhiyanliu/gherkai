# Scenario Selection Flags

> 15 nodes · cohesion 0.14

## Key Concepts

- **_tagged_feature()** (6 connections) — `cli/tests/test_main.py`
- **_plan_names()** (5 connections) — `cli/tests/test_main.py`
- **test_plan_scenario_by_id_line_or_title_substring()** (5 connections) — `cli/tests/test_main.py`
- **test_plan_tags_any_within_value_and_all_across_flags()** (5 connections) — `cli/tests/test_main.py`
- **test_run_tags_narrow_the_definition_and_report_selection()** (5 connections) — `cli/tests/test_main.py`
- **test_plan_empty_selection_exits_2_and_lists_candidates()** (4 connections) — `cli/tests/test_main.py`
- **test_scenario_digit_selector_is_line_only_and_outline_declaration_line_selects_all_examples()** (4 connections) — `cli/tests/test_main.py`
- **test_scope_filter_selects_whole_named_scope_by_id()** (4 connections) — `cli/tests/test_main.py`
- **test_empty_selection_flag_values_are_rejected()** (3 connections) — `cli/tests/test_main.py`
- **一个 --tags 值内逗号表示任一命中；重复 --tags 表示都要命中；@ 可省。** (1 connections) — `cli/tests/test_main.py`
- **--scenario：<uri>:<行> / 行号 / :行号 / 标题子串；多个为或；与 --tags 同给为且。** (1 connections) — `cli/tests/test_main.py`
- **筛空 → 以退出码 2 结束并列出全部候选（id 标题），别静默运行空批。** (1 connections) — `cli/tests/test_main.py`
- **run 与 plan 同一解析：筛后的 job 集就是 definition（schedule 只收到被选中的），stderr 打「筛选：N/M」。** (1 connections) — `cli/tests/test_main.py`
- **纯数字 SEL 只当行号、不回落标题子串（标题「重试3次」不被 --scenario 3 连带选中）；Scenario Outline 的 id 是…** (1 connections) — `cli/tests/test_main.py`
- **--scope 即报告里的 scope_id：named scope 的名字选中整个 scope（两条都运行），未标 scope 的用 <文件>:<行>； 与…** (1 connections) — `cli/tests/test_main.py`

## Relationships

- [CLI Entry Wiring Tests](CLI_Entry_Wiring_Tests.md) (10 shared connections)
- [CLI Plan Command Behavior](CLI_Plan_Command_Behavior.md) (7 shared connections)

## Source Files

- `cli/tests/test_main.py`

## Audit Trail

- EXTRACTED: 32 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*