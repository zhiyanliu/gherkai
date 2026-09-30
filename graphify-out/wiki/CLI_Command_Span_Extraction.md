# CLI Command Span Extraction

> 10 nodes · cohesion 0.20

## Key Concepts

- **extract_command_spans()** (8 connections) — `cli/tests/_doc_rules.py`
- **clean_flag()** (4 connections) — `cli/tests/_doc_rules.py`
- **CommandSpan** (4 connections) — `cli/tests/_doc_rules.py`
- **_deploy_spans()** (4 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **test_deploy_flags_are_attached_to_the_right_subverb()** (4 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **NamedTuple** (1 connections)
- **一个 `gherkai …` 代码跨的拆解结果。 `words` = `gherkai` 之后、第一个 flag…** (1 connections) — `cli/tests/_doc_rules.py`
- **抽出 `gherkai …` 形态的代码跨。行号按跨在原文里的位置算，报错时能直接点到人。** (1 connections) — `cli/tests/_doc_rules.py`
- **`--scope=<id>，` → `--scope`；不是 flag 则 None。`--` 单独出现（参数分隔符）不算 flag。** (1 connections) — `cli/tests/_doc_rules.py`
- **`gherkai deploy [<子动词>] --flag` 逐对比对。父层给法合法（`deploy --prefix p push-worker …`），…** (1 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`

## Relationships

- [Skill Docs Guardrail Tests](Skill_Docs_Guardrail_Tests.md) (5 shared connections)
- [Doc Rules Scan Sources](Doc_Rules_Scan_Sources.md) (4 shared connections)
- [Skill Deploy Token Guardrail](Skill_Deploy_Token_Guardrail.md) (2 shared connections)

## Source Files

- `cli/tests/_doc_rules.py`
- `deploy_aws/tests/test_skill_deploy_tokens.py`

## Audit Trail

- EXTRACTED: 17 (85%)
- INFERRED: 3 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*