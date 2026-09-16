# Doc Command Scanning Rules

> 12 nodes · cohesion 0.21

## Key Concepts

- **_doc_rules.py** (11 connections) — `cli/tests/_doc_rules.py`
- **extract_command_spans()** (8 connections) — `cli/tests/_doc_rules.py`
- **bare_flags()** (5 connections) — `cli/tests/_doc_rules.py`
- **clean_flag()** (4 connections) — `cli/tests/_doc_rules.py`
- **CommandSpan** (4 connections) — `cli/tests/_doc_rules.py`
- **Path** (2 connections)
- **NamedTuple** (1 connections)
- **使用者面 markdown 的共享规则与扫描器：多处护栏共用的**单一事实源**。…** (1 connections) — `cli/tests/_doc_rules.py`
- **`--scope=<id>，` → `--scope`；不是 flag 则 None。`--` 单独出现（参数分隔符）不算 flag。** (1 connections) — `cli/tests/_doc_rules.py`
- **一个 `gherkai …` 代码跨的拆解结果。 `words` = `gherkai` 之后、第一个 flag…** (1 connections) — `cli/tests/_doc_rules.py`
- **抽出 `gherkai …` 形态的代码跨。行号按跨在原文里的位置算，报错时能直接点到人。** (1 connections) — `cli/tests/_doc_rules.py`
- **代码跨里出现的全部 `--flag`（含 `gherkai …` 跨内的），→ (flag, 行号, 跨原文)。弱断言用。** (1 connections) — `cli/tests/_doc_rules.py`

## Relationships

- [Agent Skill Guardrails](Agent_Skill_Guardrails.md) (7 shared connections)
- [Skill Deploy Token Guardrail](Skill_Deploy_Token_Guardrail.md) (2 shared connections)
- [README & Docs Guardrails](README_%26_Docs_Guardrails.md) (1 shared connections)
- [Skill Contract Rendering](Skill_Contract_Rendering.md) (1 shared connections)
- [Doc Flag Path Validation](Doc_Flag_Path_Validation.md) (1 shared connections)

## Source Files

- `cli/tests/_doc_rules.py`

## Audit Trail

- EXTRACTED: 25 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*