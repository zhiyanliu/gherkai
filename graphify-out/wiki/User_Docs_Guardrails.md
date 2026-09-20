# User Docs Guardrails

> 37 nodes · cohesion 0.09

## Key Concepts

- **test_user_docs.py** (21 connections) — `cli/tests/test_user_docs.py`
- **_rel()** (10 connections) — `cli/tests/test_user_docs.py`
- **changelog_unreleased()** (8 connections) — `cli/tests/_doc_rules.py`
- **Path** (8 connections)
- **test_default_model_ids_match_the_engine_constants()** (7 connections) — `cli/tests/test_user_docs.py`
- **test_user_doc_prose_has_no_symbolic_shorthand()** (7 connections) — `cli/tests/test_user_docs.py`
- **parametrize** (6 connections)
- **test_user_doc_has_no_internal_references()** (6 connections) — `cli/tests/test_user_docs.py`
- **test_user_doc_uses_current_terminology()** (6 connections) — `cli/tests/test_user_docs.py`
- **test_diagram_source_has_no_internal_references()** (5 connections) — `cli/tests/test_user_docs.py`
- **_default_model_claims()** (4 connections) — `cli/tests/test_user_docs.py`
- **_default_model_ids()** (4 connections) — `cli/tests/test_user_docs.py`
- **test_diagram_exports_match_their_sources()** (4 connections) — `cli/tests/test_user_docs.py`
- **test_user_doc_links_resolve_and_stay_in_user_land()** (4 connections) — `cli/tests/test_user_docs.py`
- **test_no_mermaid_blocks_remain()** (3 connections) — `cli/tests/test_user_docs.py`
- **test_published_interactive_html_is_tracked_and_indexed()** (3 connections) — `cli/tests/test_user_docs.py`
- **test_diagram_skill_points_at_the_method()** (2 connections) — `cli/tests/test_user_docs.py`
- **test_diagram_sources_and_exports_come_in_pairs()** (2 connections) — `cli/tests/test_user_docs.py`
- **test_retired_terms_are_all_in_the_glossary()** (2 connections) — `cli/tests/test_user_docs.py`
- **test_user_guide_index_matches_directory()** (2 connections) — `cli/tests/test_user_docs.py`
- **CHANGELOG 交给退役词表与口头语表扫的部分 = 截到第一个已发行版本节之前。…** (1 connections) — `cli/tests/_doc_rules.py`
- **仓库内用户文档的护栏：`docs/user-guide/**`、根 `README.md`、`CHANGELOG.md`（ADR 0045 决策一 /…** (1 connections) — `cli/tests/test_user_docs.py`
- **owner 表（docs/user-guide/README.md）与目录里的页一一对应：两向差集。** (1 connections) — `cli/tests/test_user_docs.py`
- **docs/diagrams/<name>.json（图源）与 <name>.svg（导出）成对：缺任一半即漂（HTML 不入库，由 JSON 现场构建）。** (1 connections) — `cli/tests/test_user_docs.py`
- **交互 HTML 只对发布到 Pages 的图入库：git 跟踪的每个 <name>.html 必须有同名图源，且在 index.html 里有链接 （发布 =…** (1 connections) — `cli/tests/test_user_docs.py`
- *... and 12 more nodes in this community*

## Relationships

- [Doc Scanning Rules](Doc_Scanning_Rules.md) (3 shared connections)
- [ADR Hygiene Checks](ADR_Hygiene_Checks.md) (2 shared connections)
- [Skill Doc Flag Guardrails](Skill_Doc_Flag_Guardrails.md) (2 shared connections)

## Source Files

- `cli/tests/_doc_rules.py`
- `cli/tests/test_user_docs.py`

## Audit Trail

- EXTRACTED: 69 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*