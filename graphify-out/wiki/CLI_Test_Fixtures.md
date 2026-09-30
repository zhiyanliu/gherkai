# CLI Test Fixtures

> 80 nodes · cohesion 0.03

## Key Concepts

- **_fixture()** (37 connections) — `engines/novaact/tests/test_evidence.py`
- **evidence.py** (19 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **ActRecord** (16 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **write_step_evidence()** (16 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **act_evidence()** (12 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **step_evidence()** (8 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **step_dir()** (7 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **test_undecodable_image_leaves_screenshot_null()** (7 connections) — `engines/novaact/tests/test_evidence.py`
- **test_prompt_is_worker_instruction_not_sdk_rewritten_one()** (5 connections) — `engines/novaact/tests/test_evidence.py`
- **cli/tests/conftest.py** (4 connections) — `cli/tests/conftest.py`
- **s3_report_store()** (4 connections) — `core/tests/conftest.py`
- **s3_result_store()** (4 connections) — `core/tests/conftest.py`
- **_actions()** (4 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **_decode_data_url()** (4 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **_kwargs()** (4 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **read_trajectory()** (4 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **select_screenshots()** (4 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **_thought()** (4 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **test_act_fixture_maps_actions_by_name_and_last_frame_url()** (4 connections) — `engines/novaact/tests/test_evidence.py`
- **test_assert_fixture_maps_thought_result_url_vote()** (4 connections) — `engines/novaact/tests/test_evidence.py`
- **test_step_evidence_schema_keys()** (4 connections) — `engines/novaact/tests/test_evidence.py`
- **_presentation_is_environment_independent()** (3 connections) — `cli/tests/conftest.py`
- **aws()** (3 connections) — `core/tests/conftest.py`
- **_fake_aws_creds()** (3 connections) — `core/tests/conftest.py`
- **fargate()** (3 connections) — `core/tests/conftest.py`
- *... and 55 more nodes in this community*

## Relationships

- [Scenario Evidence Keys](Scenario_Evidence_Keys.md) (23 shared connections)
- [S3 Step Argument Offload](S3_Step_Argument_Offload.md) (9 shared connections)
- [Worker Event Sink](Worker_Event_Sink.md) (3 shared connections)
- [Nova Act Worker Runtime](Nova_Act_Worker_Runtime.md) (3 shared connections)
- [Composition Root Helpers](Composition_Root_Helpers.md) (3 shared connections)
- [Interrupt and Signal Handling](Interrupt_and_Signal_Handling.md) (2 shared connections)
- [Resource Naming and Variants](Resource_Naming_and_Variants.md) (2 shared connections)
- [Tunnel Host Orchestration](Tunnel_Host_Orchestration.md) (1 shared connections)
- [Report Store Adapters](Report_Store_Adapters.md) (1 shared connections)
- [S3 Result Store](S3_Result_Store.md) (1 shared connections)
- [Cloud Launcher and EventLog](Cloud_Launcher_and_EventLog.md) (1 shared connections)
- [Lambda Handler Event Tests](Lambda_Handler_Event_Tests.md) (1 shared connections)

## Source Files

- `cli/tests/conftest.py`
- `core/tests/conftest.py`
- `core/tests/test_cloud_reconcile.py`
- `deploy_aws/tests/test_lambda_handlers.py`
- `deploy_aws/tests/test_provider.py`
- `engines/novaact/gherkai_worker_novaact/evidence.py`
- `engines/novaact/tests/test_evidence.py`
- `engines/novaact/tests/test_user_steps.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_textui.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 168 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*