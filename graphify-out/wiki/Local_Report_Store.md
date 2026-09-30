# Local Report Store

> 34 nodes · cohesion 0.18

## Key Concepts

- **LocalReportStore** (39 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **test_report_store.py** (37 connections) — `core/tests/test_report_store.py`
- **_jr()** (21 connections) — `core/tests/test_report_store.py`
- **_rr()** (21 connections) — `core/tests/test_report_store.py`
- **Path** (18 connections)
- **_uri_to_path()** (13 connections) — `core/tests/test_report_store.py`
- **test_index_html_no_taint_on_plain_failed()** (8 connections) — `core/tests/test_report_store.py`
- **test_index_html_shows_verdict_even_without_report_refs()** (8 connections) — `core/tests/test_report_store.py`
- **test_index_html_step_reason_follows_job_style_and_has_no_orphan_css_class()** (8 connections) — `core/tests/test_report_store.py`
- **test_index_html_taints_shortcircuited_step()** (8 connections) — `core/tests/test_report_store.py`
- **test_index_reason_with_error_type_but_no_message_has_no_orphan_colon()** (8 connections) — `core/tests/test_report_store.py`
- **test_index_html_votes_tally_shown_only_when_multi_vote()** (7 connections) — `core/tests/test_report_store.py`
- **test_index_shows_fail_fast_reason_in_neutral_note_not_error_red()** (7 connections) — `core/tests/test_report_store.py`
- **test_empty_report_refs_still_valid_index()** (6 connections) — `core/tests/test_report_store.py`
- **test_file_uri_with_remote_host_kept_as_ref()** (6 connections) — `core/tests/test_report_store.py`
- **test_href_falls_back_absolute_for_artifact_outside_run_tree()** (6 connections) — `core/tests/test_report_store.py`
- **test_href_relativized_for_bare_path_ref()** (6 connections) — `core/tests/test_report_store.py`
- **test_href_relativized_percent_encoded_path()** (6 connections) — `core/tests/test_report_store.py`
- **test_href_relativized_through_symlinked_run_dir()** (6 connections) — `core/tests/test_report_store.py`
- **test_remote_ref_kept_as_ref()** (6 connections) — `core/tests/test_report_store.py`
- **test_index_html_links_and_summary()** (5 connections) — `core/tests/test_report_store.py`
- **test_report_files_keep_explicit_mode_under_tight_umask()** (5 connections) — `core/tests/test_report_store.py`
- **test_writes_manifest_and_index()** (5 connections) — `core/tests/test_report_store.py`
- **test_href_relativized_for_artifact_in_run_tree()** (4 connections) — `core/tests/test_report_store.py`
- **test_manifest_shape()** (4 connections) — `core/tests/test_report_store.py`
- *... and 9 more nodes in this community*

## Relationships

- [Result Store & Report Refs](Result_Store_%26_Report_Refs.md) (22 shared connections)
- [S3 Report Store Tests](S3_Report_Store_Tests.md) (16 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (14 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (6 shared connections)
- [Atomic Write and Report Stores](Atomic_Write_and_Report_Stores.md) (4 shared connections)
- [Report Index Collection](Report_Index_Collection.md) (2 shared connections)
- [Event Formatting](Event_Formatting.md) (2 shared connections)
- [Local Backend Preflight No-op](Local_Backend_Preflight_No-op.md) (1 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (1 shared connections)
- [Local Subprocess Launcher](Local_Subprocess_Launcher.md) (1 shared connections)
- [Run Store Adapters](Run_Store_Adapters.md) (1 shared connections)
- [Local Detached Execution](Local_Detached_Execution.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/report_store/local.py`
- `core/tests/test_report_store.py`

## Audit Trail

- EXTRACTED: 162 (93%)
- INFERRED: 12 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*