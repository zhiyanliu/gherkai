# Feature Planning to Jobs

> 11 nodes · cohesion 0.27

## Key Concepts

- **FeatureSource** (26 connections) — `core/gherkai_core/scope.py`
- **plan()** (19 connections) — `core/gherkai_core/scope.py`
- **PlanConfig** (12 connections) — `core/gherkai_core/scope.py`
- **test_assertion_votes_from_config_propagates_to_all_jobs()** (4 connections) — `core/tests/test_plan.py`
- **test_cross_file_scope_merge_warns()** (3 connections) — `core/tests/test_plan.py`
- **test_distinct_uri_ok()** (3 connections) — `core/tests/test_plan.py`
- **test_duplicate_uri_errors()** (3 connections) — `core/tests/test_plan.py`
- **test_engine_default()** (3 connections) — `core/tests/test_plan.py`
- **Job** (1 connections)
- **core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。 严格契约：`features` 的 uri 必须互异（uri…** (1 connections) — `core/gherkai_core/scope.py`
- **plan 的输入：feature 文件内容（非路径——core 不碰 FS，ADR 0025）。** (1 connections) — `core/gherkai_core/scope.py`

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (15 shared connections)
- [Plan Parsing Tests](Plan_Parsing_Tests.md) (13 shared connections)
- [S3 ReportStore & Subprocess Engine](S3_ReportStore_%26_Subprocess_Engine.md) (5 shared connections)
- [Cloud Resource Preflight Fakes](Cloud_Resource_Preflight_Fakes.md) (4 shared connections)
- [Job Serialization & E2E Harness](Job_Serialization_%26_E2E_Harness.md) (3 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (2 shared connections)
- [CLI Run/Submit Commands](CLI_Run-Submit_Commands.md) (2 shared connections)
- [Engine Resolver Building](Engine_Resolver_Building.md) (1 shared connections)
- [Backend Version Stamp Check](Backend_Version_Stamp_Check.md) (1 shared connections)

## Source Files

- `core/gherkai_core/scope.py`
- `core/tests/test_plan.py`

## Audit Trail

- EXTRACTED: 43 (70%)
- INFERRED: 18 (30%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*