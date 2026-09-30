# CLI Run Command Tests

> 85 nodes · cohesion 0.05

## Key Concepts

- **test_main.py** (144 connections) — `cli/tests/test_main.py`
- **_write_feature()** (37 connections) — `cli/tests/test_main.py`
- **_fake_schedule_factory()** (19 connections) — `cli/tests/test_main.py`
- **_capturing_schedule()** (14 connections) — `cli/tests/test_main.py`
- **.cmd()** (9 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **test_submit_local_exits_2_when_worker_runtime_missing()** (7 connections) — `cli/tests/test_main.py`
- **Path** (6 connections)
- **test_local_run_asks_each_engine_for_capabilities_once()** (6 connections) — `cli/tests/test_main.py`
- **test_report_run_passes_absolute_artifact_dirs_and_no_flag()** (6 connections) — `cli/tests/test_main.py`
- **test_run_default_steps_dir_used_only_when_it_exists()** (6 connections) — `cli/tests/test_main.py`
- **test_run_engine_self_describe_failure_refuses_to_run()** (6 connections) — `cli/tests/test_main.py`
- **test_run_exits_2_before_spawn_when_worker_runtime_missing()** (6 connections) — `cli/tests/test_main.py`
- **test_run_steps_dir_flag_resolves_absolute_and_persists()** (6 connections) — `cli/tests/test_main.py`
- **test_submit_local_persists_steps_dir_into_definition()** (6 connections) — `cli/tests/test_main.py`
- **test_submit_local_writes_max_concurrency_into_definition()** (6 connections) — `cli/tests/test_main.py`
- **_miss()** (5 connections) — `cli/tests/test_main.py`
- **_spy_build_engines()** (5 connections) — `cli/tests/test_main.py`
- **test_no_report_disables_artifacts_instead_of_tempdir()** (5 connections) — `cli/tests/test_main.py`
- **test_realtime_commit_point_write_order()** (5 connections) — `cli/tests/test_main.py`
- **test_run_and_submit_exit_2_before_spawn_when_user_steps_fail()** (5 connections) — `cli/tests/test_main.py`
- **test_run_grace_nan_inf_rejected()** (5 connections) — `cli/tests/test_main.py`
- **test_run_grace_sentinel_derives_from_engine_self_report()** (5 connections) — `cli/tests/test_main.py`
- **test_run_lists_each_job_but_submit_only_prints_the_count()** (5 connections) — `cli/tests/test_main.py`
- **test_run_quiet_writes_worker_log_and_reports_its_location()** (5 connections) — `cli/tests/test_main.py`
- **test_run_steps_dir_env_and_flag_precedence()** (5 connections) — `cli/tests/test_main.py`
- *... and 60 more nodes in this community*

## Relationships

- [CLI Entry and Plan](CLI_Entry_and_Plan.md) (60 shared connections)
- [Doctor Self-Check](Doctor_Self-Check.md) (30 shared connections)
- [Explain Command Tests](Explain_Command_Tests.md) (17 shared connections)
- [Scenario Selection Filters](Scenario_Selection_Filters.md) (10 shared connections)
- [Run Status Rendering](Run_Status_Rendering.md) (8 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (6 shared connections)
- [Run State Store](Run_State_Store.md) (2 shared connections)
- [Result Store & Report Refs](Result_Store_%26_Report_Refs.md) (2 shared connections)
- [Tunnel CLI Wiring](Tunnel_CLI_Wiring.md) (2 shared connections)
- [Tunnel Host Orchestration](Tunnel_Host_Orchestration.md) (1 shared connections)
- [CLI Command Handlers](CLI_Command_Handlers.md) (1 shared connections)
- [Explain Rendering](Explain_Rendering.md) (1 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `core/gherkai_core/adapters/subprocess_engine.py`

## Audit Trail

- EXTRACTED: 294 (95%)
- INFERRED: 16 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*