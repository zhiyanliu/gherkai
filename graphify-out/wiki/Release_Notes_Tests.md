# Release Notes Tests

> 10 nodes · cohesion 0.29

## Key Concepts

- **test_release_notes.py** (7 connections) — `cli/tests/test_release_notes.py`
- **_mod()** (5 connections) — `cli/tests/test_release_notes.py`
- **test_repo_changelog_has_every_released_tag_and_unreleased()** (3 connections) — `cli/tests/test_release_notes.py`
- **test_cli_check_exit_codes()** (2 connections) — `cli/tests/test_release_notes.py`
- **test_render_pins_links_to_the_tag()** (2 connections) — `cli/tests/test_release_notes.py`
- **test_section_extracts_exactly_one_version()** (2 connections) — `cli/tests/test_release_notes.py`
- **test_section_missing_or_empty_is_an_error()** (2 connections) — `cli/tests/test_release_notes.py`
- **Path** (1 connections)
- **`.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」与 Release…** (1 connections) — `cli/tests/test_release_notes.py`
- **真 CHANGELOG.md 对照真值集：每个已发行 tag `vX.Y.Z` 都要有非空节；`## [Unreleased]` 要在。** (1 connections) — `cli/tests/test_release_notes.py`

## Relationships

- No strong cross-community connections detected

## Source Files

- `cli/tests/test_release_notes.py`

## Audit Trail

- EXTRACTED: 13 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*