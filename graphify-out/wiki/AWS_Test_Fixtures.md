# AWS Test Fixtures

> 74 nodes · cohesion 0.04

## Key Concepts

- **_fixture()** (35 connections) — `engines/novaact/tests/test_evidence.py`
- **evidence.py** (17 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **ActRecord** (15 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **write_step_evidence()** (14 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **act_evidence()** (12 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **step_evidence()** (8 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **step_dir()** (7 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **test_undecodable_image_leaves_screenshot_null()** (7 connections) — `engines/novaact/tests/test_evidence.py`
- **test_prompt_is_worker_instruction_not_sdk_rewritten_one()** (5 connections) — `engines/novaact/tests/test_evidence.py`
- **s3_report_store()** (4 connections) — `core/tests/conftest.py`
- **s3_result_store()** (4 connections) — `core/tests/conftest.py`
- **_actions()** (4 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **_decode_data_url()** (4 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **_kwargs()** (4 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **read_trajectory()** (4 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **select_screenshots()** (4 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **_thought()** (4 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **_act_record()** (4 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_act_fixture_maps_actions_by_name_and_last_frame_url()** (4 connections) — `engines/novaact/tests/test_evidence.py`
- **test_assert_fixture_maps_thought_result_url_vote()** (4 connections) — `engines/novaact/tests/test_evidence.py`
- **test_step_evidence_schema_keys()** (4 connections) — `engines/novaact/tests/test_evidence.py`
- **aws()** (3 connections) — `core/tests/conftest.py`
- **_fake_aws_creds()** (3 connections) — `core/tests/conftest.py`
- **fargate()** (3 connections) — `core/tests/conftest.py`
- **real_aws()** (3 connections) — `core/tests/conftest.py`
- *... and 49 more nodes in this community*

## Relationships

- [Scenario Key & Evidence Tests](Scenario_Key_%26_Evidence_Tests.md) (21 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (9 shared connections)
- [Nova Act Worker Package](Nova_Act_Worker_Package.md) (3 shared connections)
- [Container Worker Tests](Container_Worker_Tests.md) (2 shared connections)
- [Interrupt & Termination Model](Interrupt_%26_Termination_Model.md) (2 shared connections)
- [Cloud Target & Worker Resolution](Cloud_Target_%26_Worker_Resolution.md) (2 shared connections)
- [Worker Variant Resolution](Worker_Variant_Resolution.md) (2 shared connections)
- [S3 Report Store & Control Plane](S3_Report_Store_%26_Control_Plane.md) (1 shared connections)
- [S3 Result Store](S3_Result_Store.md) (1 shared connections)
- [Cloud Job Launcher](Cloud_Job_Launcher.md) (1 shared connections)
- [Lambda Handler Tests](Lambda_Handler_Tests.md) (1 shared connections)
- [Deploy Provider Tests](Deploy_Provider_Tests.md) (1 shared connections)

## Source Files

- `core/tests/conftest.py`
- `core/tests/test_cloud_reconcile.py`
- `deploy_aws/tests/test_lambda_handlers.py`
- `deploy_aws/tests/test_provider.py`
- `deploy_aws/tests/test_workers.py`
- `engines/novaact/gherkai_worker_novaact/evidence.py`
- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_evidence.py`
- `engines/novaact/tests/test_user_steps.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 156 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*