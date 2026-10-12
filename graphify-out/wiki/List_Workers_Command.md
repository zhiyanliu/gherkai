# List Workers Command

> 22 nodes · cohesion 0.11

## Key Concepts

- **_out()** (26 connections) — `deploy_aws/tests/test_workers.py`
- **list_workers()** (23 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **test_list_workers_enumerates_ssm_once_for_all_engines()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_skew_gate_read_failure_exits_2_without_a_traceback()** (7 connections) — `deploy_aws/tests/test_workers.py`
- **test_run_deploy_steps_reports_a_missing_container_engine_as_exit_1()** (6 connections) — `deploy_aws/tests/test_workers.py`
- **test_sync_base_skips_non_pure_release_but_deploy_continues()** (6 connections) — `deploy_aws/tests/test_workers.py`
- **test_list_workers_json_sends_diagnostics_to_err_sink()** (5 connections) — `deploy_aws/tests/test_workers.py`
- **test_sync_base_pull_failure_points_at_the_half_published_state()** (5 connections) — `deploy_aws/tests/test_workers.py`
- **test_init_default_pointer_only_when_missing()** (4 connections) — `deploy_aws/tests/test_workers.py`
- **test_list_workers_is_blocked_by_skew()** (4 connections) — `deploy_aws/tests/test_workers.py`
- **test_list_workers_reports_unreachable_aws_without_a_traceback()** (4 connections) — `deploy_aws/tests/test_workers.py`
- **test_list_workers_says_when_the_default_pointer_is_missing()** (4 connections) — `deploy_aws/tests/test_workers.py`
- **_pushed_at_human()** (3 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **推送时间的人读形态：`2026-09-29T07:09:14.961520+00:00` → `2026-09-29 07:09`（换算到 UTC、到分钟）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **按引擎列**当前版本**的 variant（tag / digest / 推送时间 / revision）+ 默认指针 + 待清理与孤儿。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **收集打印文本的 out 替身 → (调用函数, 取全文函数)。** (1 connections) — `deploy_aws/tests/test_workers.py`
- **dev 版（`.dev`/`.post`/本地段）**GHCR 上不存在对应基础镜像** → 明确警告 + 跳过基础镜像同步，第 3/4 步照常执行。…** (1 connections) — `deploy_aws/tests/test_workers.py`
- **cdk 已成功、机器上没有容器引擎 → 退出码 1 + 「stack 已生效、重新运行幂等收敛」（不是退出码 2：账户已被改过）。** (1 connections) — `deploy_aws/tests/test_workers.py`
- **读戳失败（无凭证/无权限）→ 退出码 2 + 一句人话。 `compose.read_backend_version`…** (1 connections) — `deploy_aws/tests/test_workers.py`
- **建不出 client（这里用不存在的 profile 名）→ 退出码 2 + 一句人话，不吐 botocore 堆栈。…** (1 connections) — `deploy_aws/tests/test_workers.py`
- **`list-workers` 的全量枚举（待清理对账用的映射集 + 各引擎当前版本的 variant）只执行一次、两个引擎共用。…** (1 connections) — `deploy_aws/tests/test_workers.py`
- **--json 下 stdout 只留一个 JSON 文档：skew 提示 / 读失败诊断走 err（stderr），文本输出行为不变。** (1 connections) — `deploy_aws/tests/test_workers.py`

## Relationships

- [Container Worker Image Tests](Container_Worker_Image_Tests.md) (41 shared connections)
- [AWS Worker Image Registry](AWS_Worker_Image_Registry.md) (15 shared connections)
- [Container Image Inspection](Container_Image_Inspection.md) (3 shared connections)
- [Revision Cleanup Pass](Revision_Cleanup_Pass.md) (2 shared connections)
- [Task Definition Revision Cleanup](Task_Definition_Revision_Cleanup.md) (1 shared connections)
- [Text UI Rendering](Text_UI_Rendering.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/workers.py`
- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 89 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*