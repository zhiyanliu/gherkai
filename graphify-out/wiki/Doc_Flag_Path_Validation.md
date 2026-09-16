# Doc Flag Path Validation

> 8 nodes · cohesion 0.29

## Key Concepts

- **is_placeholder()** (6 connections) — `cli/tests/_doc_rules.py`
- **test_flags_are_attached_to_the_right_subcommand()** (6 connections) — `cli/tests/test_skill.py`
- **_resolve()** (4 connections) — `cli/tests/test_skill.py`
- **_allowed_flags()** (3 connections) — `cli/tests/test_skill.py`
- **`<命令>` / `…` / `[<scope_id>]` 这类占位符不是子命令名，解析路径时跳过、不当拼错。** (1 connections) — `cli/tests/_doc_rules.py`
- **只认**同一个反引号代码跨**内的 `gherkai <子命令> … --flag` 组合，逐对对照该 subparser 的真 flag 集。…** (1 connections) — `cli/tests/test_skill.py`
- **裸词序列 → 子命令路径。第一个词不是已知子命令且不是占位符 → None（拼错的子命令）。** (1 connections) — `cli/tests/test_skill.py`
- **路径上（含各级祖先）声明的 flag 全集——`deploy --prefix p push-worker …` 这种父层给法是合法的。** (1 connections) — `cli/tests/test_skill.py`

## Relationships

- [Agent Skill Guardrails](Agent_Skill_Guardrails.md) (5 shared connections)
- [Doc Command Scanning Rules](Doc_Command_Scanning_Rules.md) (1 shared connections)
- [Skill Deploy Token Guardrail](Skill_Deploy_Token_Guardrail.md) (1 shared connections)

## Source Files

- `cli/tests/_doc_rules.py`
- `cli/tests/test_skill.py`

## Audit Trail

- EXTRACTED: 14 (93%)
- INFERRED: 1 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*