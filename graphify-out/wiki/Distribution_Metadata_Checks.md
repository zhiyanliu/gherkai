# Distribution Metadata Checks

> 13 nodes · cohesion 0.28

## Key Concepts

- **check_dist_metadata.py** (7 connections) — `.github/scripts/check_dist_metadata.py`
- **main()** (7 connections) — `.github/scripts/check_dist_metadata.py`
- **check_skill_payload()** (5 connections) — `.github/scripts/check_dist_metadata.py`
- **Path** (5 connections)
- **member_dist_names()** (4 connections) — `.github/scripts/check_dist_metadata.py`
- **skill_source_files()** (4 connections) — `.github/scripts/check_dist_metadata.py`
- **normalize()** (3 connections) — `.github/scripts/check_dist_metadata.py`
- **wheel_metadata()** (3 connections) — `.github/scripts/check_dist_metadata.py`
- **fail()** (2 connections) — `.github/scripts/check_dist_metadata.py`
- **发行名 → 产物文件名里的形态（PEP 503 规范化后 `-`/`.` 变 `_`，见 PEP 427/625）。** (1 connections) — `.github/scripts/check_dist_metadata.py`
- **真值集：workspace 成员目录 → 其 `[project] name`（发行名）。** (1 connections) — `.github/scripts/check_dist_metadata.py`
- **真值集：源目录的文件系统遍历（**不用 `git ls-files`**——见模块 docstring 断言 4 的理由： 受不受 git 跟踪与进不进…** (1 connections) — `.github/scripts/check_dist_metadata.py`
- **断言 4：wheel 内 skill 文件集 == 源目录文件集，且 wheel 里不含评测资产。** (1 connections) — `.github/scripts/check_dist_metadata.py`

## Relationships

- No strong cross-community connections detected

## Source Files

- `.github/scripts/check_dist_metadata.py`

## Audit Trail

- EXTRACTED: 22 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*