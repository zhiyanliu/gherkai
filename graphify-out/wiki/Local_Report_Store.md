# Local Report Store

> 52 nodes · cohesion 0.12

## Key Concepts

- **LocalReportStore** (39 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **test_report_store.py** (37 connections) — `core/tests/test_report_store.py`
- **StepResult** (35 connections) — `core/gherkai_core/model.py`
- **ReportRef** (30 connections) — `core/gherkai_core/model.py`
- **_jr()** (21 connections) — `core/tests/test_report_store.py`
- **_rr()** (21 connections) — `core/tests/test_report_store.py`
- **_run_with_refs()** (19 connections) — `core/tests/test_report_store.py`
- **test_s3_report_store.py** (19 connections) — `core/tests/test_s3_report_store.py`
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
- **_read_s3()** (6 connections) — `core/tests/test_s3_report_store.py`
- *... and 27 more nodes in this community*

## Relationships

- [Text Render & Wording Guards](Text_Render_%26_Wording_Guards.md) (23 shared connections)
- [S3 Report Store & Control Plane](S3_Report_Store_%26_Control_Plane.md) (9 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (8 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (8 shared connections)
- [Report Index Collection](Report_Index_Collection.md) (7 shared connections)
- [Schedule Core & Fakes](Schedule_Core_%26_Fakes.md) (6 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (6 shared connections)
- [Event Formatting](Event_Formatting.md) (6 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (5 shared connections)
- [S3 Result Store](S3_Result_Store.md) (5 shared connections)
- [Explain Command Tests](Explain_Command_Tests.md) (4 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (2 shared connections)

## Source Files

- `core/gherkai_core/adapters/report_store/local.py`
- `core/gherkai_core/model.py`
- `core/tests/test_report_store.py`
- `core/tests/test_s3_report_store.py`

## Audit Trail

- EXTRACTED: 238 (93%)
- INFERRED: 18 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*