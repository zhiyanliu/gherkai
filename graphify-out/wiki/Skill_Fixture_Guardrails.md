# Skill Fixture Guardrails

> 15 nodes · cohesion 0.17

## Key Concepts

- **parametrize** (5 connections)
- **_fixture_files()** (4 connections) — `cli/tests/test_skill.py`
- **_is_ignored()** (4 connections) — `cli/tests/test_skill.py`
- **Path** (4 connections)
- **test_every_fixture_file_is_tracked()** (4 connections) — `cli/tests/test_skill.py`
- **test_github_urls_are_pinned_to_head_or_tag()** (4 connections) — `cli/tests/test_skill.py`
- **test_skill_markdown_has_no_relative_links()** (4 connections) — `cli/tests/test_skill.py`
- **test_skill_markdown_is_product_facing()** (4 connections) — `cli/tests/test_skill.py`
- **test_fixture_derived_artifact_shapes_are_not_ignored()** (3 connections) — `cli/tests/test_skill.py`
- **test_fixture_secret_shapes_stay_ignored()** (3 connections) — `cli/tests/test_skill.py`
- **test_fixtures_carry_no_absolute_paths()** (2 connections) — `cli/tests/test_skill.py`
- **零内部指代：skill 落在使用方项目里，ADR 编号 / 决策号 / 内部机制名对那边的 agent 是噪声。** (1 connections) — `cli/tests/test_skill.py`
- **markdown 相对链接一律禁：出 skill 的（`](../…)`）在安装态必死；skill 内的（`](references/x.md)`）虽活，…** (1 connections) — `cli/tests/test_skill.py`
- **指本仓库的 URL 只用 `blob/HEAD/` / `tree/HEAD/` / `tree/v…/`（裸仓库首页不指内容，也放行）：…** (1 connections) — `cli/tests/test_skill.py`
- **提交前抓漏：磁盘上 `fixtures/**` 每个文件都在 `git ls-files` 里（干净克隆上恒绿，不是 CI 的唯一防线—— 行为式…** (1 connections) — `cli/tests/test_skill.py`

## Relationships

- [Agent Skill Guardrails](Agent_Skill_Guardrails.md) (9 shared connections)

## Source Files

- `cli/tests/test_skill.py`

## Audit Trail

- EXTRACTED: 27 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*