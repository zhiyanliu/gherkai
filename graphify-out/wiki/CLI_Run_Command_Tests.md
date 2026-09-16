# CLI Run Command Tests

> 96 nodes · cohesion 0.04

## Key Concepts

- **test_main.py** (129 connections) — `cli/tests/test_main.py`
- **_write_feature()** (35 connections) — `cli/tests/test_main.py`
- **_fake_schedule_factory()** (19 connections) — `cli/tests/test_main.py`
- **_capturing_schedule()** (11 connections) — `cli/tests/test_main.py`
- **_det_feature()** (7 connections) — `cli/tests/test_main.py`
- **test_submit_local_exits_2_when_worker_runtime_missing()** (7 connections) — `cli/tests/test_main.py`
- **Path** (6 connections)
- **test_report_run_passes_absolute_artifact_dirs_and_no_flag()** (6 connections) — `cli/tests/test_main.py`
- **test_run_default_steps_dir_used_only_when_it_exists()** (6 connections) — `cli/tests/test_main.py`
- **test_run_exits_2_before_spawn_when_worker_runtime_missing()** (6 connections) — `cli/tests/test_main.py`
- **test_run_steps_dir_flag_resolves_absolute_and_persists()** (6 connections) — `cli/tests/test_main.py`
- **_miss()** (5 connections) — `cli/tests/test_main.py`
- **_spy_build_engines()** (5 connections) — `cli/tests/test_main.py`
- **test_no_report_disables_artifacts_instead_of_tempdir()** (5 connections) — `cli/tests/test_main.py`
- **test_realtime_commit_point_write_order()** (5 connections) — `cli/tests/test_main.py`
- **test_run_and_submit_exit_2_before_spawn_when_user_steps_fail()** (5 connections) — `cli/tests/test_main.py`
- **test_run_grace_nan_inf_rejected()** (5 connections) — `cli/tests/test_main.py`
- **test_run_lists_each_job_but_submit_only_prints_the_count()** (5 connections) — `cli/tests/test_main.py`
- **test_run_quiet_writes_worker_log_and_reports_its_location()** (5 connections) — `cli/tests/test_main.py`
- **test_run_steps_dir_env_and_flag_precedence()** (5 connections) — `cli/tests/test_main.py`
- **test_run_terminal_prints_the_same_three_artifact_lines()** (5 connections) — `cli/tests/test_main.py`
- **test_run_unused_engine_miss_does_not_block()** (5 connections) — `cli/tests/test_main.py`
- **test_run_wires_artifact_dirs_to_build_engines()** (5 connections) — `cli/tests/test_main.py`
- **test_steps_dir_explicit_but_missing_exits_2()** (5 connections) — `cli/tests/test_main.py`
- **.engine()** (5 connections) — `core/gherkai_core/model.py`
- *... and 71 more nodes in this community*

## Relationships

- [CLI Main Flow Tests](CLI_Main_Flow_Tests.md) (54 shared connections)
- [Explain Command Tests](Explain_Command_Tests.md) (17 shared connections)
- [Doctor Self-Check](Doctor_Self-Check.md) (14 shared connections)
- [Scenario Selection Filters](Scenario_Selection_Filters.md) (10 shared connections)
- [Run Status Rendering](Run_Status_Rendering.md) (7 shared connections)
- [Submit & Tunnel CLI Tests](Submit_%26_Tunnel_CLI_Tests.md) (7 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (3 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (3 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (1 shared connections)
- [Deploy CLI Shell](Deploy_CLI_Shell.md) (1 shared connections)
- [Runtime Composition & Tunnel Host](Runtime_Composition_%26_Tunnel_Host.md) (1 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (1 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `core/gherkai_core/model.py`

## Audit Trail

- EXTRACTED: 291 (97%)
- INFERRED: 8 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*