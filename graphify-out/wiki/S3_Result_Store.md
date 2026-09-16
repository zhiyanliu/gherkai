# S3 Result Store

> 43 nodes · cohesion 0.08

## Key Concepts

- **JobResult** (83 connections) — `core/gherkai_core/model.py`
- **job_result_from_dict()** (22 connections) — `core/gherkai_core/serialize.py`
- **S3ResultStore** (17 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **test_s3_result_store.py** (15 connections) — `core/tests/test_s3_result_store.py`
- **_job_def()** (14 connections) — `core/tests/test_stores.py`
- **result_store/s3.py** (9 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **test_job_timeout_s_round_trip()** (6 connections) — `core/tests/test_stores.py`
- **.load_all()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.load_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.save_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **test_new_states_round_trip()** (5 connections) — `core/tests/test_lifecycle_states.py`
- **test_result_store_scope_id_not_path_traversal()** (5 connections) — `core/tests/test_stores.py`
- **.load_all()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.load_job_result()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **._key()** (4 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **test_prefix_isolates_runs()** (4 connections) — `core/tests/test_s3_result_store.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **._jobs_prefix()** (3 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **_ref_from_dict()** (3 connections) — `core/gherkai_core/serialize.py`
- **_votes_from_dict()** (3 connections) — `core/gherkai_core/serialize.py`
- **test_load_all_paginated_preserves_failed_verdict()** (3 connections) — `core/tests/test_s3_result_store.py`
- **test_load_all_paginates_beyond_1000()** (3 connections) — `core/tests/test_s3_result_store.py`
- **test_load_all_stable_order()** (3 connections) — `core/tests/test_s3_result_store.py`
- **test_scope_id_with_slash_not_subprefix()** (3 connections) — `core/tests/test_s3_result_store.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- *... and 18 more nodes in this community*

## Relationships

- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (24 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (16 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (11 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (10 shared connections)
- [Text Render & Wording Guards](Text_Render_%26_Wording_Guards.md) (9 shared connections)
- [Event Formatting](Event_Formatting.md) (8 shared connections)
- [S3 Report Store & Control Plane](S3_Report_Store_%26_Control_Plane.md) (7 shared connections)
- [Local Report Store](Local_Report_Store.md) (5 shared connections)
- [Job Execution with Retry](Job_Execution_with_Retry.md) (4 shared connections)
- [Typed Errors & Severity](Typed_Errors_%26_Severity.md) (4 shared connections)
- [Atomic Local Writes](Atomic_Local_Writes.md) (3 shared connections)
- [Cloud Adapter Integration Tests](Cloud_Adapter_Integration_Tests.md) (2 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/local.py`
- `core/gherkai_core/adapters/result_store/s3.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/serialize.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_s3_result_store.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 160 (86%)
- INFERRED: 25 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*