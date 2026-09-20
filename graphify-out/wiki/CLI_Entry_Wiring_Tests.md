# CLI Entry Wiring Tests

> 104 nodes · cohesion 0.04

## Key Concepts

- **test_main.py** (143 connections) — `cli/tests/test_main.py`
- **_write_feature()** (37 connections) — `cli/tests/test_main.py`
- **_fake_schedule_factory()** (19 connections) — `cli/tests/test_main.py`
- **.engine()** (15 connections) — `core/gherkai_core/model.py`
- **_capturing_schedule()** (14 connections) — `cli/tests/test_main.py`
- **_cloud_backend_ok()** (7 connections) — `cli/tests/test_main.py`
- **test_doctor_cloud_worker_grace_shortfall_is_optional_gap_not_failure()** (7 connections) — `cli/tests/test_main.py`
- **test_submit_local_exits_2_when_worker_runtime_missing()** (7 connections) — `cli/tests/test_main.py`
- **_doctor_cloud_json()** (6 connections) — `cli/tests/test_main.py`
- **Path** (6 connections)
- **test_doctor_cloud_worker_grace_ok_and_skips_engine_without_local_worker()** (6 connections) — `cli/tests/test_main.py`
- **test_doctor_cloud_worker_grace_query_failure_lands_in_detail()** (6 connections) — `cli/tests/test_main.py`
- **test_doctor_cloud_worker_grace_unset_stop_timeout_is_reported()** (6 connections) — `cli/tests/test_main.py`
- **test_local_run_asks_each_engine_for_capabilities_once()** (6 connections) — `cli/tests/test_main.py`
- **test_report_run_passes_absolute_artifact_dirs_and_no_flag()** (6 connections) — `cli/tests/test_main.py`
- **test_run_default_steps_dir_used_only_when_it_exists()** (6 connections) — `cli/tests/test_main.py`
- **test_run_engine_self_describe_failure_refuses_to_run()** (6 connections) — `cli/tests/test_main.py`
- **test_run_exits_2_before_spawn_when_worker_runtime_missing()** (6 connections) — `cli/tests/test_main.py`
- **test_run_grace_mixed_engines_takes_max_of_self_reported()** (6 connections) — `cli/tests/test_main.py`
- **test_run_steps_dir_flag_resolves_absolute_and_persists()** (6 connections) — `cli/tests/test_main.py`
- **_miss()** (5 connections) — `cli/tests/test_main.py`
- **_spy_build_engines()** (5 connections) — `cli/tests/test_main.py`
- **test_no_report_disables_artifacts_instead_of_tempdir()** (5 connections) — `cli/tests/test_main.py`
- **test_realtime_commit_point_write_order()** (5 connections) — `cli/tests/test_main.py`
- **test_run_and_submit_exit_2_before_spawn_when_user_steps_fail()** (5 connections) — `cli/tests/test_main.py`
- *... and 79 more nodes in this community*

## Relationships

- [CLI Plan Command Behavior](CLI_Plan_Command_Behavior.md) (62 shared connections)
- [Doctor Self-Check Tests](Doctor_Self-Check_Tests.md) (25 shared connections)
- [Explain Command Tests](Explain_Command_Tests.md) (16 shared connections)
- [Scenario Selection Flags](Scenario_Selection_Flags.md) (10 shared connections)
- [Status Command](Status_Command.md) (8 shared connections)
- [Submit & Tunnel CLI Wiring](Submit_%26_Tunnel_CLI_Wiring.md) (7 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (3 shared connections)
- [Explain Rendering Tests](Explain_Rendering_Tests.md) (3 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (2 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (2 shared connections)
- [Deploy Command Frontend](Deploy_Command_Frontend.md) (1 shared connections)
- [CLI Test Fixtures](CLI_Test_Fixtures.md) (1 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `core/gherkai_core/model.py`

## Audit Trail

- EXTRACTED: 325 (95%)
- INFERRED: 18 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*