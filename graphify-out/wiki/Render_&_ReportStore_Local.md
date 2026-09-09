# Render & ReportStore Local

> 77 nodes · cohesion 0.07

## Key Concepts

- **LocalReportStore** (35 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **test_report_store.py** (33 connections) — `core/tests/test_report_store.py`
- **ReportRef** (26 connections) — `core/gherkai_core/model.py`
- **StepResult** (24 connections) — `core/gherkai_core/model.py`
- **ScenarioResult** (23 connections) — `core/gherkai_core/model.py`
- **_rr()** (19 connections) — `core/tests/test_report_store.py`
- **test_s3_report_store.py** (19 connections) — `core/tests/test_s3_report_store.py`
- **_jr()** (18 connections) — `core/tests/test_report_store.py`
- **_run_with_refs()** (18 connections) — `core/tests/test_report_store.py`
- **Path** (17 connections)
- **test_render.py** (15 connections) — `cli/tests/test_render.py`
- **report_store/local.py** (13 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **_sample_run()** (11 connections) — `cli/tests/test_render.py`
- **_uri_to_path()** (10 connections) — `core/tests/test_report_store.py`
- **test_render_text_shows_step_level_report_refs()** (9 connections) — `cli/tests/test_render.py`
- **report_store/s3.py** (9 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **test_index_html_no_taint_on_plain_failed()** (8 connections) — `core/tests/test_report_store.py`
- **test_index_html_shows_verdict_even_without_report_refs()** (8 connections) — `core/tests/test_report_store.py`
- **test_index_html_taints_shortcircuited_step()** (8 connections) — `core/tests/test_report_store.py`
- **test_index_html_votes_tally_shown_only_when_multi_vote()** (8 connections) — `core/tests/test_report_store.py`
- **collect_report_index()** (7 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **._collect()** (7 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **_render_index_html()** (7 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **.write()** (6 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **.write()** (6 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- *... and 52 more nodes in this community*

## Relationships

- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (28 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (13 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (10 shared connections)
- [Event Formatting & Cost Model](Event_Formatting_%26_Cost_Model.md) (9 shared connections)
- [S3 ReportStore & Subprocess Engine](S3_ReportStore_%26_Subprocess_Engine.md) (9 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (8 shared connections)
- [ResultStore Local/S3](ResultStore_Local-S3.md) (7 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (6 shared connections)
- [Plan Command & Rendering](Plan_Command_%26_Rendering.md) (3 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (2 shared connections)
- [Deploy Command Shell Tests](Deploy_Command_Shell_Tests.md) (1 shared connections)
- [Subprocess Worker Launcher](Subprocess_Worker_Launcher.md) (1 shared connections)

## Source Files

- `cli/tests/test_render.py`
- `core/gherkai_core/adapters/report_store/__init__.py`
- `core/gherkai_core/adapters/report_store/local.py`
- `core/gherkai_core/adapters/report_store/s3.py`
- `core/gherkai_core/model.py`
- `core/tests/test_report_store.py`
- `core/tests/test_s3_report_store.py`

## Audit Trail

- EXTRACTED: 284 (93%)
- INFERRED: 22 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*