# S3 Report Store Tests

> 13 nodes · cohesion 0.31

## Key Concepts

- **_run_with_refs()** (19 connections) — `core/tests/test_report_store.py`
- **test_s3_report_store.py** (19 connections) — `core/tests/test_s3_report_store.py`
- **_read_s3()** (6 connections) — `core/tests/test_s3_report_store.py`
- **test_index_html_taints_shortcircuited_step()** (6 connections) — `core/tests/test_s3_report_store.py`
- **test_empty_report_refs_still_valid_index()** (5 connections) — `core/tests/test_s3_report_store.py`
- **_read_manifest()** (4 connections) — `core/tests/test_s3_report_store.py`
- **test_index_html_links_and_summary()** (3 connections) — `core/tests/test_s3_report_store.py`
- **test_manifest_shape()** (3 connections) — `core/tests/test_s3_report_store.py`
- **test_prefix_lands_under_prefix()** (3 connections) — `core/tests/test_s3_report_store.py`
- **test_s3_href_not_relativized_kept_as_ref()** (3 connections) — `core/tests/test_s3_report_store.py`
- **test_writes_manifest_and_index()** (3 connections) — `core/tests/test_s3_report_store.py`
- **S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…** (1 connections) — `core/tests/test_s3_report_store.py`
- **把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。** (1 connections) — `core/tests/test_s3_report_store.py`

## Relationships

- [Local Report Store](Local_Report_Store.md) (16 shared connections)
- [Result Store & Report Refs](Result_Store_%26_Report_Refs.md) (7 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (2 shared connections)
- [S3 Store Adapters](S3_Store_Adapters.md) (2 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (1 shared connections)

## Source Files

- `core/tests/test_report_store.py`
- `core/tests/test_s3_report_store.py`

## Audit Trail

- EXTRACTED: 52 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*