# S3 Report Store Tests

> 12 nodes · cohesion 0.33

## Key Concepts

- **test_s3_report_store.py** (19 connections) — `core/tests/test_s3_report_store.py`
- **_run_with_refs()** (18 connections) — `core/tests/test_report_store.py`
- **_read_s3()** (6 connections) — `core/tests/test_s3_report_store.py`
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

- [Report Refs & Results](Report_Refs_%26_Results.md) (20 shared connections)
- [S3 Report Store & Subprocess](S3_Report_Store_%26_Subprocess.md) (2 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (1 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (1 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (1 shared connections)

## Source Files

- `core/tests/test_report_store.py`
- `core/tests/test_s3_report_store.py`

## Audit Trail

- EXTRACTED: 47 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*