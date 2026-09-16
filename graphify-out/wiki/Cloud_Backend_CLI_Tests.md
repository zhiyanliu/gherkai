# Cloud Backend CLI Tests

> 98 nodes · cohesion 0.05

## Key Concepts

- **test_backend_cloud.py** (67 connections) — `cli/tests/test_backend_cloud.py`
- **_patch_cloud_handles()** (50 connections) — `cli/tests/test_backend_cloud.py`
- **_write_feature()** (48 connections) — `cli/tests/test_backend_cloud.py`
- **_fake_schedule_factory()** (33 connections) — `cli/tests/test_backend_cloud.py`
- **test_variant_gate_only_probes_engines_the_run_uses()** (9 connections) — `cli/tests/test_backend_cloud.py`
- **test_run_cloud_resolves_variant_into_definition_and_engines()** (8 connections) — `cli/tests/test_backend_cloud.py`
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
- **_definition()** (5 connections) — `cli/tests/test_backend_cloud.py`
- *... and 73 more nodes in this community*

## Relationships

- [CLI Main Flow Tests](CLI_Main_Flow_Tests.md) (50 shared connections)
- [Cloud Status Artifacts](Cloud_Status_Artifacts.md) (5 shared connections)
- [Fake S3 Client](Fake_S3_Client.md) (2 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (1 shared connections)
- [Deploy CLI Shell](Deploy_CLI_Shell.md) (1 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (1 shared connections)
- [Fake DynamoDB Table](Fake_DynamoDB_Table.md) (1 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (1 shared connections)
- [CLI Run Command Tests](CLI_Run_Command_Tests.md) (1 shared connections)
- [Submit & Tunnel CLI Tests](Submit_%26_Tunnel_CLI_Tests.md) (1 shared connections)
- [CLI Parser Construction](CLI_Parser_Construction.md) (1 shared connections)
- [Runtime Composition Root](Runtime_Composition_Root.md) (1 shared connections)

## Source Files

- `cli/tests/test_backend_cloud.py`

## Audit Trail

- EXTRACTED: 294 (99%)
- INFERRED: 4 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*