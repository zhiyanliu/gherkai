# Text Render & Wording Guards

> 27 nodes · cohesion 0.13

## Key Concepts

- **RunResult** (63 connections) — `core/gherkai_core/model.py`
- **ScenarioResult** (33 connections) — `core/gherkai_core/model.py`
- **test_render.py** (19 connections) — `cli/tests/test_render.py`
- **render_text()** (14 connections) — `cli/gherkai_cli/render.py`
- **_sample_run()** (11 connections) — `cli/tests/test_render.py`
- **test_index_html_shortcircuit_note_matches_cli_wording()** (9 connections) — `cli/tests/test_render.py`
- **test_render_text_shows_step_level_report_refs()** (9 connections) — `cli/tests/test_render.py`
- **test_render_text_step_reason_line_is_single_line_and_only_when_present()** (9 connections) — `cli/tests/test_render.py`
- **test_render_text_annotates_shortcircuited_step()** (8 connections) — `cli/tests/test_render.py`
- **test_render_text_no_annotation_on_plain_failed()** (8 connections) — `cli/tests/test_render.py`
- **test_job_line_with_error_type_but_no_message_has_no_orphan_colon()** (7 connections) — `cli/tests/test_render.py`
- **test_render_text_shows_reason_for_fail_fast_states()** (7 connections) — `cli/tests/test_render.py`
- **.write()** (4 connections) — `core/gherkai_core/ports.py`
- **test_render_text_nests_and_shows_cost_and_duration()** (3 connections) — `cli/tests/test_render.py`
- **.finalize()** (3 connections) — `core/gherkai_core/persist.py`
- **test_to_dict_shape_and_no_dollar()** (2 connections) — `cli/tests/test_render.py`
- **RunResult → 人看的多行汇总（嵌套 job/scenario/step + 时长 + 成本 + 报告指针）。…** (1 connections) — `cli/gherkai_cli/render.py`
- **render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，零费用。** (1 connections) — `cli/tests/test_render.py`
- **跨包措辞护栏（ADR 0031 决定六）：报告入口页的短路旁注与本模块的旁注是同一句。 core 不能 import…** (1 connections) — `cli/tests/test_render.py`
- **skipped/aborted 的 error_type 恒 None（ADR 0031 决定一）——「为什么没跑」只在 message，人读文本必须显； 且…** (1 connections) — `cli/tests/test_render.py`
- **step 级原因行（ADR 0042 决策三）：failed/error step 下附「原因: …」，多行/多余空白折叠成一行；passed 步不显。** (1 connections) — `cli/tests/test_render.py`
- **job 行有分类、message 为 None → 只显分类 `(worker_crashed)`，不打 `(worker_crashed:…** (1 connections) — `cli/tests/test_render.py`
- **一次执行的机器可读汇总判定 = **definition（run_meta）+ 判定（jobs）的显式合成**（ADR 0016/0026）。…** (1 connections) — `core/gherkai_core/model.py`
- **.run_id()** (1 connections) — `core/gherkai_core/model.py`
- **run 结束（schedule 返回后）：commit point。 写总 status + ended_at（finalize_run = commit…** (1 connections) — `core/gherkai_core/persist.py`
- *... and 2 more nodes in this community*

## Relationships

- [Local Report Store](Local_Report_Store.md) (23 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (17 shared connections)
- [Event Formatting](Event_Formatting.md) (14 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (10 shared connections)
- [S3 Result Store](S3_Result_Store.md) (9 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (9 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (8 shared connections)
- [Report Index Collection](Report_Index_Collection.md) (7 shared connections)
- [S3 Report Store & Control Plane](S3_Report_Store_%26_Control_Plane.md) (6 shared connections)
- [Explain Rendering](Explain_Rendering.md) (5 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (3 shared connections)
- [Schedule Core & Fakes](Schedule_Core_%26_Fakes.md) (3 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`

## Audit Trail

- EXTRACTED: 146 (84%)
- INFERRED: 27 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*