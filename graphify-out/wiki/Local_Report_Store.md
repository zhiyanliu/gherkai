# Local Report Store

> 37 nodes · cohesion 0.18

## Key Concepts

- **LocalReportStore** (39 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **test_report_store.py** (37 connections) — `core/tests/test_report_store.py`
- **ReportRef** (31 connections) — `core/gherkai_core/model.py`
- **_jr()** (21 connections) — `core/tests/test_report_store.py`
- **_rr()** (21 connections) — `core/tests/test_report_store.py`
- **_run_with_refs()** (19 connections) — `core/tests/test_report_store.py`
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
- *... and 12 more nodes in this community*

## Relationships

- [Result Rendering & Explain](Result_Rendering_%26_Explain.md) (25 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (13 shared connections)
- [S3 Report Store](S3_Report_Store.md) (13 shared connections)
- [Report Store Collection](Report_Store_Collection.md) (7 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (5 shared connections)
- [S3 Result Store](S3_Result_Store.md) (5 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (3 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (2 shared connections)
- [Local Result Store](Local_Result_Store.md) (2 shared connections)
- [Job State Serialization](Job_State_Serialization.md) (2 shared connections)
- [Local Store Preflight](Local_Store_Preflight.md) (1 shared connections)
- [Atomic Local File Writes](Atomic_Local_File_Writes.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/report_store/local.py`
- `core/gherkai_core/model.py`
- `core/tests/test_report_store.py`

## Audit Trail

- EXTRACTED: 193 (94%)
- INFERRED: 13 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*