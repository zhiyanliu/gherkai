# Report Store Adapters

> 55 nodes · cohesion 0.11

## Key Concepts

- **test_report_store.py** (37 connections) — `core/tests/test_report_store.py`
- **LocalReportStore** (32 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **ReportRef** (31 connections) — `core/gherkai_core/model.py`
- **_jr()** (21 connections) — `core/tests/test_report_store.py`
- **_rr()** (21 connections) — `core/tests/test_report_store.py`
- **_run_with_refs()** (19 connections) — `core/tests/test_report_store.py`
- **test_s3_report_store.py** (19 connections) — `core/tests/test_s3_report_store.py`
- **Path** (18 connections)
- **_uri_to_path()** (13 connections) — `core/tests/test_report_store.py`
- **S3ReportStore** (11 connections) — `core/gherkai_core/adapters/report_store/s3.py`
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
- *... and 30 more nodes in this community*

## Relationships

- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (35 shared connections)
- [Atomic Local Writes](Atomic_Local_Writes.md) (9 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (6 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (5 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (3 shared connections)
- [Result Store Serialization](Result_Store_Serialization.md) (3 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (3 shared connections)
- [S3 Step Argument Offload](S3_Step_Argument_Offload.md) (2 shared connections)
- [Boto3 Adapter Guard](Boto3_Adapter_Guard.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [Event Wire Serialization](Event_Wire_Serialization.md) (2 shared connections)
- [Subprocess Launcher](Subprocess_Launcher.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/report_store/local.py`
- `core/gherkai_core/adapters/report_store/s3.py`
- `core/gherkai_core/model.py`
- `core/tests/test_report_store.py`
- `core/tests/test_s3_report_store.py`

## Audit Trail

- EXTRACTED: 228 (97%)
- INFERRED: 8 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*