# Skill Frontmatter Validation

> 4 nodes · cohesion 0.50

## Key Concepts

- **_frontmatter_and_body()** (3 connections) — `cli/tests/test_skill.py`
- **test_skill_form_limits()** (3 connections) — `cli/tests/test_skill.py`
- **极简 frontmatter 解析（不引 yaml：dev 依赖里没有，为一条护栏引一个包不值）。 支持 `key: 单行值`、引号值，以及 `key:…** (1 connections) — `cli/tests/test_skill.py`
- **`name` 形态且等于目录名（安装目标目录名由它派生）；`description` 非空 ≤ 1024（description 优化循环…** (1 connections) — `cli/tests/test_skill.py`

## Relationships

- [Agent Skill Guardrails](Agent_Skill_Guardrails.md) (2 shared connections)

## Source Files

- `cli/tests/test_skill.py`

## Audit Trail

- EXTRACTED: 5 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*