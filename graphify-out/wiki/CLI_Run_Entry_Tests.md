# CLI Run Entry Tests

> 91 nodes · cohesion 0.05

## Key Concepts

- **main()** (137 connections) — `cli/gherkai_cli/__main__.py`
- **test_main.py** (72 connections) — `cli/tests/test_main.py`
- **_write_feature()** (29 connections) — `cli/tests/test_main.py`
- **_fake_schedule_factory()** (17 connections) — `cli/tests/test_main.py`
- **_capturing_schedule()** (8 connections) — `cli/tests/test_main.py`
- **_det_feature()** (7 connections) — `cli/tests/test_main.py`
- **test_submit_local_exits_2_when_worker_runtime_missing()** (7 connections) — `cli/tests/test_main.py`
- **.cmd()** (7 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **Path** (6 connections)
- **test_report_run_passes_absolute_artifact_dirs_and_no_flag()** (6 connections) — `cli/tests/test_main.py`
- **test_run_default_steps_dir_used_only_when_it_exists()** (6 connections) — `cli/tests/test_main.py`
- **test_run_exits_2_before_spawn_when_worker_runtime_missing()** (6 connections) — `cli/tests/test_main.py`
- **test_run_steps_dir_flag_resolves_absolute_and_persists()** (6 connections) — `cli/tests/test_main.py`
- **test_submit_local_persists_steps_dir_into_definition()** (6 connections) — `cli/tests/test_main.py`
- **test_submit_local_writes_max_concurrency_into_definition()** (6 connections) — `cli/tests/test_main.py`
- **_miss()** (5 connections) — `cli/tests/test_main.py`
- **_spy_build_engines()** (5 connections) — `cli/tests/test_main.py`
- **test_no_report_disables_artifacts_instead_of_tempdir()** (5 connections) — `cli/tests/test_main.py`
- **test_realtime_commit_point_write_order()** (5 connections) — `cli/tests/test_main.py`
- **test_run_and_submit_exit_2_before_spawn_when_user_steps_fail()** (5 connections) — `cli/tests/test_main.py`
- **test_run_steps_dir_env_and_flag_precedence()** (5 connections) — `cli/tests/test_main.py`
- **test_run_unused_engine_miss_does_not_block()** (5 connections) — `cli/tests/test_main.py`
- **test_run_wires_artifact_dirs_to_build_engines()** (5 connections) — `cli/tests/test_main.py`
- **test_steps_dir_explicit_but_missing_exits_2()** (5 connections) — `cli/tests/test_main.py`
- **.engine()** (5 connections) — `core/gherkai_core/model.py`
- *... and 66 more nodes in this community*

## Relationships

- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (49 shared connections)
- [Deploy Command Shell Tests](Deploy_Command_Shell_Tests.md) (18 shared connections)
- [Tunnel CLI Wiring Tests](Tunnel_CLI_Wiring_Tests.md) (10 shared connections)
- [Status Command Rendering](Status_Command_Rendering.md) (8 shared connections)
- [CLI Main Entry](CLI_Main_Entry.md) (6 shared connections)
- [CLI Run/Submit Commands](CLI_Run-Submit_Commands.md) (3 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (3 shared connections)
- [Deploy/Destroy CLI Commands](Deploy-Destroy_CLI_Commands.md) (2 shared connections)
- [Deploy Provider Discovery](Deploy_Provider_Discovery.md) (1 shared connections)
- [List Deterministic CLI Command](List_Deterministic_CLI_Command.md) (1 shared connections)
- [Plan Command & Rendering](Plan_Command_%26_Rendering.md) (1 shared connections)
- [Version Skew Test Patches](Version_Skew_Test_Patches.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/tests/test_main.py`
- `core/gherkai_core/adapters/subprocess_engine.py`
- `core/gherkai_core/model.py`

## Audit Trail

- EXTRACTED: 306 (96%)
- INFERRED: 14 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*