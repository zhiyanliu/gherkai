# Skill Doc Flag Guardrails

> 62 nodes · cohesion 0.05

## Key Concepts

- **test_skill.py** (37 connections) — `cli/tests/test_skill.py`
- **skill_markdown_files()** (12 connections) — `cli/tests/_doc_rules.py`
- **extract_command_spans()** (8 connections) — `cli/tests/_doc_rules.py`
- **is_placeholder()** (6 connections) — `cli/tests/_doc_rules.py`
- **parametrize** (6 connections)
- **test_flags_are_attached_to_the_right_subcommand()** (6 connections) — `cli/tests/test_skill.py`
- **bare_flags()** (5 connections) — `cli/tests/_doc_rules.py`
- **_all_command_spans()** (5 connections) — `cli/tests/test_skill.py`
- **Path** (5 connections)
- **test_skill_prose_has_no_symbolic_shorthand()** (5 connections) — `cli/tests/test_skill.py`
- **clean_flag()** (4 connections) — `cli/tests/_doc_rules.py`
- **_documented_keys()** (4 connections) — `cli/tests/test_skill.py`
- **_fixture_files()** (4 connections) — `cli/tests/test_skill.py`
- **_is_ignored()** (4 connections) — `cli/tests/test_skill.py`
- **_resolve()** (4 connections) — `cli/tests/test_skill.py`
- **test_bare_flags_exist_somewhere()** (4 connections) — `cli/tests/test_skill.py`
- **test_every_fixture_file_is_tracked()** (4 connections) — `cli/tests/test_skill.py`
- **test_github_urls_are_pinned_to_head_or_tag()** (4 connections) — `cli/tests/test_skill.py`
- **test_key_shaped_tokens_are_documented_keys()** (4 connections) — `cli/tests/test_skill.py`
- **test_skill_markdown_has_no_relative_links()** (4 connections) — `cli/tests/test_skill.py`
- **test_skill_markdown_is_product_facing()** (4 connections) — `cli/tests/test_skill.py`
- **_allowed_flags()** (3 connections) — `cli/tests/test_skill.py`
- **_frontmatter_and_body()** (3 connections) — `cli/tests/test_skill.py`
- **_parser_nodes()** (3 connections) — `cli/tests/test_skill.py`
- **test_exclusive_claims_are_true()** (3 connections) — `cli/tests/test_skill.py`
- *... and 37 more nodes in this community*

## Relationships

- [Doc Scanning Rules](Doc_Scanning_Rules.md) (8 shared connections)
- [Skill Deploy Token Checks](Skill_Deploy_Token_Checks.md) (3 shared connections)
- [User Docs Guardrails](User_Docs_Guardrails.md) (2 shared connections)
- [ADR Hygiene Checks](ADR_Hygiene_Checks.md) (2 shared connections)
- [Command Span Parsing](Command_Span_Parsing.md) (1 shared connections)
- [Deploy Command Frontend](Deploy_Command_Frontend.md) (1 shared connections)
- [CLI Command Dispatch](CLI_Command_Dispatch.md) (1 shared connections)
- [Run Summarization Script](Run_Summarization_Script.md) (1 shared connections)
- [CLI Parser Assembly](CLI_Parser_Assembly.md) (1 shared connections)

## Source Files

- `cli/tests/_doc_rules.py`
- `cli/tests/test_skill.py`

## Audit Trail

- EXTRACTED: 108 (96%)
- INFERRED: 4 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*