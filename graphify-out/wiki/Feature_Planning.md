# Feature Planning

> 46 nodes · cohesion 0.08

## Key Concepts

- **test_plan.py** (33 connections) — `core/tests/test_plan.py`
- **FeatureSource** (26 connections) — `core/gherkai_core/scope.py`
- **_plan()** (23 connections) — `core/tests/test_plan.py`
- **plan()** (19 connections) — `core/gherkai_core/scope.py`
- **PlanConfig** (12 connections) — `core/gherkai_core/scope.py`
- **e2e_harness.py** (7 connections) — `tools/e2e_harness.py`
- **build_job()** (6 connections) — `tools/e2e_harness.py`
- **run()** (6 connections) — `tools/e2e_harness.py`
- **test_assertion_votes_from_config_propagates_to_all_jobs()** (4 connections) — `core/tests/test_plan.py`
- **worker_cmd()** (4 connections) — `tools/e2e_harness.py`
- **test_cross_file_scope_merge_warns()** (3 connections) — `core/tests/test_plan.py`
- **test_distinct_uri_ok()** (3 connections) — `core/tests/test_plan.py`
- **test_duplicate_uri_errors()** (3 connections) — `core/tests/test_plan.py`
- **test_engine_default()** (3 connections) — `core/tests/test_plan.py`
- **test_leading_and_keyword_fails_fast()** (3 connections) — `core/tests/test_plan.py`
- **test_star_step_keyword_fails_fast()** (3 connections) — `core/tests/test_plan.py`
- **test_timeout_default_fills_untagged_tag_wins()** (3 connections) — `core/tests/test_plan.py`
- **test_timeout_non_finite_values_error()** (3 connections) — `core/tests/test_plan.py`
- **snapshot_disk()** (3 connections) — `tools/e2e_harness.py`
- **test_assertion_votes_default_is_one()** (2 connections) — `core/tests/test_plan.py`
- **test_background_prepended()** (2 connections) — `core/tests/test_plan.py`
- **test_datatable_and_docstring_argument()** (2 connections) — `core/tests/test_plan.py`
- **test_engine_conflict_errors()** (2 connections) — `core/tests/test_plan.py`
- **test_engine_inherited_within_scope()** (2 connections) — `core/tests/test_plan.py`
- **test_feature_level_scope_propagates()** (2 connections) — `core/tests/test_plan.py`
- *... and 21 more nodes in this community*

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (22 shared connections)
- [S3 Report Store & Subprocess](S3_Report_Store_%26_Subprocess.md) (5 shared connections)
- [Cloud Preflight Checks](Cloud_Preflight_Checks.md) (4 shared connections)
- [SSM Path & Client Composition](SSM_Path_%26_Client_Composition.md) (2 shared connections)
- [CLI Plan & Submit](CLI_Plan_%26_Submit.md) (2 shared connections)
- [Engine Composition Helpers](Engine_Composition_Helpers.md) (1 shared connections)
- [Backend Version Stamp](Backend_Version_Stamp.md) (1 shared connections)
- [Job JSON Serialization](Job_JSON_Serialization.md) (1 shared connections)
- [Cloud Target Resolution](Cloud_Target_Resolution.md) (1 shared connections)

## Source Files

- `core/gherkai_core/scope.py`
- `core/tests/test_plan.py`
- `tools/e2e_harness.py`

## Audit Trail

- EXTRACTED: 106 (85%)
- INFERRED: 19 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*