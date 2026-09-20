# CLI Plan Command Behavior

> 53 nodes · cohesion 0.06

## Key Concepts

- **main()** (215 connections) — `cli/gherkai_cli/__main__.py`
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
- **test_agent_all_writes_both_locations()** (2 connections) — `cli/tests/test_skill_install.py`
- **test_agent_codex_writes_agents_skills_only()** (2 connections) — `cli/tests/test_skill_install.py`
- **test_bare_skill_exits_2()** (2 connections) — `cli/tests/test_skill_install.py`
- **test_dir_and_global_are_mutually_exclusive()** (2 connections) — `cli/tests/test_skill_install.py`
- **test_empty_target_dir_is_accepted()** (2 connections) — `cli/tests/test_skill_install.py`
- *... and 28 more nodes in this community*

## Relationships

- [CLI Entry Wiring Tests](CLI_Entry_Wiring_Tests.md) (62 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (52 shared connections)
- [Deploy Command Frontend](Deploy_Command_Frontend.md) (20 shared connections)
- [Submit & Tunnel CLI Wiring](Submit_%26_Tunnel_CLI_Wiring.md) (18 shared connections)
- [Doctor Self-Check Tests](Doctor_Self-Check_Tests.md) (14 shared connections)
- [CLI Command Dispatch](CLI_Command_Dispatch.md) (8 shared connections)
- [Scenario Selection Flags](Scenario_Selection_Flags.md) (7 shared connections)
- [Deploy Provider Resolution](Deploy_Provider_Resolution.md) (3 shared connections)
- [Run & Submit Commands](Run_%26_Submit_Commands.md) (3 shared connections)
- [Cloud Status Command](Cloud_Status_Command.md) (3 shared connections)
- [Doctor & Skill Install](Doctor_%26_Skill_Install.md) (2 shared connections)
- [Explain Command Tests](Explain_Command_Tests.md) (2 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/tests/test_main.py`
- `cli/tests/test_skill_install.py`

## Audit Trail

- EXTRACTED: 280 (100%)
- INFERRED: 1 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*