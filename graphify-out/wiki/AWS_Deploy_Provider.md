# AWS Deploy Provider

> 29 nodes · cohesion 0.10

## Key Concepts

- **Provider** (95 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.add_arguments()** (8 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._add_worker_subverbs()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **ArgumentParser** (6 connections)
- **._add_container_engine_flag()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._add_locator_flags()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._declares_worker_subverbs()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._is_destroy_parser()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **test_contributed_flag_surface_is_exactly_the_provider_specific_set()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_provider_doctor_reports_toolchain()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_the_two_action_knobs_are_only_on_deploy()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_worker_subverb_surface_is_exactly_three_and_only_on_deploy()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **.delete_worker()** (2 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **test_app_command_uses_current_interpreter_and_module()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_generated_cdk_json_carries_app_and_feature_flags_verbatim()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_provider_name_is_aws()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_yes_is_destroy_only()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **把 provider 特有 flag 挂上 CLI 给的 parser。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **这个 parser 是 **deploy** 的那个吗？ 前端对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字以退出码 2 结束、不静默回落。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **留的口子（ADR 0038「命令族」）：**尚未提供**，以退出码 2 结束并说清为什么与将来怎么落。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- *... and 4 more nodes in this community*

## Relationships

- [Deploy Provider Tests](Deploy_Provider_Tests.md) (43 shared connections)
- [Provider Deploy Commands](Provider_Deploy_Commands.md) (17 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (7 shared connections)
- [Deploy CLI Backend Helpers](Deploy_CLI_Backend_Helpers.md) (7 shared connections)
- [CDK Deploy Argv Tests](CDK_Deploy_Argv_Tests.md) (5 shared connections)
- [AWS Client Stubs](AWS_Client_Stubs.md) (3 shared connections)
- [CDK Destroy Confirmation](CDK_Destroy_Confirmation.md) (2 shared connections)
- [Skill Deploy Token Guardrail](Skill_Deploy_Token_Guardrail.md) (2 shared connections)
- [Container Engine Errors](Container_Engine_Errors.md) (1 shared connections)
- [Container Engine Probe Stub](Container_Engine_Probe_Stub.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 118 (93%)
- INFERRED: 9 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*