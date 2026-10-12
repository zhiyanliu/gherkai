# S3 Report Store

> 15 nodes · cohesion 0.20

## Key Concepts

- **test_s3_report_store.py** (19 connections) — `core/tests/test_s3_report_store.py`
- **S3ReportStore** (18 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **_read_s3()** (6 connections) — `core/tests/test_s3_report_store.py`
- **test_empty_report_refs_still_valid_index()** (5 connections) — `core/tests/test_s3_report_store.py`
- **_read_manifest()** (4 connections) — `core/tests/test_s3_report_store.py`
- **test_index_html_links_and_summary()** (3 connections) — `core/tests/test_s3_report_store.py`
- **test_manifest_shape()** (3 connections) — `core/tests/test_s3_report_store.py`
- **test_prefix_lands_under_prefix()** (3 connections) — `core/tests/test_s3_report_store.py`
- **test_s3_href_not_relativized_kept_as_ref()** (3 connections) — `core/tests/test_s3_report_store.py`
- **test_writes_manifest_and_index()** (3 connections) — `core/tests/test_s3_report_store.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…** (1 connections) — `core/tests/test_s3_report_store.py`
- **把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。** (1 connections) — `core/tests/test_s3_report_store.py`

## Relationships

- [Explain Reads And Report Store](Explain_Reads_And_Report_Store.md) (15 shared connections)
- [Store Port Definitions](Store_Port_Definitions.md) (5 shared connections)
- [Cloud Adapter Test Fixtures](Cloud_Adapter_Test_Fixtures.md) (2 shared connections)
- [Report Store Local](Report_Store_Local.md) (2 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (2 shared connections)
- [boto3 Client Injection](boto3_Client_Injection.md) (1 shared connections)
- [Result Tree Rendering](Result_Tree_Rendering.md) (1 shared connections)
- [SSM Paths And Compose](SSM_Paths_And_Compose.md) (1 shared connections)
- [Step Argument S3 Offload](Step_Argument_S3_Offload.md) (1 shared connections)
- [Cloud Compose Root](Cloud_Compose_Root.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/report_store/s3.py`
- `core/tests/test_s3_report_store.py`

## Audit Trail

- EXTRACTED: 43 (83%)
- INFERRED: 9 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*