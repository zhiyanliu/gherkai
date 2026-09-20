# Local Report Store

> 37 nodes · cohesion 0.18

## Key Concepts

- **LocalReportStore** (39 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **test_report_store.py** (37 connections) — `core/tests/test_report_store.py`
- **ReportRef** (30 connections) — `core/gherkai_core/model.py`
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

- [Explain Rendering Tests](Explain_Rendering_Tests.md) (26 shared connections)
- [S3 Report Store](S3_Report_Store.md) (14 shared connections)
- [Report Store Adapters](Report_Store_Adapters.md) (7 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (6 shared connections)
- [Local & S3 Result Stores](Local_%26_S3_Result_Stores.md) (5 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (5 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (3 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (3 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (2 shared connections)
- [Worker Capability Query](Worker_Capability_Query.md) (2 shared connections)
- [Atomic Result Store](Atomic_Result_Store.md) (2 shared connections)
- [Local File Backend Preflight](Local_File_Backend_Preflight.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/report_store/local.py`
- `core/gherkai_core/model.py`
- `core/tests/test_report_store.py`

## Audit Trail

- EXTRACTED: 192 (94%)
- INFERRED: 13 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*