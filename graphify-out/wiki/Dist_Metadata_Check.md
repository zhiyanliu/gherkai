# Dist Metadata Check

> 9 nodes · cohesion 0.39

## Key Concepts

- **main()** (6 connections) — `.github/scripts/check_dist_metadata.py`
- **check_dist_metadata.py** (5 connections) — `.github/scripts/check_dist_metadata.py`
- **member_dist_names()** (4 connections) — `.github/scripts/check_dist_metadata.py`
- **normalize()** (3 connections) — `.github/scripts/check_dist_metadata.py`
- **Path** (3 connections)
- **wheel_metadata()** (3 connections) — `.github/scripts/check_dist_metadata.py`
- **fail()** (2 connections) — `.github/scripts/check_dist_metadata.py`
- **发行名 → 产物文件名里的形态（PEP 503 规范化后 `-`/`.` 变 `_`，见 PEP 427/625）。** (1 connections) — `.github/scripts/check_dist_metadata.py`
- **真值集：workspace 成员目录 → 其 `[project] name`（发行名）。** (1 connections) — `.github/scripts/check_dist_metadata.py`

## Relationships

- No strong cross-community connections detected

## Source Files

- `.github/scripts/check_dist_metadata.py`

## Audit Trail

- EXTRACTED: 14 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*