# Skill Markdown Command Linting

> 45 nodes · cohesion 0.06

## Key Concepts

- **test_skill.py** (37 connections) — `cli/tests/test_skill.py`
- **skill_markdown_files()** (12 connections) — `cli/tests/_doc_rules.py`
- **extract_command_spans()** (8 connections) — `cli/tests/_doc_rules.py`
- **is_placeholder()** (6 connections) — `cli/tests/_doc_rules.py`
- **test_flags_are_attached_to_the_right_subcommand()** (6 connections) — `cli/tests/test_skill.py`
- **bare_flags()** (5 connections) — `cli/tests/_doc_rules.py`
- **_all_command_spans()** (5 connections) — `cli/tests/test_skill.py`
- **clean_flag()** (4 connections) — `cli/tests/_doc_rules.py`
- **_documented_keys()** (4 connections) — `cli/tests/test_skill.py`
- **_resolve()** (4 connections) — `cli/tests/test_skill.py`
- **test_bare_flags_exist_somewhere()** (4 connections) — `cli/tests/test_skill.py`
- **test_key_shaped_tokens_are_documented_keys()** (4 connections) — `cli/tests/test_skill.py`
- **_allowed_flags()** (3 connections) — `cli/tests/test_skill.py`
- **_frontmatter_and_body()** (3 connections) — `cli/tests/test_skill.py`
- **_parser_nodes()** (3 connections) — `cli/tests/test_skill.py`
- **test_exclusive_claims_are_true()** (3 connections) — `cli/tests/test_skill.py`
- **test_scan_face_is_not_empty()** (3 connections) — `cli/tests/test_skill.py`
- **test_skill_form_limits()** (3 connections) — `cli/tests/test_skill.py`
- **test_skill_mentions_commands_at_all()** (3 connections) — `cli/tests/test_skill.py`
- **_claimed_flags()** (2 connections) — `cli/tests/test_skill.py`
- **test_contract_copy_equals_transform_of_source()** (2 connections) — `cli/tests/test_skill.py`
- **test_rewrite_tables_are_all_used()** (2 connections) — `cli/tests/test_skill.py`
- **test_skill_directory_whitelist()** (2 connections) — `cli/tests/test_skill.py`
- **test_sync_hook_is_wired_for_the_contract_copy()** (2 connections) — `cli/tests/test_skill.py`
- **skill 目录下全部 markdown（含契约副本——转换后它本就不含内部指代，无例外）。** (1 connections) — `cli/tests/_doc_rules.py`
- *... and 20 more nodes in this community*

## Relationships

- [Skill Fixture Doc Guards](Skill_Fixture_Doc_Guards.md) (10 shared connections)
- [Human Doc Rules Source](Human_Doc_Rules_Source.md) (8 shared connections)
- [Skill Deploy Token Guards](Skill_Deploy_Token_Guards.md) (3 shared connections)
- [User Docs Guardrails](User_Docs_Guardrails.md) (2 shared connections)
- [Command Span Parsing](Command_Span_Parsing.md) (1 shared connections)
- [ADR Hygiene Tests](ADR_Hygiene_Tests.md) (1 shared connections)
- [Deploy Command Frontend](Deploy_Command_Frontend.md) (1 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (1 shared connections)
- [Agent Skill Eval Harness](Agent_Skill_Eval_Harness.md) (1 shared connections)
- [CLI Parser & Selection Flags](CLI_Parser_%26_Selection_Flags.md) (1 shared connections)

## Source Files

- `cli/tests/_doc_rules.py`
- `cli/tests/test_skill.py`

## Audit Trail

- EXTRACTED: 86 (96%)
- INFERRED: 4 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*