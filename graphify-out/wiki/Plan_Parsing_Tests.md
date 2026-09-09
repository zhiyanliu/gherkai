# Plan Parsing Tests

> 22 nodes · cohesion 0.17

## Key Concepts

- **test_plan.py** (33 connections) — `core/tests/test_plan.py`
- **_plan()** (23 connections) — `core/tests/test_plan.py`
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
- **test_rule_nested_scenario_id_has_real_line()** (2 connections) — `core/tests/test_plan.py`
- **test_rule_nested_scenarios_get_distinct_ids()** (2 connections) — `core/tests/test_plan.py`
- **test_timeout_absent_and_no_default_is_none()** (2 connections) — `core/tests/test_plan.py`
- **test_timeout_conflict_errors()** (2 connections) — `core/tests/test_plan.py`
- **test_timeout_invalid_values_error()** (2 connections) — `core/tests/test_plan.py`
- **test_timeout_tag_sets_job_budget()** (2 connections) — `core/tests/test_plan.py`
- **test_unlabeled_scope_independent_jobs()** (2 connections) — `core/tests/test_plan.py`
- **parametrize** (1 connections)
- **plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。** (1 connections) — `core/tests/test_plan.py`

## Relationships

- [Feature Planning to Jobs](Feature_Planning_to_Jobs.md) (13 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (3 shared connections)
- [Unknown Step Keyword Failure](Unknown_Step_Keyword_Failure.md) (1 shared connections)
- [Leading And Keyword Failure](Leading_And_Keyword_Failure.md) (1 shared connections)

## Source Files

- `core/tests/test_plan.py`

## Audit Trail

- EXTRACTED: 57 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*