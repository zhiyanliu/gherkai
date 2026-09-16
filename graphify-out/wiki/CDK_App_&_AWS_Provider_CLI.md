# CDK App & AWS Provider CLI

> 41 nodes · cohesion 0.06

## Key Concepts

- **cli.py** (24 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **gherkai_deploy_aws/names.py** (16 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **stack.py** (8 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **synth_fixture.py** (8 connections) — `deploy_aws/tests/synth_fixture.py`
- **gherkai_deploy_aws/__init__.py** (7 connections) — `deploy_aws/gherkai_deploy_aws/__init__.py`
- **app.py** (6 connections) — `deploy_aws/gherkai_deploy_aws/app.py`
- **_error_code()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_read_stored_vpc_spec()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_stack_exists()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **ssm_vpc_path()** (4 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **main()** (3 connections) — `deploy_aws/gherkai_deploy_aws/app.py`
- **_make_cfn_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_make_ssm_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_make_sts_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_node_major()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_vpc_flag()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **ssm_security_groups_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **ssm_subnets_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **ssm_version_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **stack_name()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **test_stack_not_found_detection_needs_both_code_and_text()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/app.py`
- **Exception** (1 connections)
- **`gherkai deploy` 的 AWS provider（entry point group `gherkai.deploy` 的 `aws`…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`--vpc` 的取值校验：`default` / `new` / `vpc-<id>` 三档，**无隐式默认**（ADR 0037 决策 6； 三档与…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- *... and 16 more nodes in this community*

## Relationships

- [VPC State & Deploy Flow](VPC_State_%26_Deploy_Flow.md) (6 shared connections)
- [CDK Toolchain Preflight](CDK_Toolchain_Preflight.md) (5 shared connections)
- [Lambda Asset Build Tests](Lambda_Asset_Build_Tests.md) (5 shared connections)
- [Runtime Composition Root](Runtime_Composition_Root.md) (5 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (4 shared connections)
- [Deploy Provider Tests](Deploy_Provider_Tests.md) (4 shared connections)
- [CDK Stack Synth Tests](CDK_Stack_Synth_Tests.md) (4 shared connections)
- [Worker Image Management](Worker_Image_Management.md) (3 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (2 shared connections)
- [Container Worker Tests](Container_Worker_Tests.md) (2 shared connections)
- [Skill Deploy Token Guardrail](Skill_Deploy_Token_Guardrail.md) (1 shared connections)
- [AWS Deploy Provider](AWS_Deploy_Provider.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/__init__.py`
- `deploy_aws/gherkai_deploy_aws/app.py`
- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/gherkai_deploy_aws/names.py`
- `deploy_aws/gherkai_deploy_aws/stack.py`
- `deploy_aws/tests/synth_fixture.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 92 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*