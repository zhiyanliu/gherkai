# Test Fixtures & Conftest

> 55 nodes · cohesion 0.04

## Key Concepts

- **_fixture()** (41 connections) — `engines/novaact/tests/test_evidence.py`
- **core/tests/conftest.py** (14 connections) — `core/tests/conftest.py`
- **real_aws()** (5 connections) — `core/tests/conftest.py`
- **cli/tests/conftest.py** (4 connections) — `cli/tests/conftest.py`
- **arg_offloader()** (4 connections) — `core/tests/conftest.py`
- **ddb_run_store()** (4 connections) — `core/tests/conftest.py`
- **ddb_run_store_offload()** (4 connections) — `core/tests/conftest.py`
- **_fake_aws_creds()** (4 connections) — `core/tests/conftest.py`
- **s3_report_store()** (4 connections) — `core/tests/conftest.py`
- **_color_env_independent()** (4 connections) — `core/tests/test_subprocess_engine.py`
- **_presentation_is_environment_independent()** (3 connections) — `cli/tests/conftest.py`
- **aws()** (3 connections) — `core/tests/conftest.py`
- **fargate()** (3 connections) — `core/tests/conftest.py`
- **events_table()** (3 connections) — `core/tests/test_cloud_reconcile.py`
- **cloud_env()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_clean_aws_env()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **_presentation_is_environment_independent()** (3 connections) — `deploy_aws/tests/test_workers.py`
- **logs_dir()** (3 connections) — `engines/novaact/tests/test_evidence.py`
- **test_real_output_has_is_return_false_everywhere_so_we_map_by_name()** (3 connections) — `engines/novaact/tests/test_evidence.py`
- **_reset_stop()** (3 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **_isolate()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **fresh_caps_cache()** (3 connections) — `runtime/tests/test_compose.py`
- **novaact_env_cmd()** (3 connections) — `runtime/tests/test_compose.py`
- **_presentation_is_environment_independent()** (3 connections) — `runtime/tests/test_textui.py`
- **aws()** (3 connections) — `runtime/tests/test_worker_variant.py`
- *... and 30 more nodes in this community*

## Relationships

- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (5 shared connections)
- [Step Evidence Records](Step_Evidence_Records.md) (5 shared connections)
- [S3 Result Store](S3_Result_Store.md) (3 shared connections)
- [Worker Image Tests](Worker_Image_Tests.md) (3 shared connections)
- [Scenario Evidence Tests](Scenario_Evidence_Tests.md) (3 shared connections)
- [AWS Target & Network Resolution](AWS_Target_%26_Network_Resolution.md) (3 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (2 shared connections)
- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (2 shared connections)
- [Interrupt & Signal Handling](Interrupt_%26_Signal_Handling.md) (2 shared connections)
- [Worker Variant Resolution](Worker_Variant_Resolution.md) (2 shared connections)
- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (1 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (1 shared connections)

## Source Files

- `cli/tests/conftest.py`
- `core/gherkai_core/adapters/subprocess_engine.py`
- `core/tests/conftest.py`
- `core/tests/test_cloud_reconcile.py`
- `core/tests/test_subprocess_engine.py`
- `deploy_aws/tests/test_lambda_handlers.py`
- `deploy_aws/tests/test_provider.py`
- `deploy_aws/tests/test_workers.py`
- `engines/novaact/tests/test_evidence.py`
- `engines/novaact/tests/test_interrupt_model.py`
- `engines/novaact/tests/test_user_steps.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_textui.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 107 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*