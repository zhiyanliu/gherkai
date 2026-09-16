# Contract Key Documentation Check

> 7 nodes · cohesion 0.33

## Key Concepts

- **_documented_keys()** (4 connections) — `cli/tests/test_skill.py`
- **test_key_shaped_tokens_are_documented_keys()** (4 connections) — `cli/tests/test_skill.py`
- **collect()** (3 connections) — `skills/gherkai-evals/summarize_runs.py`
- **summarize_runs.py** (2 connections) — `skills/gherkai-evals/summarize_runs.py`
- **main()** (2 connections) — `skills/gherkai-evals/summarize_runs.py`
- **契约页记载的字段名。取「字段表里（任一列）+『顶层…』/『每项…』散文里」的反引号 token， 再按键形状过滤——ADR…** (1 connections) — `cli/tests/test_skill.py`
- **skill 里形如 JSON 键的反引号 token 必须是契约页记载的键，否则显式登记成非键。 挡的是「把 `record_missing` 写成…** (1 connections) — `cli/tests/test_skill.py`

## Relationships

- [Agent Skill Guardrails](Agent_Skill_Guardrails.md) (3 shared connections)

## Source Files

- `cli/tests/test_skill.py`
- `skills/gherkai-evals/summarize_runs.py`

## Audit Trail

- EXTRACTED: 9 (90%)
- INFERRED: 1 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*