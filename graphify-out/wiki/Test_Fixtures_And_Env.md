# Test Fixtures And Env

> 21 nodes · cohesion 0.10

## Key Concepts

- **_fixture()** (41 connections) — `engines/novaact/tests/test_evidence.py`
- **events_table()** (3 connections) — `core/tests/test_cloud_reconcile.py`
- **cloud_env()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_clean_aws_env()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **_presentation_is_environment_independent()** (3 connections) — `deploy_aws/tests/test_workers.py`
- **logs_dir()** (3 connections) — `engines/novaact/tests/test_evidence.py`
- **_isolate()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **fresh_caps_cache()** (3 connections) — `runtime/tests/test_compose.py`
- **_presentation_is_environment_independent()** (3 connections) — `runtime/tests/test_textui.py`
- **_fake_aws_creds()** (3 connections) — `runtime/tests/test_worker_variant.py`
- **_aws_env()** (2 connections) — `deploy_aws/tests/test_workers.py`
- **midscene_env_cmd()** (2 connections) — `runtime/tests/test_compose.py`
- **events 表（PK=pk/SK=seq，同 conftest 的 runs 表不同）——云端后端测试单独建，schema 见 ADR 0033/0024。** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **moto 内存 runs/events 表 + 桶 + 推进器 Lambda 的 env（先盖假凭证、再 mock，绝不连真 AWS）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **把 AWS/前缀相关 env 清干净：解析链会读它们（`compose.resolve_cloud_target`），开发机上的值会让断言飘。** (1 connections) — `deploy_aws/tests/test_provider.py`
- **人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。** (1 connections) — `deploy_aws/tests/test_workers.py`
- **注入产物落点（NOVA_LOGS_DIR），并重置 uploader 单例（no-op 路径：ref 报 file://、不连 AWS）。** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **注册表 snapshot/restore + 清掉本测试塞进 sys.modules 的合成模块（跨文件顺序性假绿/假红的防线）。** (1 connections) — `engines/novaact/tests/test_user_steps.py`
- **每个用例一份空缓存：模块级缓存跨用例泄漏会让「问了几次」的断言与失败情形全部失真。** (1 connections) — `runtime/tests/test_compose.py`
- **人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。** (1 connections) — `runtime/tests/test_textui.py`
- **硬隔离：假凭证 + 固定 region，绝不误连真 AWS（同 core/tests/conftest.py 的套装）。** (1 connections) — `runtime/tests/test_worker_variant.py`

## Relationships

- [Cloud Adapter Test Fixtures](Cloud_Adapter_Test_Fixtures.md) (8 shared connections)
- [Step Evidence Extraction](Step_Evidence_Extraction.md) (5 shared connections)
- [Container Worker Image Tests](Container_Worker_Image_Tests.md) (3 shared connections)
- [CLI Test Fixtures](CLI_Test_Fixtures.md) (2 shared connections)
- [Fake Event Sink](Fake_Event_Sink.md) (2 shared connections)
- [Scenario Evidence Keys](Scenario_Evidence_Keys.md) (2 shared connections)
- [AWS Target Resolution](AWS_Target_Resolution.md) (2 shared connections)
- [Cloud Launcher Reconcile Tests](Cloud_Launcher_Reconcile_Tests.md) (1 shared connections)
- [Lambda Handler Event Parsing Tests](Lambda_Handler_Event_Parsing_Tests.md) (1 shared connections)
- [AWS Deploy Provider Tests](AWS_Deploy_Provider_Tests.md) (1 shared connections)
- [Tool/Return Flag Mapping](Tool-Return_Flag_Mapping.md) (1 shared connections)
- [Moto DynamoDB/S3 Fixtures](Moto_DynamoDB-S3_Fixtures.md) (1 shared connections)

## Source Files

- `core/tests/test_cloud_reconcile.py`
- `deploy_aws/tests/test_lambda_handlers.py`
- `deploy_aws/tests/test_provider.py`
- `deploy_aws/tests/test_workers.py`
- `engines/novaact/tests/test_evidence.py`
- `engines/novaact/tests/test_user_steps.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_textui.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 61 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*