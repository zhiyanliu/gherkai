# Worker Variant Listing

> 14 nodes · cohesion 0.14

## Key Concepts

- **list_workers()** (23 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **test_skew_gate_read_failure_exits_2_without_a_traceback()** (7 connections) — `deploy_aws/tests/test_workers.py`
- **test_list_workers_json_sends_diagnostics_to_err_sink()** (5 connections) — `deploy_aws/tests/test_workers.py`
- **_mapped_arn()** (4 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_skew_gate()** (4 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **test_list_workers_reports_unreachable_aws_without_a_traceback()** (4 connections) — `deploy_aws/tests/test_workers.py`
- **_pushed_at_human()** (3 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **推送时间的人读形态：`2026-09-29T07:09:14.961520+00:00` → `2026-09-29 07:09`（换算到 UTC、到分钟）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **映射 JSON → 它引用的 revision ARN（读不懂 → 不产出）。 **读不懂时产出空** 有安全含义：那条映射保护不了它的…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **版本 skew 前置：block → 以退出码 2 结束（无放行口）；warn/skip → 打一行继续；ok → 静默；**读不到戳（凭证/权限）…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **按引擎列**当前版本**的 variant（tag / digest / 推送时间 / revision）+ 默认指针 + 待清理与孤儿。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **读戳失败（无凭证/无权限）→ 退出码 2 + 一句人话。 `compose.read_backend_version`…** (1 connections) — `deploy_aws/tests/test_workers.py`
- **建不出 client（这里用不存在的 profile 名）→ 退出码 2 + 一句人话，不吐 botocore 堆栈。…** (1 connections) — `deploy_aws/tests/test_workers.py`
- **--json 下 stdout 只留一个 JSON 文档：skew 提示 / 读失败诊断走 err（stderr），文本输出行为不变。** (1 connections) — `deploy_aws/tests/test_workers.py`

## Relationships

- [Worker Image Management](Worker_Image_Management.md) (15 shared connections)
- [Worker Push Deploy Tests](Worker_Push_Deploy_Tests.md) (15 shared connections)
- [Rich Text UI Presentation](Rich_Text_UI_Presentation.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/workers.py`
- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 44 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*