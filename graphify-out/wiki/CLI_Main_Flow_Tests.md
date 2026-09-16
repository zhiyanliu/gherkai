# CLI Main Flow Tests

> 39 nodes · cohesion 0.08

## Key Concepts

- **main()** (205 connections) — `cli/gherkai_cli/__main__.py`
- **test_skill_install.py** (27 connections) — `cli/tests/test_skill_install.py`
- **_tree()** (6 connections) — `cli/tests/test_skill_install.py`
- **test_fresh_install_writes_packaged_tree_plus_marker()** (4 connections) — `cli/tests/test_skill_install.py`
- **test_tty_asks_once_and_honours_the_answer()** (4 connections) — `cli/tests/test_skill_install.py`
- **_Tty** (4 connections) — `cli/tests/test_skill_install.py`
- **test_explain_cloud_blocks_on_version_skew_before_any_cloud_read()** (3 connections) — `cli/tests/test_main.py`
- **test_plan_degrades_when_worker_missing()** (3 connections) — `cli/tests/test_main.py`
- **test_plan_rejects_a_directory_as_feature()** (3 connections) — `cli/tests/test_main.py`
- **test_version_flag_prints_dist_version()** (3 connections) — `cli/tests/test_main.py`
- **test_agent_all_refuses_before_touching_the_other_location()** (3 connections) — `cli/tests/test_skill_install.py`
- **test_reinstall_converges_and_drops_stale_files()** (3 connections) — `cli/tests/test_skill_install.py`
- **test_agent_all_writes_both_locations()** (2 connections) — `cli/tests/test_skill_install.py`
- **test_agent_codex_writes_agents_skills_only()** (2 connections) — `cli/tests/test_skill_install.py`
- **test_bare_skill_exits_2()** (2 connections) — `cli/tests/test_skill_install.py`
- **test_dir_and_global_are_mutually_exclusive()** (2 connections) — `cli/tests/test_skill_install.py`
- **test_empty_target_dir_is_accepted()** (2 connections) — `cli/tests/test_skill_install.py`
- **test_global_installs_under_home()** (2 connections) — `cli/tests/test_skill_install.py`
- **test_missing_dir_is_refused()** (2 connections) — `cli/tests/test_skill_install.py`
- **test_non_tty_default_does_not_touch_pointer_file()** (2 connections) — `cli/tests/test_skill_install.py`
- **test_non_utf8_pointer_file_stays_inside_the_exit_code_set()** (2 connections) — `cli/tests/test_skill_install.py`
- **test_pointer_no_leaves_instruction_file_alone()** (2 connections) — `cli/tests/test_skill_install.py`
- **test_pointer_yes_appends_exactly_once_across_two_runs()** (2 connections) — `cli/tests/test_skill_install.py`
- **test_pointer_yes_for_codex_appends_to_agents_md_keeping_existing()** (2 connections) — `cli/tests/test_skill_install.py`
- **test_print_outputs_packaged_skill_md_exactly()** (2 connections) — `cli/tests/test_skill_install.py`
- *... and 14 more nodes in this community*

## Relationships

- [CLI Run Command Tests](CLI_Run_Command_Tests.md) (54 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (50 shared connections)
- [Deploy CLI Shell](Deploy_CLI_Shell.md) (20 shared connections)
- [Submit & Tunnel CLI Tests](Submit_%26_Tunnel_CLI_Tests.md) (18 shared connections)
- [Doctor Self-Check](Doctor_Self-Check.md) (12 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (10 shared connections)
- [Scenario Selection Filters](Scenario_Selection_Filters.md) (7 shared connections)
- [Deploy Command Parsers](Deploy_Command_Parsers.md) (3 shared connections)
- [CLI Parser Construction](CLI_Parser_Construction.md) (3 shared connections)
- [Cloud Status Artifacts](Cloud_Status_Artifacts.md) (3 shared connections)
- [Explain Command Tests](Explain_Command_Tests.md) (3 shared connections)
- [Doctor Self-Check Command](Doctor_Self-Check_Command.md) (2 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/tests/test_main.py`
- `cli/tests/test_skill_install.py`

## Audit Trail

- EXTRACTED: 250 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*