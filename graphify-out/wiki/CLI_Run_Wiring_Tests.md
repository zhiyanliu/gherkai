# CLI Run Wiring Tests

> 111 nodes · cohesion 0.03

## Key Concepts

- **test_main.py** (144 connections) — `cli/tests/test_main.py`
- **_write_feature()** (37 connections) — `cli/tests/test_main.py`
- **_fake_schedule_factory()** (19 connections) — `cli/tests/test_main.py`
- **_capturing_schedule()** (14 connections) — `cli/tests/test_main.py`
- **.cmd()** (9 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **test_submit_local_exits_2_when_worker_runtime_missing()** (7 connections) — `cli/tests/test_main.py`
- **Path** (6 connections)
- **_tagged_feature()** (6 connections) — `cli/tests/test_main.py`
- **test_local_run_asks_each_engine_for_capabilities_once()** (6 connections) — `cli/tests/test_main.py`
- **test_report_run_passes_absolute_artifact_dirs_and_no_flag()** (6 connections) — `cli/tests/test_main.py`
- **test_run_default_steps_dir_used_only_when_it_exists()** (6 connections) — `cli/tests/test_main.py`
- **test_run_engine_self_describe_failure_refuses_to_run()** (6 connections) — `cli/tests/test_main.py`
- **test_run_exits_2_before_spawn_when_worker_runtime_missing()** (6 connections) — `cli/tests/test_main.py`
- **test_run_steps_dir_flag_resolves_absolute_and_persists()** (6 connections) — `cli/tests/test_main.py`
- **test_submit_local_persists_steps_dir_into_definition()** (6 connections) — `cli/tests/test_main.py`
- **test_submit_local_writes_max_concurrency_into_definition()** (6 connections) — `cli/tests/test_main.py`
- **_miss()** (5 connections) — `cli/tests/test_main.py`
- **_plan_names()** (5 connections) — `cli/tests/test_main.py`
- **_spy_build_engines()** (5 connections) — `cli/tests/test_main.py`
- **test_no_report_disables_artifacts_instead_of_tempdir()** (5 connections) — `cli/tests/test_main.py`
- **test_plan_scenario_by_id_line_or_title_substring()** (5 connections) — `cli/tests/test_main.py`
- **test_plan_tags_any_within_value_and_all_across_flags()** (5 connections) — `cli/tests/test_main.py`
- **test_realtime_commit_point_write_order()** (5 connections) — `cli/tests/test_main.py`
- **test_run_and_submit_exit_2_before_spawn_when_user_steps_fail()** (5 connections) — `cli/tests/test_main.py`
- **test_run_grace_nan_inf_rejected()** (5 connections) — `cli/tests/test_main.py`
- *... and 86 more nodes in this community*

## Relationships

- [Plan Command CLI Tests](Plan_Command_CLI_Tests.md) (67 shared connections)
- [Doctor Self-check Tests](Doctor_Self-check_Tests.md) (30 shared connections)
- [Explain Command Tests](Explain_Command_Tests.md) (17 shared connections)
- [Status Rendering & Exit Codes](Status_Rendering_%26_Exit_Codes.md) (7 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (5 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (5 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (2 shared connections)
- [Tunnel CLI Wiring Tests](Tunnel_CLI_Wiring_Tests.md) (2 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (1 shared connections)
- [Deploy Command Frontend Tests](Deploy_Command_Frontend_Tests.md) (1 shared connections)
- [Tunnel Host Orchestration](Tunnel_Host_Orchestration.md) (1 shared connections)
- [CLI Command Entrypoints](CLI_Command_Entrypoints.md) (1 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `core/gherkai_core/adapters/subprocess_engine.py`

## Audit Trail

- EXTRACTED: 329 (95%)
- INFERRED: 16 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*