# CDK App & AWS Provider CLI

> 41 nodes · cohesion 0.06

## Key Concepts

- **cli.py** (25 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **gherkai_deploy_aws/names.py** (18 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **._guard_vpc_spec()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **app.py** (8 connections) — `deploy_aws/gherkai_deploy_aws/app.py`
- **stack.py** (8 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **gherkai_deploy_aws/__init__.py** (7 connections) — `deploy_aws/gherkai_deploy_aws/__init__.py`
- **_read_stored_vpc_spec()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_stack_exists()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_error_code()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
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
- **`--vpc` 的取值校验：`default` / `new` / `vpc-<id>` 三种取值，**无隐式默认**（ADR 0037 决策 6； 三者与…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- *... and 16 more nodes in this community*

## Relationships

- [Deploy Provider & Container Seam](Deploy_Provider_%26_Container_Seam.md) (8 shared connections)
- [Backend CDK Stack Constructs](Backend_CDK_Stack_Constructs.md) (5 shared connections)
- [Deploy Provider Commands](Deploy_Provider_Commands.md) (5 shared connections)
- [CDK Command Execution](CDK_Command_Execution.md) (5 shared connections)
- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (5 shared connections)
- [Worker Image Mapping & Cleanup](Worker_Image_Mapping_%26_Cleanup.md) (3 shared connections)
- [VPC State Classification](VPC_State_Classification.md) (3 shared connections)
- [Lambda Asset Build Tests](Lambda_Asset_Build_Tests.md) (3 shared connections)
- [Cloud Backend Docs & Diagrams](Cloud_Backend_Docs_%26_Diagrams.md) (2 shared connections)
- [Container Engine Port](Container_Engine_Port.md) (2 shared connections)
- [Worker Image Tests](Worker_Image_Tests.md) (2 shared connections)
- [CDK Stack Synthesis Tests](CDK_Stack_Synthesis_Tests.md) (2 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/__init__.py`
- `deploy_aws/gherkai_deploy_aws/app.py`
- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/gherkai_deploy_aws/names.py`
- `deploy_aws/gherkai_deploy_aws/stack.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 98 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*