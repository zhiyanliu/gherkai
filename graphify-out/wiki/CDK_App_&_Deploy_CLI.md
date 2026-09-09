# CDK App & Deploy CLI

> 40 nodes · cohesion 0.07

## Key Concepts

- **cli.py** (25 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **gherkai_deploy_aws/names.py** (16 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **._guard_vpc_spec()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **app.py** (8 connections) — `deploy_aws/gherkai_deploy_aws/app.py`
- **check_node()** (8 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.bootstrap()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **gherkai_deploy_aws/__init__.py** (7 connections) — `deploy_aws/gherkai_deploy_aws/__init__.py`
- **cdk_command()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_error_code()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_read_stored_vpc_spec()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_stack_exists()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **ssm_vpc_path()** (4 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **main()** (3 connections) — `deploy_aws/gherkai_deploy_aws/app.py`
- **_make_cfn_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_make_ssm_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_make_sts_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_node_major()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **stack_name()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **test_stack_not_found_detection_needs_both_code_and_text()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_cdk_command_prefers_path_cdk_then_npx()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_node_too_old_is_rejected()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_unparseable_node_version_does_not_block()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/app.py`
- **Exception** (1 connections)
- **`gherkai deploy` 的 AWS provider（entry point group `gherkai.deploy` 的 `aws`…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- *... and 15 more nodes in this community*

## Relationships

- [AWS Deploy Provider](AWS_Deploy_Provider.md) (10 shared connections)
- [Provider Deploy Commands](Provider_Deploy_Commands.md) (7 shared connections)
- [Stack Synth Fixtures](Stack_Synth_Fixtures.md) (6 shared connections)
- [SSM Path & Client Composition](SSM_Path_%26_Client_Composition.md) (4 shared connections)
- [Worker Image Management](Worker_Image_Management.md) (3 shared connections)
- [VPC State Classification](VPC_State_Classification.md) (3 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (2 shared connections)
- [Architecture Decision Records](Architecture_Decision_Records.md) (2 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (2 shared connections)
- [Container Worker Push Tests](Container_Worker_Push_Tests.md) (2 shared connections)
- [Runtime Naming Source](Runtime_Naming_Source.md) (2 shared connections)
- [Provider Flag Wiring](Provider_Flag_Wiring.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/__init__.py`
- `deploy_aws/gherkai_deploy_aws/app.py`
- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/gherkai_deploy_aws/names.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 98 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*