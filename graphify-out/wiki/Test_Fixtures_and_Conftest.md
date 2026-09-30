# Test Fixtures and Conftest

> 42 nodes · cohesion 0.05

## Key Concepts

- **_fixture()** (40 connections) — `engines/novaact/tests/test_evidence.py`
- **cli/tests/conftest.py** (4 connections) — `cli/tests/conftest.py`
- **_presentation_is_environment_independent()** (3 connections) — `cli/tests/conftest.py`
- **aws()** (3 connections) — `core/tests/conftest.py`
- **_fake_aws_creds()** (3 connections) — `core/tests/conftest.py`
- **fargate()** (3 connections) — `core/tests/conftest.py`
- **real_aws()** (3 connections) — `core/tests/conftest.py`
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
- **_fake_aws_creds()** (3 connections) — `runtime/tests/test_worker_variant.py`
- **_stub_engine_capabilities()** (2 connections) — `cli/tests/conftest.py`
- **_aws_env()** (2 connections) — `deploy_aws/tests/test_workers.py`
- **midscene_env_cmd()** (2 connections) — `runtime/tests/test_compose.py`
- **cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-…** (1 connections) — `cli/tests/conftest.py`
- **人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。** (1 connections) — `cli/tests/conftest.py`
- *... and 17 more nodes in this community*

## Relationships

- [S3 Store Adapters](S3_Store_Adapters.md) (8 shared connections)
- [Step Evidence Records](Step_Evidence_Records.md) (5 shared connections)
- [Worker Image Management Tests](Worker_Image_Management_Tests.md) (3 shared connections)
- [Evidence Upload Tests](Evidence_Upload_Tests.md) (3 shared connections)
- [Cloud Resource Resolution](Cloud_Resource_Resolution.md) (3 shared connections)
- [Interrupt and Signal Handling](Interrupt_and_Signal_Handling.md) (2 shared connections)
- [Worker Variant Resolution](Worker_Variant_Resolution.md) (2 shared connections)
- [Tunnel Host Orchestration](Tunnel_Host_Orchestration.md) (1 shared connections)
- [Cloud Reconcile Tests](Cloud_Reconcile_Tests.md) (1 shared connections)
- [Lambda Handler Tests](Lambda_Handler_Tests.md) (1 shared connections)
- [AWS Deploy Provider](AWS_Deploy_Provider.md) (1 shared connections)
- [Boto Guard and Arg Offload](Boto_Guard_and_Arg_Offload.md) (1 shared connections)

## Source Files

- `cli/tests/conftest.py`
- `core/tests/conftest.py`
- `core/tests/test_cloud_reconcile.py`
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

- EXTRACTED: 81 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*