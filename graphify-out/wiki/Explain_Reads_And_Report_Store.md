# Explain Reads And Report Store

> 49 nodes · cohesion 0.13

## Key Concepts

- **LocalReportStore** (39 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **test_report_store.py** (37 connections) — `core/tests/test_report_store.py`
- **StepResult** (36 connections) — `core/gherkai_core/model.py`
- **ScenarioResult** (34 connections) — `core/gherkai_core/model.py`
- **ReportRef** (31 connections) — `core/gherkai_core/model.py`
- **_jr()** (21 connections) — `core/tests/test_report_store.py`
- **_rr()** (21 connections) — `core/tests/test_report_store.py`
- **_run_with_refs()** (19 connections) — `core/tests/test_report_store.py`
- **Path** (18 connections)
- **test_explain_cloud_reads_evidence_from_s3()** (13 connections) — `cli/tests/test_main.py`
- **_uri_to_path()** (13 connections) — `core/tests/test_report_store.py`
- **test_run_tree_attaches_reason_and_refs_under_their_step()** (10 connections) — `cli/tests/test_render.py`
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
- *... and 24 more nodes in this community*

## Relationships

- [Result Tree Rendering](Result_Tree_Rendering.md) (21 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (16 shared connections)
- [S3 Report Store](S3_Report_Store.md) (15 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (10 shared connections)
- [DynamoDB Job State Store](DynamoDB_Job_State_Store.md) (8 shared connections)
- [Run Scheduling Events Core](Run_Scheduling_Events_Core.md) (7 shared connections)
- [Report Store Local](Report_Store_Local.md) (7 shared connections)
- [Run Persistence Local Stores](Run_Persistence_Local_Stores.md) (7 shared connections)
- [Result Store Adapters](Result_Store_Adapters.md) (7 shared connections)
- [S3 Result Store](S3_Result_Store.md) (5 shared connections)
- [Store Port Definitions](Store_Port_Definitions.md) (5 shared connections)
- [Explain Command Tests](Explain_Command_Tests.md) (4 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/adapters/report_store/local.py`
- `core/gherkai_core/model.py`
- `core/tests/test_report_store.py`
- `core/tests/test_s3_report_store.py`

## Audit Trail

- EXTRACTED: 260 (92%)
- INFERRED: 23 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*