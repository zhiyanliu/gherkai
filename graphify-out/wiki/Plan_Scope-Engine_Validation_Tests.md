# Plan Scope/Engine Validation Tests

> 40 nodes · cohesion 0.09

## Key Concepts

- **test_plan.py** (41 connections) — `core/tests/test_plan.py`
- **_plan()** (27 connections) — `core/tests/test_plan.py`
- **PlanConfig** (13 connections) — `core/gherkai_core/scope.py`
- **test_scope_id_collision_across_files_errors()** (5 connections) — `core/tests/test_plan.py`
- **test_assertion_votes_from_config_propagates_to_all_jobs()** (4 connections) — `core/tests/test_plan.py`
- **test_bare_tag_without_value_errors_with_location()** (4 connections) — `core/tests/test_plan.py`
- **test_plan_select_keeps_scope_engine_and_timeout()** (4 connections) — `core/tests/test_plan.py`
- **parametrize** (3 connections)
- **test_engine_default()** (3 connections) — `core/tests/test_plan.py`
- **test_leading_and_keyword_fails_fast()** (3 connections) — `core/tests/test_plan.py`
- **test_named_scope_colliding_with_unlabeled_scenario_id_errors()** (3 connections) — `core/tests/test_plan.py`
- **test_named_scope_matching_a_tagged_scenario_id_is_ok()** (3 connections) — `core/tests/test_plan.py`
- **test_scope_id_collision_errors_regardless_of_order()** (3 connections) — `core/tests/test_plan.py`
- **test_star_step_keyword_fails_fast()** (3 connections) — `core/tests/test_plan.py`
- **test_timeout_default_fills_untagged_tag_wins()** (3 connections) — `core/tests/test_plan.py`
- **test_timeout_non_finite_values_error()** (3 connections) — `core/tests/test_plan.py`
- **test_assertion_votes_default_is_one()** (2 connections) — `core/tests/test_plan.py`
- **test_background_prepended()** (2 connections) — `core/tests/test_plan.py`
- **test_datatable_and_docstring_argument()** (2 connections) — `core/tests/test_plan.py`
- **test_engine_conflict_errors()** (2 connections) — `core/tests/test_plan.py`
- **test_engine_inherited_within_scope()** (2 connections) — `core/tests/test_plan.py`
- **test_feature_level_scope_propagates()** (2 connections) — `core/tests/test_plan.py`
- **test_multi_scope_errors()** (2 connections) — `core/tests/test_plan.py`
- **test_out_of_order_steps_preserved()** (2 connections) — `core/tests/test_plan.py`
- **test_outline_expands_and_distinguishable()** (2 connections) — `core/tests/test_plan.py`
- *... and 15 more nodes in this community*

## Relationships

- [Feature Parsing & Errors](Feature_Parsing_%26_Errors.md) (24 shared connections)
- [CLI Command Dispatch Entry](CLI_Command_Dispatch_Entry.md) (1 shared connections)
- [E2E Interrupt Harness](E2E_Interrupt_Harness.md) (1 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (1 shared connections)

## Source Files

- `core/gherkai_core/scope.py`
- `core/tests/test_plan.py`

## Audit Trail

- EXTRACTED: 93 (97%)
- INFERRED: 3 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*