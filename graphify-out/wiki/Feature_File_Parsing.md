# Feature File Parsing

> 79 nodes · cohesion 0.05

## Key Concepts

- **test_plan.py** (41 connections) — `core/tests/test_plan.py`
- **FeatureSource** (31 connections) — `core/gherkai_core/scope.py`
- **plan()** (29 connections) — `core/gherkai_core/scope.py`
- **_plan()** (27 connections) — `core/tests/test_plan.py`
- **scope.py** (20 connections) — `core/gherkai_core/scope.py`
- **PlanError** (15 connections) — `core/gherkai_core/errors.py`
- **parse.py** (15 connections) — `core/gherkai_core/parse.py`
- **parse_feature()** (15 connections) — `core/gherkai_core/parse.py`
- **ParsedScenario** (14 connections) — `core/gherkai_core/parse.py`
- **PlanConfig** (13 connections) — `core/gherkai_core/scope.py`
- **_resolve_engine()** (6 connections) — `core/gherkai_core/scope.py`
- **_resolve_timeout()** (6 connections) — `core/gherkai_core/scope.py`
- **_scope_key()** (6 connections) — `core/gherkai_core/scope.py`
- **_values_with_prefix()** (6 connections) — `core/gherkai_core/scope.py`
- **_map_argument()** (5 connections) — `core/gherkai_core/parse.py`
- **test_scope_id_collision_across_files_errors()** (5 connections) — `core/tests/test_plan.py`
- **_step_keyword()** (4 connections) — `core/gherkai_core/parse.py`
- **test_assertion_votes_from_config_propagates_to_all_jobs()** (4 connections) — `core/tests/test_plan.py`
- **test_bare_tag_without_value_errors_with_location()** (4 connections) — `core/tests/test_plan.py`
- **test_plan_select_dropped_scope_does_not_block_iteration()** (4 connections) — `core/tests/test_plan.py`
- **test_plan_select_keeps_scope_engine_and_timeout()** (4 connections) — `core/tests/test_plan.py`
- **test_scope_id_collision_errors_even_when_narrowed_away()** (4 connections) — `core/tests/test_plan.py`
- **_index_ast_lines()** (3 connections) — `core/gherkai_core/parse.py`
- **_scenario_line_and_example_line()** (3 connections) — `core/gherkai_core/parse.py`
- **parametrize** (3 connections)
- *... and 54 more nodes in this community*

## Relationships

- [Job Explain Data Model](Job_Explain_Data_Model.md) (13 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (7 shared connections)
- [E2E Harness Script](E2E_Harness_Script.md) (6 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (5 shared connections)
- [Store Port Definitions](Store_Port_Definitions.md) (5 shared connections)
- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (4 shared connections)
- [SSM Paths And Compose](SSM_Paths_And_Compose.md) (2 shared connections)
- [Worker Job Source Input](Worker_Job_Source_Input.md) (1 shared connections)
- [AWS Target Resolution](AWS_Target_Resolution.md) (1 shared connections)
- [Local Compose Root](Local_Compose_Root.md) (1 shared connections)
- [Step Argument S3 Offload](Step_Argument_S3_Offload.md) (1 shared connections)
- [Backend Version Skew Check](Backend_Version_Skew_Check.md) (1 shared connections)

## Source Files

- `core/gherkai_core/errors.py`
- `core/gherkai_core/parse.py`
- `core/gherkai_core/scope.py`
- `core/tests/test_plan.py`

## Audit Trail

- EXTRACTED: 191 (89%)
- INFERRED: 23 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*