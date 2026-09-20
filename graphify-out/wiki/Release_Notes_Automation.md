# Release Notes Automation

> 12 nodes · cohesion 0.26

## Key Concepts

- **release.yml 发布链** (8 connections) — `.github/workflows/release.yml`
- **CI 与发布链说明** (7 connections) — `.github/workflows/README.md`
- **release_notes.py** (6 connections) — `.github/scripts/release_notes.py`
- **section()** (5 connections) — `.github/scripts/release_notes.py`
- **main()** (3 connections) — `.github/scripts/release_notes.py`
- **render()** (3 connections) — `.github/scripts/release_notes.py`
- **wait_for_index.sh** (3 connections) — `.github/scripts/wait_for_index.sh`
- **ci.yml 工作流** (3 connections) — `.github/workflows/ci.yml`
- **版本真源 (single version source)** (2 connections) — `CONTEXT.md`
- **GitHub Release 正文固定块** (2 connections) — `.github/release_body_footer.md`
- **`## [version]` 到下一个 `## ` 之间的正文（不含标题行），两端空行去掉。找不到节 → ValueError。** (1 connections) — `.github/scripts/release_notes.py`
- **wait_for_index.sh script** (1 connections) — `.github/scripts/wait_for_index.sh`

## Relationships

- [Distribution Metadata Checks](Distribution_Metadata_Checks.md) (3 shared connections)
- [Contributor Guardrail Docs](Contributor_Guardrail_Docs.md) (3 shared connections)
- [Changelog & Skill Docs](Changelog_%26_Skill_Docs.md) (2 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (1 shared connections)
- [Core Package Docs](Core_Package_Docs.md) (1 shared connections)

## Source Files

- `.github/release_body_footer.md`
- `.github/scripts/release_notes.py`
- `.github/scripts/wait_for_index.sh`
- `.github/workflows/README.md`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `CONTEXT.md`

## Audit Trail

- EXTRACTED: 26 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*