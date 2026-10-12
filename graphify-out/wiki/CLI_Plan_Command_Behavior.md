# CLI Plan Command Behavior

> 61 nodes · cohesion 0.05

## Key Concepts

- **main()** (216 connections) — `cli/gherkai_cli/__main__.py`
- **test_skill_install.py** (27 connections) — `cli/tests/test_skill_install.py`
- **_det_feature()** (7 connections) — `cli/tests/test_main.py`
- **_tree()** (6 connections) — `cli/tests/test_skill_install.py`
- **test_plan_and_list_deterministic_pass_steps_dir_to_worker()** (5 connections) — `cli/tests/test_main.py`
- **test_plan_annotates_deterministic_hits()** (4 connections) — `cli/tests/test_main.py`
- **test_plan_annotation_degrades_gracefully()** (4 connections) — `cli/tests/test_main.py`
- **test_plan_conflict_annotated_and_warned()** (4 connections) — `cli/tests/test_main.py`
- **test_plan_degrades_when_worker_runtime_missing()** (4 connections) — `cli/tests/test_main.py`
- **test_fresh_install_writes_packaged_tree_plus_marker()** (4 connections) — `cli/tests/test_skill_install.py`
- **test_tty_asks_once_and_honours_the_answer()** (4 connections) — `cli/tests/test_skill_install.py`
- **_Tty** (4 connections) — `cli/tests/test_skill_install.py`
- **test_explain_cloud_blocks_on_version_skew_before_any_cloud_read()** (3 connections) — `cli/tests/test_main.py`
- **test_help_hides_internal_entry_points()** (3 connections) — `cli/tests/test_main.py`
- **test_plan_degrades_when_worker_missing()** (3 connections) — `cli/tests/test_main.py`
- **test_plan_json_carries_deterministic_field()** (3 connections) — `cli/tests/test_main.py`
- **test_plan_rejects_a_directory_as_feature()** (3 connections) — `cli/tests/test_main.py`
- **test_version_flag_prints_dist_version()** (3 connections) — `cli/tests/test_main.py`
- **test_agent_all_refuses_before_touching_the_other_location()** (3 connections) — `cli/tests/test_skill_install.py`
- **test_reinstall_converges_and_drops_stale_files()** (3 connections) — `cli/tests/test_skill_install.py`
- **test_default_engine_flag_has_choices()** (2 connections) — `cli/tests/test_main.py`
- **test_list_deterministic_worker_failure_exits_2()** (2 connections) — `cli/tests/test_main.py`
- **test_list_deterministic_worker_not_found_exits_2()** (2 connections) — `cli/tests/test_main.py`
- **test_plan_json_shape()** (2 connections) — `cli/tests/test_main.py`
- **test_plan_rejects_engine_conflict()** (2 connections) — `cli/tests/test_main.py`
- *... and 36 more nodes in this community*

## Relationships

- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (66 shared connections)
- [Cloud Backend CLI Wiring Tests](Cloud_Backend_CLI_Wiring_Tests.md) (52 shared connections)
- [Deploy Command Frontend Tests](Deploy_Command_Frontend_Tests.md) (20 shared connections)
- [Doctor Self-Check Command](Doctor_Self-Check_Command.md) (19 shared connections)
- [Local Tunnel Exposure Tests](Local_Tunnel_Exposure_Tests.md) (16 shared connections)
- [CLI Command Dispatch Entry](CLI_Command_Dispatch_Entry.md) (14 shared connections)
- [Deploy CLI Provider Discovery](Deploy_CLI_Provider_Discovery.md) (3 shared connections)
- [Cloud Status Command](Cloud_Status_Command.md) (3 shared connections)
- [Explain Command Tests](Explain_Command_Tests.md) (3 shared connections)
- [CLI JSON Contract Tests](CLI_JSON_Contract_Tests.md) (2 shared connections)
- [Skill Install Command](Skill_Install_Command.md) (2 shared connections)
- [Run State Rendering & DDB Store](Run_State_Rendering_%26_DDB_Store.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/tests/test_main.py`
- `cli/tests/test_skill_install.py`

## Audit Trail

- EXTRACTED: 289 (100%)
- INFERRED: 1 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*