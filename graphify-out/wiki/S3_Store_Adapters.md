# S3 Store Adapters

> 40 nodes · cohesion 0.07

## Key Concepts

- **S3ReportStore** (18 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **S3ResultStore** (17 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **test_s3_result_store.py** (15 connections) — `core/tests/test_s3_result_store.py`
- **core/tests/conftest.py** (14 connections) — `core/tests/conftest.py`
- **_job_def()** (14 connections) — `core/tests/test_stores.py`
- **build_cloud_stores()** (11 connections) — `runtime/gherkai_runtime/compose.py`
- **test_job_timeout_s_round_trip()** (6 connections) — `core/tests/test_stores.py`
- **.load_all()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.load_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.save_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **._key()** (4 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **ddb_run_store()** (4 connections) — `core/tests/conftest.py`
- **ddb_run_store_offload()** (4 connections) — `core/tests/conftest.py`
- **s3_report_store()** (4 connections) — `core/tests/conftest.py`
- **s3_result_store()** (4 connections) — `core/tests/conftest.py`
- **test_prefix_isolates_runs()** (4 connections) — `core/tests/test_s3_result_store.py`
- **._jobs_prefix()** (3 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **test_load_all_paginated_preserves_failed_verdict()** (3 connections) — `core/tests/test_s3_result_store.py`
- **test_load_all_paginates_beyond_1000()** (3 connections) — `core/tests/test_s3_result_store.py`
- **test_load_all_stable_order()** (3 connections) — `core/tests/test_s3_result_store.py`
- **test_scope_id_with_slash_not_subprefix()** (3 connections) — `core/tests/test_s3_result_store.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **test_save_load_round_trip()** (2 connections) — `core/tests/test_s3_result_store.py`
- **Job** (2 connections)
- *... and 15 more nodes in this community*

## Relationships

- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (18 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (13 shared connections)
- [Test Fixtures and Conftest](Test_Fixtures_and_Conftest.md) (8 shared connections)
- [Boto Guard and Arg Offload](Boto_Guard_and_Arg_Offload.md) (5 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (5 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (5 shared connections)
- [Run State Store](Run_State_Store.md) (4 shared connections)
- [S3 Report Store Tests](S3_Report_Store_Tests.md) (2 shared connections)
- [Cloud Integration Tests](Cloud_Integration_Tests.md) (2 shared connections)
- [Cloud Resource Resolution](Cloud_Resource_Resolution.md) (2 shared connections)
- [Atomic Write and Report Stores](Atomic_Write_and_Report_Stores.md) (1 shared connections)
- [Report Index Collection](Report_Index_Collection.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/report_store/s3.py`
- `core/gherkai_core/adapters/result_store/s3.py`
- `core/tests/conftest.py`
- `core/tests/test_s3_result_store.py`
- `core/tests/test_stores.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 106 (89%)
- INFERRED: 13 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*