# ADR Hygiene Checks

> 22 nodes · cohesion 0.17

## Key Concepts

- **test_adr_hygiene.py** (19 connections) — `cli/tests/test_adr_hygiene.py`
- **prose_lines()** (9 connections) — `cli/tests/_doc_rules.py`
- **Path** (8 connections)
- **test_ai_side_docs_avoid_coined_compounds()** (6 connections) — `cli/tests/test_adr_hygiene.py`
- **test_long_term_docs_have_no_dangling_pointers()** (6 connections) — `cli/tests/test_adr_hygiene.py`
- **test_superseded_links_are_bidirectional()** (6 connections) — `cli/tests/test_adr_hygiene.py`
- **parametrize** (5 connections)
- **_rel()** (4 connections) — `cli/tests/test_adr_hygiene.py`
- **_status_line()** (4 connections) — `cli/tests/test_adr_hygiene.py`
- **test_adr_has_standard_status_head()** (4 connections) — `cli/tests/test_adr_hygiene.py`
- **_superseders()** (3 connections) — `cli/tests/test_adr_hygiene.py`
- **test_docs_filenames_are_kebab_case()** (3 connections) — `cli/tests/test_adr_hygiene.py`
- **_adrs()** (2 connections) — `cli/tests/test_adr_hygiene.py`
- **test_numbered_docs_do_not_reuse_numbers()** (2 connections) — `cli/tests/test_adr_hygiene.py`
- **_tracked_docs()** (2 connections) — `cli/tests/test_adr_hygiene.py`
- **markdown 的正文行：剥掉围栏代码块、行内反引号代码，可选剥掉 YAML frontmatter；行号与原文一致。…** (1 connections) — `cli/tests/_doc_rules.py`
- **ADR、journey 与长期文档的机械卫生项（CLAUDE.md 文档纪律里能逐行判定的那几条，此前每轮 doc-health 靠人查）。 - 每篇 ADR…** (1 connections) — `cli/tests/test_adr_hygiene.py`
- **长期文档只指稳定物：不链具体的 journey 文件、不写裸 WP 编号（代码块与行内代码不算）。** (1 connections) — `cli/tests/test_adr_hygiene.py`
- **AI 侧文档口吻放开，但决策六形态②的自造复合词全仓不用（歧义不是效率）；讨论这些词本身的文档除外。** (1 connections) — `cli/tests/test_adr_hygiene.py`
- **Status 头里点名的取代方编号（只看 superseded-by 之后、到第一个注解分隔符为止那一段）。** (1 connections) — `cli/tests/test_adr_hygiene.py`
- **被取代方点了谁，谁就得回指它——机械差集，不靠读。** (1 connections) — `cli/tests/test_adr_hygiene.py`
- **test_journey_files_declare_their_type()** (1 connections) — `cli/tests/test_adr_hygiene.py`

## Relationships

- [Doc Scanning Rules](Doc_Scanning_Rules.md) (7 shared connections)
- [Skill Doc Flag Guardrails](Skill_Doc_Flag_Guardrails.md) (2 shared connections)
- [User Docs Guardrails](User_Docs_Guardrails.md) (2 shared connections)
- [Contributor Guardrail Docs](Contributor_Guardrail_Docs.md) (1 shared connections)

## Source Files

- `cli/tests/_doc_rules.py`
- `cli/tests/test_adr_hygiene.py`

## Audit Trail

- EXTRACTED: 51 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*