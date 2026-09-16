# Doctor Self-Check

> 22 nodes · cohesion 0.13

## Key Concepts

- **_fake_locator()** (14 connections) — `cli/tests/test_main.py`
- **_no_provider()** (10 connections) — `cli/tests/test_main.py`
- **test_doctor_cloud_credential_failure_is_required_and_exits_2()** (5 connections) — `cli/tests/test_main.py`
- **test_doctor_cloud_profile_error_at_target_resolution_is_a_credential_failure()** (5 connections) — `cli/tests/test_main.py`
- **test_doctor_cloud_without_region_fails_region_check_first()** (5 connections) — `cli/tests/test_main.py`
- **test_doctor_local_json_checks_and_exit_codes()** (5 connections) — `cli/tests/test_main.py`
- **test_doctor_runs_worker_self_describe_even_without_steps_dir()** (5 connections) — `cli/tests/test_main.py`
- **test_doctor_cloud_missing_default_pointer_is_required_failure()** (4 connections) — `cli/tests/test_main.py`
- **test_doctor_cloud_reports_backend_failures_and_exits_2()** (4 connections) — `cli/tests/test_main.py`
- **test_doctor_no_engine_at_all_fails_locally_but_not_for_cloud()** (4 connections) — `cli/tests/test_main.py`
- **test_doctor_provider_installed_but_broken_is_required_failure()** (4 connections) — `cli/tests/test_main.py`
- **test_doctor_provider_section_comes_from_provider_doctor()** (4 connections) — `cli/tests/test_main.py`
- **test_doctor_steps_dir_error_reason_lands_in_json_detail()** (4 connections) — `cli/tests/test_main.py`
- **test_list_engines_json_shape()** (3 connections) — `cli/tests/test_main.py`
- **把定位链换成假的：available 里的引擎命中「同 venv 模块」，其余 miss（带安装指引）。** (1 connections) — `cli/tests/test_main.py`
- **local 自检：引擎（一缺一在→any ok）、steps 目录加载、云端项标未查、provider 未装标可选；全 required ok → 0；…** (1 connections) — `cli/tests/test_main.py`
- **装了 deploy-aws extra → 经 provider 接缝调它的 doctor(args)，required 项失败让整体退 2。** (1 connections) — `cli/tests/test_main.py`
- **凭证探针抛 → aws.identity 必修失败、backend 标未查（可选）、退 2；不去碰后端。** (1 connections) — `cli/tests/test_main.py`
- **region 解析不出 → aws.region 必修失败、后端标未查，不会把 NoRegionError 误诊成「prefix 配错」。** (1 connections) — `cli/tests/test_main.py`
- **--profile 打错在 resolve_cloud_target 就炸（读 profile config）→ 与探针失败同一句诊断、退 2，不冒…** (1 connections) — `cli/tests/test_main.py`
- **装了 deploy-aws extra 却加载失败（半装/版本不匹配）→ 必修失败：明确装了的东西坏了；靠 entry point 结构判、不靠文案前缀。** (1 connections) — `cli/tests/test_main.py`
- **无 steps/ 目录也对可用引擎跑一次自述（验 worker 起得来），但只作可选项：自述失败不改退出码。** (1 connections) — `cli/tests/test_main.py`

## Relationships

- [CLI Run Command Tests](CLI_Run_Command_Tests.md) (14 shared connections)
- [CLI Main Flow Tests](CLI_Main_Flow_Tests.md) (12 shared connections)

## Source Files

- `cli/tests/test_main.py`

## Audit Trail

- EXTRACTED: 55 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*