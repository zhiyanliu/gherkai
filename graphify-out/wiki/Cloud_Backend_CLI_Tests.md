# Cloud Backend CLI Tests

> 102 nodes · cohesion 0.05

## Key Concepts

- **test_backend_cloud.py** (69 connections) — `cli/tests/test_backend_cloud.py`
- **_patch_cloud_handles()** (52 connections) — `cli/tests/test_backend_cloud.py`
- **_write_feature()** (50 connections) — `cli/tests/test_backend_cloud.py`
- **_fake_schedule_factory()** (34 connections) — `cli/tests/test_backend_cloud.py`
- **test_variant_gate_only_probes_engines_the_run_uses()** (9 connections) — `cli/tests/test_backend_cloud.py`
- **test_run_cloud_resolves_variant_into_definition_and_engines()** (8 connections) — `cli/tests/test_backend_cloud.py`
- **test_cloud_does_not_ask_local_worker_for_grace_floor()** (7 connections) — `cli/tests/test_backend_cloud.py`
- **test_cloud_ignores_default_steps_dir_silently()** (7 connections) — `cli/tests/test_backend_cloud.py`
- **test_cloud_omits_steps_dir_and_warns_when_given()** (7 connections) — `cli/tests/test_backend_cloud.py`
- **test_cloud_run_does_not_consult_local_worker_chain()** (7 connections) — `cli/tests/test_backend_cloud.py`
- **test_submit_cloud_resolves_variant_into_definition()** (7 connections) — `cli/tests/test_backend_cloud.py`
- **test_variant_missing_exits_2_with_the_errors_message()** (7 connections) — `cli/tests/test_backend_cloud.py`
- **test_bad_default_pointer_name_exits_2_pointing_at_the_parameter()** (6 connections) — `cli/tests/test_backend_cloud.py`
- **test_local_backend_ignores_worker_variant_with_one_note()** (6 connections) — `cli/tests/test_backend_cloud.py`
- **test_local_definition_omits_worker_variant_fields()** (6 connections) — `cli/tests/test_backend_cloud.py`
- **test_resource_preflight_failure_prevents_variant_resolution()** (6 connections) — `cli/tests/test_backend_cloud.py`
- **test_skew_block_prevents_both_resource_preflight_and_variant()** (6 connections) — `cli/tests/test_backend_cloud.py`
- **test_skew_block_stops_run_before_resource_preflight()** (6 connections) — `cli/tests/test_backend_cloud.py`
- **test_skew_ok_is_silent()** (6 connections) — `cli/tests/test_backend_cloud.py`
- **test_skew_reads_stamp_with_resolved_prefix()** (6 connections) — `cli/tests/test_backend_cloud.py`
- **test_skew_warn_and_skip_pass_through_with_one_line()** (6 connections) — `cli/tests/test_backend_cloud.py`
- **test_submit_cloud_forks_tunnel_watch_daemon()** (6 connections) — `cli/tests/test_backend_cloud.py`
- **test_variant_gate_reuses_the_one_stamp_read()** (6 connections) — `cli/tests/test_backend_cloud.py`
- **test_variant_print_suppressed_by_quiet()** (6 connections) — `cli/tests/test_backend_cloud.py`
- **test_variant_resolution_prints_one_line_per_engine()** (6 connections) — `cli/tests/test_backend_cloud.py`
- *... and 77 more nodes in this community*

## Relationships

- [CLI Plan Command Behavior](CLI_Plan_Command_Behavior.md) (52 shared connections)
- [Cloud Status Command](Cloud_Status_Command.md) (5 shared connections)
- [Fake S3 Client](Fake_S3_Client.md) (2 shared connections)
- [CLI Entry Wiring Tests](CLI_Entry_Wiring_Tests.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (1 shared connections)
- [Deploy Command Frontend](Deploy_Command_Frontend.md) (1 shared connections)
- [CLI Command Dispatch](CLI_Command_Dispatch.md) (1 shared connections)
- [Fake DynamoDB Table](Fake_DynamoDB_Table.md) (1 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (1 shared connections)
- [Submit & Tunnel CLI Wiring](Submit_%26_Tunnel_CLI_Wiring.md) (1 shared connections)
- [CLI Parser Assembly](CLI_Parser_Assembly.md) (1 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (1 shared connections)

## Source Files

- `cli/tests/test_backend_cloud.py`

## Audit Trail

- EXTRACTED: 305 (98%)
- INFERRED: 5 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*