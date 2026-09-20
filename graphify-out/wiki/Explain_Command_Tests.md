# Explain Command Tests

> 28 nodes · cohesion 0.11

## Key Concepts

- **_explain_run()** (25 connections) — `cli/tests/test_main.py`
- **_explain()** (14 connections) — `cli/tests/test_main.py`
- **_evidence_fixture()** (5 connections) — `cli/tests/test_main.py`
- **test_explain_long_thought_is_truncated_with_pointer()** (5 connections) — `cli/tests/test_main.py`
- **test_explain_scenario_selector_matches_id_line_title_and_ors()** (5 connections) — `cli/tests/test_main.py`
- **test_explain_unreadable_and_unsupported_evidence()** (5 connections) — `cli/tests/test_main.py`
- **test_explain_all_expands_passed_and_full_drops_the_text_budget()** (4 connections) — `cli/tests/test_main.py`
- **test_explain_detached_run_without_job_files_exits_0_with_one_hint()** (4 connections) — `cli/tests/test_main.py`
- **test_explain_filter_to_unrecorded_step_does_not_fake_job_verdict_block()** (4 connections) — `cli/tests/test_main.py`
- **test_explain_job_without_step_records_gets_a_job_block()** (4 connections) — `cli/tests/test_main.py`
- **test_explain_json_is_single_document_with_record_and_evidence_gaps()** (4 connections) — `cli/tests/test_main.py`
- **test_explain_named_step_expands_even_when_passed()** (4 connections) — `cli/tests/test_main.py`
- **test_explain_nonterminal_sync_run_says_partial()** (4 connections) — `cli/tests/test_main.py`
- **test_explain_step_needs_scenario_and_lists_candidates_when_absent()** (4 connections) — `cli/tests/test_main.py`
- **test_explain_text_renders_reason_thought_screenshot_and_gaps()** (4 connections) — `cli/tests/test_main.py`
- **在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真…** (1 connections) — `cli/tests/test_main.py`
- **文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、 短路旁注只在…** (1 connections) — `cli/tests/test_main.py`
- **--json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing； 有记录但没挂…** (1 connections) — `cli/tests/test_main.py`
- **--scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三种匹配，可重复且彼此为或。** (1 connections) — `cli/tests/test_main.py`
- **--step 单给即以退出码 2 结束（步号没有归属）；命中的 scenario 都没有第 N 步 → 同样以退出码 2 结束并列出候选 id 与步数；…** (1 connections) — `cli/tests/test_main.py`
- **显式 --step 点名的那一步即展开证据（点名就是想看），不必再给 --all；默认视图对同一 passed 步仍不展开。** (1 connections) — `cli/tests/test_main.py`
- **--all 也展开 passed step；--full 逐 frame 全文（省略计数消失、无推理的 frame 也现身）。** (1 connections) — `cli/tests/test_main.py`
- **单段推理超预算 → 截断并指出完整内容在哪（--json 或那份 evidence.json）；--full 不截断。** (1 connections) — `cli/tests/test_main.py`
- **读不到/解不开 → unreadable；schema_version 不认识 → unsupported_schema。两者都不影响退出码（0）。** (1 connections) — `cli/tests/test_main.py`
- **detached run 未终态时零判定明细（全 job 终态才一次性落）→ 退出码 0 + 一行提示；--json 不打提示、 stdout…** (1 connections) — `cli/tests/test_main.py`
- *... and 3 more nodes in this community*

## Relationships

- [CLI Entry Wiring Tests](CLI_Entry_Wiring_Tests.md) (16 shared connections)
- [Explain Rendering Tests](Explain_Rendering_Tests.md) (3 shared connections)
- [CLI Plan Command Behavior](CLI_Plan_Command_Behavior.md) (2 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [Local Report Store](Local_Report_Store.md) (1 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (1 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (1 shared connections)

## Source Files

- `cli/tests/test_main.py`

## Audit Trail

- EXTRACTED: 68 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*