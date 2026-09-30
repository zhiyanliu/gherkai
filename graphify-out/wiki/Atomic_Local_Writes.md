# Atomic Local Writes

> 47 nodes · cohesion 0.06

## Key Concepts

- **report_store/local.py** (17 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **atomic_write_json()** (14 connections) — `core/gherkai_core/adapters/_atomic.py`
- **test_atomic_write.py** (10 connections) — `core/tests/test_atomic_write.py`
- **atomic_write_text()** (9 connections) — `core/gherkai_core/adapters/_atomic.py`
- **render_index_html()** (9 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **.write()** (8 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **_atomic.py** (7 connections) — `core/gherkai_core/adapters/_atomic.py`
- **collect_report_index()** (7 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **._collect()** (7 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **.write()** (6 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **local_path_from_uri()** (5 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **_relative_href()** (5 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **.save_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **Path** (4 connections)
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
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/report_store/local.py`
- *... and 22 more nodes in this community*

## Relationships

- [Report Store Adapters](Report_Store_Adapters.md) (9 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (8 shared connections)
- [Result Store Serialization](Result_Store_Serialization.md) (3 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (3 shared connections)
- [Boto3 Adapter Guard](Boto3_Adapter_Guard.md) (3 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (1 shared connections)
- [Cloud Engine Resolver Build](Cloud_Engine_Resolver_Build.md) (1 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/_atomic.py`
- `core/gherkai_core/adapters/report_store/__init__.py`
- `core/gherkai_core/adapters/report_store/local.py`
- `core/gherkai_core/adapters/report_store/s3.py`
- `core/gherkai_core/adapters/result_store/local.py`
- `core/tests/test_atomic_write.py`

## Audit Trail

- EXTRACTED: 95 (98%)
- INFERRED: 2 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*