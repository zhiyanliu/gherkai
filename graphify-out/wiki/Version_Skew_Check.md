# Version Skew Check

> 16 nodes · cohesion 0.12

## Key Concepts

- **check_version_skew()** (12 connections) — `runtime/gherkai_runtime/compose.py`
- **test_skew_block_when_cli_newer_names_both_exits()** (3 connections) — `runtime/tests/test_compose.py`
- **test_skew_cli_version_is_mandatory_no_runtime_fallback()** (3 connections) — `runtime/tests/test_compose.py`
- **test_skew_compares_release_segment_only()** (3 connections) — `runtime/tests/test_compose.py`
- **test_skew_skip_when_either_side_impure()** (3 connections) — `runtime/tests/test_compose.py`
- **test_skew_skip_when_own_version_unknown()** (3 connections) — `runtime/tests/test_compose.py`
- **test_skew_warn_when_stamp_missing_points_at_deploy()** (3 connections) — `runtime/tests/test_compose.py`
- **test_skew_ok_same_release_is_silent()** (2 connections) — `runtime/tests/test_compose.py`
- **test_skew_warn_when_cli_older()** (2 connections) — `runtime/tests/test_compose.py`
- **比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict ∈ ok/warn/block/skip（ADR 0037 决策…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **CLI 新于后端 → block，且消息必须点名**两条**出路（决策 7 不设放行口，只有这两条）。** (1 connections) — `runtime/tests/test_compose.py`
- **戳缺失 = 本机制之前部署的环境 → warn（不拦）+ 提示跑一次 `gherkai deploy` 写入。** (1 connections) — `runtime/tests/test_compose.py`
- **任一侧带 .dev/.post/本地段 → skip（dev 逐提交前进，逐字比会把每次都判成 skew）。** (1 connections) — `runtime/tests/test_compose.py`
- **未装成包（源码直跑）→ 调用点取不到自身版本、传 None → skip，不误判成 skew。** (1 connections) — `runtime/tests/test_compose.py`
- **只比 release 段（决策 7）：位数不同补零后比；同 release 段的 rc 与正式版视作同版本。** (1 connections) — `runtime/tests/test_compose.py`
- **`cli_version` 必给（决策 7 比的是「写任务定义那一方」的版本）：不缺省成 gherkai-runtime 的版本—— editable…** (1 connections) — `runtime/tests/test_compose.py`

## Relationships

- [Cloud Target Resolution](Cloud_Target_Resolution.md) (8 shared connections)
- [SSM Path & Client Composition](SSM_Path_%26_Client_Composition.md) (2 shared connections)
- [Backend Version Stamp](Backend_Version_Stamp.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 26 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*