# Result Rendering & Explain

> 35 nodes · cohesion 0.11

## Key Concepts

- **RunResult** (65 connections) — `core/gherkai_core/model.py`
- **StepResult** (36 connections) — `core/gherkai_core/model.py`
- **ScenarioResult** (34 connections) — `core/gherkai_core/model.py`
- **test_render.py** (20 connections) — `cli/tests/test_render.py`
- **render_text()** (13 connections) — `cli/gherkai_cli/render.py`
- **test_explain_cloud_reads_evidence_from_s3()** (13 connections) — `cli/tests/test_main.py`
- **_sample_run()** (11 connections) — `cli/tests/test_render.py`
- **test_run_tree_attaches_reason_and_refs_under_their_step()** (10 connections) — `cli/tests/test_render.py`
- **test_index_html_shortcircuit_note_matches_cli_wording()** (9 connections) — `cli/tests/test_render.py`
- **test_render_text_shows_step_level_report_refs()** (9 connections) — `cli/tests/test_render.py`
- **test_render_text_step_reason_line_is_single_line_and_only_when_present()** (9 connections) — `cli/tests/test_render.py`
- **test_render_text_annotates_shortcircuited_step()** (8 connections) — `cli/tests/test_render.py`
- **test_render_text_no_annotation_on_plain_failed()** (8 connections) — `cli/tests/test_render.py`
- **test_job_line_with_error_type_but_no_message_has_no_orphan_colon()** (7 connections) — `cli/tests/test_render.py`
- **test_render_text_shows_reason_for_fail_fast_states()** (7 connections) — `cli/tests/test_render.py`
- **_explain_cloud_stores()** (4 connections) — `cli/tests/test_main.py`
- **.write()** (4 connections) — `core/gherkai_core/ports.py`
- **test_render_text_nests_and_shows_cost_and_duration()** (3 connections) — `cli/tests/test_render.py`
- **test_tick_runs_isolates_defensive_scan_failure()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_to_dict_shape_and_no_dollar()** (2 connections) — `cli/tests/test_render.py`
- **.run_id()** (2 connections) — `core/gherkai_core/model.py`
- **RunResult → 人看的判定汇总树（job → scenario → step，带时长、成本与报告指针；ADR 0047）。…** (1 connections) — `cli/gherkai_cli/render.py`
- **假的云端两 store（explain 只读 RunStore/ResultStore）：验接线与读路径，不连真 AWS。** (1 connections) — `cli/tests/test_main.py`
- **云端后端：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。** (1 connections) — `cli/tests/test_main.py`
- **render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，零费用。** (1 connections) — `cli/tests/test_render.py`
- *... and 10 more nodes in this community*

## Relationships

- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (39 shared connections)
- [Local Report Store](Local_Report_Store.md) (25 shared connections)
- [S3 Result Store](S3_Result_Store.md) (16 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (12 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (11 shared connections)
- [Job State Serialization](Job_State_Serialization.md) (10 shared connections)
- [Report Store Collection](Report_Store_Collection.md) (7 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (6 shared connections)
- [Plan & Explain Rendering](Plan_%26_Explain_Rendering.md) (5 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (5 shared connections)
- [Run State Rendering & DDB Store](Run_State_Rendering_%26_DDB_Store.md) (4 shared connections)
- [Local Result Store](Local_Result_Store.md) (4 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_main.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/ports.py`
- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 194 (85%)
- INFERRED: 33 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*