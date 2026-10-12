# CLI Run Entry Tests

> 98 nodes · cohesion 0.04

## Key Concepts

- **test_main.py** (144 connections) — `cli/tests/test_main.py`
- **_write_feature()** (37 connections) — `cli/tests/test_main.py`
- **_fake_schedule_factory()** (19 connections) — `cli/tests/test_main.py`
- **_capturing_schedule()** (14 connections) — `cli/tests/test_main.py`
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
- **test_run_grace_sentinel_derives_from_engine_self_report()** (5 connections) — `cli/tests/test_main.py`
- *... and 73 more nodes in this community*

## Relationships

- [CLI Plan Command Behavior](CLI_Plan_Command_Behavior.md) (66 shared connections)
- [Doctor Self-Check Command](Doctor_Self-Check_Command.md) (30 shared connections)
- [Explain Command Tests](Explain_Command_Tests.md) (17 shared connections)
- [Status Render Output](Status_Render_Output.md) (8 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (5 shared connections)
- [Local Tunnel Exposure Tests](Local_Tunnel_Exposure_Tests.md) (4 shared connections)
- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (2 shared connections)
- [CLI Command Dispatch Entry](CLI_Command_Dispatch_Entry.md) (2 shared connections)
- [Run State Rendering & DDB Store](Run_State_Rendering_%26_DDB_Store.md) (2 shared connections)
- [Result Rendering & Explain](Result_Rendering_%26_Explain.md) (2 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (1 shared connections)
- [Deploy Command Frontend Tests](Deploy_Command_Frontend_Tests.md) (1 shared connections)

## Source Files

- `cli/tests/test_main.py`

## Audit Trail

- EXTRACTED: 314 (96%)
- INFERRED: 13 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*