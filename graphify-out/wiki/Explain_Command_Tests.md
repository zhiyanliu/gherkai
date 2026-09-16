# Explain Command Tests

> 30 nodes · cohesion 0.09

## Key Concepts

- **_explain_run()** (24 connections) — `cli/tests/test_main.py`
- **_explain()** (13 connections) — `cli/tests/test_main.py`
- **test_explain_cloud_reads_evidence_from_s3()** (13 connections) — `cli/tests/test_main.py`
- **_evidence_fixture()** (5 connections) — `cli/tests/test_main.py`
- **test_explain_long_thought_is_truncated_with_pointer()** (5 connections) — `cli/tests/test_main.py`
- **test_explain_scenario_selector_matches_id_line_title_and_ors()** (5 connections) — `cli/tests/test_main.py`
- **test_explain_unreadable_and_unsupported_evidence()** (5 connections) — `cli/tests/test_main.py`
- **_explain_cloud_stores()** (4 connections) — `cli/tests/test_main.py`
- **test_explain_all_expands_passed_and_full_drops_the_text_budget()** (4 connections) — `cli/tests/test_main.py`
- **test_explain_detached_run_without_job_files_exits_0_with_one_hint()** (4 connections) — `cli/tests/test_main.py`
- **test_explain_filter_to_unrecorded_step_does_not_fake_job_verdict_block()** (4 connections) — `cli/tests/test_main.py`
- **test_explain_job_without_step_records_gets_a_job_block()** (4 connections) — `cli/tests/test_main.py`
- **test_explain_json_is_single_document_with_record_and_evidence_gaps()** (4 connections) — `cli/tests/test_main.py`
- **test_explain_nonterminal_sync_run_says_partial()** (4 connections) — `cli/tests/test_main.py`
- **test_explain_step_needs_scenario_and_lists_candidates_when_absent()** (4 connections) — `cli/tests/test_main.py`
- **test_explain_text_renders_reason_thought_screenshot_and_gaps()** (4 connections) — `cli/tests/test_main.py`
- **在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真…** (1 connections) — `cli/tests/test_main.py`
- **文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、 短路旁注只在…** (1 connections) — `cli/tests/test_main.py`
- **--json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing； 有记录但没挂…** (1 connections) — `cli/tests/test_main.py`
- **--scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三档，可重复且彼此为或。** (1 connections) — `cli/tests/test_main.py`
- **--step 单给退 2（步号没有归属）；命中的 scenario 都没有第 N 步 → 退 2 并列出候选 id 与步数； 正常时只渲染每条命中…** (1 connections) — `cli/tests/test_main.py`
- **--all 也展开 passed step；--full 逐 frame 全文（省略计数消失、无推理的 frame 也现身）。** (1 connections) — `cli/tests/test_main.py`
- **单段推理超预算 → 截断并指出完整内容在哪（--json 或那份 evidence.json）；--full 不截断。** (1 connections) — `cli/tests/test_main.py`
- **读不到/解不开 → unreadable；schema_version 不认识 → unsupported_schema。两者都不影响退出码（0）。** (1 connections) — `cli/tests/test_main.py`
- **detached run 未终态时零判定明细（全 job 终态才一次性落）→ 退 0 + 一行提示；--json 不打提示、 stdout…** (1 connections) — `cli/tests/test_main.py`
- *... and 5 more nodes in this community*

## Relationships

- [CLI Run Command Tests](CLI_Run_Command_Tests.md) (17 shared connections)
- [Local Report Store](Local_Report_Store.md) (4 shared connections)
- [CLI Main Flow Tests](CLI_Main_Flow_Tests.md) (3 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (3 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (3 shared connections)
- [Text Render & Wording Guards](Text_Render_%26_Wording_Guards.md) (2 shared connections)
- [Schedule Core & Fakes](Schedule_Core_%26_Fakes.md) (2 shared connections)
- [S3 Result Store](S3_Result_Store.md) (2 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (2 shared connections)

## Source Files

- `cli/tests/test_main.py`

## Audit Trail

- EXTRACTED: 79 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*