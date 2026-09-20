# Skill Contract Rendering

> 12 nodes · cohesion 0.26

## Key Concepts

- **render_skill_contract.py** (7 connections) — `tools/render_skill_contract.py`
- **transform()** (6 connections) — `tools/render_skill_contract.py`
- **TransformError** (5 connections) — `tools/render_skill_contract.py`
- **_assert_clean()** (4 connections) — `tools/render_skill_contract.py`
- **_paragraphs()** (3 connections) — `tools/render_skill_contract.py`
- **render()** (3 connections) — `tools/render_skill_contract.py`
- **main()** (2 connections) — `tools/render_skill_contract.py`
- **RuntimeError** (1 connections)
- **按空行切段（段内保留原始换行——源页的长段是手工折行的，副本逐字继承才好 diff）。** (1 connections) — `tools/render_skill_contract.py`
- **转换后的三条硬断言：无禁词、无相对链接、无仓库内路径。命中即报行号，让人回去补登记表。** (1 connections) — `tools/render_skill_contract.py`
- **源页形态或内容超出登记范围。宁可失败，也不把内部指代发进使用方项目。** (1 connections) — `tools/render_skill_contract.py`
- **纯函数：源页正文 → 副本正文。无 IO、无全局状态，护栏直接拿它比对入库副本。** (1 connections) — `tools/render_skill_contract.py`

## Relationships

- [Doc Scanning Rules](Doc_Scanning_Rules.md) (1 shared connections)

## Source Files

- `tools/render_skill_contract.py`

## Audit Trail

- EXTRACTED: 18 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*