# Doc Scanning Rules

> 33 nodes · cohesion 0.12

## Key Concepts

- **_doc_rules.py** (32 connections) — `cli/tests/_doc_rules.py`
- **scan()** (14 connections) — `cli/tests/_doc_rules.py`
- **Path** (12 connections)
- **classify()** (9 connections) — `cli/tests/_doc_rules.py`
- **test_code_comments.py** (7 connections) — `cli/tests/test_code_comments.py`
- **test_technical_docs.py** (7 connections) — `cli/tests/test_technical_docs.py`
- **test_comments_follow_the_written_register()** (6 connections) — `cli/tests/test_code_comments.py`
- **test_technical_doc_uses_written_register()** (6 connections) — `cli/tests/test_technical_docs.py`
- **ai_side_docs()** (5 connections) — `cli/tests/_doc_rules.py`
- **code_comment_files()** (5 connections) — `cli/tests/_doc_rules.py`
- **_rel()** (5 connections) — `cli/tests/_doc_rules.py`
- **technical_docs()** (5 connections) — `cli/tests/_doc_rules.py`
- **long_term_docs()** (4 connections) — `cli/tests/_doc_rules.py`
- **_rel()** (4 connections) — `cli/tests/test_technical_docs.py`
- **comment_units()** (3 connections) — `cli/tests/_doc_rules.py`
- **diagram_sources()** (3 connections) — `cli/tests/_doc_rules.py`
- **user_docs()** (3 connections) — `cli/tests/_doc_rules.py`
- **_rel()** (3 connections) — `cli/tests/test_code_comments.py`
- **test_scan_face_is_not_empty()** (3 connections) — `cli/tests/test_technical_docs.py`
- **Path** (2 connections)
- **test_scan_face_is_not_empty()** (2 connections) — `cli/tests/test_code_comments.py`
- **Path** (2 connections)
- **人读文本的规则、扫描面与抽取器：护栏三层共用的**单一事实源**（ADR 0046）。 内容三类：①规则——内部指代表 FORBIDDEN、口吻表…** (1 connections) — `cli/tests/_doc_rules.py`
- **寿命长、只许指稳定物的文档（悬空指针红线的适用面）。** (1 connections) — `cli/tests/_doc_rules.py`
- **contributor 侧 AI agent 文档：口吻放开，但形态②的自造词与悬空指针照样不许（ADR 0045 决策六 / 悬空指针红线）。** (1 connections) — `cli/tests/_doc_rules.py`
- *... and 8 more nodes in this community*

## Relationships

- [Skill Doc Flag Guardrails](Skill_Doc_Flag_Guardrails.md) (8 shared connections)
- [ADR Hygiene Checks](ADR_Hygiene_Checks.md) (7 shared connections)
- [User Docs Guardrails](User_Docs_Guardrails.md) (3 shared connections)
- [Doc Rules Checker](Doc_Rules_Checker.md) (3 shared connections)
- [Contributor Guardrail Docs](Contributor_Guardrail_Docs.md) (2 shared connections)
- [Context Glossary Checks](Context_Glossary_Checks.md) (1 shared connections)
- [Package README Guardrails](Package_README_Guardrails.md) (1 shared connections)
- [Skill Deploy Token Checks](Skill_Deploy_Token_Checks.md) (1 shared connections)
- [Skill Materialization Checks](Skill_Materialization_Checks.md) (1 shared connections)
- [Skill Contract Rendering](Skill_Contract_Rendering.md) (1 shared connections)
- [Command Span Parsing](Command_Span_Parsing.md) (1 shared connections)

## Source Files

- `cli/tests/_doc_rules.py`
- `cli/tests/test_code_comments.py`
- `cli/tests/test_technical_docs.py`

## Audit Trail

- EXTRACTED: 89 (98%)
- INFERRED: 2 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*