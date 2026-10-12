# Result Tree Rendering

> 22 nodes · cohesion 0.16

## Key Concepts

- **RunResult** (65 connections) — `core/gherkai_core/model.py`
- **test_render.py** (20 connections) — `cli/tests/test_render.py`
- **render_text()** (13 connections) — `cli/gherkai_cli/render.py`
- **_sample_run()** (11 connections) — `cli/tests/test_render.py`
- **test_index_html_shortcircuit_note_matches_cli_wording()** (9 connections) — `cli/tests/test_render.py`
- **test_render_text_shows_step_level_report_refs()** (9 connections) — `cli/tests/test_render.py`
- **test_render_text_step_reason_line_is_single_line_and_only_when_present()** (9 connections) — `cli/tests/test_render.py`
- **test_render_text_annotates_shortcircuited_step()** (8 connections) — `cli/tests/test_render.py`
- **test_render_text_no_annotation_on_plain_failed()** (8 connections) — `cli/tests/test_render.py`
- **test_job_line_with_error_type_but_no_message_has_no_orphan_colon()** (7 connections) — `cli/tests/test_render.py`
- **test_render_text_shows_reason_for_fail_fast_states()** (7 connections) — `cli/tests/test_render.py`
- **test_render_text_nests_and_shows_cost_and_duration()** (3 connections) — `cli/tests/test_render.py`
- **.finalize()** (3 connections) — `core/gherkai_core/persist.py`
- **test_to_dict_shape_and_no_dollar()** (2 connections) — `cli/tests/test_render.py`
- **RunResult → 人看的判定汇总树（job → scenario → step，带时长、成本与报告指针；ADR 0047）。…** (1 connections) — `cli/gherkai_cli/render.py`
- **render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，零费用。** (1 connections) — `cli/tests/test_render.py`
- **跨包措辞护栏（ADR 0031 决定六）：报告入口页的短路旁注与本模块的旁注是同一句。 core 不能 import…** (1 connections) — `cli/tests/test_render.py`
- **skipped/aborted 的 error_type 恒 None（ADR 0031 决定一）——「为什么没执行」只在 message，人读文本必须显；…** (1 connections) — `cli/tests/test_render.py`
- **step 级原因行（ADR 0042 决策三）：failed/error step 下附「原因: …」，多行/多余空白折叠成一行；passed 步不显。** (1 connections) — `cli/tests/test_render.py`
- **job 行有分类、message 为 None → 只显分类 `(worker_crashed)`，不打 `(worker_crashed:…** (1 connections) — `cli/tests/test_render.py`
- **一次执行的机器可读汇总判定，即 **definition（run_meta）与判定（jobs）的显式合成**（ADR 0016/0026）。…** (1 connections) — `core/gherkai_core/model.py`
- **run 结束（schedule 返回后）：commit point。 写总 status + ended_at（finalize_run 就是 commit…** (1 connections) — `core/gherkai_core/persist.py`

## Relationships

- [Explain Reads And Report Store](Explain_Reads_And_Report_Store.md) (21 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (16 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (14 shared connections)
- [S3 Result Store](S3_Result_Store.md) (8 shared connections)
- [Report Store Local](Report_Store_Local.md) (7 shared connections)
- [Plan Explain Rendering](Plan_Explain_Rendering.md) (6 shared connections)
- [Run Persistence Local Stores](Run_Persistence_Local_Stores.md) (6 shared connections)
- [DynamoDB Job State Store](DynamoDB_Job_State_Store.md) (5 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (3 shared connections)
- [Run Scheduling Events Core](Run_Scheduling_Events_Core.md) (3 shared connections)
- [Store Port Definitions](Store_Port_Definitions.md) (3 shared connections)
- [Reconciler Event Projection](Reconciler_Event_Projection.md) (3 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`

## Audit Trail

- EXTRACTED: 123 (85%)
- INFERRED: 22 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*