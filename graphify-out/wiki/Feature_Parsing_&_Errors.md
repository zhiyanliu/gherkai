# Feature Parsing & Errors

> 41 nodes · cohesion 0.09

## Key Concepts

- **FeatureSource** (31 connections) — `core/gherkai_core/scope.py`
- **plan()** (29 connections) — `core/gherkai_core/scope.py`
- **scope.py** (20 connections) — `core/gherkai_core/scope.py`
- **PlanError** (15 connections) — `core/gherkai_core/errors.py`
- **parse.py** (15 connections) — `core/gherkai_core/parse.py`
- **parse_feature()** (15 connections) — `core/gherkai_core/parse.py`
- **ParsedScenario** (14 connections) — `core/gherkai_core/parse.py`
- **errors.py** (12 connections) — `core/gherkai_core/errors.py`
- **_resolve_engine()** (6 connections) — `core/gherkai_core/scope.py`
- **_resolve_timeout()** (6 connections) — `core/gherkai_core/scope.py`
- **_scope_key()** (6 connections) — `core/gherkai_core/scope.py`
- **_values_with_prefix()** (6 connections) — `core/gherkai_core/scope.py`
- **_map_argument()** (5 connections) — `core/gherkai_core/parse.py`
- **_step_keyword()** (4 connections) — `core/gherkai_core/parse.py`
- **test_plan_select_dropped_scope_does_not_block_iteration()** (4 connections) — `core/tests/test_plan.py`
- **test_scope_id_collision_errors_even_when_narrowed_away()** (4 connections) — `core/tests/test_plan.py`
- **_index_ast_lines()** (3 connections) — `core/gherkai_core/parse.py`
- **_scenario_line_and_example_line()** (3 connections) — `core/gherkai_core/parse.py`
- **test_cross_file_scope_merge_warns()** (3 connections) — `core/tests/test_plan.py`
- **test_distinct_uri_ok()** (3 connections) — `core/tests/test_plan.py`
- **test_duplicate_uri_errors()** (3 connections) — `core/tests/test_plan.py`
- **core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…** (1 connections) — `core/gherkai_core/errors.py`
- **feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…** (1 connections) — `core/gherkai_core/errors.py`
- **StepArgument** (1 connections)
- **parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。 藏住第三方库 gherkin-…** (1 connections) — `core/gherkai_core/parse.py`
- *... and 16 more nodes in this community*

## Relationships

- [Plan Scope/Engine Validation Tests](Plan_Scope-Engine_Validation_Tests.md) (24 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (14 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (12 shared connections)
- [CLI Command Dispatch Entry](CLI_Command_Dispatch_Entry.md) (4 shared connections)
- [E2E Interrupt Harness](E2E_Interrupt_Harness.md) (4 shared connections)
- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (4 shared connections)
- [Severity Aggregation & Fake Engine](Severity_Aggregation_%26_Fake_Engine.md) (2 shared connections)
- [Fargate Engine Adapter Tests](Fargate_Engine_Adapter_Tests.md) (1 shared connections)
- [Worker Job Source Input](Worker_Job_Source_Input.md) (1 shared connections)
- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (1 shared connections)
- [AWS Target & Network Resolution](AWS_Target_%26_Network_Resolution.md) (1 shared connections)
- [Engine Composition Helpers](Engine_Composition_Helpers.md) (1 shared connections)

## Source Files

- `core/gherkai_core/errors.py`
- `core/gherkai_core/parse.py`
- `core/gherkai_core/scope.py`
- `core/tests/test_plan.py`

## Audit Trail

- EXTRACTED: 128 (85%)
- INFERRED: 22 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*