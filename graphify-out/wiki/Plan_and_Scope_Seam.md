# Plan and Scope Seam

> 76 nodes · cohesion 0.06

## Key Concepts

- **test_plan.py** (41 connections) — `core/tests/test_plan.py`
- **_plan()** (27 connections) — `core/tests/test_plan.py`
- **plan()** (24 connections) — `core/gherkai_core/scope.py`
- **scope.py** (23 connections) — `core/gherkai_core/scope.py`
- **FeatureSource** (23 connections) — `core/gherkai_core/scope.py`
- **PlanError** (15 connections) — `core/gherkai_core/errors.py`
- **ParsedScenario** (14 connections) — `core/gherkai_core/parse.py`
- **PlanConfig** (13 connections) — `core/gherkai_core/scope.py`
- **e2e_harness.py** (8 connections) — `tools/e2e_harness.py`
- **run()** (8 connections) — `tools/e2e_harness.py`
- **_resolve_engine()** (6 connections) — `core/gherkai_core/scope.py`
- **_resolve_timeout()** (6 connections) — `core/gherkai_core/scope.py`
- **_scope_key()** (6 connections) — `core/gherkai_core/scope.py`
- **_values_with_prefix()** (6 connections) — `core/gherkai_core/scope.py`
- **build_job()** (6 connections) — `tools/e2e_harness.py`
- **test_scope_id_collision_across_files_errors()** (5 connections) — `core/tests/test_plan.py`
- **test_assertion_votes_from_config_propagates_to_all_jobs()** (4 connections) — `core/tests/test_plan.py`
- **test_bare_tag_without_value_errors_with_location()** (4 connections) — `core/tests/test_plan.py`
- **test_plan_select_dropped_scope_does_not_block_iteration()** (4 connections) — `core/tests/test_plan.py`
- **test_plan_select_keeps_scope_engine_and_timeout()** (4 connections) — `core/tests/test_plan.py`
- **test_scope_id_collision_errors_even_when_narrowed_away()** (4 connections) — `core/tests/test_plan.py`
- **worker_cmd()** (4 connections) — `tools/e2e_harness.py`
- **parametrize** (3 connections)
- **test_cross_file_scope_merge_warns()** (3 connections) — `core/tests/test_plan.py`
- **test_distinct_uri_ok()** (3 connections) — `core/tests/test_plan.py`
- *... and 51 more nodes in this community*

## Relationships

- [Feature File Parsing](Feature_File_Parsing.md) (10 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (7 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (5 shared connections)
- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (4 shared connections)
- [CLI Command Entrypoints](CLI_Command_Entrypoints.md) (3 shared connections)
- [Cloud Composition Helpers](Cloud_Composition_Helpers.md) (2 shared connections)
- [Composition Root Helpers](Composition_Root_Helpers.md) (2 shared connections)
- [Event Wire Serialization](Event_Wire_Serialization.md) (2 shared connections)
- [Release Notes Rendering](Release_Notes_Rendering.md) (1 shared connections)
- [Version Stamp Skew Check](Version_Stamp_Skew_Check.md) (1 shared connections)
- [Task Def Stop Timeout](Task_Def_Stop_Timeout.md) (1 shared connections)
- [Worker Self-Describe Spawn](Worker_Self-Describe_Spawn.md) (1 shared connections)

## Source Files

- `README.md`
- `core/gherkai_core/errors.py`
- `core/gherkai_core/parse.py`
- `core/gherkai_core/scope.py`
- `core/tests/test_plan.py`
- `tools/e2e_harness.py`

## Audit Trail

- EXTRACTED: 176 (90%)
- INFERRED: 20 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*