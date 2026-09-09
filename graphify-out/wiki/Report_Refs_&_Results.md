# Report Refs & Results

> 32 nodes · cohesion 0.21

## Key Concepts

- **LocalReportStore** (35 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **test_report_store.py** (33 connections) — `core/tests/test_report_store.py`
- **ReportRef** (26 connections) — `core/gherkai_core/model.py`
- **StepResult** (24 connections) — `core/gherkai_core/model.py`
- **ScenarioResult** (23 connections) — `core/gherkai_core/model.py`
- **_rr()** (19 connections) — `core/tests/test_report_store.py`
- **_jr()** (18 connections) — `core/tests/test_report_store.py`
- **Path** (17 connections)
- **_uri_to_path()** (10 connections) — `core/tests/test_report_store.py`
- **test_index_html_no_taint_on_plain_failed()** (8 connections) — `core/tests/test_report_store.py`
- **test_index_html_shows_verdict_even_without_report_refs()** (8 connections) — `core/tests/test_report_store.py`
- **test_index_html_taints_shortcircuited_step()** (8 connections) — `core/tests/test_report_store.py`
- **test_index_html_votes_tally_shown_only_when_multi_vote()** (8 connections) — `core/tests/test_report_store.py`
- **test_empty_report_refs_still_valid_index()** (6 connections) — `core/tests/test_report_store.py`
- **test_file_uri_with_remote_host_kept_as_ref()** (6 connections) — `core/tests/test_report_store.py`
- **test_href_falls_back_absolute_for_artifact_outside_run_tree()** (6 connections) — `core/tests/test_report_store.py`
- **test_href_relativized_for_bare_path_ref()** (6 connections) — `core/tests/test_report_store.py`
- **test_href_relativized_percent_encoded_path()** (6 connections) — `core/tests/test_report_store.py`
- **test_href_relativized_through_symlinked_run_dir()** (6 connections) — `core/tests/test_report_store.py`
- **test_remote_ref_kept_as_ref()** (6 connections) — `core/tests/test_report_store.py`
- **test_index_html_taints_shortcircuited_step()** (6 connections) — `core/tests/test_s3_report_store.py`
- **test_index_html_links_and_summary()** (5 connections) — `core/tests/test_report_store.py`
- **test_writes_manifest_and_index()** (5 connections) — `core/tests/test_report_store.py`
- **test_href_relativized_for_artifact_in_run_tree()** (4 connections) — `core/tests/test_report_store.py`
- **test_manifest_shape()** (4 connections) — `core/tests/test_report_store.py`
- *... and 7 more nodes in this community*

## Relationships

- [Run Result Rendering](Run_Result_Rendering.md) (28 shared connections)
- [S3 Report Store Tests](S3_Report_Store_Tests.md) (20 shared connections)
- [Local Report Store](Local_Report_Store.md) (8 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (8 shared connections)
- [S3 Result Store](S3_Result_Store.md) (7 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (7 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (6 shared connections)
- [S3 Report Store & Subprocess](S3_Report_Store_%26_Subprocess.md) (5 shared connections)
- [SSM Path & Client Composition](SSM_Path_%26_Client_Composition.md) (2 shared connections)
- [Local Run Store](Local_Run_Store.md) (2 shared connections)
- [Local Store Preflight](Local_Store_Preflight.md) (1 shared connections)
- [Store Composition & Step Query](Store_Composition_%26_Step_Query.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/report_store/local.py`
- `core/gherkai_core/model.py`
- `core/tests/test_report_store.py`
- `core/tests/test_s3_report_store.py`

## Audit Trail

- EXTRACTED: 182 (89%)
- INFERRED: 22 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*