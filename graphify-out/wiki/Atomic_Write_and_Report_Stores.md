# Atomic Write and Report Stores

> 34 nodes · cohesion 0.09

## Key Concepts

- **report_store/local.py** (17 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **atomic_write_json()** (14 connections) — `core/gherkai_core/adapters/_atomic.py`
- **test_atomic_write.py** (10 connections) — `core/tests/test_atomic_write.py`
- **atomic_write_text()** (9 connections) — `core/gherkai_core/adapters/_atomic.py`
- **render_index_html()** (9 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **report_store/s3.py** (9 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **.write()** (8 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **_atomic.py** (7 connections) — `core/gherkai_core/adapters/_atomic.py`
- **report_store/__init__.py** (3 connections) — `core/gherkai_core/adapters/report_store/__init__.py`
- **_reason_html()** (3 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **_page()** (3 connections) — `core/tests/test_atomic_write.py`
- **test_concurrent_reader_never_sees_empty_or_truncated_text()** (3 connections) — `core/tests/test_atomic_write.py`
- **test_failed_replace_leaves_no_tmp_behind()** (3 connections) — `core/tests/test_atomic_write.py`
- **test_json_round_trip_and_default_mode_readable_by_others()** (3 connections) — `core/tests/test_atomic_write.py`
- **test_mode_can_be_narrowed()** (3 connections) — `core/tests/test_atomic_write.py`
- **test_target_name_at_name_max_still_writable()** (3 connections) — `core/tests/test_atomic_write.py`
- **Path** (2 connections)
- **_fmt_ms()** (2 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。…** (1 connections) — `core/gherkai_core/adapters/_atomic.py`
- **把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。** (1 connections) — `core/gherkai_core/adapters/_atomic.py`
- **同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。** (1 connections) — `core/gherkai_core/adapters/_atomic.py`
- **ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…** (1 connections) — `core/gherkai_core/adapters/report_store/__init__.py`
- **ResourceUri** (1 connections)
- **LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **渲染一行的「原因」片段——job 行与 step 行共用同一份，**别再造第三种样式**。 两分支口径同 render_text（有分类 → err…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- *... and 9 more nodes in this community*

## Relationships

- [Report Index Collection](Report_Index_Collection.md) (6 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (5 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (4 shared connections)
- [Local Report Store](Local_Report_Store.md) (4 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (2 shared connections)
- [Boto Guard and Arg Offload](Boto_Guard_and_Arg_Offload.md) (2 shared connections)
- [Local Result Store](Local_Result_Store.md) (1 shared connections)
- [Run Store Adapters](Run_Store_Adapters.md) (1 shared connections)
- [Result Store & Report Refs](Result_Store_%26_Report_Refs.md) (1 shared connections)
- [S3 Store Adapters](S3_Store_Adapters.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/_atomic.py`
- `core/gherkai_core/adapters/report_store/__init__.py`
- `core/gherkai_core/adapters/report_store/local.py`
- `core/gherkai_core/adapters/report_store/s3.py`
- `core/tests/test_atomic_write.py`

## Audit Trail

- EXTRACTED: 76 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*