# Explain Rendering Tests

> 35 nodes · cohesion 0.11

## Key Concepts

- **RunResult** (63 connections) — `core/gherkai_core/model.py`
- **StepResult** (35 connections) — `core/gherkai_core/model.py`
- **ScenarioResult** (33 connections) — `core/gherkai_core/model.py`
- **test_render.py** (19 connections) — `cli/tests/test_render.py`
- **render_text()** (14 connections) — `cli/gherkai_cli/render.py`
- **test_explain_cloud_reads_evidence_from_s3()** (13 connections) — `cli/tests/test_main.py`
- **test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact()** (11 connections) — `cli/tests/test_main.py`
- **_sample_run()** (11 connections) — `cli/tests/test_render.py`
- **test_index_html_shortcircuit_note_matches_cli_wording()** (9 connections) — `cli/tests/test_render.py`
- **test_render_text_shows_step_level_report_refs()** (9 connections) — `cli/tests/test_render.py`
- **test_render_text_step_reason_line_is_single_line_and_only_when_present()** (9 connections) — `cli/tests/test_render.py`
- **test_render_text_annotates_shortcircuited_step()** (8 connections) — `cli/tests/test_render.py`
- **test_render_text_no_annotation_on_plain_failed()** (8 connections) — `cli/tests/test_render.py`
- **test_job_line_with_error_type_but_no_message_has_no_orphan_colon()** (7 connections) — `cli/tests/test_render.py`
- **test_render_text_shows_reason_for_fail_fast_states()** (7 connections) — `cli/tests/test_render.py`
- **test_index_html_taints_shortcircuited_step()** (6 connections) — `core/tests/test_s3_report_store.py`
- **_explain_cloud_stores()** (4 connections) — `cli/tests/test_main.py`
- **.write()** (4 connections) — `core/gherkai_core/ports.py`
- **test_render_text_nests_and_shows_cost_and_duration()** (3 connections) — `cli/tests/test_render.py`
- **.finalize()** (3 connections) — `core/gherkai_core/persist.py`
- **test_to_dict_shape_and_no_dollar()** (2 connections) — `cli/tests/test_render.py`
- **RunResult → 人看的多行汇总（嵌套 job/scenario/step + 时长 + 成本 + 报告指针）。…** (1 connections) — `cli/gherkai_cli/render.py`
- **假的云端两 store（explain 只读 RunStore/ResultStore）：验接线与读路径，不连真 AWS。** (1 connections) — `cli/tests/test_main.py`
- **云端后端：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。** (1 connections) — `cli/tests/test_main.py`
- **多 scope 下 --scenario 只命中其一：未命中的 scope 不产空壳条目（文本与 JSON 规则一致）；命中的 scope 的…** (1 connections) — `cli/tests/test_main.py`
- *... and 10 more nodes in this community*

## Relationships

- [Local Report Store](Local_Report_Store.md) (26 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (22 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (21 shared connections)
- [Event Log & Projection](Event_Log_%26_Projection.md) (19 shared connections)
- [Local & S3 Result Stores](Local_%26_S3_Result_Stores.md) (15 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (13 shared connections)
- [Report Store Adapters](Report_Store_Adapters.md) (7 shared connections)
- [CLI Render Layer](CLI_Render_Layer.md) (6 shared connections)
- [Local Result Store](Local_Result_Store.md) (6 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (5 shared connections)
- [S3 Report Store](S3_Report_Store.md) (5 shared connections)
- [Atomic Result Store](Atomic_Result_Store.md) (4 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_main.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `core/tests/test_s3_report_store.py`

## Audit Trail

- EXTRACTED: 197 (86%)
- INFERRED: 32 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*