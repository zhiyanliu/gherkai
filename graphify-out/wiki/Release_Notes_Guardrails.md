# Release Notes Guardrails

> 15 nodes · cohesion 0.21

## Key Concepts

- **test_release_notes.py** (10 connections) — `cli/tests/test_release_notes.py`
- **_mod()** (7 connections) — `cli/tests/test_release_notes.py`
- **_check()** (4 connections) — `cli/tests/test_release_notes.py`
- **test_cli_check_exit_codes()** (3 connections) — `cli/tests/test_release_notes.py`
- **test_repo_changelog_has_every_released_tag_and_unreleased()** (3 connections) — `cli/tests/test_release_notes.py`
- **test_repo_readme_pins_skill_install_to_changelog_top_version()** (3 connections) — `cli/tests/test_release_notes.py`
- **Path** (2 connections)
- **test_render_pins_links_to_the_tag()** (2 connections) — `cli/tests/test_release_notes.py`
- **test_section_extracts_exactly_one_version()** (2 connections) — `cli/tests/test_release_notes.py`
- **test_section_missing_or_empty_is_an_error()** (2 connections) — `cli/tests/test_release_notes.py`
- **test_skill_install_tag_problems()** (2 connections) — `cli/tests/test_release_notes.py`
- **`.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」（ADR 0045…** (1 connections) — `cli/tests/test_release_notes.py`
- **真 CHANGELOG.md 对照真值集：每个已发行 tag `vX.Y.Z` 都要有非空节；`## [Unreleased]` 要在。** (1 connections) — `cli/tests/test_release_notes.py`
- **真 README / user guide 对照真值集：skill 安装命令钉的 tag 等于 CHANGELOG 顶部已发行版本（发版前两处同一次改）。** (1 connections) — `cli/tests/test_release_notes.py`
- **CompletedProcess** (1 connections)

## Relationships

- No strong cross-community connections detected

## Source Files

- `cli/tests/test_release_notes.py`

## Audit Trail

- EXTRACTED: 22 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*