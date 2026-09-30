# Doctor Self-check Tests

> 43 nodes · cohesion 0.07

## Key Concepts

- **_fake_locator()** (21 connections) — `cli/tests/test_main.py`
- **.engine()** (15 connections) — `core/gherkai_core/model.py`
- **_no_provider()** (13 connections) — `cli/tests/test_main.py`
- **_cloud_backend_ok()** (7 connections) — `cli/tests/test_main.py`
- **test_doctor_cloud_worker_grace_shortfall_is_optional_gap_not_failure()** (7 connections) — `cli/tests/test_main.py`
- **_doctor_cloud_json()** (6 connections) — `cli/tests/test_main.py`
- **test_doctor_cloud_worker_grace_ok_and_skips_engine_without_local_worker()** (6 connections) — `cli/tests/test_main.py`
- **test_doctor_cloud_worker_grace_query_failure_lands_in_detail()** (6 connections) — `cli/tests/test_main.py`
- **test_doctor_cloud_worker_grace_unset_stop_timeout_is_reported()** (6 connections) — `cli/tests/test_main.py`
- **test_doctor_local_json_checks_and_exit_codes()** (6 connections) — `cli/tests/test_main.py`
- **test_doctor_omits_model_row_when_self_describe_fails()** (6 connections) — `cli/tests/test_main.py`
- **test_doctor_reports_worker_self_reported_model()** (6 connections) — `cli/tests/test_main.py`
- **test_run_grace_mixed_engines_takes_max_of_self_reported()** (6 connections) — `cli/tests/test_main.py`
- **test_doctor_cloud_credential_failure_is_required_and_exits_2()** (5 connections) — `cli/tests/test_main.py`
- **test_doctor_cloud_profile_error_at_target_resolution_is_a_credential_failure()** (5 connections) — `cli/tests/test_main.py`
- **test_doctor_cloud_without_region_fails_region_check_first()** (5 connections) — `cli/tests/test_main.py`
- **test_doctor_runs_worker_self_describe_even_without_steps_dir()** (5 connections) — `cli/tests/test_main.py`
- **_stub_stop_timeout()** (4 connections) — `cli/tests/test_main.py`
- **test_doctor_cloud_missing_default_pointer_is_required_failure()** (4 connections) — `cli/tests/test_main.py`
- **test_doctor_cloud_reports_backend_failures_and_exits_2()** (4 connections) — `cli/tests/test_main.py`
- **test_doctor_no_engine_at_all_fails_locally_but_not_for_cloud()** (4 connections) — `cli/tests/test_main.py`
- **test_doctor_provider_installed_but_broken_is_required_failure()** (4 connections) — `cli/tests/test_main.py`
- **test_doctor_provider_section_comes_from_provider_doctor()** (4 connections) — `cli/tests/test_main.py`
- **test_doctor_steps_dir_error_reason_lands_in_json_detail()** (4 connections) — `cli/tests/test_main.py`
- **test_list_deterministic_text_and_json()** (4 connections) — `cli/tests/test_main.py`
- *... and 18 more nodes in this community*

## Relationships

- [CLI Run Wiring Tests](CLI_Run_Wiring_Tests.md) (30 shared connections)
- [Plan Command CLI Tests](Plan_Command_CLI_Tests.md) (19 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (2 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (1 shared connections)
- [Engine Listing and JSON Contract](Engine_Listing_and_JSON_Contract.md) (1 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `core/gherkai_core/model.py`

## Audit Trail

- EXTRACTED: 104 (88%)
- INFERRED: 14 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*